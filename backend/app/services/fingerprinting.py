import httpx
import re
import logging
import asyncio
from typing import Optional, Dict, Any, List

logger = logging.getLogger(__name__)

class FingerprintService:
    """
    Service for identifying devices by probing their web interfaces (HTTP/HTTPS).
    Designed to recognize common smart home and network infrastructure devices.
    """
    
    # Signature Database
    # Priority based: First match wins
    SIGNATURES = [
        # --- SMART HOME ---
        {
            "id": "shelly",
            "name": "Shelly Device",
            "type": "Smart Plug/Switch",
            "icon": "plug",
            "rules": [
                {"type": "title", "pattern": r"Shelly"},
                {"type": "header", "key": "Server", "pattern": r"Shelly"}
            ]
        },
        {
            "id": "tasmota",
            "name": "Tasmota Device",
            "type": "Smart Plug/Switch",
            "icon": "plug",
            "rules": [
                {"type": "title", "pattern": r"Tasmota"},
                {"type": "body", "pattern": r"Tasmota Settings"}
            ]
        },
        {
            "id": "esphome",
            "name": "ESPHome Device",
            "type": "IoT Device",
            "icon": "cpu",
            "rules": [
                {"type": "title", "pattern": r"ESPHome"},
                {"type": "body", "pattern": r"esphome-header"}
            ]
        },
        {
            "id": "homeassistant",
            "name": "Home Assistant",
            "type": "Home Automation",
            "icon": "home",
            "rules": [
                {"type": "title", "pattern": r"Home Assistant"},
                {"type": "body", "pattern": r"home-assistant-main"}
            ]
        },
        {
            "id": "wled",
            "name": "WLED Controller",
            "type": "Smart Bulb",
            "icon": "lightbulb",
            "rules": [
                {"type": "title", "pattern": r"WLED"}
            ]
        },
        {
            "id": "zigbee2mqtt",
            "name": "Zigbee2MQTT",
            "type": "Network Bridge",
            "icon": "network",
            "rules": [
                {"type": "title", "pattern": r"Zigbee2MQTT"}
            ]
        },

        # --- INFRASTRUCTURE ---
        {
            "id": "pihole",
            "name": "Pi-hole",
            "type": "Server Admin",
            "icon": "shield-check",
            "rules": [
                {"type": "title", "pattern": r"Pi-hole"},
                {"type": "body", "pattern": r"pi-hole.net"}
            ]
        },
        {
            "id": "adguard",
            "name": "AdGuard Home",
            "type": "Server Admin",
            "icon": "shield-check",
            "rules": [
                {"type": "title", "pattern": r"AdGuard Home"},
                {"type": "body", "pattern": r"ag_home"}
            ]
        },
        {
            "id": "synology",
            "name": "Synology NAS",
            "type": "NAS/Storage",
            "icon": "hard-drive",
            "rules": [
                {"type": "title", "pattern": r"Synology"},
                {"type": "header", "key": "Server", "pattern": r"Synology"}
            ]
        },
        {
            "id": "octoprint",
            "name": "OctoPrint",
            "type": "Server",
            "icon": "printer",
            "rules": [
                {"type": "title", "pattern": r"OctoPrint"}
            ]
        },
        {
            "id": "openwrt",
            "name": "OpenWrt Router",
            "type": "Router/Gateway",
            "icon": "router",
            "rules": [
                {"type": "title", "pattern": r"LuCI"},
                {"type": "body", "pattern": r"cgi-bin/luci"}
            ]
        },
        {
            "id": "unifi",
            "name": "UniFi Controller",
            "type": "Server Admin",
            "icon": "settings",
            "rules": [
                {"type": "title", "pattern": r"UniFi"}
            ]
        }
    ]

    @staticmethod
    async def fingerprint_device(ip: str) -> Optional[Dict[str, Any]]:
        """
        Probes a device and returns identification info if a signature matches.
        """
        # We try port 80 (HTTP) first as it's most common for IoT
        # We also check 443 (HTTPS) and 8080 as fallbacks
        targets = [
            f"http://{ip}",
            f"http://{ip}:8080",
            f"https://{ip}"
        ]

        async with httpx.AsyncClient(timeout=3.0, verify=False) as client:
            for url in targets:
                try:
                    logger.debug(f"Probing {url} for fingerprinting...")
                    resp = await client.get(url, follow_redirects=True)
                    if resp.status_code != 200:
                        continue
                    
                    content = resp.text
                    headers = resp.headers
                    
                    # Try to extract title
                    title_match = re.search(r"<title>(.*?)</title>", content, re.IGNORECASE)
                    title = title_match.group(1) if title_match else ""

                    # Run Signatures
                    for sig in FingerprintService.SIGNATURES:
                        for rule in sig["rules"]:
                            matched = False
                            if rule["type"] == "title":
                                if re.search(rule["pattern"], title, re.IGNORECASE):
                                    matched = True
                            elif rule["type"] == "header":
                                header_val = headers.get(rule["key"], "")
                                if re.search(rule["pattern"], header_val, re.IGNORECASE):
                                    matched = True
                            elif rule["type"] == "body":
                                if re.search(rule["pattern"], content, re.IGNORECASE):
                                    matched = True
                            
                            if matched:
                                logger.info(f"FINGERPRINT MATCH: {ip} is identified as {sig['name']} ({sig['id']})")
                                return {
                                    "id": sig["id"],
                                    "name": sig["name"],
                                    "type": sig["type"],
                                    "icon": sig["icon"],
                                    "detected_title": title,
                                    "url": url
                                }
                except Exception as e:
                    # Silent fail per target to allow fallback
                    continue
        
        return None
