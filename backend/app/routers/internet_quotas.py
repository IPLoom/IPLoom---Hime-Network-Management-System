from fastapi import APIRouter, HTTPException, Depends
from typing import List, Optional
from app.core.db import get_connection, commit
from app.models.internet_quotas import DeviceQuota, DeviceQuotaCreate, DeviceQuotaUpdate, DeviceQuotaStatus
from app.services.internet_quotas import get_quota_status
from app.services.policy import update_policy_flag
import uuid
from datetime import datetime

from app.core.auth import get_current_user

router = APIRouter()

@router.get("/devices/{device_id}", response_model=Optional[DeviceQuota])
async def get_device_quota(device_id: str, current_user: dict = Depends(get_current_user)):
    conn = get_connection()
    try:
        row = conn.execute("SELECT * FROM device_quotas WHERE device_id = ?", [device_id]).fetchone()
        if not row:
            return None
        # Manual mapping because duckdb cursor might not return dicts
        cols = [c[0] for c in conn.description]
        data = dict(zip(cols, row))
        return data
    finally:
        conn.close()

@router.get("/devices/{device_id}/status", response_model=Optional[DeviceQuotaStatus])
async def get_device_quota_status_api(device_id: str, current_user: dict = Depends(get_current_user)):
    status = get_quota_status(device_id)
    if not status:
        return None
    return status

@router.post("/devices/{device_id}", response_model=DeviceQuota)
async def set_device_quota(device_id: str, quota: DeviceQuotaCreate, current_user: dict = Depends(get_current_user)):
    conn = get_connection()
    try:
        # Check if device exists
        dev = conn.execute("SELECT id FROM devices WHERE id = ?", [device_id]).fetchone()
        if not dev:
            raise HTTPException(status_code=404, detail="Device not found")
            
        q_id = str(uuid.uuid4())
        now = datetime.utcnow()
        
        # Insert or update
        conn.execute("""
            INSERT INTO device_quotas (id, device_id, limit_bytes, period_hours, enabled, last_reset_at)
            VALUES (?, ?, ?, ?, ?, ?)
            ON CONFLICT (device_id) DO UPDATE SET
                limit_bytes = excluded.limit_bytes,
                period_hours = excluded.period_hours,
                enabled = excluded.enabled
        """, [q_id, device_id, quota.limit_bytes, quota.period_hours, quota.enabled, now])
        
        commit()
        
        # Re-evaluate policy immediately (in case they set a limit lower than current usage)
        # But wait, ON CONFLICT update doesn't reset current_usage.
        # We should check if current usage > new limit
        row = conn.execute("SELECT current_usage, limit_bytes FROM device_quotas WHERE device_id = ?", [device_id]).fetchone()
        if row:
            usage, limit = row
            if usage >= limit:
                conn.execute("UPDATE device_quotas SET is_exceeded = TRUE WHERE device_id = ?", [device_id])
                commit()
                await update_policy_flag(device_id, "is_quota_exceeded", True)
            else:
                conn.execute("UPDATE device_quotas SET is_exceeded = FALSE WHERE device_id = ?", [device_id])
                commit()
                await update_policy_flag(device_id, "is_quota_exceeded", False)

        return await get_device_quota(device_id)
    finally:
        conn.close()

@router.delete("/devices/{device_id}")
async def delete_device_quota(device_id: str, current_user: dict = Depends(get_current_user)):
    conn = get_connection()
    try:
        conn.execute("DELETE FROM device_quotas WHERE device_id = ?", [device_id])
        commit()
        # Reset flag
        await update_policy_flag(device_id, "is_quota_exceeded", False)
        return {"status": "success"}
    finally:
        conn.close()

@router.post("/devices/{device_id}/reset")
async def reset_device_quota_manually(device_id: str, current_user: dict = Depends(get_current_user)):
    conn = get_connection()
    try:
        now = datetime.utcnow()
        conn.execute("""
            UPDATE device_quotas 
            SET current_usage = 0, last_reset_at = ?, is_exceeded = FALSE 
            WHERE device_id = ?
        """, [now, device_id])
        commit()
        
        await update_policy_flag(device_id, "is_quota_exceeded", False)
        return {"status": "success"}
    finally:
        conn.close()
