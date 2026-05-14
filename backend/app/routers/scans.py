from fastapi import APIRouter, HTTPException
from app.core.db import get_connection
from app.models.scans import ScanCreate, ScanRead, ScanResultRead, PaginatedScansResponse
from datetime import datetime, timezone
from app.core.date_utils import now as utc_now
import json, uuid, asyncio
from typing import List
from app.services.scans import scan_device

router = APIRouter()

@router.get("/gist")
async def get_scan_gist():
    def query():
        conn = get_connection()
        try:
            total_count = conn.execute("SELECT COUNT(*) FROM scans").fetchone()[0]
            done_count = conn.execute("SELECT COUNT(*) FROM scans WHERE status = 'done'").fetchone()[0]
            running_count = conn.execute("SELECT COUNT(*) FROM scans WHERE status IN ('running', 'queued')").fetchone()[0]
            
            latest_row = conn.execute(
                """
                SELECT id, started_at, finished_at, target
                FROM scans
                WHERE status = 'done'
                ORDER BY finished_at DESC
                LIMIT 1
                """
            ).fetchone()
            
            last_scan_time = latest_row[2] if latest_row else None
            
            return {
                "total_scans": total_count,
                "scans_done": done_count,
                "scans_running": running_count,
                "last_scan_time": last_scan_time,
                "has_scan": latest_row is not None
            }
        finally:
            conn.close()
    return await asyncio.to_thread(query)

@router.post("/discovery")
async def trigger_discovery():
    def get_discovery_target():
        conn = get_connection()
        try:
            row = conn.execute("SELECT value FROM config WHERE key = 'scan_subnets'").fetchone()
            target = None
            if row and row[0]:
                try:
                    subnets = json.loads(row[0])
                    if isinstance(subnets, list) and subnets:
                        target = " ".join(subnets)
                except:
                    target = row[0]
            
            if not target:
                target_row = conn.execute("SELECT value FROM config WHERE key = 'scan_target'").fetchone()
                target = target_row[0] if target_row else None
            
            if not target:
                from app.core.config import get_settings
                target = get_settings().default_subnet
            return target
        finally:
            conn.close()

    target = await asyncio.to_thread(get_discovery_target)
    from app.services.worker import enqueue_scan
    scan_id = await enqueue_scan(target, "arp")
    
    if not scan_id:
        return {"status": "already_active", "message": "A scan is already in progress for this target.", "target": target}
    return {"status": "enqueued", "scan_id": scan_id, "target": target}

@router.post("/", response_model=ScanRead)
async def create_scan(payload: ScanCreate):
    def sync_create():
        conn = get_connection()
        try:
            scan_id = str(uuid.uuid4())
            now = utc_now()
            options_json = json.dumps(payload.options) if payload.options else None
            conn.execute(
                "INSERT INTO scans (id, target, scan_type, options, status, created_at) VALUES (?, ?, ?, ?, 'queued', ?)",
                [scan_id, payload.target, payload.scan_type, options_json, now],
            )
            conn.commit()
            return scan_id, now
        finally:
            conn.close()
            
    scan_id, now = await asyncio.to_thread(sync_create)
    return ScanRead(
        id=scan_id, target=payload.target, scan_type=payload.scan_type,
        options=payload.options, status="queued", created_at=now,
        started_at=None, finished_at=None, error_message=None
    )

@router.get("/", response_model=PaginatedScansResponse)
async def list_scans(page: int = 1, limit: int = 20):
    def query():
        offset = (page - 1) * limit
        conn = get_connection()
        try:
            total = conn.execute("SELECT COUNT(*) FROM scans").fetchone()[0]
            rows = conn.execute(
                """
                SELECT id, target, scan_type, options, status,
                       created_at, started_at, finished_at, error_message
                FROM scans 
                ORDER BY created_at DESC
                LIMIT ? OFFSET ?
                """,
                [limit, offset]
            ).fetchall()
            return total, rows
        finally:
            conn.close()

    total, rows = await asyncio.to_thread(query)
    items = []
    for r in rows:
        try:
            opts = None
            if r[3]:
                try: opts = json.loads(r[3])
                except: opts = {"raw": str(r[3])}

            items.append(ScanRead(
                id=r[0], target=str(r[1]), scan_type=str(r[2]), options=opts, status=str(r[4]),
                created_at=r[5], started_at=r[6], finished_at=r[7], error_message=r[8]
            ))
        except: continue
            
    return PaginatedScansResponse(
        items=items, total=total, page=page, limit=limit,
        total_pages=(total + limit - 1) // limit
    )

@router.get("/{scan_id}/results", response_model=List[ScanResultRead])
async def get_scan_results(scan_id: str):
    def query():
        conn = get_connection()
        try:
            rows = conn.execute(
                """
                SELECT id, scan_id, ip, mac, hostname, open_ports, os, first_seen, last_seen
                FROM scan_results
                WHERE scan_id = ?
                """,
                [scan_id]
            ).fetchall()
            
            results = []
            for r in rows:
                try:
                    ports = json.loads(r[5]) if r[5] else []
                    results.append(ScanResultRead(
                        id=r[0], scan_id=r[1], ip=r[2], mac=r[3], hostname=r[4],
                        open_ports=ports, os=r[6], first_seen=r[7], last_seen=r[8]
                    ))
                except: continue
            return results
        finally:
            conn.close()
    return await asyncio.to_thread(query)

@router.get("/{scan_id}", response_model=ScanRead)
async def get_scan(scan_id: str):
    def query():
        conn = get_connection()
        try:
            row = conn.execute(
                "SELECT id, target, scan_type, options, status, created_at, started_at, finished_at, error_message FROM scans WHERE id = ?",
                [scan_id]
            ).fetchone()
            return row
        finally:
            conn.close()
    row = await asyncio.to_thread(query)
    if not row:
        raise HTTPException(status_code=404, detail="Scan not found")
        
    opts = None
    if row[3]:
        try: opts = json.loads(row[3])
        except: opts = {"raw": str(row[3])}

    return ScanRead(
        id=row[0], target=str(row[1]), scan_type=str(row[2]), options=opts, status=str(row[4]),
        created_at=row[5], started_at=row[6], finished_at=row[7], error_message=row[8]
    )

@router.post("/audit/{device_id}")
async def trigger_device_audit(device_id: str):
    def get_details():
        conn = get_connection()
        try:
            row = conn.execute("SELECT ip FROM devices WHERE id = ?", [device_id]).fetchone()
            return row[0] if row else None
        finally:
            conn.close()
    
    ip = await asyncio.to_thread(get_details)
    if not ip:
        raise HTTPException(status_code=404, detail="Device not found")
    
    # Run deep scan
    ports = await scan_device(device_id, ip)
    return {"status": "done", "ports": ports}

@router.delete("/queue")
async def clear_scan_queue():
    def sync_cancel_all():
        conn = get_connection()
        try:
            conn.execute(
                "UPDATE scans SET status = 'interrupted', finished_at = ?, error_message = 'Batch canceled' WHERE status = 'queued'",
                [utc_now()]
            )
            conn.commit()
        finally:
            conn.close()
    await asyncio.to_thread(sync_cancel_all)
    return {"status": "success", "message": "All queued scans marked as cancelled"}

@router.delete("/{scan_id}")
async def cancel_scan(scan_id: str):
    def sync_cancel():
        conn = get_connection()
        try:
            # Check status
            row = conn.execute("SELECT status FROM scans WHERE id = ?", [scan_id]).fetchone()
            if not row:
                raise HTTPException(status_code=404, detail="Scan not found")
            
            # User wants to mark as cancelled, never delete.
            # Only allowed for queued or running scans.
            if row[0] in ('running', 'queued'):
                conn.execute(
                    "UPDATE scans SET status = 'interrupted', finished_at = ?, error_message = 'Canceled by user' WHERE id = ?", 
                    [utc_now(), scan_id]
                )
                conn.commit()
                return {"status": "success", "message": "Scan marked as cancelled"}
            else:
                raise HTTPException(status_code=400, detail="Finished scans cannot be modified")
        finally:
            conn.close()
    return await asyncio.to_thread(sync_cancel)

@router.delete("/")
async def clear_all_history():
    def sync_delete():
        conn = get_connection()
        try:
            conn.execute("DELETE FROM scan_results")
            conn.execute("DELETE FROM scans")
            conn.commit()
        finally:
            conn.close()
    await asyncio.to_thread(sync_delete)
    return {"status": "success", "message": "All scan history cleared"}
