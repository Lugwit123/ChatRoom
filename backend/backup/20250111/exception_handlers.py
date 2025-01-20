# exception_handlers.py
from fastapi import Request, HTTPException
from fastapi.responses import JSONResponse
import logging

async def http_exception_handler(request: Request, exc: HTTPException):
    logging.error(f"HTTPException: {exc.detail} - Path: {request.url.path}")
    return JSONResponse(status_code=exc.status_code, content={"detail": exc.detail})

async def general_exception_handler(request: Request, exc: Exception):
    logging.error(f"Unhandled exception: {exc} - Path: {request.url.path}")
    return JSONResponse(status_code=500, content={"detail": "Internal Server Error"})
