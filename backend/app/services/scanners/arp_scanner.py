import asyncio
import logging
from typing import List, Dict, Any
from scapy.all import ARP, Ether, srp
from .base import BaseScanner

logger = logging.getLogger(__name__)

class ARPScanner(BaseScanner):
    @property
    def name(self) -> str:
        return "arp"

    async def scan(self, target: str, **kwargs) -> List[Dict[str, Any]]:
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
                    logger.warning("Scapy Layer 2 discovery restricted: Npcap/WinPcap not found.")
                else:
                    logger.error(f"Scapy scan failed: {e}")
                return []

        return await asyncio.to_thread(network_discovery)
