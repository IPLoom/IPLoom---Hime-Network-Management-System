from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class DeviceRead(BaseModel):
    id: str
    ip: str
    mac: Optional[str] = None
    name: Optional[str] = None
    display_name: Optional[str] = None
    device_type: Optional[str] = None
    first_seen: Optional[datetime] = None
    last_seen: Optional[datetime] = None
    vendor: Optional[str] = None
    icon: Optional[str] = None
    status: Optional[str] = "unknown"
    is_trusted: bool = False
    ip_type: Optional[str] = None
    open_ports: Optional[list] = []
    attributes: Optional[dict] = {}
    traffic_history: Optional[list] = [] # List of {down: int, up: int, timestamp: datetime}
    brand: Optional[str] = None
    brand_icon: Optional[str] = None
    parent_id: Optional[str] = None
    is_blocked: bool = False
    has_schedule: bool = False
    is_manual_block: bool = False
    is_scheduled_block: bool = False
    is_quota_exceeded: bool = False
    is_manual_unblock: bool = False
    quota: Optional[dict] = None # {limit_bytes: int, current_usage: int, enabled: bool}

class DeviceUpdate(BaseModel):
    name: Optional[str] = None
    display_name: Optional[str] = None
    device_type: Optional[str] = None
    vendor: Optional[str] = None
    icon: Optional[str] = None
    ip_type: Optional[str] = None
    is_trusted: Optional[bool] = None
    attributes: Optional[dict] = None
    brand: Optional[str] = None
    brand_icon: Optional[str] = None
    parent_id: Optional[str] = None
    open_ports: Optional[list] = None
    is_blocked: Optional[bool] = None

class PaginatedDevicesResponse(BaseModel):
    items: list[DeviceRead]
    total: int
    page: int
    limit: int
    total_pages: int
    global_stats: Optional[dict] = None
