import asyncio
import logging
import socket
from typing import List, Dict, Any
from zeroconf import Zeroconf, ServiceBrowser, ServiceListener
from .base import BaseScanner

logger = logging.getLogger(__name__)

class MDNSListener(ServiceListener):
    def __init__(self):
        self.results = []

    def update_service(self, zc: Zeroconf, type_: str, name: str) -> None:
        pass

    def remove_service(self, zc: Zeroconf, type_: str, name: str) -> None:
        pass

    def add_service(self, zc: Zeroconf, type_: str, name: str) -> None:
        info = zc.get_service_info(type_, name)
        if info:
            addresses = [socket.inet_ntoa(addr) for addr in info.addresses]
            if addresses:
                # Clean up name (e.g. "my-esp._http._tcp.local." -> "my-esp")
                clean_name = name.split('.')[0]
                self.results.append({
                    "ip": addresses[0],
                    "hostname": clean_name,
                    "type": type_,
                    "properties": {k.decode() if isinstance(k, bytes) else k: v.decode() if isinstance(v, bytes) else v for k, v in info.properties.items()}
                })

class MDNSScanner(BaseScanner):
    @property
    def name(self) -> str:
        return "mdns"

    async def scan(self, target: str = None, **kwargs) -> List[Dict[str, Any]]:
        """
        Scan for MDNS services. Target is ignored as it scans the whole network segment.
        """
        def perform_discovery():
            zeroconf = Zeroconf()
            listener = MDNSListener()
            # Common IoT service types
            types = ["_http._tcp.local.", "_mqtt._tcp.local.", "_esphomelib._tcp.local.", "_homeassistant._tcp.local."]
            browsers = [ServiceBrowser(zeroconf, t, listener) for t in types]
            
            # Wait for 3 seconds to gather results
            import time
            time.sleep(3)
            
            zeroconf.close()
            return listener.results

        logger.info("Starting MDNS discovery...")
        results = await asyncio.to_thread(perform_discovery)
        
        # Deduplicate by IP
        unique_map = {}
        for r in results:
            if r["ip"] not in unique_map:
                unique_map[r["ip"]] = r
            else:
                # Merge properties if needed
                unique_map[r["ip"]]["properties"].update(r["properties"])
        
        final_results = list(unique_map.values())
        logger.info(f"MDNS discovery found {len(final_results)} devices.")
        return final_results
