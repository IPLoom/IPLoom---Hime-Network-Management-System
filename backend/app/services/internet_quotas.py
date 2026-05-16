import logging
from datetime import datetime, timedelta
from app.core.db import get_connection, commit
from app.services.policy import update_policy_flag, update_policy_flags
import json

logger = logging.getLogger(__name__)

async def check_and_apply_quotas():
    """
    Periodic task to:
    1. Reset quotas that have expired.
    2. Check if remaining active quotas are exceeded.
    """
    conn = get_connection()
    try:
        now = datetime.utcnow()
        
        # 1. Reset expired quotas
        # Using epoch comparison or standard timestamp math
        expired_quotas = conn.execute("""
            SELECT id, device_id, last_reset_at, period_hours, is_exceeded, current_usage
            FROM device_quotas
            WHERE enabled = TRUE
        """).fetchall()
        
        for q_id, dev_id, last_reset, period, exceeded, usage in expired_quotas:
            # last_reset might be string or datetime depending on duckdb version/adapter
            if isinstance(last_reset, str):
                last_reset = datetime.fromisoformat(last_reset.replace('Z', '+00:00')).replace(tzinfo=None)
            
            reset_time = last_reset + timedelta(hours=period)
            
            if now >= reset_time:
                logger.info(f"[Quota] Resetting quota for device {dev_id}")
                conn.execute("""
                    UPDATE device_quotas 
                    SET current_usage = 0, last_reset_at = ?, is_exceeded = FALSE 
                    WHERE id = ?
                """, [now, q_id])
                commit()
                
                # If it was blocked by quota, re-evaluate policy and clear any manual override
                await update_policy_flags(dev_id, {
                    "is_quota_exceeded": False,
                    "is_manual_unblock": False
                })
            
            # 2. Check for newly exceeded quotas (that aren't already flagged)
            elif not exceeded:
                # Refresh data in case openwrt sync just happened
                row = conn.execute("SELECT current_usage, limit_bytes FROM device_quotas WHERE id = ?", [q_id]).fetchone()
                if row:
                    usage, limit = row
                    if usage >= limit:
                        logger.info(f"[Quota] Quota EXCEEDED for device {dev_id} ({usage} >= {limit})")
                        conn.execute("UPDATE device_quotas SET is_exceeded = TRUE WHERE id = ?", [q_id])
                        commit()
                        
                        # Trigger blocking via policy
                        await update_policy_flag(dev_id, "is_quota_exceeded", True)
                        
    except Exception as e:
        logger.error(f"[Quota] Error in check_and_apply_quotas: {e}", exc_info=True)
    finally:
        conn.close()

def get_quota_status(device_id: str):
    """Returns detailed quota status for a device."""
    conn = get_connection()
    try:
        row = conn.execute("""
            SELECT q.limit_bytes, q.current_usage, q.is_exceeded, q.last_reset_at, q.period_hours,
                   d.is_manual_block, d.is_scheduled_block
            FROM device_quotas q
            JOIN devices d ON q.device_id = d.id
            WHERE q.device_id = ?
        """, [device_id]).fetchone()
        
        if not row:
            return None
            
        limit, usage, exceeded, last_reset, period, manual, scheduled = row
        
        if isinstance(last_reset, str):
            last_reset = datetime.fromisoformat(last_reset.replace('Z', '+00:00')).replace(tzinfo=None)
            
        return {
            "device_id": device_id,
            "limit_bytes": limit,
            "current_usage": usage,
            "percent_used": round((usage / limit * 100) if limit > 0 else 0, 2),
            "is_exceeded": bool(exceeded),
            "last_reset_at": last_reset,
            "next_reset_at": last_reset + timedelta(hours=period),
            "is_manual_block": bool(manual),
            "is_scheduled_block": bool(scheduled)
        }
    finally:
        conn.close()
