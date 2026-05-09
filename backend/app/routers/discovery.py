from fastapi import APIRouter, Depends, HTTPException
from typing import List, Dict, Any
import logging
from app.services.discovery import DiscoveryService
from app.core.auth import get_current_user

router = APIRouter()
logger = logging.getLogger(__name__)

@router.post("/scan")
async def start_rapid_discovery(current_user: Any = Depends(get_current_user)):
    """
    Trigger a high-speed discovery scan of the local subnet.
    Returns a list of all detected devices with status flags.
    """
    try:
        results = await DiscoveryService.rapid_scan_v2()
        return results
    except Exception as e:
        logger.error(f"Rapid discovery failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))
