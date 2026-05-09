from fastapi import APIRouter, Query, HTTPException, Depends
from typing import List, Annotated, Optional, Dict, Any
from app.core.db import get_connection
from app.models.devices import DeviceRead, DeviceUpdate, PaginatedDevicesResponse
from app.services.devices import update_device_fields
from app.core.auth import get_current_user
import json, asyncio, math

router = APIRouter()

async def _internal_list_devices(
    device_type: str | None = None, 
    status: str | None = None,
    search: str | None = None,
    sort_by: str = "ip",
    sort_order: str = "asc",
    page: int = 1,
    limit: int = 20
):
    def query():
        conn = get_connection()
        try:
            # First, get total count for pagination
            count_sql = "SELECT COUNT(*) FROM devices"
            clauses: list[str] = []
            params: list[object] = []
            
            if device_type:
                clauses.append("device_type = ?")
                params.append(device_type)
            if status:
                clauses.append("status = ?")
                params.append(status)
            if search:
                clauses.append("(ip ILIKE ? OR mac ILIKE ? OR name ILIKE ? OR display_name ILIKE ? OR vendor ILIKE ?)")
                # Support multi-word wild search by replacing spaces with %
                search_param = f"%{search.strip().replace(' ', '%')}%"
                params.extend([search_param] * 5)
            
            if clauses:
                count_sql += " WHERE " + " AND ".join(clauses)
                
            total = conn.execute(count_sql, params).fetchone()[0]
            
            # Calculate global stats for top cards
            global_stats = {
                "total": conn.execute("SELECT COUNT(*) FROM devices").fetchone()[0],
                "online": conn.execute("SELECT COUNT(*) FROM devices WHERE status = 'online'").fetchone()[0],
                "offline": conn.execute("SELECT COUNT(*) FROM devices WHERE status = 'offline'").fetchone()[0],
                "untrusted": conn.execute("SELECT COUNT(*) FROM devices WHERE is_trusted = FALSE").fetchone()[0],
                "trusted": conn.execute("SELECT COUNT(*) FROM devices WHERE is_trusted = TRUE").fetchone()[0],
                "new_24h": conn.execute("SELECT COUNT(*) FROM devices WHERE first_seen > now() - interval '24 hours'").fetchone()[0],
                "total_ports": conn.execute("SELECT COUNT(*) FROM device_ports").fetchone()[0]
            }
            vendor_row = conn.execute("""
                SELECT vendor, COUNT(*) as count 
                FROM devices 
                WHERE vendor IS NOT NULL AND vendor != 'Unknown' AND vendor != ''
                GROUP BY vendor ORDER BY count DESC LIMIT 1
            """).fetchone()
            global_stats["top_vendor"] = vendor_row[0] if vendor_row else "None"
            global_stats["top_vendor_count"] = vendor_row[1] if vendor_row else 0
            global_stats["unique_vendors"] = conn.execute("SELECT COUNT(DISTINCT vendor) FROM devices WHERE vendor IS NOT NULL AND vendor != 'Unknown' AND vendor != ''").fetchone()[0]

            # Now fetch the data
            base_sql = """
                SELECT id, ip, mac, name, display_name, device_type,
                       first_seen, last_seen, vendor, icon, open_ports, status, ip_type, attributes, is_trusted
                FROM devices
            """
            if clauses:
                base_sql += " WHERE " + " AND ".join(clauses)
                
            # Validate sort_by to prevent injection
            allowed_sort = ["ip", "mac", "display_name", "device_type", "last_seen", "status", "vendor"]
            if sort_by not in allowed_sort:
                safe_sort = "ip"
            else:
                safe_sort = sort_by
                
            order = "DESC" if sort_order.lower() == "desc" else "ASC"
            
            if safe_sort == "ip":
                # Use numerical IP sorting via INET cast
                # Use TRY_CAST to be safe against invalid IP strings (though we try to keep them valid)
                base_sql += f" ORDER BY TRY_CAST(ip AS INET) {order}"
            else:
                base_sql += f" ORDER BY {safe_sort} {order}"
            
            # Pagination
            if limit > 0:
                offset = (page - 1) * limit
                base_sql += " LIMIT ? OFFSET ?"
                params.extend([limit, offset])
            
            rows = conn.execute(base_sql, params).fetchall()
            items = []
            device_ids = [r[0] for r in rows]
            
            # Fetch traffic history for sparklines (last 20 points)
            traffic_map = {}
            if device_ids:
                placeholders = ','.join(['?'] * len(device_ids))
                # optimization: ensure we have an index on device_id, timestamp
                hist_sql = f"""
                    SELECT device_id, down_rate, up_rate, timestamp
                    FROM device_traffic_history
                    WHERE device_id IN ({placeholders})
                    QUALIFY ROW_NUMBER() OVER (PARTITION BY device_id ORDER BY timestamp DESC) <= 20
                """
                hist_rows = conn.execute(hist_sql, device_ids).fetchall()
                for h_r in hist_rows:
                    did, down, up, ts = h_r
                    if did not in traffic_map: traffic_map[did] = []
                    # We want chronological order for charts
                    traffic_map[did].append({"down": down, "up": up, "timestamp": ts})
                
                # Sort each list by timestamp asc
                for did in traffic_map:
                    traffic_map[did].sort(key=lambda x: x["timestamp"])

            items = [
                DeviceRead(
                    id=r[0], ip=r[1], mac=r[2], name=r[3], display_name=r[4], device_type=r[5],
                    first_seen=r[6], last_seen=r[7], vendor=r[8], icon=r[9],
                    open_ports=json.loads(r[10]) if r[10] else [],
                    status=r[11],
                    ip_type=r[12],
                    attributes=json.loads(r[13]) if r[13] else {},
                    is_trusted=r[14] if r[14] is not None else False,
                    traffic_history=traffic_map.get(r[0], [])
                )
                for r in rows
            ]
            
            # Calculate total pages correctly
            total_pages = 1
            if limit > 0:
                total_pages = math.ceil(total / limit) if total > 0 else 1

            return PaginatedDevicesResponse(
                items=items,
                total=total,
                page=page,
                limit=limit if limit > 0 else total,
                total_pages=total_pages,
                global_stats=global_stats
            )
        finally:
            conn.close()
    return await asyncio.to_thread(query)

@router.get("/", response_model=PaginatedDevicesResponse)
async def list_devices(
    device_type: Annotated[str | None, Query()] = None,
    status: Annotated[str | None, Query()] = None,
    search: Annotated[str | None, Query()] = None,
    sort_by: Annotated[str, Query()] = "ip",
    sort_order: Annotated[str, Query()] = "asc",
    page: Annotated[int, Query(ge=1)] = 1,
    limit: Annotated[int, Query(ge=-1)] = 20,
):
    return await _internal_list_devices(
        device_type=device_type, 
        status=status, 
        search=search,
        sort_by=sort_by,
        sort_order=sort_order,
        page=page,
        limit=limit
    )

@router.get("/{device_id}", response_model=DeviceRead)
async def get_device(device_id: str):
    def query():
        conn = get_connection()
        try:
            row = conn.execute(
                """
                SELECT id, ip, mac, name, display_name, device_type,
                       first_seen, last_seen, vendor, icon, open_ports, status, ip_type, attributes, is_trusted
                FROM devices WHERE id = ?
                """,
                [device_id],
            ).fetchone()
            if not row:
                raise HTTPException(status_code=404, detail="Device not found")
            ports_rows = conn.execute("SELECT port, service, protocol FROM device_ports WHERE device_id = ? ORDER BY port", [device_id]).fetchall()
            detailed_ports = [{"port": r[0], "service": r[1], "protocol": r[2]} for r in ports_rows] if ports_rows else (json.loads(row[10]) if row[10] else [])
            
            # Traffic History for details (last 100 points or 24h)
            h_rows = conn.execute("""
                SELECT down_rate, up_rate, timestamp 
                FROM device_traffic_history 
                WHERE device_id = ? 
                ORDER BY timestamp DESC LIMIT 200
            """, [device_id]).fetchall()
            
            traffic = [{"down": hr[0], "up": hr[1], "timestamp": hr[2]} for hr in h_rows]
            traffic.sort(key=lambda x: x["timestamp"])

            return DeviceRead(
                id=row[0], ip=row[1], mac=row[2], name=row[3], display_name=row[4], device_type=row[5],
                first_seen=row[6], last_seen=row[7], vendor=row[8], icon=row[9],
                open_ports=detailed_ports, status=row[11],
                ip_type=row[12],
                attributes=json.loads(row[13]) if row[13] else {},
                is_trusted=row[14] if row[14] is not None else False,
                traffic_history=traffic
            )
        finally:
            conn.close()
    try:
        return await asyncio.to_thread(query)
    except HTTPException as e: raise e

@router.patch("/{device_id}", response_model=DeviceRead)
async def update_device_by_patch(device_id: str, update_data: DeviceUpdate):
    fields = {k: v for k, v in update_data.model_dump().items() if v is not None}
    if not fields: raise HTTPException(status_code=400, detail="No fields provided for update")
    
    # If attributes is a dict, stringify it for the service/DB
    if fields.get("attributes") is not None:
        if isinstance(fields["attributes"], dict):
            fields["attributes"] = json.dumps(fields["attributes"])
        elif not isinstance(fields["attributes"], str):
            fields["attributes"] = json.dumps(fields["attributes"])
        
    updated_device = await update_device_fields(device_id, fields)
    if not updated_device: raise HTTPException(status_code=404, detail="Device not found")
    return await get_device(device_id)

@router.put("/{device_id}", response_model=DeviceRead)
async def update_device_by_put(device_id: str, update_data: DeviceUpdate):
    """Identical to PATCH to support frontend axios.put calls."""
    return await update_device_by_patch(device_id, update_data)

@router.get("/export/json")
async def export_devices():
    return await _internal_list_devices(limit=-1)

@router.post("/import/json")
async def import_devices(devices_data: List[DeviceRead]):
    def sync_import():
        conn = get_connection()
        try:
            count = 0
            for d in devices_data:
                # Store as string in DB
                attrs_raw = json.dumps(d.attributes) if d.attributes else "{}"
                conn.execute(
                    """
                    INSERT OR REPLACE INTO devices 
                    (id, ip, mac, name, display_name, device_type, first_seen, last_seen, vendor, icon, status, ip_type, open_ports, attributes, is_trusted)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    [
                        d.id, d.ip, d.mac, d.name, d.display_name, d.device_type,
                        d.first_seen, d.last_seen, d.vendor, d.icon, d.status, d.ip_type, json.dumps(d.open_ports), attrs_raw, d.is_trusted
                    ]
                )
                count += 1
            from app.core.db import commit
            commit()
            return count
        finally:
            conn.close()
    count = await asyncio.to_thread(sync_import)
    return {"status": "success", "imported": count}

@router.delete("/{device_id}")
async def delete_device(device_id: str):
    def sync_delete():
        conn = get_connection()
        try:
            row = conn.execute("SELECT id FROM devices WHERE id = ?", [device_id]).fetchone()
            if not row: raise HTTPException(status_code=404, detail="Device not found")
            conn.execute("DELETE FROM device_ports WHERE device_id = ?", [device_id])
            conn.execute("DELETE FROM device_status_history WHERE device_id = ?", [device_id])
            conn.execute("DELETE FROM devices WHERE id = ?", [device_id])
            from app.core.db import commit
            commit()
        finally:
            conn.close()
    try:
        await asyncio.to_thread(sync_delete)
        return {"status": "success", "message": f"Device {device_id} deleted"}
    except HTTPException as e: raise e

@router.post("/onboard")
async def onboard_discovered_device(data: Dict[str, Any], current_user: Any = Depends(get_current_user)):
    """
    Onboard a newly discovered device. 
    Triggers an immediate deep scan.
    """
    ip = data.get("ip")
    mac = data.get("mac")
    hostname = data.get("hostname")
    
    if not ip or not mac:
        raise HTTPException(status_code=400, detail="IP and MAC are required")
    
    from app.services.devices import upsert_device_from_scan
    from app.services.scans import scan_device
    
    # 1. Immediate simple upsert
    device_id = await upsert_device_from_scan(ip, mac, hostname, [])
    
    # 2. Trigger deep scan in background
    asyncio.create_task(scan_device(device_id, ip))
    
    return {"status": "success", "device_id": device_id}
