import psutil
import socket
import ipaddress
import logging
import httpx
import os
import json
import asyncio
import sys
import subprocess
import re
from datetime import datetime, timezone
from app.core.date_utils import now as utc_now
from app.core.db import get_connection

logger = logging.getLogger(__name__)

CACHE_PATH = "../data/discovery.json"

class DiscoveryService:
    @staticmethod
    async def _async_is_port_open(host, port, timeout=1.5):
        """Asynchronously check if a port is open with better reliability."""
        try:
            def check():
                try:
                    with socket.create_connection((host, port), timeout=timeout):
                        return True
                except:
                    return False
            return await asyncio.to_thread(check)
        except:
            return False

    @staticmethod
    async def rapid_scan_v2():
        """
        Ultra-fast network scanner that identifies NEW devices vs known ones.
        Uses modular scanners for Layer 2/3 discovery.
        """
        logger.info("Starting Modular Rapid Discovery Scan v2...")
        
        # 1. Detect Subnet
        from app.services.scans import resolve_hostname
        interfaces = psutil.net_if_addrs()
        target_network = None
        for iface, addrs in interfaces.items():
            for addr in addrs:
                if addr.family == socket.AF_INET and not addr.address.startswith("127."):
                    ip = addr.address
                    mask = addr.netmask
                    if ip and mask:
                        if ip.startswith(("192.168.", "10.", "172.16.", "172.31.")):
                            target_network = ipaddress.IPv4Network(f"{ip}/{mask}", strict=False)
                            break
            if target_network: break
        
        target_str = str(target_network) if target_network else "192.168.1.0/24"

        # 2. Fetch Known Devices
        def get_known():
            conn = get_connection()
            try:
                rows = conn.execute("SELECT mac, ip, display_name FROM devices").fetchall()
                return {r[0]: {"ip": r[1], "name": r[2]} for r in rows if r[0]}
            finally:
                conn.close()
        
        known_devices = await asyncio.to_thread(get_known)

        # 3. Modular Discovery
        from app.services.scanners import ARPScanner, PingScanner
        arp_scanner = ARPScanner()
        ping_scanner = PingScanner()
        
        arp_res = await arp_scanner.scan(target_str)
        ping_res = await ping_scanner.scan(target_str)
        
        # Merge
        found_map = {d["ip"]: d for d in arp_res}
        for p in ping_res:
            if p["ip"] not in found_map: found_map[p["ip"]] = p
            elif p.get("mac") and p["mac"] != "unknown" and found_map[p["ip"]].get("mac") == "unknown":
                found_map[p["ip"]]["mac"] = p["mac"]

        # 4. Enrichment & Classification
        from app.services.classification import classify_device, get_vendor_locally
        enriched = []
        for dev in found_map.values():
            ip, mac = dev["ip"], dev.get("mac", "unknown")
            
            status = "NEW"
            known_info = known_devices.get(mac)
            if known_info:
                status = "KNOWN" if known_info["ip"] == ip else "MOVED"
            
            hostname = await resolve_hostname(ip)
            vendor = get_vendor_locally(mac) or "Unknown"
            
            # Rapid classification (no ports/titles here)
            classification = classify_device(hostname, vendor, [])

            enriched.append({
                "ip": ip,
                "mac": mac,
                "hostname": hostname or (known_info["name"] if known_info else "unknown"),
                "status": status,
                "is_new": status == "NEW",
                "vendor": vendor,
                "device_type": classification["type"],
                "icon": classification["icon"],
                "brand": classification.get("brand"),
                "brand_icon": classification.get("brand_icon")
            })

        logger.info(f"Rapid Scan complete. Found {len(enriched)} devices.")
        return sorted(enriched, key=lambda x: (x["status"] != "NEW", x["ip"]))


    @staticmethod
    async def _async_verify_http(url, service_type, timeout=3.0):
        """Asynchronously verify service type using deep fingerprinting and heuristics."""
        try:
            async with httpx.AsyncClient(timeout=timeout, verify=False, follow_redirects=True) as client:
                resp = await client.get(url)
                body = resp.text
                body_lower = body.lower()
                
                if service_type == "adguard":
                    signatures = ["adguard", "ag_home", "dns protection", "dns server", "dashboard"]
                    for sig in signatures:
                        if sig in body_lower:
                            return True
                    if ":3000" in url and resp.status_code == 200:
                        return True
                elif service_type == "luci":
                    if "luci" in body_lower or "cgi-bin/luci" in body_lower:
                        return True
                return False
        except:
            return False

    @staticmethod
    async def discover_network():
        """Attempt to auto-detect local network configuration and services via profile-based parallel scan."""
        logger.info("Starting ultra-reliable profile-based network discovery...")
        discovery = {
            "subnet": "192.168.1.0/24",
            "mqtt_host": "",
            "mqtt_port": 1883,
            "adguard_url": "",
            "openwrt_host": "",
            "detected": []
        }
        
        try:
            # Detect Subnet
            interfaces = psutil.net_if_addrs()
            target_network = None
            local_ip = None

            for iface, addrs in interfaces.items():
                for addr in addrs:
                    if addr.family == socket.AF_INET and not addr.address.startswith("127."):
                        ip = addr.address
                        mask = addr.netmask
                        if ip and mask:
                            # 169.254.x.x is Link-Local (APIPA), skip it for automatic discovery
                            if ip.startswith("169.254."):
                                continue
                                
                            is_rfc1918 = ip.startswith(("192.168.", "10.", "172.16.", "172.31."))
                            if not target_network or is_rfc1918:
                                target_network = ipaddress.IPv4Network(f"{ip}/{mask}", strict=False)
                                local_ip = ip
                                if is_rfc1918: break
                if target_network and target_network.is_private and not str(target_network).startswith("169.254"): 
                    break

            if not target_network or str(target_network).startswith("169.254"):
                target_network = ipaddress.IPv4Network("192.168.1.0/24")
                local_ip = "127.0.0.1"

            discovery["subnet"] = str(target_network)
            logger.info(f"Scanning subnet: {discovery['subnet']} (Local IP: {local_ip})")

            gateway = str(list(target_network.hosts())[0])
            all_hosts = ["127.0.0.1", "host.docker.internal", gateway] + [str(h) for h in list(target_network.hosts())]
            unique_hosts = []
            for h in all_hosts:
                if h not in unique_hosts: unique_hosts.append(h)

            semaphore = asyncio.Semaphore(15) 

            async def save_progress():
                """Helper to save current discovery state to disk."""
                try:
                    os.makedirs(os.path.dirname(CACHE_PATH), exist_ok=True)
                    # Create a copy for thread-safe-ish saving
                    current_data = discovery.copy()
                    current_data["detected"] = list(set(current_data["detected"]))
                    with open(CACHE_PATH, "w") as f:
                        json.dump(current_data, f)
                except:
                    pass

            async def probe_host(host_str):
                async with semaphore:
                    # 1. Check MQTT
                    if not discovery["mqtt_host"]:
                        if await DiscoveryService._async_is_port_open(host_str, 1883, timeout=2.0):
                            discovery["mqtt_host"] = host_str
                            if "mqtt" not in discovery["detected"]: discovery["detected"].append("mqtt")
                            logger.info(f"SUCCESS: Found MQTT Broker at {host_str}")
                            await save_progress()

                    # 2. Check AdGuard
                    has_dns = await DiscoveryService._async_is_port_open(host_str, 53, timeout=1.5)
                    for p in [3000, 80, 8080, 81]:
                        if await DiscoveryService._async_is_port_open(host_str, p, timeout=2.0):
                            if (has_dns and p == 3000) or await DiscoveryService._async_verify_http(f"http://{host_str}:{p}", "adguard"):
                                if not discovery["adguard_url"] or p == 3000:
                                    discovery["adguard_url"] = f"http://{host_str}:{p}"
                                    if "adguard" not in discovery["detected"]: discovery["detected"].append("adguard")
                                    logger.info(f"SUCCESS: Identified AdGuard Home at {discovery['adguard_url']}")
                                    await save_progress()
                                    break
                    
                    # 3. Check OpenWrt
                    if not discovery["openwrt_host"]:
                        if await DiscoveryService._async_is_port_open(host_str, 80, timeout=1.5):
                            if await DiscoveryService._async_verify_http(f"http://{host_str}/cgi-bin/luci/", "luci"):
                                discovery["openwrt_host"] = host_str
                                if "openwrt" not in discovery["detected"]: discovery["detected"].append("openwrt")
                                logger.info(f"SUCCESS: Found OpenWrt router at {host_str}")
                                await save_progress()

            logger.info(f"Probing {len(unique_hosts)} targets...")
            await asyncio.gather(*(probe_host(h) for h in unique_hosts))

        except Exception as e:
            logger.error(f"Async discovery failed: {e}")
            
        discovery["detected"] = list(set(discovery["detected"]))
        return discovery

    @staticmethod
    async def run_and_cache():
        """Run discovery in background and cache result."""
        logger.info("Initializing high-speed background network discovery...")
        data = await DiscoveryService.discover_network()
        try:
            os.makedirs(os.path.dirname(CACHE_PATH), exist_ok=True)
            with open(CACHE_PATH, "w") as f:
                json.dump(data, f)
            logger.info(f"Network discovery cached to {CACHE_PATH}")
        except Exception as e:
            logger.error(f"Failed to cache discovery: {e}")

    @staticmethod
    async def get_cached_discovery():
        """Get discovery result from cache or return live results if cache missing."""
        if os.path.exists(CACHE_PATH):
            try:
                with open(CACHE_PATH, "r") as f:
                    return json.load(f)
            except Exception as e:
                logger.error(f"Failed to read discovery cache: {e}")
        
        # Fallback to live discovery if cache is not ready
        return await DiscoveryService.discover_network()
