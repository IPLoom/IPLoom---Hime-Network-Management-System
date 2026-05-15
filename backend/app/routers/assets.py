import uuid
import shutil
from pathlib import Path
from typing import List, Dict, Any
from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from app.core.db import get_connection, commit

from app.core.config import get_settings

router = APIRouter(tags=["Assets"])
settings = get_settings()

UPLOAD_DIR = Path(settings.assets_dir)

@router.post("/upload")
async def upload_asset(
    name: str = Form(...),
    type: str = Form(...), # 'brand' or 'device'
    file: UploadFile = File(...)
):
    if type not in ['brand', 'device']:
        raise HTTPException(status_code=400, detail="Invalid asset type. Must be 'brand' or 'device'.")

    # Validate file extension
    ext = Path(file.filename).suffix.lower()
    if ext not in ['.svg', '.png', '.jpg', '.jpeg']:
        raise HTTPException(status_code=400, detail="Invalid file type. Supported: SVG, PNG, JPG.")

    # Save file
    target_dir = UPLOAD_DIR / f"{type}_icons"
    target_dir.mkdir(parents=True, exist_ok=True)
    
    file_id = str(uuid.uuid4())
    file_path = target_dir / f"{file_id}{ext}"
    
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    # Relative path for serving
    asset_path = f"/static/{type}_icons/{file_id}{ext}"

    # Store in DB
    conn = get_connection()
    try:
        conn.execute(
            "INSERT INTO custom_assets (id, name, type, path) VALUES (?, ?, ?, ?)",
            [file_id, name, type, asset_path]
        )
        commit()
    except Exception as e:
        # Cleanup file if DB insert fails
        if file_path.exists(): file_path.unlink()
        raise HTTPException(status_code=500, detail=f"Database error: {e}")
    finally:
        conn.close()

    return {"id": file_id, "name": name, "type": type, "path": asset_path}

@router.get("")
async def list_assets(type: str = None):
    conn = get_connection()
    try:
        query = "SELECT id, name, type, path, created_at FROM custom_assets"
        params = []
        if type:
            query += " WHERE type = ?"
            params.append(type)
        
        rows = conn.execute(query, params).fetchall()
        return [
            {
                "id": r[0],
                "name": r[1],
                "type": r[2],
                "path": r[3],
                "created_at": r[4]
            } for r in rows
        ]
    finally:
        conn.close()

@router.delete("/{asset_id}")
async def delete_asset(asset_id: str):
    conn = get_connection()
    try:
        row = conn.execute("SELECT path FROM custom_assets WHERE id = ?", [asset_id]).fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Asset not found.")
        
        asset_path = row[0]
        # Delete from filesystem
        relative_path = asset_path.replace("/static/", "")
        full_path = Path(settings.assets_dir) / relative_path
        if full_path.exists():
            full_path.unlink()
            
        # Delete from DB
        conn.execute("DELETE FROM custom_assets WHERE id = ?", [asset_id])
        commit()
    finally:
        conn.close()
    
    return {"status": "success"}
