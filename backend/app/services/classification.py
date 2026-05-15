import re
import json
import logging
import time
from typing import Optional, Tuple, List, Dict, Any
from app.core.db import get_connection

logger = logging.getLogger(__name__)

# Mapping of device_type to Lucide icon names
TYPE_TO_ICON = {
    "Smartphone": "smartphone",
    "Tablet": "tablet",
    "Laptop": "laptop",
    "Desktop": "monitor",
    "Server": "server",
    "Router/Gateway": "router",
    "Network Bridge": "network",
    "Switch": "layers",
    "Access Point": "rss",
    "TV/Entertainment": "tv",
    "IoT Device": "cpu",
    "Smart Bulb": "lightbulb",
    "Smart Plug": "plug",
    "Wall Panel": "layout-panel-left",
    "Motion Sensor": "activity",
    "Smoke Detector": "flame",
    "Motion Detector": "radar",
    "Door/Window Sensor": "door-open",
    "Temperature Sensor": "thermometer",
    "Humidity Sensor": "droplets",
    "Smart Lock": "lock",
    "Microcontroller": "microchip",
    "Security Camera": "camera",
    "Sensor": "waves",
    "Audio/Speaker": "speaker",
    "Streaming Device": "play",
    "Printer": "printer",
    "NAS/Storage": "hard-drive",
    "Game Console": "gamepad-2",
    "Media Server": "play-circle",
    "Home Automation": "home",
    "Generic": "help-circle",
    "unknown": "help-circle"
}

# Metadata for available icons to provide friendly names and categorization in UI
ICON_METADATA = {
    "smartphone": {"label": "Smartphone", "category": "Devices"},
    "tablet": {"label": "Tablet", "category": "Devices"},
    "laptop": {"label": "Laptop", "category": "Devices"},
    "monitor": {"label": "Desktop PC", "category": "Devices"},
    "server": {"label": "Server", "category": "Infrastructure"},
    "router": {"label": "Router", "category": "Network"},
    "network": {"label": "Network Bridge", "category": "Network"},
    "layers": {"label": "Network Switch", "category": "Network"},
    "rss": {"label": "Access Point", "category": "Network"},
    "wifi": {"label": "WiFi Node", "category": "Network"},
    "tv": {"label": "Television", "category": "Entertainment"},
    "cpu": {"label": "IoT Device", "category": "IoT"},
    "lightbulb": {"label": "Smart Light", "category": "Smart Home"},
    "plug": {"label": "Smart Plug", "category": "Smart Home"},
    "layout-panel-left": {"label": "Wall Panel", "category": "Smart Home"},
    "activity": {"label": "Motion Sensor", "category": "Smart Home"},
    "radar": {"label": "Motion Detector", "category": "Smart Home"},
    "flame": {"label": "Smoke Detector", "category": "Safety"},
    "door-open": {"label": "Door Sensor", "category": "Smart Home"},
    "thermometer": {"label": "Temp Sensor", "category": "Sensors"},
    "droplets": {"label": "Humidity Sensor", "category": "Sensors"},
    "lock": {"label": "Smart Lock", "category": "Smart Home"},
    "microchip": {"label": "Microcontroller", "category": "IoT"},
    "camera": {"label": "Security Camera", "category": "Safety"},
    "waves": {"label": "General Sensor", "category": "Sensors"},
    "speaker": {"label": "Speaker/Audio", "category": "Entertainment"},
    "play": {"label": "Streaming Box", "category": "Entertainment"},
    "printer": {"label": "Printer", "category": "Devices"},
    "hard-drive": {"label": "NAS/Storage", "category": "Infrastructure"},
    "gamepad-2": {"label": "Game Console", "category": "Entertainment"},
    "play-circle": {"label": "Media Server", "category": "Entertainment"},
    "home": {"label": "Home Hub", "category": "IoT"},
    "help-circle": {"label": "Generic Device", "category": "Misc"}
}

# Fuzzy Icon Keywords (Regex -> (Type, Icon))
FUZZY_KEYWORDS = {
    r"(bulb|lamp|light|led|hue)": ("Smart Bulb", "lightbulb"),
    r"(plug|outlet|socket|switch|relay|zap|sonoff|shelly)": ("Smart Plug", "plug"),
    r"(cam|camera|eye|video|doorbell|ring)": ("Security Camera", "camera"),
    r"(speaker|sonos|echo|alexa|dot|google_home|nest|audio)": ("Audio/Speaker", "speaker"),
    r"(tv|television|roku|firestick|chromecast|shield|display|screen)": ("TV/Entertainment", "tv"),
    r"(hub|bridge|gateway|gateway_central|zigbee|zwave)": ("Home Automation", "home"),
    r"(motion|presence|pir|activity)": ("Motion Sensor", "activity"),
    r"(smoke|co2|fire|gas|flame)": ("Smoke Detector", "flame"),
    r"(panel|touch|wallpad)": ("Wall Panel", "layout-panel-left"),
    r"(radar|detector)": ("Motion Detector", "radar"),
    r"(lock|gate|latch)": ("Smart Lock", "lock"),
    r"(temp|thermometer)": ("Temperature Sensor", "thermometer"),
    r"(hum|humidity|droplet)": ("Humidity Sensor", "droplets"),
    r"(nas|storage|synology|qnap|unraid|truenas|drive)": ("NAS/Storage", "hard-drive"),
    r"(printer|inkjet|laserjet|epson|hp|canon|brother)": ("Printer", "printer"),
    r"(server|proxmox|esxi|unraid|docker|kubernetes|node)": ("Server", "server"),
    r"(router|pfsense|opnsense|unifi|edgerouter|asuswrt|openwrt|mikrotik)": ("Router/Gateway", "router"),
    r"(esp|tasmota|esphome|arduino|raspberry|pi|wemos|m5stack)": ("Microcontroller", "microchip"),
}

# Brand Keywords (Regex -> Brand ID)
BRAND_KEYWORDS = {
    r"(tasmota)": "tasmota",
    r"(esphome)": "esphome",
    r"(philips|hue)": "philips",
    r"(shelly)": "shelly",
    r"(sonoff)": "sonoff",
    r"(tp-link|tplink|kasa)": "tplink",
    r"(ubiquiti|unifi)": "ubiquiti",
    r"(synology)": "synology",
    r"(raspberry|raspi|pi-hole|pihole)": "raspberry",
    r"(apple|iphone|ipad|macbook|imac|apple_tv)": "apple",
    r"(google|nest|chromecast)": "google",
    r"(amazon|echo|dot|alexa|firetv)": "amazon",
}

# Cache for classification rules
_RULES_CACHE = []
_LAST_CACHE_UPDATE = 0
CACHE_TTL = 60 # Refresh rules every minute

def get_rules() -> List[Dict]:
    """Fetches classification rules from DB with caching."""
    global _RULES_CACHE, _LAST_CACHE_UPDATE
    now = time.time()
    
    if _RULES_CACHE and (now - _LAST_CACHE_UPDATE < CACHE_TTL):
        return _RULES_CACHE
    
    conn = get_connection()
    try:
        rows = conn.execute(
            "SELECT pattern_hostname, pattern_vendor, ports, device_type, icon FROM classification_rules ORDER BY priority ASC, name ASC"
        ).fetchall()
        _RULES_CACHE = [
            {
                "hostname": r[0],
                "vendor": r[1],
                "ports": json.loads(r[2] or "[]"),
                "type": r[3],
                "icon": r[4]
            } for r in rows
        ]
        _LAST_CACHE_UPDATE = now
        return _RULES_CACHE
    except Exception as e:
        logger.error(f"Error fetching classification rules: {e}")
        return []
    finally:
        conn.close()

# Local OUI mapping for common vendors
COMMON_OUIS = {
    "00:0c:29": "VMware, Inc.",
    "00:50:56": "VMware, Inc.",
    "08:00:27": "Oracle Corporation (VirtualBox)",
    "00:1c:c3": "Huawei Technologies",
    "00:25:9c": "Cisco Systems",
    "3c:5a:b4": "Google, Inc.",
    "d8:3b:bf": "Apple, Inc.",
    "f0:18:98": "Apple, Inc.",
    "00:03:93": "Apple, Inc.",
    "00:05:02": "Apple, Inc.",
    "00:15:5d": "Microsoft Corporation (Hyper-V)",
    "b8:27:eb": "Raspberry Pi Foundation",
    "dc:a6:32": "Raspberry Pi Foundation",
    "e4:5f:01": "Raspberry Pi Foundation",
    "00:14:d1": "TP-Link Technologies",
    "bc:d1:d3": "TP-Link Technologies",
    "c0:4a:00": "TP-Link Technologies",
    "8c:ae:4c": "ASUSTek Computer Inc.",
    "fc:db:b3": "Amazon Technologies (Echo/Kindle)",
}

def get_vendor_locally(mac: str) -> Optional[str]:
    if not mac or len(mac) < 8:
        return None
    prefix = mac.lower()[:8]
    return COMMON_OUIS.get(prefix)

# Cache for custom assets
_ASSETS_CACHE = {}
_LAST_ASSETS_UPDATE = 0

def get_custom_assets() -> Dict[str, str]:
    """Fetches custom brand/device icons from DB."""
    global _ASSETS_CACHE, _LAST_ASSETS_UPDATE
    now = time.time()
    if _ASSETS_CACHE and (now - _LAST_ASSETS_UPDATE < 60):
        return _ASSETS_CACHE
    
    conn = get_connection()
    try:
        rows = conn.execute("SELECT name, path, type FROM custom_assets").fetchall()
        _ASSETS_CACHE = {r[0].lower(): {"path": r[1], "type": r[2]} for r in rows}
        _LAST_ASSETS_UPDATE = now
        return _ASSETS_CACHE
    except:
        return {}
    finally:
        conn.close()

def classify_device(
    hostname: Optional[str], 
    vendor: Optional[str], 
    ports: list[int] = [],
    page_title: Optional[str] = None
) -> Dict[str, Any]:
    """
    Returns a dictionary with classification details:
    {
        "type": str,
        "icon": str (Lucide),
        "brand": Optional[str],
        "brand_icon": Optional[str] (Static path)
    }
    """
    hostname = (hostname or "").lower()
    vendor = (vendor or "").lower()
    page_title = (page_title or "").lower()
    
    search_text = f"{hostname} {vendor} {page_title}"
    
    # 1. Check DB Rules
    rules = get_rules()
    for rule in rules:
        matched = False
        if rule["hostname"] and re.search(rule["hostname"], hostname, re.IGNORECASE):
            matched = True
        elif rule["vendor"] and re.search(rule["vendor"], vendor, re.IGNORECASE):
            matched = True
        elif rule["ports"] and any(p in ports for p in rule["ports"]):
            matched = True
            
        if matched:
            return {
                "type": rule["type"],
                "icon": rule["icon"],
                "brand": None,
                "brand_icon": None
            }

    # 2. Fuzzy Keyword Match (for Type/Icon)
    for pattern, (d_type, d_icon) in FUZZY_KEYWORDS.items():
        if re.search(pattern, search_text, re.IGNORECASE):
            res = {"type": d_type, "icon": d_icon}
            # Also try to find a brand
            brand_info = identify_brand(search_text)
            res.update(brand_info)
            return res

    # 3. Fallback: Service-based Classification
    d_type, d_icon = "unknown", TYPE_TO_ICON["unknown"]
    if any(p in ports for p in [22, 23, 21, 25, 53, 5900]):
         d_type, d_icon = "Server", TYPE_TO_ICON["Server"]
    elif any(p in ports for p in [1883, 8883, 5683, 6053]):
         d_type, d_icon = "IoT Device", TYPE_TO_ICON["IoT Device"]
    elif any(p in ports for p in [139, 445, 548]):
         d_type, d_icon = "NAS/Storage", TYPE_TO_ICON["NAS/Storage"]
    elif any(p in ports for p in [80, 443, 8080, 8443, 8123, 8006, 9000, 9443, 32400, 8096]):
         d_type, d_icon = "Generic", TYPE_TO_ICON["Generic"]
    elif ports:
         p = sorted(ports)[0]
         d_type, d_icon = f"Service ({p})", TYPE_TO_ICON["Generic"]

    res = {"type": d_type, "icon": d_icon}
    brand_info = identify_brand(search_text)
    res.update(brand_info)
    return res

def identify_brand(text: str) -> Dict[str, Optional[str]]:
    """Identifies brand and brand icon from text."""
    brand_id = None
    for pattern, b_id in BRAND_KEYWORDS.items():
        if re.search(pattern, text, re.IGNORECASE):
            brand_id = b_id
            break
            
    if not brand_id:
        return {"brand": None, "brand_icon": None}
        
    # Check for custom icon in DB
    assets = get_custom_assets()
    brand_asset = assets.get(brand_id)
    
    # Fallback to local static asset if it exists (assuming naming convention)
    brand_icon = brand_asset["path"] if brand_asset else f"/static/brand_icons/{brand_id}.svg"
    
    return {
        "brand": brand_id.capitalize(),
        "brand_icon": brand_icon
    }

