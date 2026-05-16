import uuid
from typing import List, Optional
from app.core.db import get_connection, commit
from app.models.internet_schedules import DeviceBlockScheduleCreate, DeviceBlockScheduleUpdate, DeviceBlockScheduleRead
from datetime import datetime

async def _update_device_has_schedule(device_id: str):
    conn = get_connection()
    try:
        # Check if there are any ENABLED schedules for this device
        count = conn.execute("SELECT count(*) FROM device_block_schedules WHERE device_id = ? AND enabled = TRUE", [device_id]).fetchone()[0]
        conn.execute("UPDATE devices SET has_schedule = ? WHERE id = ?", [count > 0, device_id])
        from app.core.db import commit
        commit()
    finally:
        conn.close()

async def create_schedule(schedule: DeviceBlockScheduleCreate) -> DeviceBlockScheduleRead:
    conn = get_connection()
    try:
        schedule_id = str(uuid.uuid4())
        conn.execute(
            """
            INSERT INTO device_block_schedules (id, device_id, name, start_time, end_time, days, enabled)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            [schedule_id, schedule.device_id, schedule.name, schedule.start_time, schedule.end_time, schedule.days, schedule.enabled]
        )
        commit()
        await _update_device_has_schedule(schedule.device_id)
        return await get_schedule(schedule_id)
    finally:
        conn.close()

async def get_schedule(schedule_id: str) -> Optional[DeviceBlockScheduleRead]:
    conn = get_connection()
    try:
        row = conn.execute("SELECT id, device_id, name, start_time, end_time, days, enabled, created_at FROM device_block_schedules WHERE id = ?", [schedule_id]).fetchone()
        if not row:
            return None
        return DeviceBlockScheduleRead(
            id=row[0], device_id=row[1], name=row[2], start_time=row[3], end_time=row[4], days=row[5], enabled=row[6], created_at=row[7]
        )
    finally:
        conn.close()

async def get_device_schedules(device_id: str) -> List[DeviceBlockScheduleRead]:
    conn = get_connection()
    try:
        rows = conn.execute("SELECT id, device_id, name, start_time, end_time, days, enabled, created_at FROM device_block_schedules WHERE device_id = ?", [device_id]).fetchall()
        return [
            DeviceBlockScheduleRead(
                id=r[0], device_id=r[1], name=r[2], start_time=r[3], end_time=r[4], days=r[5], enabled=r[6], created_at=r[7]
            ) for r in rows
        ]
    finally:
        conn.close()

async def update_schedule(schedule_id: str, update: DeviceBlockScheduleUpdate) -> Optional[DeviceBlockScheduleRead]:
    conn = get_connection()
    try:
        fields = update.model_dump(exclude_unset=True)
        if not fields:
            return await get_schedule(schedule_id)
        
        query = "UPDATE device_block_schedules SET "
        params = []
        for k, v in fields.items():
            query += f"{k} = ?, "
            params.append(v)
        query = query.rstrip(", ") + " WHERE id = ?"
        params.append(schedule_id)
        
        conn.execute(query, params)
        commit()
        
        # We need the device_id to update the flag
        row = conn.execute("SELECT device_id FROM device_block_schedules WHERE id = ?", [schedule_id]).fetchone()
        if row:
            await _update_device_has_schedule(row[0])
            
        return await get_schedule(schedule_id)
    finally:
        conn.close()

async def delete_schedule(schedule_id: str) -> bool:
    conn = get_connection()
    try:
        row = conn.execute("SELECT device_id FROM device_block_schedules WHERE id = ?", [schedule_id]).fetchone()
        if not row:
            return False
        device_id = row[0]
        conn.execute("DELETE FROM device_block_schedules WHERE id = ?", [schedule_id])
        commit()
        await _update_device_has_schedule(device_id)
        return True
    finally:
        conn.close()

# --- Scheduler Logic ---
import asyncio
import json
from app.services.openwrt import OpenWRTClient
from app.core.task_logger import log_task_event

# Keep track of previous window state in memory
# { device_id: bool }
_last_window_state = {}

def is_time_in_range(start: str, end: str, current: str) -> bool:
    """Check if current HH:MM is within start and end HH:MM."""
    if start <= end:
        return start <= current < end
    else: # Overnight window (e.g. 22:00 to 06:00)
        return current >= start or current < end

async def check_and_apply_schedules():
    from app.core.db import get_connection
    now = datetime.now()
    current_time = now.strftime("%H:%M")
    current_day = str(now.weekday()) # 0=Monday

    conn = get_connection()
    try:
        # 0. Fetch OpenWRT configuration
        ow_row = conn.execute("SELECT config FROM integrations WHERE name = 'openwrt'").fetchone()
        if not ow_row:
            return
        
        try:
            ow_config = json.loads(ow_row[0])
        except:
            return
            
        if not ow_config.get("url") or not ow_config.get("username"):
            return

        # 1. Fetch all active schedules
        schedules = conn.execute("SELECT device_id, start_time, end_time, days FROM device_block_schedules WHERE enabled = TRUE").fetchall()
        
        # 2. Determine desired window state for each device that has at least one schedule
        devices_in_window = {} # {device_id: bool}
        for device_id, start, end, days in schedules:
            if device_id not in devices_in_window:
                devices_in_window[device_id] = False
            
            if current_day in days.split(','):
                if is_time_in_range(start, end, current_time):
                    devices_in_window[device_id] = True

        # 3. Process transitions
        for device_id, in_window in devices_in_window.items():
            prev_in_window = _last_window_state.get(device_id)
            
            # Fetch device MAC and current DB status
            dev_row = conn.execute("SELECT mac, display_name, is_blocked, is_manual_block FROM devices WHERE id = ?", [device_id]).fetchone()
            if not dev_row: continue
            mac, name, db_is_blocked, is_manual_block = dev_row
            
            # If first run for this device, use DB state as baseline
            if prev_in_window is None:
                prev_in_window = bool(db_is_blocked)
                _last_window_state[device_id] = prev_in_window
            
            # Only act on transition (desired state vs baseline/previous state)
            if in_window != prev_in_window:
                # SPECIAL CASE: If schedule window ends but device is manually blocked, DO NOT UNBLOCK
                if not in_window and is_manual_block:
                    print(f"[Scheduler] Window ended for {name or mac} but manual block is active. Skipping unblock.")
                    _last_window_state[device_id] = in_window
                    continue

                action = "blocking" if in_window else "unblocking"
                print(f"[Scheduler] Transition detected for {name or mac}: {action}")
                
                try:
                    client = OpenWRTClient(ow_config["url"], ow_config["username"], ow_config.get("password"))
                    
                    if in_window:
                        await asyncio.to_thread(client.block_device, mac)
                        log_msg = f"Scheduled block applied to {name or mac}"
                    else:
                        await asyncio.to_thread(client.unblock_device, mac)
                        log_msg = f"Scheduled block removed from {name or mac}"
                    
                    log_task_event(
                        task_type="internet_schedule",
                        event_type="completed",
                        message=log_msg,
                        level="INFO",
                        target=device_id
                    )
                    
                    # Update device state in DB and update our memory state
                    # Note: We don't touch is_manual_block here
                    conn.execute("UPDATE devices SET is_blocked = ? WHERE id = ?", [in_window, device_id])
                    from app.core.db import commit
                    commit()
                    _last_window_state[device_id] = in_window
                    
                except Exception as e:
                    print(f"[Scheduler] Failed to apply {action} to {device_id}: {e}")
                    log_task_event(
                        task_type="internet_schedule",
                        event_type="failed",
                        message=f"Failed to apply scheduled {action} to {name or mac}: {str(e)}",
                        level="ERROR",
                        target=device_id
                    )
                    # We DON'T update _last_window_state on failure so it retries next cycle

    finally:
        conn.close()


