import json
import logging
import httpx
import re
import asyncio
from datetime import datetime, timezone
from app.core.date_utils import now as utc_now
from uuid import uuid4
from typing import Optional, List, Dict, Any

from app.core.db import get_connection
from app.services.mqtt import publish_device_online, publish_device_offline
from app.core.task_logger import log_task_event

logger = logging.getLogger(__name__)

# Standard columns for device SELECTs
DEVICE_COLUMNS = "id, ip, mac, name, display_name, device_type, first_seen, last_seen, vendor, icon, status, ip_type, open_ports, attributes, is_trusted, brand, brand_icon, parent_id, is_blocked, has_schedule, is_manual_block"

def row_to_dict(row):
    if not row: return None
    d = {
        "id": row[0],
        "ip": row[1],
        "mac": row[2],
        "name": row[3],
        "display_name": row[4],
        "device_type": row[5],
        "first_seen": row[6],
        "last_seen": row[7],
        "vendor": row[8],
        "icon": row[9],
        "status": row[10],
        "ip_type": row[11],
        "open_ports": json.loads(row[12]) if row[12] and isinstance(row[12], str) else (row[12] if row[12] else []),
        "attributes": json.loads(row[13]) if row[13] and isinstance(row[13], str) else (row[13] if row[13] else {}),
        "is_trusted": bool(row[14])
    }
    if len(row) > 15: d["brand"] = row[15]
    if len(row) > 16: d["brand_icon"] = row[16]
    if len(row) > 17: d["parent_id"] = row[17]
    if len(row) > 18: d["is_blocked"] = bool(row[18])
    if len(row) > 19: d["has_schedule"] = bool(row[19])
    if len(row) > 20: d["is_manual_block"] = bool(row[20])
    return d

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
            now = utc_now()
            upserted_ids = []
            new_devices_to_enrich = [] # (id, mac)
            online_notifications = [] # device_info dicts
            
            new_count = 0
            recovered_count = 0
            last_new_device = None
            last_recovered_device = None

            from app.services.classification import classify_device, get_vendor_locally

            for data in devices_data:
                ip = data["ip"]
                mac = data.get("mac")
                hostname = data.get("hostname")
                ports = data.get("ports", [])
                
                device_id = None
                existing_device = None
                
                # Optimized: Fetch all necessary fields in one go
                if mac and mac.lower() != "unknown":
                    existing_device = conn.execute(
                        f"SELECT {DEVICE_COLUMNS} FROM devices WHERE mac = ?", 
                        [mac]
                    ).fetchone()
                
                if not existing_device:
                    existing_device = conn.execute(
                        f"SELECT {DEVICE_COLUMNS} FROM devices WHERE ip = ?", 
                        [ip]
                    ).fetchone()

                is_new = False
                old_status = 'unknown'
                
                port_numbers = [p["port"] for p in ports]
                classification = classify_device(hostname, None, port_numbers, page_title=data.get("page_title"))
                guessed_type = classification["type"]
                guessed_icon = classification["icon"]
                guessed_brand = classification.get("brand")
                guessed_brand_icon = classification.get("brand_icon")

                if existing_device:
                    # Map the row using our standard helper
                    dev = row_to_dict(existing_device)
                    device_id = dev["id"]
                    is_trusted = dev["is_trusted"]
                    old_status = dev["status"]
                    
                    if is_trusted:
                        # Only update telemetry/status for trusted devices
                        conn.execute(
                            "UPDATE devices SET last_seen = ?, ip = ?, mac = COALESCE(?, mac), open_ports = ?, status = 'online', missing_count = 0 WHERE id = ?",
                            [now, ip, mac, json.dumps(ports), device_id]
                        )
                        final_name = dev["display_name"] or dev["name"]
                        final_type = dev["device_type"]
                        final_icon = dev["icon"]
                        final_brand = dev["brand"]
                        final_brand_icon = dev["brand_icon"]
                    else:
                        # Update metadata for non-trusted devices if we have better info
                        final_icon = dev["icon"] if (dev["icon"] and dev["icon"] != 'help-circle') else guessed_icon
                        final_type = dev["device_type"] if (dev["device_type"] and dev["device_type"] != 'unknown') else guessed_type
                        final_brand = dev["brand"] if dev["brand"] else guessed_brand
                        final_brand_icon = dev["brand_icon"] if dev["brand_icon"] else guessed_brand_icon
                        final_name = dev["name"] if dev["name"] else hostname
                        
                        conn.execute(
                            """
                            UPDATE devices
                            SET last_seen = ?,
                                ip = ?,
                                mac = COALESCE(?, mac),
                                name = ?,
                                device_type = ?,
                                icon = ?,
                                brand = ?,
                                brand_icon = ?,
                                open_ports = ?,
                                status = ?,
                                missing_count = 0
                            WHERE id = ?
                            """,
                            [now, ip, mac, final_name, final_type, final_icon, final_brand, final_brand_icon, json.dumps(ports), 'online', device_id]
                        )
                else:
                    is_new = True
                    device_id = str(uuid4())
                    conn.execute(
                        """
                        INSERT INTO devices (id, ip, mac, name, display_name, device_type, icon, brand, brand_icon, ip_type, open_ports, first_seen, last_seen, attributes, status, missing_count)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'online', 0)
                        """,
                        [device_id, ip, mac, hostname, hostname or ip, guessed_type, guessed_icon, guessed_brand, guessed_brand_icon, data.get("ip_type"), json.dumps(ports), now, now, "{}"]
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
                
                # Collect stats for batched notifications
                if is_new:
                    new_count += 1
                    last_new_device = {"ip": ip, "name": hostname or ip, "id": device_id}
                elif old_status != 'online':
                    recovered_count += 1
                    last_recovered_device = {"ip": ip, "name": hostname or ip, "id": device_id}

                # Always notify on discovery to ensure MQTT state (HA) stays fresh
                dev_row = conn.execute(f"SELECT {DEVICE_COLUMNS} FROM devices WHERE id = ?", [device_id]).fetchone()
                if dev_row:
                    dev_data = row_to_dict(dev_row)
                    online_notifications.append({
                        "ip": dev_data["ip"], 
                        "mac": dev_data["mac"], 
                        "hostname": dev_data["display_name"] or dev_data["name"], 
                        "vendor": dev_data["vendor"], 
                        "icon": dev_data["icon"], 
                        "device_type": dev_data["device_type"],
                        "ip_type": dev_data["ip_type"], 
                        "last_seen": dev_data["last_seen"],
                        "brand": dev_data.get("brand"), 
                        "brand_icon": dev_data.get("brand_icon")
                    })

            # Send batched notifications after processing all devices
            if new_count == 1:
                log_task_event("discovery", "new_device", f"New device discovered: {last_new_device['name']}", target=last_new_device['id'], details={"ip": last_new_device['ip']})
            else:
                log_task_event("discovery", "new_device", f"Discovered {new_count} new devices", details={"count": new_count})
        
            if recovered_count > 0:
                if recovered_count == 1:
                    log_task_event("discovery", "status_changed", f"Device is back online: {last_recovered_device['name']}", target=last_recovered_device['id'], details={"ip": last_recovered_device['ip'], "status": "online"})
                else:
                    log_task_event("discovery", "status_changed", f"{recovered_count} devices came back online", details={"count": recovered_count, "status": "online"})

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

    def get_existing_vendor_by_mac():
        conn = get_connection()
        try:
            row = conn.execute("SELECT vendor FROM devices WHERE id = ?", [device_id]).fetchone()
            if row and row[0] and row[0].lower() != "unknown":
                return row[0]
            row = conn.execute("SELECT vendor FROM devices WHERE mac = ? AND vendor IS NOT NULL AND vendor != 'unknown' LIMIT 1", [mac]).fetchone()
            return row[0] if row else None
        finally:
            conn.close()
            
    existing_vendor = await asyncio.to_thread(get_existing_vendor_by_mac)
    if existing_vendor:
        vendor = existing_vendor
    else:
        vendor = get_vendor_locally(mac)
    
    if not vendor:
        from app.utilities.mac_lookup import get_vendor_from_api
        vendor = await get_vendor_from_api(mac)

    def get_ip():
        conn = get_connection()
        try:
            row = conn.execute("SELECT ip FROM devices WHERE id = ?", [device_id]).fetchone()
            return row[0] if row else None
        finally:
            conn.close()
    
    ip = await asyncio.to_thread(get_ip)
    if not ip: return

    if vendor:
        from app.services.fingerprinting import FingerprintService
        fingerprint = await FingerprintService.fingerprint_device(ip)

        def sync_update():
            conn = get_connection()
            try:
                    row = conn.execute(f"SELECT {DEVICE_COLUMNS} FROM devices WHERE id = ?", [device_id]).fetchone()
                    if row:
                        dev = row_to_dict(row)
                        display_name = dev["display_name"]
                        current_type = dev["device_type"]
                        current_icon = dev["icon"]
                        attrs = dev["attributes"]
                        current_brand = dev.get("brand")
                        current_brand_icon = dev.get("brand_icon")
                        is_trusted = dev["is_trusted"]
                        
                        # If device is trusted, stop enrichment from touching metadata
                        if is_trusted:
                            # Still update attributes/vendor as they are more 'discovery' oriented but keep UI fields locked
                            attrs = dev["attributes"]
                            attrs["vendor"] = vendor
                            conn.execute("UPDATE devices SET vendor = COALESCE(vendor, ?), attributes = ? WHERE id = ?", [vendor, json.dumps(attrs), device_id])
                            return

                        # Never overwrite user-customized details
                        icon_is_user_set = current_icon and current_icon != 'help-circle'
                        type_is_user_set = current_type and current_type != 'unknown'
                        brand_is_user_set = current_brand is not None
                        name_is_user_set = display_name and not re.match(r"^\d+\.\d+\.\d+\.\d+$", display_name)

                        new_type, new_icon = current_type, current_icon
                        new_brand, new_brand_icon = current_brand, current_brand_icon
                        new_display = display_name
                        
                        attrs = dev["attributes"]
                        attrs["vendor"] = vendor
                        
                        # Enhanced classification using current info
                        classification = classify_device(
                            hostname=display_name, 
                            vendor=vendor, 
                            ports=[], 
                            page_title=attrs.get("web_title")
                        )
                        
                        if fingerprint:
                            if not type_is_user_set:
                                new_type = fingerprint["type"]
                            if not icon_is_user_set:
                                new_icon = fingerprint["icon"]
                            if not name_is_user_set:
                                new_display = fingerprint["name"]
                            attrs["fingerprint_id"] = fingerprint["id"]
                            attrs["web_interface"] = fingerprint["url"]
                            if fingerprint.get("detected_title"):
                                attrs["web_title"] = fingerprint["detected_title"]
                        else:
                            if not type_is_user_set:
                                new_type = classification["type"]
                            if not icon_is_user_set:
                                new_icon = classification["icon"]
                            if not brand_is_user_set:
                                new_brand = classification.get("brand")
                                new_brand_icon = classification.get("brand_icon")
                            
                            if not name_is_user_set:
                                 new_display = vendor
                        conn.execute(
                            "UPDATE devices SET vendor = COALESCE(vendor, ?), device_type = ?, icon = ?, brand = ?, brand_icon = ?, display_name = ?, attributes = ? WHERE id = ?",
                            [vendor, new_type, new_icon, new_brand, new_brand_icon, new_display, json.dumps(attrs), device_id]
                        )
                    from app.core.db import commit
                    commit()
            finally:
                conn.close()
        await asyncio.to_thread(sync_update)
        
        def sync_notify():
            conn = get_connection()
            try:
                row = conn.execute(f"SELECT {DEVICE_COLUMNS} FROM devices WHERE id = ?", [device_id]).fetchone()
                if row:
                    dev = row_to_dict(row)
                    publish_device_online({
                        "ip": dev["ip"], 
                        "mac": dev["mac"], 
                        "hostname": dev["display_name"] or dev["name"], 
                        "vendor": dev["vendor"], 
                        "icon": dev["icon"], 
                        "device_type": dev["device_type"],
                        "ip_type": dev["ip_type"], 
                        "last_seen": dev["last_seen"],
                        "brand": dev.get("brand"), 
                        "brand_icon": dev.get("brand_icon")
                    })
            finally:
                conn.close()
        await asyncio.to_thread(sync_notify)

async def update_device_fields(device_id: str, fields: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    def sync_update():
        conn = get_connection()
        try:
            row = conn.execute(f"SELECT {DEVICE_COLUMNS} FROM devices WHERE id = ?", [device_id]).fetchone()
            if not row: return None
            valid_cols = {'name', 'display_name', 'device_type', 'icon', 'attributes', 'ip_type', 'is_trusted', 'parent_id', 'brand', 'brand_icon', 'vendor', 'open_ports'}
            updates = []
            params = []
            for k, v in fields.items():
                if k in valid_cols:
                    # Handle JSON serialization for dict/list fields
                    if k in ('attributes', 'open_ports') and not isinstance(v, str):
                        v = json.dumps(v)
                    updates.append(f"{k} = ?")
                    params.append(v)
            if updates:
                params.append(device_id)
                conn.execute(f"UPDATE devices SET {', '.join(updates)} WHERE id = ?", params)
                from app.core.db import commit
                commit()
            updated = conn.execute(f"SELECT {DEVICE_COLUMNS} FROM devices WHERE id = ?", [device_id]).fetchone()
            return row_to_dict(updated)
        finally:
            conn.close()

    dev_info = await asyncio.to_thread(sync_update)
    if not dev_info: return None
    
    # Notify MQTT about the update
    await asyncio.to_thread(publish_device_online, {
        "ip": dev_info["ip"], 
        "mac": dev_info["mac"], 
        "hostname": dev_info["display_name"] or dev_info["name"],
        "vendor": dev_info["vendor"], 
        "icon": dev_info["icon"], 
        "device_type": dev_info["device_type"],
        "ip_type": dev_info["ip_type"], 
        "last_seen": dev_info["last_seen"],
        "brand": dev_info.get("brand"), 
        "brand_icon": dev_info.get("brand_icon")
    })
    return dev_info
