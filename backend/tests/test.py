

import os
import json
import logging
import sys
from logging_config import setup_logging
from pathlib import Path

import time

import uuid
import traceback
from datetime import datetime, timedelta
from typing import Optional, List, Set, Dict, Any

import socketio  # python-socketio
from fastapi import (
    FastAPI,
    File,
    UploadFile,
    HTTPException,
    Depends,
    status,
    BackgroundTasks,
    Request,
    Response,
    WebSocket
)
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordRequestForm
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import JSONResponse

from passlib.context import CryptContext
from dotenv import load_dotenv

import aiofiles


import schemas

from dependencies import get_current_user_response, get_current_user_db

# Load environment variables
load_dotenv()

# Initialize logging

logging.info("Starting Chat App API")
logging.error("Starting Chat App API")
