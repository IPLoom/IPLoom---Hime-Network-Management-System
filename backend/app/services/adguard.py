
import logging
import requests
import json
import os
from datetime import datetime, timezone, timedelta
from app.core.config import get_settings
from app.core.db import get_connection, commit
from app.core.dns_db import get_dns_connection, commit_dns
from app.core.task_logger import log_task_event
import time

logger = logging.getLogger(__name__)

class AdguardClient:
    def __init__(self, base_url, username, password):
        self.base_url = base_url.rstrip('/')
        self.username = username
        self.password = password
        self.session = requests.Session()
        if password:
            # Default to 'admin' if username is missing but password is provided
            self.session.auth = (username or "admin", password)

    def test_connection(self):
        """Check if Adguard is reachable and auth works"""
        try:
            # Use /control/status to verify we can actually read data (requires auth)
            resp = self.session.get(f"{self.base_url}/control/status", timeout=5)
            resp.raise_for_status()
            return True
        except requests.exceptions.HTTPError as e:
            logger.error(f"Adguard connection failed: {e}. Response: {e.response.text}")
            raise Exception(f"HTTP Error {e.response.status_code}: {e.response.text}")
        except Exception as e:
            logger.error(f"Adguard connection failed: {e}")
            raise e

    def get_query_log(self):
        """Fetch recent query logs"""
        # Adguard API: /control/querylog
        # We fetch the latest batch. We might need pagination if volume is huge, 
        # but for now let's grab the default or a reasonable limit.
        try:
            # Fetch generic stats for overview
            stats_resp = self.session.get(f"{self.base_url}/control/stats", timeout=10)
            stats = stats_resp.json() if stats_resp.ok else {}

            # Fetch detailed query log
            # params: limit (default 50), older_than (cursor)
            # We want to fetch everything since last sync ideally. 
            # But the API uses 'older_than' (pagination backwards). 
            # So we fetch the LATEST X entries and filter by time > last_sync.
            resp = self.session.get(f"{self.base_url}/control/querylog?limit=1000", timeout=10)
            resp.raise_for_status()
            return {"stats": stats, "logs": resp.json().get("data", [])}
        except Exception as e:
            logger.error(f"Failed to fetch Adguard data: {e}")
            raise e

    def sync(self, force: bool = False):
        """Fetch data and update both DNS DB and Main DB
        :param force: Force sync even if not enabled
        :return: True if successful
        """
        logger.info("Starting Adguard sync...")
        log_task_event(
            task_type="adguard_sync", 
            event_type="started", 
            message="Starting AdGuard sync", 
            target="adguard"
        )
        
        start_time = time.time()
        total_queries = 0 # Initialize total_queries

        conn_main = get_connection()
        try:
            # 1. Get Configuration & Last Sync Time
            row = conn_main.execute("SELECT config FROM integrations WHERE name = 'adguard'").fetchone()
            if not row:
                logger.warning("Adguard integration not configured (no DB entry).")
                log_task_event(
                    task_type="adguard_sync", 
                    event_type="skipped", 
                    message="AdGuard integration not configured.", 
                    target="adguard",
                    level="WARNING"
                )
                return False

            config = json.loads(row[0])
            
            # Check if enabled
            if not force and not config.get("enabled", False):
                logger.info("Adguard sync skipped: integration not enabled.")
                log_task_event(
                    task_type="adguard_sync", 
                    event_type="skipped", 
                    message="AdGuard sync skipped: integration not enabled.", 
                    target="adguard"
                )
                return False

            last_sync_str = config.get("last_sync")
            last_sync_ts = 0
            if last_sync_str:
                try:
                    last_sync_ts = datetime.fromisoformat(last_sync_str).timestamp()
                except:
                    pass
            
            # 2. Fetch Data
            try:
                data = self.get_query_log()
                logs = data["logs"]
                # Sort by time asc (API returns desc usually)
                logs.reverse() 
            except Exception as e:
                raise e # Propagate to worker
            
            # 3. Process Logs -> DNS DB
            conn_dns = get_dns_connection()
            new_last_sync_ts = last_sync_ts
            processed_count = 0
            
            # Pre-fetch devices for mapping (IP, Name, Display Name)
            device_map = {} # identifier -> device_id
            dev_rows = conn_main.execute("SELECT id, ip, name, display_name FROM devices").fetchall()
            for r in dev_rows:
                did, ip, name, display_name = r
                if ip: device_map[ip.lower()] = did
                if name: device_map[name.lower()] = did
                if display_name: device_map[display_name.lower()] = did
            
            # Cache for domain IDs to avoid DB hammered lookups
            domain_cache = {} 
            
            processed_device_stats = {} # device_id -> {queries: 0, blocked: 0}

            try:
                for item in logs:
                    # item format: { "time": "2023-...", "question": { "name": "..." }, "client": "1.2.3.4", "status": "FilteredBlackList", "elapsedMs": "..." }
                    ts_str = item.get("time")
                    # Parse timestamp (Adguard usually returns ISO 8601)
                    # Python 3.11+ supports fromisoformat("2023-10-10T10:10:10.123Z") usually
                    # If simplified parsing needed:
                    try:
                        ts = datetime.fromisoformat(ts_str.replace('Z', '+00:00'))
                    except:
                        continue
                        
                    if ts.timestamp() <= last_sync_ts:
                        continue # Already processed
                    
                    if ts.timestamp() > new_last_sync_ts:
                        new_last_sync_ts = ts.timestamp()

                    # Extract Data
                    domain = item.get("question", {}).get("name", "").lower()
                    if not domain: continue
                    
                    client_ip = item.get("client")
                    status = item.get("status", "OK") 
                    reason = item.get("reason", "")
                    query_type = item.get("question", {}).get("type", "A") # e.g. 'A', 'AAAA', 'PTR'
                    
                    # Broaden blocked check:
                    # 1. Standard statuses
                    # 2. 'Filtered' status generic
                    # 3. Presence of filterId/rule if status is ambiguous (AdGuard versions vary)
                    is_blocked = (
                        status in ["FilteredBlackList", "SafeBrowsing", "ParentalControl", "Blocked"] or
                        (status.startswith("Filtered") and status != "FilteredSafeSearch") or
                        (bool(item.get("filterId")) and "Filtered" in status)
                    )
                    elapsed = item.get("elapsedMs", 0)
                    
                    category = item.get("reason", "") # sometimes reason gives list name
                    
                    # Resolve Domain ID
                    if domain not in domain_cache:
                        # Upsert Domain
                        # DuckDB doesn't have ON CONFLICT DO UPDATE for all cases easily in Python client sometimes, but INSERT OR IGNORE works or standard check.
                        # We use a check-insert pattern or INSERT OR IGNORE
                        
                        # 1. Check exist
                        d_row = conn_dns.execute("SELECT id FROM dns_domains WHERE domain = ?", [domain]).fetchone()
                        if d_row:
                            d_id = d_row[0]
                            # Update status (blind update last_seen)
                            conn_dns.execute("UPDATE dns_domains SET last_seen = ?, is_blocked = ? WHERE id = ?", [ts, is_blocked, d_id])
                        else:
                            # Insert
                            conn_dns.execute("INSERT INTO dns_domains (domain, category, is_blocked, last_seen) VALUES (?, ?, ?, ?) RETURNING id", 
                                           [domain, category, is_blocked, ts])
                            d_id = conn_dns.fetchone()[0]
                        domain_cache[domain] = d_id
                    else:
                        d_id = domain_cache[domain]
                    
                    # Resolve Device ID
                    device_id = device_map.get(client_ip.lower() if client_ip else "")
                    if not device_id:
                        logger.debug(f"DNS Sync: Could not map client '{client_ip}' to device ID. Map has {len(device_map)} devices.")
                    else:
                        logger.debug(f"DNS Sync: Mapped '{client_ip}' to device '{device_id}'")
                    
                    # Insert Log
                    conn_dns.execute("""
                        INSERT INTO dns_logs (timestamp, device_id, domain_id, status, query_type, client_ip, response_time, is_blocked)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    """, [ts, device_id, d_id, status, query_type, client_ip, elapsed, is_blocked])
                    
                    processed_count += 1
                    total_queries += 1 # Increment total queries
                    
                    # Aggregation stats
                    if device_id:
                        if device_id not in processed_device_stats:
                            processed_device_stats[device_id] = {"queries": 0, "blocked": 0}
                        processed_device_stats[device_id]["queries"] += 1
                        if is_blocked:
                            processed_device_stats[device_id]["blocked"] += 1

                commit_dns()
                logger.info(f"Adguard Sync: {processed_count} new entries.")

            except Exception as e:
                logger.error(f"Error during DNS DB operations: {e}")
                pass # Don't crash, try to save what we can?

            # 4. Update Main DB Stats (Devices)
            # We want "24h stats". 
            # Current approach: The 'processed_device_stats' is just the delta since last sync.
            # Real 24h stats need a query on dns_logs.duckdb.
            # Doing a big aggregate query on dns_logs every sync might be heavy?
            # Let's do it efficiently: Query DNS DB for 24h stats GROUP BY device_id
            
            try:
                logger.info("Calculating 24h stats...")
                one_day_ago = datetime.now(timezone.utc) - timedelta(days=1)
                
                stats_rows = conn_dns.execute("""
                    SELECT 
                        device_id, 
                        COUNT(*) as total, 
                        COUNT(CASE WHEN status IN ('FilteredBlackList', 'SafeBrowsing', 'ParentalControl') THEN 1 END) as blocked,
                        arg_max(timestamp, timestamp) as last_activity
                    FROM dns_logs 
                    WHERE timestamp > ? AND device_id IS NOT NULL
                    GROUP BY device_id
                """, [one_day_ago]).fetchall()
                
                # Update devices table
                for r in stats_rows:
                    dev_id, total, blocked, last_act = r
                    
                    stats_json = json.dumps({
                        "queries_24h": total,
                        "blocked_24h": blocked,
                        "last_activity": last_act.isoformat() if last_act else None
                    })
                    
                    conn_main.execute("UPDATE devices SET dns_stats = ? WHERE id = ?", [stats_json, dev_id])
                
                # 4. Update Main DB Cursor (last_sync)
                config["last_sync"] = datetime.fromtimestamp(new_last_sync_ts, tz=timezone.utc).isoformat()
                conn_main.execute("UPDATE integrations SET config = ? WHERE name = 'adguard'", [json.dumps(config)])
                
                commit(conn_main)
                
                commit_dns()
                
                # 5. Retention Cleanup (Keep 7 days by default)
                # Ideally config driven, but 7 days is reasonable for deep logs.
                try:
                    cleanup_cutoff = datetime.now(timezone.utc) - timedelta(days=7)
                    conn_dns.execute("DELETE FROM dns_logs WHERE timestamp < ?", [cleanup_cutoff])
                    # Optional: compact if needed, but auto-checkpoint usually handles WAL
                    commit_dns()
                except Exception as e:
                    logger.error(f"Error during retention cleanup: {e}")
                
            except Exception as e:
                logger.error(f"Error updating main DB stats: {e}")

            duration = int((time.time() - start_time) * 1000)
            logger.info("Adguard sync completed successfully")
            
            log_task_event(
                task_type="adguard_sync", 
                event_type="completed", 
                message=f"AdGuard sync completed. Processed {total_queries} queries.", 
                target="adguard",
                duration_ms=duration,
                details={"query_count": total_queries}
            )
            
            return True

        except Exception as e:
            logger.error(f"Failed to fetch Adguard data: {e}")
            
            log_task_event(
                task_type="adguard_sync", 
                event_type="failed", 
                message=f"AdGuard sync failed: {str(e)}", 
                target="adguard",
                level="ERROR",
                details={"error": str(e)}
            )
            
            raise e
        finally:
            conn_main.close()
            # conn_dns closed? No, we use shared connection but we should probably leave it open or handle properly.
            # The get_dns_connection uses shared, so we don't 'close' it per se, just release cursor? 
            # The helper doesn't really close valid cursors but that's fine for duckdb.

