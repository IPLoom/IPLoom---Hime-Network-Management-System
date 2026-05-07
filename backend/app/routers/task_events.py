from fastapi import APIRouter, Query, HTTPException
from typing import List, Dict, Any
import os
import json
import logging
from app.core.task_logger import LOG_FILE

router = APIRouter()
logger = logging.getLogger(__name__)

from typing import List, Dict, Any, Optional

@router.get("/", response_model=Dict[str, Any])
async def get_task_events(
    limit: int = Query(50, ge=1, le=1000),
    page: int = Query(1, ge=1),
    task_type: Optional[str] = Query(None),
):
    """
    Retrieve task activity events from the JSON log file.
    Returns events in reverse chronological order.
    """
    events = []
    
    # Check both current log file and rotated backup
    files_to_read = []
    if os.path.exists(LOG_FILE):
        files_to_read.append(LOG_FILE)
    if os.path.exists(f"{LOG_FILE}.1"):
        files_to_read.append(f"{LOG_FILE}.1")
        
    if not files_to_read:
        return {
            "items": [],
            "total": 0,
            "page": page,
            "limit": limit,
            "total_pages": 0
        }

    try:
        all_lines = []
        # Read files (rotated one first if it exists, but usually we just want newest)
        # Actually, rotated file (.1) contains OLDER logs. 
        # So we should read .1 then current file.
        
        if os.path.exists(f"{LOG_FILE}.1"):
             with open(f"{LOG_FILE}.1", 'r', encoding='utf-8') as f:
                all_lines.extend(f.readlines())
                
        if os.path.exists(LOG_FILE):
            with open(LOG_FILE, 'r', encoding='utf-8') as f:
                all_lines.extend(f.readlines())
            
        # Parse lines
        parsed_events = []
        for line in all_lines:
            if not line.strip(): continue
            try:
                event = json.loads(line)
                # Filter by task_type if specified
                if task_type and event.get("task_type") != task_type:
                    continue
                parsed_events.append(event)
            except json.JSONDecodeError:
                continue
        
        # Reverse to show newest first
        parsed_events.reverse()
        
        # Pagination
        total = len(parsed_events)
        total_pages = (total + limit - 1) // limit
        
        start = (page - 1) * limit
        end = start + limit
        
        paginated_items = parsed_events[start:end]
        
        return {
            "items": paginated_items,
            "total": total,
            "page": page,
            "limit": limit,
            "total_pages": total_pages
        }
            
    except Exception as e:
        logger.error(f"Error reading task event logs: {e}")
        raise HTTPException(status_code=500, detail=f"Error reading task log file: {str(e)}")
