import asyncio
import json
import uuid
import logging
import sys
import subprocess
import re
import ipaddress
from datetime import datetime, timezone, timedelta
from app.core.date_utils import now as utc_now
from typing import List, Dict, Any, Optional
from scapy.all import ARP, Ether, srp, conf
from app.core.db import get_connection
from app.core.config import get_settings
from app.core.task_logger import log_task_event
import time

if sys.platform == "win32":
    try:
        conf.use_pcap = True
    except:
        pass

logger = logging.getLogger(__name__)

async def resolve_hostname(ip: str) -> Optional[str]:
    try:
        import socket
        def sync_resolve():
            try:
                return socket.gethostbyaddr(ip)[0]
            except:
                return None
        return await asyncio.to_thread(sync_resolve)
    except:
        return None

def get_lookup_ports() -> List[int]:
    """Fetches all unique ports defined in classification rules for lookup."""
    from app.services.classification import get_rules
    rules = get_rules()
    ports = set()
    for r in rules:
        for p in r.get("ports", []):
            ports.add(p)
    # Ensure some basics are always there even if not in rules
    basics = {80, 443, 22, 1883, 53, 5000, 8080, 8123}
    ports.update(basics)
    return sorted(list(ports))

async def scan_ports(ip: str, ports: Optional[List[int]] = None) -> List[Dict[str, Any]]:
    # Dynamic port lookup - only scan ports defined in rules for classification
    if ports is None:
        ports = await asyncio.to_thread(get_lookup_ports)
        
    # Use native asyncio for better performance
    semaphore = asyncio.Semaphore(50) # Allow more concurrency

    async def check_port(p):
        async with semaphore:
            try:
                # 1 second timeout
                fut = asyncio.open_connection(ip, p)
                reader, writer = await asyncio.wait_for(fut, timeout=1.0)
                writer.close()
                await writer.wait_closed()
                
                # Resolve service name 
                COMMON_SERVICES = {
                    6053: "ESPHome API",
                    8123: "Home Assistant",
                    1883: "MQTT",
                    8883: "MQTT (SSL)",
                    5432: "PostgreSQL",
                    3306: "MySQL",
                    6379: "Redis",
                    8006: "Proxmox VE",
                    5000: "Synology DSM",
                    5001: "Synology DSM (SSL)",
                    32400: "Plex Media Server",
                    8096: "Jellyfin",
                    1400: "Sonos",
                    8291: "Winbox (MikroTik)",
                    10001: "Ubiquiti Discovery",
                    8080: "HTTP Proxy/Admin",
                    8443: "HTTPS Proxy/Admin",
                    554: "RTSP (Camera)",
                    8000: "HTTP Alt/Camera",
                    3000: "AdGuard/Grafana",
                    9000: "Portainer",
                    9443: "Portainer (SSL)",
                    53: "DNS",
                    22: "SSH",
                    23: "Telnet",
                    21: "FTP",
                    445: "SMB/CIFS",
                    139: "NetBIOS",
                }

                def get_service():
                    if p in COMMON_SERVICES:
                        return COMMON_SERVICES[p]
                    import socket
                    try: return socket.getservbyport(p)
                    except: return "unknown"
                
                service = await asyncio.to_thread(get_service)
                return {"port": p, "protocol": "tcp", "service": service}
            except (asyncio.TimeoutError, ConnectionRefusedError, OSError):
                return None
            except Exception:
                return None

    results = await asyncio.gather(*(check_port(p) for p in ports))
    return [r for r in results if r]

async def scan_device(device_id: str, ip: str) -> List[Dict[str, Any]]:
    """Deep scan for a specific device."""
    top_ports = list(range(1, 1025))
    found = await scan_ports(ip, top_ports)
    
    def update_db():
        conn = get_connection()
        try:
            conn.execute("UPDATE devices SET open_ports = ?, last_seen = ? WHERE id = ?", [json.dumps(found), utc_now(), device_id])
            conn.execute("DELETE FROM device_ports WHERE device_id = ?", [device_id])
            for p in found:
                conn.execute(
                    "INSERT INTO device_ports (device_id, port, protocol, service, last_seen) VALUES (?, ?, ?, ?, ?)",
                    [device_id, p["port"], p["protocol"], p["service"], utc_now()]
                )
            conn.commit()
        finally:
            conn.close()
    
    await asyncio.to_thread(update_db)
    return found

async def run_scan_job(scan_id: str, target: str, scan_type: str = "arp", options: Optional[Dict[str, Any]] = None):
    job_start = utc_now()
    start_time = time.time()
    
    logger.info(f"Starting scan job {scan_id} for target: {target}")
    log_task_event(
        task_type="scan", 
        event_type="started", 
        message=f"Starting IP scan for target {target}", 
        target=target,
        details={"scan_id": scan_id, "target": target}
    )

    try:
        # 1. Ensure scan status is running with a start time and fetch currently online devices
        def start_scan_and_get_online():
            conn = get_connection()
            try:
                conn.execute("UPDATE scans SET status = 'running', started_at = ?, error_message = NULL WHERE id = ?", [job_start, scan_id])
                online = conn.execute("SELECT ip, mac, id FROM devices WHERE status = 'online'").fetchall()
                conn.commit()
                return [{"ip": r[0], "mac": r[1], "id": r[2]} for r in online]
            finally:
                conn.close()
        
        previously_online = await asyncio.to_thread(start_scan_and_get_online)

        # 2. Perform Network Discovery
        def network_discovery():
            try:
                logger.info(f"Triggering Scapy ARP discovery for {target}...")
                ans, unans = srp(Ether(dst="ff:ff:ff:ff:ff:ff")/ARP(pdst=target), timeout=2, retry=1, verbose=False)
                results = [{"ip": rcve.psrc, "mac": rcve.hwsrc} for sent, rcve in ans]
                logger.info(f"Scapy discovery found {len(results)} raw responses.")
                return results
            except Exception as e:
                err_str = str(e).lower()
                if "winpcap" in err_str or "pcap" in err_str:
                    logger.warning("Scapy Layer 2 discovery restricted: Npcap/WinPcap not found. Switching to Layer 3 Ping Fallback.")
                else:
                    logger.error(f"Scapy scan failed: {e}")
                return []

        async def ping_discovery_fallback(target_str: str) -> List[Dict[str, str]]:
            """Parallel ping sweep for targets when ARP fails/is restricted."""
            try:
                # Handle possible multiple targets
                subnets = target_str.split()
                all_ips = []
                for s in subnets:
                    try:
                        net = ipaddress.ip_network(s, strict=False)
                        all_ips.extend(list(net.hosts()))
                    except:
                        continue
                
                if not all_ips: return []

                logger.info(f"Falling back to Ping Sweep for {len(all_ips)} IPs...")
                
                semaphore = asyncio.Semaphore(100) # Faster sweep
                async def check_ip(ip_obj):
                    async with semaphore:
                        ip_str = str(ip_obj)
                        
                        def sync_ping():
                            try:
                                # Use synchronous subprocess in a thread to avoid event loop issues on Windows
                                cmd = ["ping", "-n", "1", "-w", "500", ip_str] if sys.platform == "win32" else ["ping", "-c", "1", "-W", "1", ip_str]
                                # We only care about return code
                                result = subprocess.run(cmd, capture_output=True, timeout=2)
                                if result.returncode == 0:
                                    # Success - try to get MAC from system ARP cache
                                    mac = get_mac_from_cache(ip_str)
                                    return mac if mac else "unknown"
                                return None
                            except:
                                return None

                        res = await asyncio.to_thread(sync_ping)
                        if res is None:
                            return None # Device didn't respond to ping
                            
                        return {"ip": ip_str, "mac": res}

                results = await asyncio.gather(*(check_ip(ip) for ip in all_ips))
                # Filter out None and deduplicate by IP
                found_map = {}
                for r in results:
                    if r and r["ip"] not in found_map:
                        found_map[r["ip"]] = r
                
                found = list(found_map.values())
                logger.info(f"Ping Sweep found {len(found)} responsive devices.")
                return found
            except Exception as e:
                logger.error(f"Ping sweep failed: {e}", exc_info=True)
                return []

        def get_mac_from_cache(ip: str) -> Optional[str]:
            """Retrieves MAC from system ARP table if available."""
            try:
                cmd = ["arp", "-a", ip]
                output = subprocess.check_output(cmd, stderr=subprocess.STDOUT, timeout=2).decode()
                # Match MAC pattern
                match = re.search(r"(([0-9a-fA-F]{2}[:-]){5}([0-9a-fA-F]{2}))", output)
                if match:
                    return match.group(1).replace('-', ':').lower()
            except:
                pass
            return None

        arp_results = await asyncio.to_thread(network_discovery)
        ping_results = await ping_discovery_fallback(target)
        
        # Merge results - ARP is highest priority for MACs
        found_map = {d["ip"]: d for d in arp_results}
        
        for p in ping_results:
            if p["ip"] not in found_map:
                found_map[p["ip"]] = p
            else:
                # If ARP found it but has a missing mac (unlikely but possible), take it from ping/cache
                if p.get("mac") and p["mac"] != "unknown":
                    found_map[p["ip"]]["mac"] = p["mac"]
        
        unique_devices = list(found_map.values())
        logger.info(f"Discovery phase complete. Scapy: {len(arp_results)}, Ping: {len(ping_results)}. Unique: {len(unique_devices)}")

        # 2.5 Intra-scan Retries for missing devices
        missing_online = [d for d in previously_online if d["ip"] not in found_map and d["mac"] not in [ud.get("mac") for ud in unique_devices if ud.get("mac")]]
        
        if missing_online:
            logger.info(f"Performing intra-scan retries for {len(missing_online)} missing devices...")
            
            async def retry_device(dev):
                ip = dev["ip"]
                mac_target = dev["mac"]
                
                for attempt in range(1, 4): # 3 retries
                    logger.debug(f"Retry {attempt}/3 for {ip}...")
                    # Try ARP first
                    try:
                        ans, _ = srp(Ether(dst="ff:ff:ff:ff:ff:ff")/ARP(pdst=ip), timeout=1.5, verbose=False)
                        if ans:
                            res = {"ip": ans[0][1].psrc, "mac": ans[0][1].hwsrc}
                            logger.info(f"Device {ip} recovered via ARP retry {attempt}")
                            return res
                    except: pass
                    
                    # Try Ping
                    try:
                        cmd = ["ping", "-n", "1", "-w", "800", ip] if sys.platform == "win32" else ["ping", "-c", "1", "-W", "1", ip]
                        result = await asyncio.to_thread(subprocess.run, cmd, capture_output=True, timeout=2)
                        if result.returncode == 0:
                            mac = get_mac_from_cache(ip) or mac_target
                            logger.info(f"Device {ip} recovered via Ping retry {attempt}")
                            return {"ip": ip, "mac": mac}
                    except: pass
                    
                    if attempt < 3:
                        await asyncio.sleep(2) # Wait between retries
                
                return None

            retry_results = await asyncio.gather(*(retry_device(d) for d in missing_online))
            for r in retry_results:
                if r:
                    unique_devices.append(r)
                    found_map[r["ip"]] = r

            logger.info(f"Retries complete. Recovered {len([r for r in retry_results if r])} devices. Final count: {len(unique_devices)}")

        # 3. Parallelize device enrichment
        semaphore = asyncio.Semaphore(4)
        async def process_single_device(device):
            async with semaphore:
                ip, mac = device["ip"], device["mac"]
                hostname = await resolve_hostname(ip)
                # Perform specialized Port Lookup for classification
                ports_list = await scan_ports(ip)
                return {"ip": ip, "mac": mac, "hostname": hostname, "ports_list": ports_list, "result_id": str(uuid.uuid4())}

        processed_results = []
        if unique_devices:
            processed_results = await asyncio.gather(*(process_single_device(d) for d in unique_devices))

        # 4. Save Results
        def save_and_update():
            conn = get_connection()
            try:
                save_now = utc_now()
                for res in processed_results:
                    ip, mac, hostname, ports_list, result_id = res["ip"], res["mac"], res["hostname"], res["ports_list"], res["result_id"]
                    
                    conn.execute(
                        "INSERT INTO scan_results (id, scan_id, ip, mac, hostname, open_ports, first_seen, last_seen) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                        [result_id, scan_id, ip, mac, hostname, json.dumps(ports_list), save_now, save_now]
                    )
                conn.commit()
            finally:
                conn.close()
        
        if processed_results:
            await asyncio.to_thread(save_and_update)
            from app.services.devices import batch_upsert_devices
            batch_data = [{"ip": r["ip"], "mac": r["mac"], "hostname": r["hostname"], "ports": r["ports_list"]} for r in processed_results]
            await batch_upsert_devices(batch_data)

        # 5. Handle Offline state with missing_count threshold
        def finalize_scan():
            conn = get_connection()
            try:
                final_now = utc_now()
                
                # Increment missing_count for online devices not seen in this scan
                conn.execute(
                    "UPDATE devices SET missing_count = missing_count + 1 WHERE status = 'online' AND last_seen < ?",
                    [job_start]
                )
                
                # Reset missing_count for devices that WERE seen (handled by batch_upsert_devices usually, but let's be safe)
                # Actually batch_upsert_devices doesn't know about missing_count yet, so we'll update it there too.
                
                # Identify devices that reached the threshold
                offline_devices = conn.execute(
                    "SELECT id, ip, mac, display_name, vendor, icon FROM devices WHERE status = 'online' AND missing_count >= 3",
                ).fetchall()
                
                for d_id, d_ip, d_mac, d_name, d_vendor, d_icon in offline_devices:
                    conn.execute("UPDATE devices SET status = 'offline' WHERE id = ?", [d_id])
                    conn.execute(
                        "INSERT INTO device_status_history (id, device_id, status, changed_at) VALUES (?, ?, ?, ?)",
                        [str(uuid.uuid4()), d_id, 'offline', final_now]
                    )

                conn.execute("UPDATE scans SET status = 'done', finished_at = ? WHERE id = ?", [final_now, scan_id])
                conn.commit()
                return offline_devices
            finally:
                conn.close()

        offline_list = await asyncio.to_thread(finalize_scan)
        
        # Publish MQTT
        from app.services.devices import publish_device_offline
        for d_id, d_ip, d_mac, d_name, d_vendor, d_icon in offline_list:
             await asyncio.to_thread(publish_device_offline, {
                "id": d_id, "ip": d_ip, "mac": d_mac, "hostname": d_name, "vendor": d_vendor, 
                "icon": d_icon, "status": "offline", "timestamp": utc_now().isoformat()
            })

        duration = int((time.time() - start_time) * 1000)
        logger.info(f"Scan job {scan_id} completed successfully. Found {len(processed_results)} devices.")
        
        log_task_event(
            task_type="scan", 
            event_type="completed", 
            message=f"IP scan completed. Found {len(processed_results)} devices.", 
            target=target,
            duration_ms=duration,
            details={"scan_id": scan_id, "device_count": len(processed_results)}
        )

    except Exception as e:
        logger.error(f"Scan job {scan_id} failed: {e}")
        def fail_scan():
            conn = get_connection()
            try:
                conn.execute("UPDATE scans SET status = 'failed', finished_at = ?, error_message = ? WHERE id = ?", [utc_now(), str(e), scan_id])
                conn.commit()
            finally:
                conn.close()
        await asyncio.to_thread(fail_scan)
        
        
        log_task_event(
            task_type="scan", 
            event_type="failed", 
            message=f"IP scan failed: {str(e)}", 
            target=target,
            level="ERROR",
            details={"scan_id": scan_id, "error": str(e)}
        )
        raise e

async def discover_network_scapy(subnets: List[str]):
    """
    Stand-alone global discovery function used by worker.
    Scans subnets and updates devices in DB.
    """
    from app.services.devices import batch_upsert_devices
    
    all_results = []
    logger.info(f"Running global discovery for: {subnets}")
    
    for subnet in subnets:
        try:
            ans, unans = srp(Ether(dst="ff:ff:ff:ff:ff:ff")/ARP(pdst=subnet), timeout=2, verbose=False)
            for sent, rcve in ans:
                all_results.append({"ip": rcve.psrc, "mac": rcve.hwsrc})
        except Exception as e:
            logger.error(f"Global discovery failed for {subnet}: {e}")
            
    # Deduplicate
    unique_map = {d["ip"]: d for d in all_results}
    unique_devs = list(unique_map.values())
    
    if unique_devs:
        logger.info(f"Global discovery found {len(unique_devs)} devices. Updating DB.")
        # We need to resolve hostnames? For speed in global discovery maybe just basic update
        # But batch_upsert requires 'ports' field?
        
        batch_data = []
        for d in unique_devs:
            batch_data.append({
                "ip": d["ip"],
                "mac": d["mac"],
                "hostname": "unknown", # fast scan, skip hostname for now?
                "ports": [] 
            })
            
        await batch_upsert_devices(batch_data)

