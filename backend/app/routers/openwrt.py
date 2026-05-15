from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel
from typing import Optional
from app.services.openwrt import OpenWRTClient
from app.core.db import get_connection
import json
import logging

logger = logging.getLogger(__name__)

router = APIRouter()

class OpenWRTConfig(BaseModel):
    url: str
    username: str
    password: Optional[str] = None
    enabled: bool = True
    interval: int = 15 # minutes
    verified: bool = False

class VerifyRequest(BaseModel):
    url: str
    username: str
    password: Optional[str] = None

@router.get("/config")
def get_config():
    conn = get_connection()
    try:
        conn.execute("CREATE TABLE IF NOT EXISTS integrations (name TEXT PRIMARY KEY, config TEXT)")
        row = conn.execute("SELECT config FROM integrations WHERE name = 'openwrt'").fetchone()
        
        # Also fetch verified status from config table
        v_row = conn.execute("SELECT value FROM config WHERE key = 'openwrt_verified'").fetchone()
        verified = (v_row[0] == "true") if v_row else False
        
        if row:
            conf = json.loads(row[0])
            conf["verified"] = verified
            
            # Mask password
            if conf.get("password"):
                conf["password"] = "*****"
            return conf
            
        return {"verified": verified}
    finally:
        conn.close()

@router.post("/config")
def save_config(config: OpenWRTConfig):
    conn = get_connection()
    try:
        conn.execute("CREATE TABLE IF NOT EXISTS integrations (name TEXT PRIMARY KEY, config TEXT)")
        
        row = conn.execute("SELECT config FROM integrations WHERE name = 'openwrt'").fetchone()
        existing = json.loads(row[0]) if row else {}
        
        new_conf = config.dict()
        if config.password is None or config.password == "*****":
             new_conf["password"] = existing.get("password")
        
        # Merge existing state fields
        for key in ["last_sync", "last_run"]:
            if key in existing and key not in new_conf:
                new_conf[key] = existing[key]
        
        # Auto-verify on save
        verified = False
        if new_conf.get("url") and new_conf.get("enabled", True):
            try:
                client = OpenWRTClient(new_conf["url"], new_conf["username"], new_conf["password"])
                client.login()
                verified = True
            except:
                verified = False

        # Save main config
        conn.execute("INSERT OR REPLACE INTO integrations (name, config) VALUES ('openwrt', ?)", [json.dumps(new_conf)])
        
        # Save verified status to config table
        conn.execute("INSERT OR REPLACE INTO config (key, value) VALUES ('openwrt_verified', ?)", ["true" if verified else "false"])
        
        conn.commit()
        return {"status": "saved", "verified": verified}
    finally:
        conn.close()

@router.post("/verify")
def verify_connection(creds: VerifyRequest):
    try:
        client = OpenWRTClient(creds.url, creds.username, creds.password)
        client.login()
        
        # Update verified status in config table
        conn = get_connection()
        try:
            conn.execute("INSERT OR REPLACE INTO config (key, value) VALUES ('openwrt_verified', 'true')")
            conn.commit()
            
            # Broadcast update
            from app.core.notifications import manager
            manager.broadcast_sync({
                "type": "integration_status",
                "integration": "openwrt",
                "data": { "verified": True }
            })
        finally:
             conn.close()

        return {"status": "success", "message": "Connected successfully", "verified": True}
    except Exception as e:
        # On failure, also update DB to false
        conn = get_connection()
        try:
            conn.execute("INSERT OR REPLACE INTO config (key, value) VALUES ('openwrt_verified', 'false')")
            conn.commit()
            
            # Broadcast update
            from app.core.notifications import manager
            manager.broadcast_sync({
                "type": "integration_status",
                "integration": "openwrt",
                "data": { "verified": False, "error": str(e) }
            })
        finally:
            conn.close()
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/sync")
async def trigger_sync(background_tasks: BackgroundTasks):
    conn = get_connection()
    try:
        row = conn.execute("SELECT config FROM integrations WHERE name = 'openwrt'").fetchone()
        if not row:
            raise HTTPException(status_code=400, detail="OpenWRT not configured")
        
        # Check verified status from config table
        v_row = conn.execute("SELECT value FROM config WHERE key = 'openwrt_verified'").fetchone()
        is_verified = (v_row[0] == "true") if v_row else False
        
        if not is_verified:
             raise HTTPException(status_code=400, detail="Configuration not verified. Please save or test connection first.")
             
        conf = json.loads(row[0])
        # Allow manual sync even if disabled
        # if not conf.get("enabled", True):
        #      raise HTTPException(status_code=400, detail="Integration disabled")
             
        client = OpenWRTClient(conf["url"], conf["username"], conf["password"])
        background_tasks.add_task(client.sync, force=True)
        return {"status": "queued", "message": "Sync started in background"}
    finally:
        conn.close()

def _get_openwrt_client(conn):
    row = conn.execute("SELECT config FROM integrations WHERE name = 'openwrt'").fetchone()
    if not row:
        raise HTTPException(status_code=400, detail="OpenWRT not configured")
    v_row = conn.execute("SELECT value FROM config WHERE key = 'openwrt_verified'").fetchone()
    is_verified = (v_row[0] == "true") if v_row else False
    if not is_verified:
         raise HTTPException(status_code=400, detail="Configuration not verified.")
    conf = json.loads(row[0])
    return OpenWRTClient(conf["url"], conf["username"], conf["password"])

@router.post("/devices/{mac}/block")
def block_device_endpoint(mac: str):
    if not mac or mac.lower() in ['unknown', 'n/a']:
        raise HTTPException(status_code=400, detail="Invalid MAC address")
    conn = get_connection()
    try:
        client = _get_openwrt_client(conn)
        res = client.block_device(mac)
        if res is None:
            raise Exception("OpenWRT API call failed")
        
        # Update DB
        conn.execute("UPDATE devices SET is_blocked = TRUE WHERE mac = ?", [mac.lower()])
        conn.commit()
        
        # Broadcast
        from app.core.notifications import manager
        manager.broadcast_sync({"type": "device_blocked", "mac": mac.lower()})
        
        return {"status": "success", "message": f"Device {mac} blocked successfully."}
    except Exception as e:
        logger.error(f"Failed to block device: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to block device: {str(e)}")
    finally:
        conn.close()

@router.post("/devices/{mac}/unblock")
def unblock_device_endpoint(mac: str):
    if not mac or mac.lower() in ['unknown', 'n/a']:
        raise HTTPException(status_code=400, detail="Invalid MAC address")
    conn = get_connection()
    try:
        client = _get_openwrt_client(conn)
        res = client.unblock_device(mac)
        if res is None:
            raise Exception("OpenWRT API call failed")
        
        # Update DB
        conn.execute("UPDATE devices SET is_blocked = FALSE WHERE mac = ?", [mac.lower()])
        conn.commit()
        
        # Broadcast
        from app.core.notifications import manager
        manager.broadcast_sync({"type": "device_unblocked", "mac": mac.lower()})
        
        return {"status": "success", "message": f"Device {mac} unblocked successfully."}
    except Exception as e:
        logger.error(f"Failed to unblock device: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to unblock device: {str(e)}")
    finally:
        conn.close()
