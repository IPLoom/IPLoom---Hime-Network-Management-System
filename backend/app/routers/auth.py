from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from app.core.auth import verify_password, get_password_hash, create_access_token, get_current_user
from app.core.db import get_connection
from app.models.auth import User, UserCreate, Token, SetupStatus
import uuid
import asyncio

router = APIRouter()

@router.post("/login", response_model=Token)
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    def query():
        conn = get_connection()
        try:
            row = conn.execute("SELECT username, hashed_password FROM users WHERE username = ?", [form_data.username]).fetchone()
            if not row:
                return None
            return {"username": row[0], "hashed_password": row[1]}
        finally:
            conn.close()
            
    user = await asyncio.to_thread(query)
    if not user or not verify_password(form_data.password, user["hashed_password"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token = create_access_token(data={"sub": user["username"]})
    return {"access_token": access_token, "token_type": "bearer"}

@router.post("/register", response_model=User)
async def register(user_in: UserCreate):
    # Check if any user exists
    def count_users():
        conn = get_connection()
        try:
            return conn.execute("SELECT count(*) FROM users").fetchone()[0]
        finally:
            conn.close()
            
    count = await asyncio.to_thread(count_users)
    
    # If users exist, we might want to restrict registration to only authenticated admins,
    # but for the "first-time setup" flow, we allow the first one.
    if count > 0:
        # For now, if users exist, registration is closed unless we add admin logic later.
        raise HTTPException(status_code=400, detail="Registration is disabled. An admin account already exists.")

    hashed_pw = get_password_hash(user_in.password)
    user_id = str(uuid.uuid4())
    
    def create_user():
        conn = get_connection()
        try:
            conn.execute(
                "INSERT INTO users (id, username, hashed_password, full_name, region) VALUES (?, ?, ?, ?, ?)",
                [user_id, user_in.username, hashed_pw, user_in.full_name, user_in.region]
            )
            conn.commit()
            return {
                "id": user_id,
                "username": user_in.username,
                "full_name": user_in.full_name,
                "region": user_in.region,
                "is_active": True
            }
        finally:
            conn.close()
            
    return await asyncio.to_thread(create_user)

@router.get("/me", response_model=User)
async def read_users_me(current_user: dict = Depends(get_current_user)):
    return current_user

@router.get("/setup-status", response_model=SetupStatus)
async def get_setup_status():
    def check():
        conn = get_connection()
        try:
            user_count = conn.execute("SELECT count(*) FROM users").fetchone()[0]
            # Check config for onboarding_completed
            onboarding_row = conn.execute("SELECT value FROM config WHERE key = 'onboarding_completed'").fetchone()
            setup_completed = onboarding_row[0] == "true" if onboarding_row else False
            
            return {
                "user_exists": user_count > 0,
                "setup_completed": setup_completed,
                "needs_setup": user_count == 0 or not setup_completed
            }
        finally:
            conn.close()
            
    return await asyncio.to_thread(check)

@router.post("/onboarding-complete")
async def complete_onboarding(current_user: dict = Depends(get_current_user)):
    def update():
        conn = get_connection()
        try:
            conn.execute(
                "INSERT OR REPLACE INTO config (key, value, updated_at) VALUES ('onboarding_completed', 'true', now())"
            )
            conn.commit()
        finally:
            conn.close()
            
    await asyncio.to_thread(update)
    return {"status": "success"}
