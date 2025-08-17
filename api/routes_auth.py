from fastapi import APIRouter, Header, HTTPException, Depends
from .security import Token as AuthTokenModel, security_manager, SECRET_KEY, ALGORITHM
from .security import Role
from pydantic import BaseModel, Field
import jwt
import time
import os
from datetime import timedelta

router = APIRouter(prefix="/api/v1/auth", tags=["auth"])


class AuthRequest(BaseModel):
    user_id: str = Field(..., pattern=r'^[a-zA-Z0-9_-]+$', max_length=100)
    role: str = Field(default=Role.USER, pattern=r'^(admin|user|agent|readonly)$')
    scopes: list[str] = []
    expires_minutes: int | None = Field(default=None, ge=1, le=10080)


class RefreshRequest(BaseModel):
    refresh_token: str


@router.post("/token", response_model=AuthTokenModel)
async def issue_token(request: AuthRequest, x_admin_secret: str = Header(None)):
    expected = os.getenv("ADMIN_SECRET")
    if os.getenv("ENVIRONMENT", "production") == "production":
        if not expected:
            raise HTTPException(status_code=500, detail="ADMIN_SECRET not configured")
        if not x_admin_secret or x_admin_secret != expected:
            raise HTTPException(status_code=403, detail="Invalid or missing X-Admin-Secret header")
    else:
        if expected and x_admin_secret != expected:
            raise HTTPException(status_code=403, detail="Invalid X-Admin-Secret")
    data = {"sub": request.user_id, "role": request.role or Role.USER, "scopes": request.scopes or []}
    expires = timedelta(minutes=request.expires_minutes) if request.expires_minutes else None
    access = security_manager.create_access_token(data, expires)
    refresh = security_manager.create_refresh_token(data)
    return AuthTokenModel(access_token=access, refresh_token=refresh)


@router.post("/refresh", response_model=AuthTokenModel)
async def refresh_token(payload: RefreshRequest):
    decoded = jwt.decode(payload.refresh_token, SECRET_KEY, algorithms=[ALGORITHM])
    if decoded.get("type") != "refresh":
        raise HTTPException(status_code=400, detail="Invalid token type")
    user_id = decoded.get("sub")
    role = decoded.get("role", Role.USER)
    scopes = decoded.get("scopes", [])
    try:
        jti = decoded.get("jti"); exp = decoded.get("exp")
        if jti and getattr(security_manager, 'redis_client', None) is not None and exp:
            ttl = max(1, int(exp - time.time()))
            security_manager.redis_client.setex(f"revoked:{jti}", ttl, "1")
    except Exception:
        pass
    access = security_manager.create_access_token({"sub": user_id, "role": role, "scopes": scopes})
    new_refresh = security_manager.create_refresh_token({"sub": user_id, "role": role, "scopes": scopes})
    return AuthTokenModel(access_token=access, refresh_token=new_refresh)


@router.post("/logout")
async def logout(token: str = Depends(security_manager.bearer_scheme)):
    security_manager.revoke_token(token.credentials)
    return {"status": "revoked"}