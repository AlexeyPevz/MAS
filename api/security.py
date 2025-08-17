"""
Security module for Root-MAS API
"""
from datetime import datetime, timedelta, timezone
from typing import Optional, Dict, Any
import secrets
import hashlib
import jwt
from fastapi import HTTPException, Security, Depends, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
import redis
import json
from functools import wraps
import time
import os
from pathlib import Path
import logging

# Configuration
def get_secret_key():
    """Get or create persistent secret key"""
    # Try environment variable first
    secret = os.getenv('MAS_SECRET_KEY')
    if secret:
        return secret
    
    # Try to load from file
    data_dir = Path(os.getenv('DATA_PATH', 'data'))
    data_dir.mkdir(parents=True, exist_ok=True)
    secret_file = data_dir / '.secret_key'
    
    if secret_file.exists():
        return secret_file.read_text().strip()
    
    # Generate new secret and save
    secret = secrets.token_urlsafe(32)
    secret_file.write_text(secret)
    secret_file.chmod(0o600)  # Only owner can read
    return secret

SECRET_KEY = get_secret_key()
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30
REFRESH_TOKEN_EXPIRE_DAYS = 7
TRUST_PROXY = os.getenv('TRUST_PROXY', 'false').lower() in {'1', 'true', 'yes'}
logger = logging.getLogger(__name__)

# Rate limiting configuration
RATE_LIMIT_REQUESTS = int(os.getenv('RATE_LIMIT_REQUESTS', '100'))
RATE_LIMIT_WINDOW = int(os.getenv('RATE_LIMIT_WINDOW', '60'))  # seconds


class Token(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


# Role definitions - moved before TokenData
class Role:
    ADMIN = "admin"
    USER = "user"
    AGENT = "agent"
    READONLY = "readonly"


class TokenData(BaseModel):
    user_id: str
    scopes: list[str] = []
    role: str = Role.USER


class RateLimiter:
    """Rate limiter using Redis or in-memory fallback"""
    
    def __init__(self):
        try:
            self.redis_client = redis.Redis(
                host=os.getenv('REDIS_HOST', 'localhost'),
                port=int(os.getenv('REDIS_PORT', '6379')),
                decode_responses=True
            )
            self.redis_client.ping()
            self.use_redis = True
        except:
            self.use_redis = False
            self.memory_store = {}
    
    def check_rate_limit(self, key: str, limit: int, window: int) -> bool:
        """Check if request is within rate limit"""
        current_time = int(time.time())
        window_start = current_time - window
        
        if self.use_redis:
            # Redis implementation
            pipe = self.redis_client.pipeline()
            pipe.zremrangebyscore(key, 0, window_start)
            pipe.zcard(key)
            pipe.zadd(key, {str(current_time): current_time})
            pipe.expire(key, window)
            results = pipe.execute()
            
            return results[1] < limit
        else:
            # In-memory fallback
            if key not in self.memory_store:
                self.memory_store[key] = []
            
            # Clean old entries
            self.memory_store[key] = [
                t for t in self.memory_store[key] 
                if t > window_start
            ]
            
            if len(self.memory_store[key]) >= limit:
                return False
            
            self.memory_store[key].append(current_time)
            return True

rate_limiter = RateLimiter()

# Permission definitions
PERMISSIONS = {
    Role.ADMIN: ["*"],  # All permissions
    Role.USER: [
        "chat:read", "chat:write",
        "agents:read", "metrics:read",
        "projects:read", "projects:write"
    ],
    Role.AGENT: [
        "chat:read", "chat:write",
        "agents:communicate",
        "memory:read", "memory:write"
    ],
    Role.READONLY: [
        "chat:read", "agents:read",
        "metrics:read", "projects:read"
    ]
}

def check_permission(role: str, permission: str) -> bool:
    """Check if role has permission"""
    if role not in PERMISSIONS:
        return False
    
    role_perms = PERMISSIONS[role]
    if "*" in role_perms:
        return True
    
    return permission in role_perms


class SecurityManager:
    """Main security manager"""
    
    def __init__(self, redis_client: Optional[redis.Redis] = None):
        self.rate_limiter = RateLimiter()
        self.bearer_scheme = HTTPBearer()
        self.blocked_tokens: set = set()
        self.redis_client = redis_client or getattr(self.rate_limiter, 'redis_client', None)
    
    def create_access_token(self, data: dict, expires_delta: Optional[timedelta] = None):
        """Create JWT access token"""
        to_encode = data.copy()
        if expires_delta:
            expire = datetime.now(timezone.utc) + expires_delta
        else:
            expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        
        to_encode.update({
            "exp": expire,
            "iat": datetime.now(timezone.utc),
            "role": data.get("role", Role.USER),
            "type": "access",
            "jti": secrets.token_urlsafe(8),
        })
        
        encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
        return encoded_jwt
    
    def create_refresh_token(self, data: dict):
        """Create JWT refresh token"""
        to_encode = data.copy()
        expire = datetime.now(timezone.utc) + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
        to_encode.update({"exp": expire, "type": "refresh", "jti": secrets.token_urlsafe(8)})
        encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
        return encoded_jwt
    
    def verify_token(self, token: str) -> TokenData:
        """Verify and decode JWT token"""
        try:
            # Check if token is blocked
            if token in self.blocked_tokens:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Token has been revoked"
                )
            
            payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
            # Check Redis-backed jti revocation
            jti = payload.get("jti")
            if jti and self.redis_client is not None:
                try:
                    if self.redis_client.get(f"revoked:{jti}"):
                        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token has been revoked")
                except Exception:
                    pass
            user_id: str = payload.get("sub")
            if user_id is None:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid token"
                )
            
            return TokenData(user_id=user_id, scopes=payload.get("scopes", []), role=payload.get("role", Role.USER))
            
        except jwt.ExpiredSignatureError:
            logger.warning("Auth failed: token expired")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token has expired"
            )
        except jwt.JWTError:
            logger.warning("Auth failed: invalid token")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token"
            )
    
    def revoke_token(self, token: str):
        """Revoke a token"""
        try:
            payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM], options={"verify_signature": False})
            exp = payload.get("exp")
            jti = payload.get("jti")
            if self.redis_client is not None and jti and exp:
                ttl = max(1, int(exp - time.time()))
                try:
                    self.redis_client.setex(f"revoked:{jti}", ttl, "1")
                    return
                except Exception:
                    pass
        except Exception:
            pass
        # Fallback in-memory
        self.blocked_tokens.add(token)
    
    def hash_password(self, password: str) -> str:
        """Hash password using bcrypt"""
        try:
            import bcrypt
            # Generate salt and hash password
            salt = bcrypt.gensalt()
            hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
            return hashed.decode('utf-8')
        except ImportError:
            # Fallback to SHA-256 if bcrypt not installed (dev only)
            import warnings
            warnings.warn("bcrypt not installed, using SHA-256 (insecure!)")
            return hashlib.sha256(password.encode()).hexdigest()
    
    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """Verify password against hash"""
        try:
            import bcrypt
            # bcrypt verification
            return bcrypt.checkpw(
                plain_password.encode('utf-8'), 
                hashed_password.encode('utf-8')
            )
        except ImportError:
            # Fallback to SHA-256 comparison
            return hashlib.sha256(plain_password.encode()).hexdigest() == hashed_password


# Dependency injection
security_manager = SecurityManager()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security_manager.bearer_scheme)
) -> TokenData:
    """Get current authenticated user"""
    token = credentials.credentials
    return security_manager.verify_token(token)


async def require_scopes(*required_scopes):
    """Require specific scopes for endpoint"""
    async def scope_checker(
        current_user: TokenData = Depends(get_current_user)
    ):
        for scope in required_scopes:
            if scope not in current_user.scopes:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Required scope '{scope}' not found"
                )
        return current_user
    return scope_checker


def rate_limit(max_requests: int = 60, window: int = 60):
    """Rate limiting decorator"""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Extract user identifier (IP or user_id)
            request = kwargs.get('request')
            if request:
                client_ip = request.client.host
                if TRUST_PROXY:
                    fwd = request.headers.get('x-forwarded-for') or request.headers.get('X-Forwarded-For')
                    if fwd:
                        client_ip = fwd.split(',')[0].strip()
                key = f"rate_limit:{client_ip}"
                
                if not security_manager.rate_limiter.check_rate_limit(key, max_requests, window):
                    logger.warning("Rate limit exceeded for %s", client_ip)
                    raise HTTPException(
                        status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                        detail="Rate limit exceeded"
                    )
            
            return await func(*args, **kwargs)
        return wrapper
    return decorator


# Example usage in API endpoints:
"""
@app.post("/api/v1/protected")
@rate_limit(max_requests=10, window=60)
async def protected_endpoint(
    current_user: TokenData = Depends(get_current_user)
):
    return {"message": f"Hello {current_user.user_id}"}

@app.post("/api/v1/admin")
async def admin_endpoint(
    current_user: TokenData = Depends(require_scopes("admin"))
):
    return {"message": "Admin access granted"}
"""

# Dependencies
def auth_user_dependency(current: TokenData = Depends(get_current_user)) -> dict:
    """Return a plain dict with user info for endpoints that accept current_user: dict."""
    return {"user_id": current.user_id, "scopes": current.scopes, "role": current.role}

def rate_limit_dependency(request: Request):
    """Rate limiting dependency"""
    client_ip = request.client.host
    if TRUST_PROXY:
        fwd = request.headers.get('x-forwarded-for') or request.headers.get('X-Forwarded-For')
        if fwd:
            client_ip = fwd.split(',')[0].strip()
    endpoint = request.url.path
    
    # Use combination of IP and endpoint for rate limiting
    rate_limit_key = f"rate_limit:{client_ip}:{endpoint}"
    
    if not rate_limiter.check_rate_limit(
        rate_limit_key, 
        RATE_LIMIT_REQUESTS, 
        RATE_LIMIT_WINDOW
    ):
        logger.warning("Rate limit exceeded for %s on %s", client_ip, endpoint)
        raise HTTPException(
            status_code=429,
            detail=f"Rate limit exceeded. Max {RATE_LIMIT_REQUESTS} requests per {RATE_LIMIT_WINDOW} seconds."
        )

def require_permission(permission: str):
    """Decorator to require specific permission"""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Get current user from kwargs (injected by FastAPI)
            current_user = kwargs.get('current_user')
            if not current_user:
                raise HTTPException(
                    status_code=401,
                    detail="Authentication required"
                )
            
            role = current_user.get('role', Role.USER)
            if not check_permission(role, permission):
                raise HTTPException(
                    status_code=403,
                    detail=f"Permission denied. Required: {permission}"
                )
            
            return await func(*args, **kwargs)
        return wrapper
    return decorator