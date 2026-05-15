import asyncio
import logging
import subprocess
import sys
import re
import ipaddress
from typing import List, Dict, Any, Optional
from .base import BaseScanner

logger = logging.getLogger(__name__)

def get_mac_from_cache(ip: str) -> Optional[str]:
    """Retrieves MAC from system ARP table if available. Supports Windows and Linux."""
    try:
        # Try 'arp -a' (Windows/Legacy Linux)
        cmd = ["arp", "-a", ip]
        output = subprocess.check_output(cmd, stderr=subprocess.STDOUT, timeout=2).decode()
        match = re.search(r"(([0-9a-fA-F]{2}[:-]){5}([0-9a-fA-F]{2}))", output)
        if match:
            return match.group(1).replace('-', ':').lower()
    except:
        pass

    # Try 'ip neigh' (Modern Linux/Raspberry Pi)
    if sys.platform != "win32":
        try:
            cmd = ["ip", "neigh", "show", ip]
            output = subprocess.check_output(cmd, stderr=subprocess.STDOUT, timeout=2).decode()
            match = re.search(r"(([0-9a-fA-F]{2}[:]){5}([0-9a-fA-F]{2}))", output)
            if match:
                return match.group(1).lower()
        except:
            pass
            
    return None

class PingScanner(BaseScanner):
    @property
    def name(self) -> str:
        return "ping"

    async def scan(self, target: str, **kwargs) -> List[Dict[str, Any]]:
        try:
            # Handle possible multiple targets
            subnets = target.split()
            all_ips = []
            for s in subnets:
                try:
                    net = ipaddress.ip_network(s, strict=False)
                    all_ips.extend(list(net.hosts()))
                except:
                    continue
            
            if not all_ips: return []

            logger.info(f"Starting Ping Sweep for {len(all_ips)} IPs...")
            
            semaphore = asyncio.Semaphore(100)
            async def check_ip(ip_obj):
                async with semaphore:
                    ip_str = str(ip_obj)
                    
                    def sync_ping():
                        try:
                            cmd = ["ping", "-n", "1", "-w", "500", ip_str] if sys.platform == "win32" else ["ping", "-c", "1", "-W", "1", ip_str]
                            result = subprocess.run(cmd, capture_output=True, timeout=2)
                            if result.returncode == 0:
                                mac = get_mac_from_cache(ip_str)
                                return mac if mac else "unknown"
                            return None
                        except:
                            return None

                    res = await asyncio.to_thread(sync_ping)
                    if res is None:
                        return None
                        
                    return {"ip": ip_str, "mac": res}

            results = await asyncio.gather(*(check_ip(ip) for ip in all_ips))
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
