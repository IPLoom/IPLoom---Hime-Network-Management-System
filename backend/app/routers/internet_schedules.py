from fastapi import APIRouter, HTTPException, Depends
from typing import List
from app.models.internet_schedules import DeviceBlockScheduleCreate, DeviceBlockScheduleUpdate, DeviceBlockScheduleRead
from app.services.internet_schedules import create_schedule, get_schedule, get_device_schedules, update_schedule, delete_schedule
from app.core.auth import get_current_user

router = APIRouter()

@router.get("/devices/{device_id}/schedules", response_model=List[DeviceBlockScheduleRead])
async def list_device_schedules(device_id: str):
    return await get_device_schedules(device_id)

@router.post("/devices/{device_id}/schedules", response_model=DeviceBlockScheduleRead)
async def add_schedule(device_id: str, schedule: DeviceBlockScheduleCreate):
    if schedule.device_id != device_id:
        raise HTTPException(status_code=400, detail="Device ID mismatch")
    return await create_schedule(schedule)

@router.get("/schedules/{schedule_id}", response_model=DeviceBlockScheduleRead)
async def get_single_schedule(schedule_id: str):
    s = await get_schedule(schedule_id)
    if not s:
        raise HTTPException(status_code=404, detail="Schedule not found")
    return s

@router.patch("/schedules/{schedule_id}", response_model=DeviceBlockScheduleRead)
async def update_single_schedule(schedule_id: str, update: DeviceBlockScheduleUpdate):
    s = await update_schedule(schedule_id, update)
    if not s:
        raise HTTPException(status_code=404, detail="Schedule not found")
    return s

@router.delete("/schedules/{schedule_id}")
async def remove_schedule(schedule_id: str):
    success = await delete_schedule(schedule_id)
    if not success:
        raise HTTPException(status_code=404, detail="Schedule not found")
    return {"status": "success"}
