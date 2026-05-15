from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query, Depends, status, HTTPException
from app.core.notifications import manager
from app.core.auth import settings, get_current_user
from app.core.db import get_connection, commit
from app.core.date_utils import now as utc_now
from jose import jwt, JWTError
from typing import List, Optional, Dict, Any
import logging
import asyncio
import json

logger = logging.getLogger(__name__)

router = APIRouter()

# --- REST Endpoints ---

from pydantic import BaseModel
from datetime import datetime

class NotificationModel(BaseModel):
    id: str
    type: str
    task_type: Optional[str] = None
    event_type: Optional[str] = None
    message: str
    level: str
    target: Optional[str] = None
    details: Optional[Any] = None
    created_at: datetime
    read_at: Optional[datetime] = None

@router.get("/", response_model=List[NotificationModel], dependencies=[Depends(get_current_user)])
async def list_notifications(
    limit: int = 50,
    offset: int = 0,
    type: Optional[str] = None,
    unread_only: bool = False
):
    def query():
        conn = get_connection()
        try:
            sql = "SELECT id, type, task_type, event_type, message, level, target, details, created_at, read_at FROM notifications"
            clauses = []
            params = []
            
            if type:
                clauses.append("type = ?")
                params.append(type)
            
            if unread_only:
                clauses.append("read_at IS NULL")
            
            if clauses:
                sql += " WHERE " + " AND ".join(clauses)
            
            sql += " ORDER BY created_at DESC LIMIT ? OFFSET ?"
            params.extend([limit, offset])
            
            rows = conn.execute(sql, params).fetchall()
            
            result = []
            for r in rows:
                # Handle details JSON string if needed
                details_val = r[7]
                if details_val and isinstance(details_val, str):
                    try:
                        details_val = json.loads(details_val)
                    except:
                        pass
                
                result.append({
                    "id": r[0], "type": r[1], "task_type": r[2], "event_type": r[3],
                    "message": r[4], "level": r[5], "target": r[6], "details": details_val,
                    "created_at": r[8], "read_at": r[9]
                })
            return result
        except Exception as e:
            logger.error(f"Error listing notifications: {e}")
            # If table missing, return empty list instead of 500
            if "Table with name notifications does not exist" in str(e):
                return []
            raise HTTPException(status_code=500, detail=str(e))
        finally:
            conn.close()
    return await asyncio.to_thread(query)

@router.get("/unread-count", dependencies=[Depends(get_current_user)])
async def get_unread_count():
    def query():
        conn = get_connection()
        try:
            row = conn.execute("SELECT count(*) FROM notifications WHERE read_at IS NULL").fetchone()
            return {"count": row[0] if row else 0}
        except Exception as e:
            if "Table with name notifications does not exist" in str(e):
                return {"count": 0}
            raise HTTPException(status_code=500, detail=str(e))
        finally:
            conn.close()
    return await asyncio.to_thread(query)



class MarkReadRequest(BaseModel):
    notif_ids: Optional[List[str]] = None
    all: bool = False

@router.post("/mark-read", dependencies=[Depends(get_current_user)])
async def mark_read(request: MarkReadRequest):
    def query():
        conn = get_connection()
        try:
            # Explicit transaction for reliability
            conn.execute("BEGIN TRANSACTION")
            if request.all:
                logger.info("Marking all notifications as read")
                conn.execute("UPDATE notifications SET read_at = CURRENT_TIMESTAMP WHERE read_at IS NULL")
            elif request.notif_ids:
                logger.info(f"Marking specific notifications as read: {request.notif_ids}")
                conn.execute("UPDATE notifications SET read_at = CURRENT_TIMESTAMP WHERE id = ANY(?) AND read_at IS NULL", [request.notif_ids])
            
            conn.execute("COMMIT")
            
            from app.core.db import commit
            commit() # Connection-level commit
            return {"status": "success"}
        except Exception as e:
            try: conn.execute("ROLLBACK")
            except: pass
            logger.error(f"Error marking notifications as read: {e}")
            raise HTTPException(status_code=500, detail=str(e))
        finally:
            conn.close()
    return await asyncio.to_thread(query)

# --- Background Maintenance ---

async def prune_old_notifications():
    """
    Background task to prune notifications older than 30 days.
    Runs every hour.
    """
    while True:
        try:
            def do_prune():
                conn = get_connection()
                try:
                    logger.info("Pruning notifications older than 30 days...")
                    conn.execute("DELETE FROM notifications WHERE created_at < (now() - INTERVAL '30 days')")
                    from app.core.db import commit
                    commit()
                finally:
                    conn.close()
            
            await asyncio.to_thread(do_prune)
        except Exception as e:
            logger.error(f"Error in background pruning: {e}")
        
        # Wait 1 hour before next run
        await asyncio.sleep(3600)

# Start background task if loop is available
try:
    loop = asyncio.get_event_loop()
    if loop.is_running():
        loop.create_task(prune_old_notifications())
except:
    pass

# --- WebSocket Endpoint ---

async def get_token_from_query(token: str = Query(None)):
    if token is None:
        return None
    try:
        payload = jwt.decode(token, settings.secret_key, algorithms=[settings.algorithm])
        return payload.get("sub")
    except JWTError:
        return None

@router.websocket("/ws")
async def websocket_endpoint(
    websocket: WebSocket,
    token: str = Query(None)
):
    # Verify token
    username = await get_token_from_query(token)
    if not username:
        logger.warning("WebSocket connection rejected: Invalid or missing token")
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return

    await manager.connect(websocket)
    try:
        while True:
            # Keep connection open and handle client messages if any
            # For now we just wait for disconnection or pings
            data = await websocket.receive_text()
            # If client sends "ping", we could send "pong"
            if data == "ping":
                await websocket.send_text("pong")
    except WebSocketDisconnect:
        manager.disconnect(websocket)
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        manager.disconnect(websocket)
