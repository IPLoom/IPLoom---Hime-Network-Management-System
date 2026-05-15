import asyncio
import logging
import subprocess
import shutil
import xml.etree.ElementTree as ET
from typing import List, Dict, Any, Optional
from .base import BaseScanner

logger = logging.getLogger(__name__)

class AuditScanner(BaseScanner):
    @property
    def name(self) -> str:
        return "audit"

    def is_nmap_available(self) -> bool:
        return shutil.which("nmap") is not None

    async def scan(self, target: str, **kwargs) -> List[Dict[str, Any]]:
        """
        Target should be an IP or hostname.
        """
        if self.is_nmap_available():
            return await self._run_nmap_scan(target)
        else:
            logger.warning("Nmap not found. Falling back to basic socket scan.")
            return await self._run_socket_scan(target)

    async def _run_nmap_scan(self, target: str) -> List[Dict[str, Any]]:
        try:
            # -sV: Service/Version detection
            # -T4: Aggressive timing
            # -oX -: Output to XML to stdout
            # -p-: Scan all ports (or top 1000 if preferred)
            # For "Audit", we'll do top 1000 ports by default
            cmd = ["nmap", "-sV", "-T4", "-oX", "-", target]
            
            logger.info(f"Running Nmap scan for {target}...")
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout, stderr = await process.communicate()
            
            if process.returncode != 0:
                logger.error(f"Nmap failed: {stderr.decode()}")
                return []

            return self._parse_nmap_xml(stdout.decode())
        except Exception as e:
            logger.error(f"Error during Nmap scan: {e}")
            return []

    def _parse_nmap_xml(self, xml_data: str) -> List[Dict[str, Any]]:
        results = []
        try:
            root = ET.fromstring(xml_data)
            for host in root.findall("host"):
                ip = host.find("address[@addrtype='ipv4']").get("addr")
                ports = []
                for port_elem in host.findall("ports/port"):
                    state = port_elem.find("state").get("state")
                    if state == "open":
                        port_id = int(port_elem.get("portid"))
                        protocol = port_elem.get("protocol")
                        service_elem = port_elem.find("service")
                        service_name = service_elem.get("name") if service_elem is not None else "unknown"
                        version = service_elem.get("product") if service_elem is not None else ""
                        
                        ports.append({
                            "port": port_id,
                            "protocol": protocol,
                            "service": service_name,
                            "version": version
                        })
                
                results.append({
                    "ip": ip,
                    "ports": ports
                })
        except Exception as e:
            logger.error(f"Error parsing Nmap XML: {e}")
        return results

    async def _run_socket_scan(self, target: str) -> List[Dict[str, Any]]:
        # Basic socket fallback for top 1000 ports
        ports_to_scan = range(1, 1025)
        found_ports = []
        
        semaphore = asyncio.Semaphore(100)
        async def check_port(port):
            async with semaphore:
                try:
                    _, writer = await asyncio.wait_for(
                        asyncio.open_connection(target, port),
                        timeout=1.0
                    )
                    writer.close()
                    await writer.wait_closed()
                    return {"port": port, "protocol": "tcp", "service": "unknown", "version": ""}
                except:
                    return None

        tasks = [check_port(p) for p in ports_to_scan]
        results = await asyncio.gather(*tasks)
        found_ports = [r for r in results if r]
        
        return [{"ip": target, "ports": found_ports}]
