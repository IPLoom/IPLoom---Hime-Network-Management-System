from datetime import datetime, timedelta, timezone
from app.core.date_utils import now as utc_now
from typing import Optional, Union, Any
from jose import jwt, JWTError
import bcrypt

# Monkeypatch bcrypt for passlib compatibility on Python 3.12+
if not hasattr(bcrypt, "__about__"):
    bcrypt.__about__ = type('about', (object,), {'__version__': bcrypt.__version__})

from passlib.context import CryptContext
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from app.core.config import get_settings
from app.core.db import get_connection

settings = get_settings()

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/v1/auth/login")

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    if expires_delta:
        expire = utc_now() + expires_delta
    else:
        expire = utc_now() + timedelta(minutes=settings.access_token_expire_minutes)
    
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.secret_key, algorithm=settings.algorithm)
    return encoded_jwt

async def get_current_user(token: str = Depends(oauth2_scheme)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, settings.secret_key, algorithms=[settings.algorithm])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    
    # Get user from DB
    def query():
        conn = get_connection()
        try:
            row = conn.execute("SELECT id, username, full_name, region, is_active FROM users WHERE username = ?", [username]).fetchone()
            if row:
                return {
                    "id": row[0],
                    "username": row[1],
                    "full_name": row[2],
                    "region": row[3],
                    "is_active": row[4]
                }
            return None
        finally:
            conn.close()
            
    user = query()
    if user is None:
        raise credentials_exception
    if not user["is_active"]:
        raise HTTPException(status_code=400, detail="Inactive user")
    
    return user
