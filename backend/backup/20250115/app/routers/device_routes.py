from fastapi import APIRouter, Depends, HTTPException
from typing import Dict, Any, List
from sqlalchemy import select
from app.db import schemas
from app.core.auth import get_current_user
from app.db.db_connection import async_session
import Lugwit_Module as LM

lprint = LM.lprint

router = APIRouter()

@router.get("/users/{username}/devices", response_model=List[schemas.DeviceResponse])
async def get_user_devices(
    username: str,
    current_user: schemas.UserBase = Depends(get_current_user)
):
    """获取用户的所有登录设备"""
    # 检查权限
    if current_user.username != username and current_user.role != schemas.UserRole.admin:
        raise HTTPException(status_code=403, detail="没有权限查看其他用户的设备信息")
    
    async with async_session() as session:
        # 获取用户
        result = await session.execute(
            select(schemas.User).where(schemas.User.username == username)
        )
        user = result.scalar_one_or_none()
        if not user:
            raise HTTPException(status_code=404, detail="用户不存在")
        
        # 获取设备列表
        result = await session.execute(
            select(schemas.Device).where(schemas.Device.user_id == user.id)
        )
        devices = result.scalars().all()
        return devices

@router.post("/users/{username}/devices", response_model=schemas.DeviceResponse)
async def create_device(
    username: str,
    device: schemas.DeviceCreate,
    current_user: schemas.UserBase = Depends(get_current_user)
):
    """创建新设备"""
    if current_user.username != username:
        raise HTTPException(status_code=403, detail="只能为自己创建设备")
    
    async with async_session() as session:
        # 获取用户
        result = await session.execute(
            select(schemas.User).where(schemas.User.username == username)
        )
        user = result.scalar_one_or_none()
        if not user:
            raise HTTPException(status_code=404, detail="用户不存在")
        
        # 检查设备ID是否已存在
        result = await session.execute(
            select(schemas.Device).where(schemas.Device.device_id == device.device_id)
        )
        if result.scalar_one_or_none():
            raise HTTPException(status_code=400, detail="设备ID已存在")
        
        # 创建新设备
        db_device = schemas.Device(
            device_id=device.device_id,
            device_name=device.device_name,
            device_type=device.device_type,
            login_status=device.login_status,
            user_id=user.id
        )
        session.add(db_device)
        await session.commit()
        await session.refresh(db_device)
        return db_device

@router.put("/users/{username}/devices/{device_id}", response_model=schemas.DeviceResponse)
async def update_device_status(
    username: str,
    device_id: str,
    device: schemas.DeviceCreate,
    current_user: schemas.UserBase = Depends(get_current_user)
):
    """更新设备状态"""
    if current_user.username != username:
        raise HTTPException(status_code=403, detail="只能更新自己的设备状态")
    
    async with async_session() as session:
        # 获取用户
        result = await session.execute(
            select(schemas.User).where(schemas.User.username == username)
        )
        user = result.scalar_one_or_none()
        if not user:
            raise HTTPException(status_code=404, detail="用户不存在")
        
        # 获取设备
        result = await session.execute(
            select(schemas.Device)
            .where(schemas.Device.device_id == device_id)
            .where(schemas.Device.user_id == user.id)
        )
        db_device = result.scalar_one_or_none()
        if not db_device:
            raise HTTPException(status_code=404, detail="设备不存在")
        
        # 更新设备信息
        db_device.device_name = device.device_name
        db_device.device_type = device.device_type
        db_device.login_status = device.login_status
        
        await session.commit()
        await session.refresh(db_device)
        return db_device

@router.delete("/users/{username}/devices/{device_id}")
async def remove_device(
    username: str,
    device_id: str,
    current_user: schemas.UserBase = Depends(get_current_user)
):
    """移除设备"""
    if current_user.username != username:
        raise HTTPException(status_code=403, detail="只能移除自己的设备")
    
    async with async_session() as session:
        # 获取用户
        result = await session.execute(
            select(schemas.User).where(schemas.User.username == username)
        )
        user = result.scalar_one_or_none()
        if not user:
            raise HTTPException(status_code=404, detail="用户不存在")
        
        # 获取设备
        result = await session.execute(
            select(schemas.Device)
            .where(schemas.Device.device_id == device_id)
            .where(schemas.Device.user_id == user.id)
        )
        device = result.scalar_one_or_none()
        if not device:
            raise HTTPException(status_code=404, detail="设备不存在")
        
        # 删除设备
        await session.delete(device)
        await session.commit()
        return {"status": "success"}
