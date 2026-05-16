import asyncio
import logging
from app.core.db import get_connection, commit
from app.services.openwrt import OpenWRTClient
import json

logger = logging.getLogger(__name__)

async def apply_device_policy(device_id: str, conn=None):
    """
    Determines and applies the final blocking state for a device based on:
    1. Manual Block flag
    2. Scheduled Block flag
    3. Quota Exceeded flag
    
    A device is BLOCKED if ANY of these are True.
    """
    should_close = False
    if conn is None:
        conn = get_connection()
        should_close = True
        
    try:
        # Fetch current state
        row = conn.execute("""
            SELECT mac, is_manual_block, is_scheduled_block, is_quota_exceeded, is_blocked, display_name, is_manual_unblock
            FROM devices WHERE id = ?
        """, [device_id]).fetchone()
        
        if not row:
            return
            
        mac, manual, scheduled, quota, current_blocked, name, unblock_override = row
        
        # Determine target state
        # Manual UNBLOCK (unblock_override) has highest priority over automated rules
        target_blocked = bool((manual or scheduled or quota) and not unblock_override)
        
        # Only act if state change is needed
        if target_blocked != bool(current_blocked):
            action = "blocking" if target_blocked else "unblocking"
            logger.info(f"[Policy] {action} {name or mac} (Manual={manual}, Sched={scheduled}, Quota={quota})")
            
            # Get OpenWRT credentials
            int_row = conn.execute("SELECT config FROM integrations WHERE name = 'openwrt'").fetchone()
            if not int_row:
                logger.error("[Policy] OpenWRT integration not configured")
                return
                
            ow_config = json.loads(int_row[0])
            client = OpenWRTClient(ow_config["url"], ow_config["username"], ow_config.get("password"))
            
            try:
                if target_blocked:
                    await asyncio.to_thread(client.block_device, mac)
                else:
                    await asyncio.to_thread(client.unblock_device, mac)
                
                # Update DB
                conn.execute("UPDATE devices SET is_blocked = ? WHERE id = ?", [target_blocked, device_id])
                commit()
                
                # Broadcast status change
                from app.core.notifications import manager
                msg_type = "device_blocked" if target_blocked else "device_unblocked"
                manager.broadcast_sync({"type": msg_type, "mac": mac, "id": device_id})
                
            except Exception as e:
                logger.error(f"[Policy] Failed to apply {action} to {mac}: {e}")
                
    finally:
        if should_close:
            conn.close()

async def update_policy_flag(device_id: str, flag_name: str, value: bool):
    """Helper to update a specific flag and re-evaluate policy."""
    await update_policy_flags(device_id, {flag_name: value})

async def update_policy_flags(device_id: str, updates: dict):
    """Update multiple policy flags and re-evaluate once."""
    conn = get_connection()
    try:
        if not updates:
            return
            
        clauses = []
        params = []
        for flag_name, value in updates.items():
            if flag_name not in ['is_manual_block', 'is_scheduled_block', 'is_quota_exceeded', 'is_manual_unblock']:
                raise ValueError(f"Invalid flag name: {flag_name}")
            clauses.append(f"{flag_name} = ?")
            params.append(value)
            
        params.append(device_id)
        sql = f"UPDATE devices SET {', '.join(clauses)} WHERE id = ?"
        conn.execute(sql, params)
        commit()
        
        # Apply the combined policy
        await apply_device_policy(device_id, conn)
    finally:
        conn.close()
