"""ABC路由模块"""
from fastapi import APIRouter, HTTPException
from typing import Dict, Any, List
import os
import json
import Lugwit_Module as LM

lprint = LM.lprint

router = APIRouter()

@router.get("/")
async def root():
    """根路由"""
    return {"message": "Welcome to ABC Router"}

@router.get("/results")
async def show_results():
    """显示结果"""
    return {"message": "Results page"}

@router.get("/files")
async def list_check_files():
    """列出检查文件"""
    return {"message": "Check files list"}
