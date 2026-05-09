import json
import logging
import httpx
import re
import asyncio
from datetime import datetime, timezone
from uuid import uuid4
from typing import Optional, List, Dict, Any

from app.core.db import get_connection
from app.services.mqtt import publish_device_online, publish_device_offline

logger = logging.getLogger(__name__)

async def upsert_device_from_scan(
    ip: str,
    mac: Optional[str],
    hostname: Optional[str],
    ports: List[Dict[str, Any]],
) -> str:
    """Wrapper for backward compatibility, uses batch_upsert for safety."""
    res = await batch_upsert_devices([{"ip": ip, "mac": mac, "hostname": hostname, "ports": ports}])
    return res[0] if res else ""

async def batch_upsert_devices(devices_data: List[Dict[str, Any]]) -> List[str]:
    """
    Upserts multiple devices in a single database transaction.
    Greatly reduces DuckDB 'Database is locked' issues.
    """
    if not devices_data:
        return []

    def sync_batch_upsert():
        conn = get_connection()
        try:
            now = datetime.now(timezone.utc)
            upserted_ids = []
            new_devices_to_enrich = [] # (id, mac)
            online_notifications = [] # device_info dicts
            
            from app.services.classification import classify_device, get_vendor_locally

            for data in devices_data:
                ip = data["ip"]
                mac = data.get("mac")
                hostname = data.get("hostname")
                protocol = data.get("protocol", "tcp").lower()
                ports = data.get("ports", [])
                
                device_id = None
                existing_device = None
                
                if mac and mac.lower() != "unknown":
                    existing_device = conn.execute(
                        "SELECT id, first_seen, last_seen, ip, ip_type, attributes, status FROM devices WHERE mac = ?", 
                        [mac]
                    ).fetchone()
                
                if not existing_device:
                    existing_device = conn.execute(
                        "SELECT id, first_seen, last_seen, ip, ip_type, attributes, status FROM devices WHERE ip = ?", 
                        [ip]
                    ).fetchone()

                is_new = False
                old_status = 'unknown'
                
                port_numbers = [p["port"] for p in ports]
                guessed_type, guessed_icon = classify_device(hostname, None, port_numbers)

                if existing_device:
                    device_id, first_seen, last_seen, old_ip, old_ip_type, attributes_raw, old_status = existing_device
                    conn.execute(
                        """
                        UPDATE devices
                        SET last_seen = ?,
                            ip = ?,
                            mac = COALESCE(?, mac),
                            name = COALESCE(name, ?),
                            device_type = COALESCE(device_type, ?),
                            icon = COALESCE(icon, ?),
                            open_ports = ?,
                            status = ?,
                            missing_count = 0
                        WHERE id = ?
                        """,
                        [now, ip, mac, hostname, guessed_type, guessed_icon, json.dumps(ports), 'online', device_id]
                    )
                else:
                    is_new = True
                    device_id = str(uuid4())
                    conn.execute(
                        """
                        INSERT INTO devices (id, ip, mac, name, display_name, device_type, icon, ip_type, open_ports, first_seen, last_seen, attributes, status, missing_count)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 0)
                        """,
                        [device_id, ip, mac, hostname, hostname or ip, guessed_type, guessed_icon, data.get("ip_type"), json.dumps(ports), now, now, "{}", 'online']
                    )

                # Record status change if needed
                if old_status != 'online':
                    conn.execute(
                        "INSERT INTO device_status_history (id, device_id, status, changed_at) VALUES (?, ?, ?, ?)",
                        [str(uuid4()), device_id, 'online', now]
                    )

                for p in ports:
                    p_proto = p.get("protocol", "tcp").lower()
                    conn.execute(
                        """
                        INSERT OR REPLACE INTO device_ports (device_id, port, protocol, service, last_seen)
                        VALUES (?, ?, ?, ?, ?)
                        """,
                        [device_id, p["port"], p_proto, p["service"], now]
                    )

                all_ports_rows = conn.execute(
                    "SELECT port, protocol, service FROM device_ports WHERE device_id = ? ORDER BY port",
                    [device_id]
                ).fetchall()
                all_ports = [{"port": r[0], "protocol": r[1], "service": r[2]} for r in all_ports_rows]

                conn.execute(
                    "UPDATE devices SET open_ports = ?, last_seen = ?, status = 'online', missing_count = 0 WHERE id = ?",
                    [json.dumps(all_ports), now, device_id]
                )

                if mac:
                    local_vendor = get_vendor_locally(mac)
                    if local_vendor:
                        conn.execute("UPDATE devices SET vendor = COALESCE(vendor, ?) WHERE id = ?", [local_vendor, device_id])
                
                upserted_ids.append(device_id)
                if mac:
                    new_devices_to_enrich.append((device_id, mac))
                
                # Always notify on discovery to ensure MQTT state (HA) stays fresh
                dev_row = conn.execute("SELECT ip, mac, display_name, vendor, icon, device_type, ip_type, last_seen FROM devices WHERE id = ?", [device_id]).fetchone()
                if dev_row:
                    online_notifications.append({
                        "ip": dev_row[0], "mac": dev_row[1], "hostname": dev_row[2], 
                        "vendor": dev_row[3], "icon": dev_row[4], "device_type": dev_row[5],
                        "ip_type": dev_row[6], "last_seen": dev_row[7]
                    })

            from app.core.db import commit
            commit()
            return upserted_ids, new_devices_to_enrich, online_notifications
        finally:
            conn.close()

    upserted_ids, to_enrich, to_notify = await asyncio.to_thread(sync_batch_upsert)

    # Trigger MQTT notifications
    for dev_info in to_notify:
        await asyncio.to_thread(publish_device_online, dev_info)

    # Background enrichment for each found device (async)
    for d_id, mac in to_enrich:
        asyncio.create_task(enrich_device(d_id, mac))
        
    return upserted_ids


async def record_status_change(conn, device_id: str, status: str, timestamp: datetime):
    # This remains for internal use if a connection is already open
    # But let's make it robust in case it's called independently
    if not conn:
        def sync_record():
            c = get_connection()
            try:
                c.execute(
                    "INSERT INTO device_status_history (id, device_id, status, changed_at) VALUES (?, ?, ?, ?)",
                    [str(uuid4()), device_id, status, timestamp]
                )
                from app.core.db import commit
                commit()
            finally:
                c.close()
        await asyncio.to_thread(sync_record)
    else:
        # We assume the caller is in a thread or knows what they are doing
        conn.execute(
            "INSERT INTO device_status_history (id, device_id, status, changed_at) VALUES (?, ?, ?, ?)",
            [str(uuid4()), device_id, status, timestamp]
        )

def format_mac(mac: str) -> str:
    if not mac or mac.lower() == "unknown": return ""
    clean = "".join(c for c in mac if c.isalnum()).upper()
    if len(clean) != 12 or not all(c in "0123456789ABCDEF" for c in clean):
        return "" 
    return ":".join(clean[i:i+2] for i in range(0, 12, 2))

async def enrich_device(device_id: str, mac: str):
    from app.services.classification import get_vendor_locally, classify_device
    
    mac = format_mac(mac)
    if not mac: return

    # Check if we already have a vendor for this MAC address anywhere in the database to avoid redundant API calls
    def get_existing_vendor_by_mac():
        conn = get_connection()
        try:
            # First try the current device
            row = conn.execute("SELECT vendor FROM devices WHERE id = ?", [device_id]).fetchone()
            if row and row[0] and row[0].lower() != "unknown":
                return row[0]
            
            # Then try any other device with the same MAC
            row = conn.execute("SELECT vendor FROM devices WHERE mac = ? AND vendor IS NOT NULL AND vendor != 'unknown' LIMIT 1", [mac]).fetchone()
            return row[0] if row else None
        finally:
            conn.close()
            
    existing_vendor = await asyncio.to_thread(get_existing_vendor_by_mac)
    if existing_vendor:
        logger.debug(f"Skipping enrichment for {mac}, vendor already known from database: {existing_vendor}")
        vendor = existing_vendor
    else:
        vendor = get_vendor_locally(mac)
    
    if not vendor:
        from app.utilities.mac_lookup import get_vendor_from_api
        vendor = await get_vendor_from_api(mac)

    if vendor:
        def sync_update():
            conn = get_connection()
            try:
                row = conn.execute("SELECT display_name, device_type, icon, attributes FROM devices WHERE id = ?", [device_id]).fetchone()
                if row:
                    display_name, current_type, current_icon, old_attrs_json = row
                    new_type, new_icon = current_type, current_icon
                    if not current_type or current_type == "unknown":
                        new_type, new_icon = classify_device(None, vendor)
                    
                    new_display = display_name
                    if not display_name or re.match(r"^\d+\.\d+\.\d+\.\d+$", display_name):
                         new_display = vendor

                    try:
                        attrs = json.loads(old_attrs_json) if old_attrs_json else {}
                    except:
                        attrs = {}
                    attrs["vendor"] = vendor

                    conn.execute(
                        """
                        UPDATE devices 
                        SET vendor = COALESCE(vendor, ?),
                            device_type = CASE WHEN device_type = 'unknown' OR device_type IS NULL THEN ? ELSE device_type END,
                            icon = CASE WHEN icon = 'help-circle' OR icon IS NULL THEN ? ELSE icon END,
                            display_name = ?,
                            attributes = ?
                        WHERE id = ?
                        """,
                        [vendor, new_type, new_icon, new_display, json.dumps(attrs), device_id]
                    )
                    from app.core.db import commit
                    commit()
            finally:
                conn.close()
        await asyncio.to_thread(sync_update)
        
        # Trigger MQTT update after enrichment
        def sync_notify():
            conn = get_connection()
            try:
                row = conn.execute("SELECT ip, mac, display_name, vendor, icon, device_type, ip_type, last_seen FROM devices WHERE id = ?", [device_id]).fetchone()
                if row:
                    dev_info = {
                        "ip": row[0], "mac": row[1], "hostname": row[2], 
                        "vendor": row[3], "icon": row[4], "device_type": row[5],
                        "ip_type": row[6], "last_seen": row[7]
                    }
                    publish_device_online(dev_info)
            finally:
                conn.close()
        await asyncio.to_thread(sync_notify)

async def update_device_fields(device_id: str, fields: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    def sync_update():
        conn = get_connection()
        try:
            row = conn.execute("SELECT id, ip, mac, name, display_name, device_type, vendor, icon, status, ip_type, first_seen, last_seen, is_trusted FROM devices WHERE id = ?", [device_id]).fetchone()
            if not row: return None
            
            valid_cols = {'display_name', 'device_type', 'icon', 'attributes', 'ip_type', 'is_trusted', 'parent_id'}
            updates = []
            params = []
            for k, v in fields.items():
                if k in valid_cols and v is not None:
                    updates.append(f"{k} = ?")
                    params.append(v)
            
            if updates:
                params.append(device_id)
                conn.execute(f"UPDATE devices SET {', '.join(updates)} WHERE id = ?", params)
                from app.core.db import commit
                commit()
            
            updated = conn.execute("SELECT id, ip, mac, name, display_name, device_type, vendor, icon, status, ip_type, first_seen, last_seen, is_trusted FROM devices WHERE id = ?", [device_id]).fetchone()
            return updated
        finally:
            conn.close()

    updated = await asyncio.to_thread(sync_update)
    if not updated: return None
    
    if updated:
        dev_info = {
            "id": updated[0], "ip": updated[1], "mac": updated[2], "name": updated[3],
            "display_name": updated[4], "device_type": updated[5], "vendor": updated[6],
            "icon": updated[7], "status": updated[8], "ip_type": updated[9], "first_seen": updated[10], "last_seen": updated[11],
            "is_trusted": updated[12]
        }
        # Trigger MQTT update on manual edit
        await asyncio.to_thread(publish_device_online, {
            "ip": dev_info["ip"], "mac": dev_info["mac"], "hostname": dev_info["display_name"],
            "vendor": dev_info["vendor"], "icon": dev_info["icon"], "device_type": dev_info["device_type"],
            "ip_type": dev_info["ip_type"], "last_seen": dev_info["last_seen"]
        })
        return dev_info
    return None
