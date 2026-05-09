import httpx
import logging
import time
from typing import Optional

logger = logging.getLogger(__name__)

_last_rate_limit_time = 0
ENRICHMENT_COOLDOWN = 3600 # 1 hour

async def get_vendor_from_api(mac: str) -> Optional[str]:
    """
    Fetches vendor name for a MAC address using multiple external APIs.
    Includes a 1-hour cool-down if any service returns a 429 Rate Limit.
    """
    global _last_rate_limit_time
    
    # Check for global cool-down
    if time.time() - _last_rate_limit_time < ENRICHMENT_COOLDOWN:
        logger.debug(f"Skipping external enrichment for {mac} due to active rate-limit cool-down.")
        return None

    async with httpx.AsyncClient() as client:
        try:
            # 1. Primary: macvendors.com
            resp = await client.get(f"https://api.macvendors.com/{mac}", timeout=5.0)
            if resp.status_code == 200:
                return resp.text.strip()
            elif resp.status_code == 429:
                logger.warning(f"Rate limited by macvendors.com for {mac}. Engaging 1-hour cool-down.")
                _last_rate_limit_time = time.time()
                return None
            
            # 2. Fallback: macvendors.co
            resp = await client.get(f"https://api.macvendors.co/{mac}", timeout=5.0)
            if resp.status_code == 200:
                return resp.text.strip()
            elif resp.status_code == 429:
                logger.warning(f"Rate limited by macvendors.co for {mac}. Engaging 1-hour cool-down.")
                _last_rate_limit_time = time.time()
                return None
                
            # 3. Fallback: maclookup.app
            resp = await client.get(f"https://api.maclookup.app/v2/macs/{mac}", timeout=5.0)
            if resp.status_code == 200:
                data = resp.json()
                if data.get("success") and data.get("company"):
                    return data["company"]
                    
        except Exception as e:
            logger.warning(f"MAC API Enrichment failed for {mac}: {e}")
            
    return None
