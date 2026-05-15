import asyncio
import logging
import httpx
from bs4 import BeautifulSoup
from typing import List, Dict, Any, Optional
from .base import BaseScanner

logger = logging.getLogger(__name__)

class HTTPFingerprinter(BaseScanner):
    @property
    def name(self) -> str:
        return "http_fingerprint"

    async def scan(self, target: str, **kwargs) -> List[Dict[str, Any]]:
        """
        Target should be an IP address.
        """
        ports = kwargs.get("ports", [80, 443, 8080, 8123, 8006, 9000])
        results = []

        async with httpx.AsyncClient(timeout=3.0, verify=False, follow_redirects=True) as client:
            tasks = [self._check_port(client, target, port) for port in ports]
            found = await asyncio.gather(*tasks)
            results = [r for r in found if r]
        
        return results

    async def _check_port(self, client: httpx.AsyncClient, ip: str, port: int) -> Optional[Dict[str, Any]]:
        protocol = "https" if port == 443 else "http"
        url = f"{protocol}://{ip}:{port}"
        
        try:
            response = await client.get(url)
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, "html.parser")
                title = soup.title.string.strip() if soup.title else "No Title"
                server = response.headers.get("Server", "Unknown")
                
                logger.info(f"Fingerprinted {url}: Title='{title}', Server='{server}'")
                return {
                    "ip": ip,
                    "port": port,
                    "url": url,
                    "title": title,
                    "server": server,
                    "headers": dict(response.headers)
                }
        except Exception:
            # Silent fail for ports that aren't web servers
            pass
        return None
