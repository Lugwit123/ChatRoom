# dependencies.py
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from authenticate import authenticate_token
import schemas
import Lugwit_Module as LM
lprint=LM.lprint

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")

async def get_current_user_response(token: str = Depends(oauth2_scheme)) -> schemas.UserResponse:
    user_data: schemas.UserBase = await authenticate_token(token)
    if user_data:
        user_response = schemas.UserResponse(**user_data.dict())
        
        return user_response
    else:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

async def get_current_user_db(token: str = Depends(oauth2_scheme)) -> schemas.UserBase:
    user_data: schemas.UserBase = await authenticate_token(token)
    if user_data:
        return user_data
    else:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
