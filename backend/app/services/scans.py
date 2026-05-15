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
from .scanners import ARPScanner, PingScanner, MDNSScanner, AuditScanner, HTTPFingerprinter
from app.core.db import get_connection
from app.core.config import get_settings
from app.core.task_logger import log_task_event
import time

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
    """Deep scan and fingerprinting for a specific device."""
    log_task_event(
        task_type="audit", 
        event_type="started", 
        message=f"Starting deep security audit and fingerprinting for {ip}", 
        target=device_id
    )
    
    # 1. Audit Scan (Nmap/Socket)
    audit_scanner = AuditScanner()
    audit_results = await audit_scanner.scan(ip)
    found = audit_results[0]["ports"] if audit_results else []
    open_port_ids = [p["port"] for p in found]

    # 2. HTTP Fingerprinting
    fingerprinter = HTTPFingerprinter()
    page_info = await fingerprinter.scan(ip, ports=open_port_ids)
    primary_page = page_info[0] if page_info else {}
    
    # 3. Enhanced Classification
    from app.services.classification import classify_device, get_vendor_locally
    
    # Get current device info for classification
    def get_dev_info():
        conn = get_connection()
        try:
            return conn.execute("SELECT display_name, mac, vendor FROM devices WHERE id = ?", [device_id]).fetchone()
        finally:
            conn.close()
            
    dev_row = await asyncio.to_thread(get_dev_info)
    hostname = dev_row[0] if dev_row else None
    mac = dev_row[1] if dev_row else None
    vendor = dev_row[2] if dev_row else None
    
    classification = classify_device(
        hostname=hostname,
        vendor=vendor,
        ports=open_port_ids,
        page_title=primary_page.get("title")
    )
    
    def update_db():
        conn = get_connection()
        try:
            # Update device with new classification and ports
            conn.execute("""
                UPDATE devices 
                SET open_ports = ?, 
                    last_seen = ?, 
                    device_type = ?, 
                    icon = ?, 
                    brand = ?, 
                    brand_icon = ?
                WHERE id = ?
            """, [
                json.dumps(found), 
                utc_now(), 
                classification["type"], 
                classification["icon"],
                classification.get("brand"),
                classification.get("brand_icon"),
                device_id
            ])
            
            # Update port history
            conn.execute("DELETE FROM device_ports WHERE device_id = ?", [device_id])
            for p in found:
                conn.execute(
                    "INSERT INTO device_ports (device_id, port, protocol, service, last_seen, banner) VALUES (?, ?, ?, ?, ?, ?)",
                    [device_id, p["port"], p["protocol"], p["service"], utc_now(), p.get("version", "")]
                )
            conn.commit()
        finally:
            conn.close()
    
    await asyncio.to_thread(update_db)
    
    log_task_event(
        task_type="audit", 
        event_type="completed", 
        message=f"Deep audit complete for {ip}. Identified as {classification['type']} ({classification.get('brand', 'Generic')}).", 
        target=device_id,
        details={"open_ports": len(found), "brand": classification.get("brand")}
    )
    return found

async def run_scan_job(scan_id: str, target: str, scan_type: str = "arp", options: Optional[Dict[str, Any]] = None):
    job_start = utc_now()
    start_time = time.time()
    
    logger.info(f"Starting modular scan job {scan_id} for target: {target}")
    log_task_event(
        task_type="scan", 
        event_type="started", 
        message=f"Starting network discovery for {target}", 
        target=target,
        details={"scan_id": scan_id}
    )

    try:
        # 1. Setup Status
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

        # 2. Network Discovery Suite
        arp_scanner = ARPScanner()
        ping_scanner = PingScanner()
        mdns_scanner = MDNSScanner()

        # Run discovery in parallel
        arp_task = arp_scanner.scan(target)
        ping_task = ping_scanner.scan(target)
        mdns_task = mdns_scanner.scan() # MDNS scans the whole local segment

        arp_results, ping_results, mdns_results = await asyncio.gather(arp_task, ping_task, mdns_task)
        
        # Merge results (IP as key)
        found_map = {d["ip"]: d for d in arp_results}
        
        for p in ping_results:
            if p["ip"] not in found_map:
                found_map[p["ip"]] = p
            elif p.get("mac") and p["mac"] != "unknown" and found_map[p["ip"]].get("mac") == "unknown":
                found_map[p["ip"]]["mac"] = p["mac"]

        # Merge MDNS (enrich hostname and metadata)
        for m in mdns_results:
            if m["ip"] in found_map:
                # Prioritize MDNS hostname if discovered
                found_map[m["ip"]]["hostname"] = m["hostname"]
                found_map[m["ip"]]["mdns_props"] = m["properties"]

        unique_devices = list(found_map.values())
        logger.info(f"Discovery complete. ARP: {len(arp_results)}, Ping: {len(ping_results)}, MDNS: {len(mdns_results)}. Unique: {len(unique_devices)}")

        # 3. Intra-scan Retries for missing devices (Layer 2 + Layer 3)
        missing_online = [d for d in previously_online if d["ip"] not in found_map and d["mac"] not in [ud.get("mac") for ud in unique_devices if ud.get("mac")]]
        
        if missing_online:
            logger.info(f"Performing modular retries for {len(missing_online)} missing devices...")
            async def retry_device(dev):
                ip = dev["ip"]
                # Try ARP then Ping via scanners
                res = await arp_scanner.scan(ip)
                if not res:
                    res = await ping_scanner.scan(ip)
                return res[0] if res else None

            retry_results = await asyncio.gather(*(retry_device(d) for d in missing_online))
            for r in retry_results:
                if r: unique_devices.append(r)

        # 4. Device Enrichment & Fingerprinting
        semaphore = asyncio.Semaphore(10) # Throttled for Pi stability
        fingerprinter = HTTPFingerprinter()

        async def enrich_device(device):
            async with semaphore:
                ip, mac = device["ip"], device.get("mac", "unknown")
                
                # 1. Hostname resolution (MDNS -> DNS)
                hostname = device.get("hostname")
                if not hostname or hostname == "unknown":
                    hostname = await resolve_hostname(ip)
                
                # 2. Port Check (for classification)
                ports_list = await scan_ports(ip)
                open_port_ids = [p["port"] for p in ports_list]
                
                # 3. HTTP Fingerprinting (if web ports open)
                page_title = None
                if any(p in open_port_ids for p in [80, 443, 8080, 8123]):
                    pages = await fingerprinter.scan(ip, ports=[p for p in open_port_ids if p in [80, 443, 8080, 8123]])
                    if pages:
                        page_title = pages[0].get("title")
                
                return {
                    "ip": ip, 
                    "mac": mac, 
                    "hostname": hostname, 
                    "ports_list": ports_list, 
                    "page_title": page_title,
                    "result_id": str(uuid.uuid4())
                }

        processed_results = []
        if unique_devices:
            processed_results = await asyncio.gather(*(enrich_device(d) for d in unique_devices))

        # 5. Save Results & Finalize
        def save_and_update():
            conn = get_connection()
            try:
                save_now = utc_now()
                for res in processed_results:
                    conn.execute(
                        "INSERT INTO scan_results (id, scan_id, ip, mac, hostname, open_ports, first_seen, last_seen) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                        [res["result_id"], scan_id, res["ip"], res["mac"], res["hostname"], json.dumps(res["ports_list"]), save_now, save_now]
                    )
                conn.commit()
            finally:
                conn.close()
        
        if processed_results:
            await asyncio.to_thread(save_and_update)
            from app.services.devices import batch_upsert_devices
            # Enriched batch for upsert (includes page_title for classification)
            batch_data = [
                {
                    "ip": r["ip"], 
                    "mac": r["mac"], 
                    "hostname": r["hostname"], 
                    "ports": r["ports_list"],
                    "page_title": r.get("page_title")
                } for r in processed_results
            ]
            await batch_upsert_devices(batch_data)

        # 6. Finalize (Offline status logic)
        def finalize_scan():
            conn = get_connection()
            try:
                final_now = utc_now()
                conn.execute("UPDATE devices SET missing_count = missing_count + 1 WHERE status = 'online' AND last_seen < ?", [job_start])
                
                offline_devices = conn.execute(
                    "SELECT id, ip, mac, display_name, vendor, icon FROM devices WHERE status = 'online' AND missing_count >= 3",
                ).fetchall()
                
                for d_id, d_ip, d_mac, d_name, d_vendor, d_icon in offline_devices:
                    conn.execute("UPDATE devices SET status = 'offline' WHERE id = ?", [d_id])
                    conn.execute("INSERT INTO device_status_history (id, device_id, status, changed_at) VALUES (?, ?, ?, ?)", [str(uuid.uuid4()), d_id, 'offline', final_now])

                conn.execute("UPDATE scans SET status = 'done', finished_at = ? WHERE id = ?", [final_now, scan_id])
                conn.commit()
                return offline_devices
            finally:
                conn.close()

        offline_list = await asyncio.to_thread(finalize_scan)
        
        # MQTT/Notifications for offline devices
        from app.services.devices import publish_device_offline
        for d_id, d_ip, d_mac, d_name, d_vendor, d_icon in offline_list:
             await asyncio.to_thread(publish_device_offline, {"id": d_id, "ip": d_ip, "mac": d_mac, "hostname": d_name, "vendor": d_vendor, "icon": d_icon, "status": "offline", "timestamp": utc_now().isoformat()})
             log_task_event("discovery", "status_changed", f"Device went offline: {d_name or d_ip}", target=d_id, details={"ip": d_ip, "mac": d_mac, "status": "offline"})

        duration = int((time.time() - start_time) * 1000)
        logger.info(f"Scan job {scan_id} completed successfully. Found {len(processed_results)} devices.")
        
        log_task_event(
            task_type="scan", 
            event_type="completed", 
            message=f"Network scan completed. Found {len(processed_results)} devices.", 
            target=target,
            duration_ms=duration,
            details={"scan_id": scan_id, "device_count": len(processed_results)}
        )

    except Exception as e:
        logger.error(f"Scan job {scan_id} failed: {e}", exc_info=True)
        def fail_scan():
            conn = get_connection()
            try:
                conn.execute("UPDATE scans SET status = 'failed', finished_at = ?, error_message = ? WHERE id = ?", [utc_now(), str(e), scan_id])
                conn.commit()
            finally:
                conn.close()
        await asyncio.to_thread(fail_scan)
        log_task_event(task_type="scan", event_type="failed", message=f"Network scan failed: {str(e)}", target=target)
        raise e


