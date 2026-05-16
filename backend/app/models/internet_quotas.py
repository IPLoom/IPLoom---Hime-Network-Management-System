from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime

class DeviceQuotaBase(BaseModel):
    limit_bytes: int = Field(..., description="Data limit in bytes")
    period_hours: int = Field(default=24, description="Reset period in hours")
    enabled: bool = True

class DeviceQuotaCreate(DeviceQuotaBase):
    device_id: str

class DeviceQuotaUpdate(BaseModel):
    limit_bytes: Optional[int] = None
    period_hours: Optional[int] = None
    enabled: Optional[bool] = None

class DeviceQuota(DeviceQuotaBase):
    id: str
    device_id: str
    current_usage: int
    last_reset_at: datetime
    is_exceeded: bool

    class Config:
        from_attributes = True

class DeviceQuotaStatus(BaseModel):
    device_id: str
    limit_bytes: int
    current_usage: int
    percent_used: float
    is_exceeded: bool
    last_reset_at: datetime
    next_reset_at: datetime
    is_manual_block: bool
    is_scheduled_block: bool
