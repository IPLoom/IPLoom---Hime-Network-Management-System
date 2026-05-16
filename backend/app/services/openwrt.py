
import logging
import requests
import json
import os
import re
from base64 import b64encode
from datetime import datetime, timezone
from app.core.date_utils import now as utc_now, parse_iso_utc
from app.core.config import get_settings
from app.core.db import get_connection
from app.core.task_logger import log_task_event
import time

logger = logging.getLogger(__name__)

class OpenWRTClient:
    def __init__(self, base_url, username, password=None):
        self.base_url = base_url.rstrip('/')
        self.username = username
        self.password = password
        self.token = None
        self.session = requests.Session()

        # No longer using local config file, state is in DB

    def login(self):
        """Authenticate with OpenWRT via ubus session login"""
        if self.token:
            return

        payload = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "call",
            "params": [
                "00000000000000000000000000000000",
                "session",
                "login",
                {
                    "username": self.username,
                    "password": self.password or ""
                }
            ]
        }
        
        try:
            resp = self.session.post(f"{self.base_url}/ubus", json=payload, timeout=10)
            data = resp.json()
            
            if "result" in data and isinstance(data["result"], list) and len(data["result"]) > 1:
                status, session_data = data["result"]
                if status == 0 and isinstance(session_data, dict) and "ubus_rpc_session" in session_data:
                    self.token = session_data["ubus_rpc_session"]
                    logger.info("OpenWRT Login successful")
                    return
            
            logger.error(f"OpenWRT login failed. Response: {data}")
            raise Exception("Login failed: Invalid credentials or response format")
            
        except Exception as e:
            logger.error(f"Failed to connect to OpenWRT: {e}")
            raise e

    def _call(self, object, method, params=None, optional=False):
        """Invoke a ubus method with standard error handling and retries"""
        if not self.token:
            self.login()
        
        payload = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "call",
            "params": [
                self.token,
                object,
                method,
                params or {}
            ]
        }
        
        try:
            resp = self.session.post(f"{self.base_url}/ubus", json=payload, timeout=10)
            data = resp.json()
            
            if "result" in data and isinstance(data["result"], list):
                status = data["result"][0]
                
                if status == 0:
                    if len(data["result"]) > 1:
                        return data["result"][1]
                    return [] 
                
                if status == 6: # Permission denied / Session expired
                    logger.warning(f"OpenWRT Permission Denied (6) for {object}.{method}. Retrying login...")
                    self.token = None
                    self.login()
                    
                    payload["params"][0] = self.token
                    resp = self.session.post(f"{self.base_url}/ubus", json=payload, timeout=10)
                    data = resp.json()
                    
                    if data and "result" in data and isinstance(data["result"], list) and data["result"][0] == 0:
                        return data["result"][1] if len(data["result"]) > 1 else []
                
                if not optional:
                    logger.error(f"OpenWRT RPC Error {status} for {object}.{method}")
                return [] if optional else None

            if "error" in data:
                logger.error(f"OpenWRT JSON-RPC Error: {data['error']}")
                return [] if optional else None
                
            return [] if optional else None
            
        except Exception as e:
            logger.error(f"OpenWRT Call Exception ({object}.{method}): {e}")
            return [] if optional else None

    def get_dhcp_leases(self):
        """Get DHCP leases using luci-rpc.getDHCPLeases"""
        res = self._call("luci-rpc", "getDHCPLeases", optional=True)
        
        leases = []
        if isinstance(res, dict) and "dhcp_leases" in res:
            for item in res["dhcp_leases"]:
                leases.append({
                    "ip": item.get("ipaddr"),
                    "mac": item.get("macaddr"),
                    "hostname": item.get("hostname", "*"),
                    "expires": item.get("expires", 0)
                })
        return leases

    def get_wireless_devices(self):
        """Get wireless associations using luci-rpc.getWirelessDevices"""
        res = self._call("luci-rpc", "getWirelessDevices", optional=True)
        
        associations = {}
        if isinstance(res, dict):
            for interface, data in res.items():
                if not isinstance(data, dict): continue
                
                # Infer band from frequency or interface name
                freq = str(data.get("frequency", "")).lower()
                band = "2.4GHz" if "2.4" in freq else ("5GHz" if "5" in freq or "6" in freq else "Unknown")
                ssid = data.get("ssid", "Unknown")
                
                assoc_list = data.get("associations", [])
                for assoc in assoc_list:
                    mac = assoc.get("mac", "").lower()
                    if mac:
                        associations[mac] = {
                            "rssi": assoc.get("signal"),
                            "noise": assoc.get("noise"),
                            "rx_rate": assoc.get("rx_rate"),
                            "tx_rate": assoc.get("tx_rate"),
                            "band": band,
                            "ssid": ssid,
                            "interface": interface
                        }
        return associations

    def get_traffic_stats(self):
        """Get traffic data and calculate deltas using /usr/sbin/nlbw"""
        stats = {}
        
        res = self._call("file", "exec", {
            "command": "/usr/sbin/nlbw", 
            "params": ["-c", "json", "-g", "mac,fam", "-o", "conn"]
        }, optional=True)
        
        if isinstance(res, dict) and "stdout" in res:
            try:
                data = json.loads(res["stdout"])
                rows = data.get("data", [])
                for row in rows:
                    if len(row) >= 6: 
                        mac = row[1].lower()
                        if not mac or mac == "00:00:00:00:00:00": continue
                        
                        rx = int(row[3]) 
                        tx = int(row[5]) 
                        
                        if mac not in stats:
                            stats[mac] = {"down": 0, "up": 0}
                        stats[mac]["down"] += rx
                        stats[mac]["up"] += tx
            except Exception as e:
                logger.error(f"Failed to calculate traffic stats: {e}")

        traffic_data = self._calculate_deltas(stats)
        return traffic_data

    def _calculate_deltas(self, current_stats):
        """Calculates usage since last sync using a local cache file"""
        cache_file = "data/openwrt_stats.json"
        prev_stats = {}
        
        if os.path.exists(cache_file):
            try:
                with open(cache_file, 'r') as f:
                    prev_stats = json.load(f)
            except:
                pass
        
        deltas = {}
        for mac, curr in current_stats.items():
            if mac not in prev_stats:
                # First time seeing this device (or cache lost). 
                # value is cumulative, so we can't determine usage since last sync.
                # Treat as 0 delta to avoid massive spikes (e.g. 60GB) being logged.
                deltas[mac] = {"down": 0, "up": 0}
                continue

            prev = prev_stats[mac]
            
            # Normal case: Calculate diff
            # Handle restart (curr < prev): assume curr is all new traffic (reset)
            down_delta = curr["down"] - prev["down"] if curr["down"] >= prev["down"] else curr["down"]
            up_delta = curr["up"] - prev["up"] if curr["up"] >= prev["up"] else curr["up"]
            
            deltas[mac] = {"down": down_delta, "up": up_delta}
        
        try:
             os.makedirs("data", exist_ok=True)
             with open(cache_file, 'w') as f:
                 json.dump(current_stats, f)
        except:
             pass
             
        return {"deltas": deltas, "totals": current_stats}

    def sync(self, force: bool = False):
        """Pull data and update DB: DHCP Leases = Dynamic, Others = Static"""
        os.makedirs("data", exist_ok=True) # Ensure data directory exists for config file



        logger.info("Starting OpenWRT Sync...")
        log_task_event(
            task_type="openwrt_sync", 
            event_type="started", 
            message="Starting OpenWRT sync", 
            target="openwrt"
        )
        
        start_time = time.time()

        try:
            self.login()
            
            leases = self.get_dhcp_leases()
            wireless_assoc = self.get_wireless_devices()
            traffic_data = self.get_traffic_stats()
            traffic_deltas = traffic_data["deltas"]
            traffic_totals = traffic_data["totals"]
            
            conn = get_connection()
            try:
                updated_count = 0
                
                # 1. Build a map of current DHCP leases
                dhcp_map = {} # mac -> lease
                for l in leases:
                    if l.get("mac"):
                        dhcp_map[l["mac"].lower()] = l

                # 2. Get set of ALL MACs involved (Traffic + DHCP + Wireless)
                all_macs = set(dhcp_map.keys())
                all_macs.update(traffic_totals.keys())
                all_macs.update(wireless_assoc.keys())

                for mac in all_macs:
                    mac = mac.lower()
                    lease = dhcp_map.get(mac)
                    
                    t_delta = traffic_deltas.get(mac, {"down": 0, "up": 0})
                    t_total = traffic_totals.get(mac, {"down": 0, "up": 0})
                    
                    # Skip if no useful data (no lease and no traffic)
                    if not lease and t_total["down"] == 0 and t_total["up"] == 0:
                        continue

                    row = conn.execute("SELECT id, name, display_name, icon, attributes, ip, ip_type, mac FROM devices WHERE mac = ?", [mac]).fetchone()
                    if not row:
                        row = conn.execute("SELECT id, name, display_name, icon, attributes, ip, ip_type, mac FROM devices WHERE id = ?", [mac]).fetchone()
                    
                    # Fallback: if scanner found it but couldn't get MAC, try mapping by IP
                    if not row and lease and lease.get("ip"):
                        row = conn.execute("SELECT id, name, display_name, icon, attributes, ip, ip_type, mac FROM devices WHERE ip = ?", [lease["ip"]]).fetchone()

                    
                    if row:
                        target_id = row[0]
                        existing_name = row[1]
                        existing_icon = row[3]
                        try:
                            attrs = json.loads(row[4]) if row[4] else {}
                        except:
                            attrs = {}
                        existing_ip = row[5]
                        existing_ip_type = row[6]
                        existing_mac = row[7]
                    else:
                        # If device not in DB, and has no lease, we skip (scanner hasn't found it yet)
                        # We only create/update if we have a known ID or if we get a lease giving us an IP
                        if not lease:
                            continue
                            
                        target_id = mac
                        existing_name = None
                        existing_icon = None
                        attrs = {}
                        existing_ip = None
                        existing_ip_type = 'dynamic'

                    # Determine IP and IP Type
                    if lease:
                        ip = lease["ip"]
                        # Prioritize lease IP if different, but if we don't update IP in devices, we just use it for record?
                        # Wait, we DO update attributes. We should probably respect Lease IP for Dynamic devices.
                        # But user said only scanner updates status. Did user imply only scanner updates IP too?
                        # Probably. But if it's dynamic, OpenWRT is the source of truth for IP assignment.
                        # "OpenART intergation will only set ip_type." => User said ONLY ip_type.
                        # So we will NOT update IP in devices table. We will just use the lease IP for our internal logic if needed.
                        ip_type = "dynamic"
                        hostname = lease["hostname"] if lease["hostname"] and lease["hostname"] != "*" else None
                        attrs["dhcp_expires"] = lease["expires"]
                        if hostname: attrs["dhcp_hostname"] = hostname
                    else:
                        # Static / No Lease - use existing DB info
                        ip = existing_ip
                        ip_type = "static" 
                        hostname = None

                    # Use lease hostname if available
                    name = existing_name or hostname or f"Device-{mac[-5:]}"
                    
                    attrs["last_sync"] = "openwrt"
                    
                    # Add Wireless Details
                    wlan = wireless_assoc.get(mac)
                    if wlan:
                        attrs["wlan_rssi"] = wlan["rssi"]
                        attrs["wlan_band"] = wlan["band"]
                        attrs["wlan_ssid"] = wlan["ssid"]
                        attrs["wlan_rx_rate"] = wlan["rx_rate"]
                        attrs["wlan_tx_rate"] = wlan["tx_rate"]
                        # Also flag as wireless
                        attrs["connection_type"] = "wireless"
                    elif lease:
                        # If in DHCP but not in wireless associations, it might be wired
                        # (Or it's just not currently active in association table)
                        attrs["connection_type"] = "wired"
                    
                    # Insert into history (Always record traffic if available)
                    if t_total["down"] > 0 or t_total["up"] > 0:
                        import uuid
                        hist_id = str(uuid.uuid4())
                        try:
                            conn.execute("""
                                INSERT INTO device_traffic_history 
                                (id, device_id, rx_bytes, tx_bytes, down_rate, up_rate) 
                                VALUES (?, ?, ?, ?, ?, ?)
                            """, [hist_id, target_id, t_total["down"], t_total["up"], t_delta["down"], t_delta["up"]])
                            
                            # Increment Quota Usage if defined
                            delta_total = t_delta["down"] + t_delta["up"]
                            if delta_total > 0:
                                conn.execute("""
                                    UPDATE device_quotas 
                                    SET current_usage = current_usage + ? 
                                    WHERE device_id = ? AND enabled = TRUE
                                """, [delta_total, target_id])
                        except Exception as e:
                             logger.error(f"Failed to insert traffic history or update quota for {mac}: {e}")

                    # Update Device Table
                    if row:
                        # Update existing - update mac if missing, ip_type, and attributes
                        try:
                             conn.execute("""
                                UPDATE devices SET
                                    mac = COALESCE(mac, ?),
                                    ip_type = ?,
                                    attributes = ?
                                WHERE id = ?
                            """, [mac, ip_type, json.dumps(attrs), target_id])
                             updated_count += 1
                        except Exception as e:
                            logger.error(f"Failed to update device {mac}: {e}")
                    # else:
                        # User requested to IGNORE unknown devices. 
                        # Only the network scanner creates devices.
                        # pass
                
                conn.commit()
                logger.info(f"OpenWRT Sync complete: {updated_count} devices processed.")
                
            finally:
                conn.close()
            
            # Update last_sync and last_run in DB
            try:
                # Read current config from DB
                conn_main = get_connection()
                try:
                    row = conn_main.execute("SELECT config FROM integrations WHERE name = 'openwrt'").fetchone()
                    if row:
                        current_config = json.loads(row[0])
                        current_config["last_sync"] = utc_now().isoformat()
                        current_config["last_run"] = utc_now().isoformat()
                        conn_main.execute("UPDATE integrations SET config = ? WHERE name = 'openwrt'", [json.dumps(current_config)])
                        from app.core.db import commit
                        commit()
                finally:
                    conn_main.close()
            except Exception as e:
                logger.error(f"Failed to update OpenWRT timestamps in DB: {e}")

            duration = int((time.time() - start_time) * 1000)
            logger.info(f"OpenWRT Sync complete: {len(leases)} leases processed.")
            
            log_task_event(
                task_type="openwrt_sync", 
                event_type="completed", 
                message=f"OpenWRT sync completed. Processed {len(leases)} leases.", 
                target="openwrt",
                duration_ms=duration,
                details={"leases_count": len(leases), "updated_devices": updated_count}
            )
            
            return True
                
        except Exception as e:
            logger.error(f"OpenWRT Sync Failed: {e}", exc_info=True)
            
            log_task_event(
                task_type="openwrt_sync", 
                event_type="failed", 
                message=f"OpenWRT sync failed: {str(e)}", 
                target="openwrt",
                level="ERROR",
                details={"error": str(e)}
            )
            
            raise e

    def block_device(self, mac: str):
        """Block a device by MAC address using OpenWrt firewall (uci)."""
        logger.info(f"OpenWRT: Blocking device {mac}")
        mac = mac.lower()
        sanitized_mac = mac.replace(':', '')
        rule_name = f"block_{sanitized_mac}"
        
        # Create the section if it doesn't exist
        self._call("uci", "add", {
            "config": "firewall",
            "type": "rule",
            "name": rule_name
        }, optional=True)
        
        # Update the named firewall rule section
        # Using DROP and ensuring both IPv4/IPv6 coverage
        self._call("uci", "set", {
            "config": "firewall",
            "type": "rule",
            "section": rule_name,
            "values": {
                "name": f"IPLoom_Block_{sanitized_mac}",
                "src": "lan",
                "dest": "wan",
                "src_mac": mac,
                "target": "DROP",
                "enabled": "1"
            }
        }, optional=False)
        
        # Commit the changes
        self._call("uci", "commit", {"config": "firewall"}, optional=False)
        
        # Move rule to top of the list to ensure it overrides 'Allow Established' logic
        self._call("file", "exec", {
            "command": "/sbin/uci",
            "params": ["insert", f"firewall.{rule_name}=0"]
        }, optional=True)
        self._call("uci", "commit", {"config": "firewall"}, optional=True)

        # Reload firewall for immediate effect on new connections
        # We use reload instead of apply to be more aggressive with ruleset rebuild
        self._call("file", "exec", {
            "command": "/etc/init.d/firewall",
            "params": ["reload"]
        }, optional=True)

        # CRITICAL: Flush established connections for this device
        # Otherwise streaming/existing sessions continue until timeout
        try:
            leases = self.get_dhcp_leases()
            ip = next((l["ip"] for l in leases if l["mac"].lower() == mac.lower()), None)
            if ip:
                logger.info(f"OpenWRT: Flushing conntrack for IP {ip}")
                # Clear all states where this IP is source or destination
                self._call("file", "exec", {
                    "command": "/usr/sbin/conntrack",
                    "params": ["-D", "-s", ip]
                }, optional=True)
                self._call("file", "exec", {
                    "command": "/usr/sbin/conntrack",
                    "params": ["-D", "-d", ip]
                }, optional=True)
        except Exception as e:
            logger.warning(f"Could not flush conntrack for {mac}: {e}")
        
        return True

    def unblock_device(self, mac: str):
        """Unblock a device by MAC address using OpenWrt firewall (uci)."""
        logger.info(f"OpenWRT: Unblocking device {mac}")
        mac = mac.lower()
        sanitized_mac = mac.replace(':', '')
        rule_name = f"block_{sanitized_mac}"
        
        # Delete the section
        res = self._call("uci", "delete", {
            "config": "firewall",
            "section": rule_name
        }, optional=True)
        
        # Commit the changes
        self._call("uci", "commit", {"config": "firewall"}, optional=True)
        
        # Reload firewall
        self._call("file", "exec", {
            "command": "/etc/init.d/firewall",
            "params": ["reload"]
        }, optional=True)
        
        return res

