from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime

class DeviceBlockScheduleBase(BaseModel):
    name: Optional[str] = None
    start_time: str = Field(..., pattern=r"^\d{2}:\d{2}$") # HH:MM
    end_time: str = Field(..., pattern=r"^\d{2}:\d{2}$")   # HH:MM
    days: str = Field(..., pattern=r"^([0-6],?)+$")       # 0,1,2,3,4,5,6
    enabled: bool = True

class DeviceBlockScheduleCreate(DeviceBlockScheduleBase):
    device_id: str

class DeviceBlockScheduleUpdate(BaseModel):
    name: Optional[str] = None
    start_time: Optional[str] = Field(None, pattern=r"^\d{2}:\d{2}$")
    end_time: Optional[str] = Field(None, pattern=r"^\d{2}:\d{2}$")
    days: Optional[str] = Field(None, pattern=r"^([0-6],?)+$")
    enabled: Optional[bool] = None

class DeviceBlockScheduleRead(DeviceBlockScheduleBase):
    id: str
    device_id: str
    created_at: datetime

    class Config:
        from_attributes = True
