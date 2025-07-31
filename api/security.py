"""
Security module for Root-MAS API
"""
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
import secrets
import hashlib
import jwt
from fastapi import HTTPException, Security, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
import redis
from functools import wraps
import time


# Configuration
SECRET_KEY = secrets.token_urlsafe(32)
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30
REFRESH_TOKEN_EXPIRE_DAYS = 7


class Token(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class TokenData(BaseModel):
    user_id: str
    scopes: list[str] = []


class RateLimiter:
    """Rate limiting implementation"""
    
    def __init__(self, redis_client: Optional[redis.Redis] = None):
        self.redis = redis_client
        self.memory_store: Dict[str, list] = {}
    
    def check_rate_limit(self, key: str, max_requests: int = 60, window: int = 60) -> bool:
        """Check if rate limit exceeded"""
        current_time = time.time()
        
        if self.redis:
            # Redis-based rate limiting
            pipe = self.redis.pipeline()
            pipe.zadd(key, {str(current_time): current_time})
            pipe.zremrangebyscore(key, 0, current_time - window)
            pipe.zcard(key)
            pipe.expire(key, window + 1)
            results = pipe.execute()
            
            request_count = results[2]
            return request_count <= max_requests
        else:
            # Memory-based fallback
            if key not in self.memory_store:
                self.memory_store[key] = []
            
            # Clean old entries
            self.memory_store[key] = [
                t for t in self.memory_store[key] 
                if t > current_time - window
            ]
            
            # Check limit
            if len(self.memory_store[key]) >= max_requests:
                return False
            
            self.memory_store[key].append(current_time)
            return True


class SecurityManager:
    """Main security manager"""
    
    def __init__(self, redis_client: Optional[redis.Redis] = None):
        self.rate_limiter = RateLimiter(redis_client)
        self.bearer_scheme = HTTPBearer()
        self.blocked_tokens: set = set()
    
    def create_access_token(self, data: dict, expires_delta: Optional[timedelta] = None):
        """Create JWT access token"""
        to_encode = data.copy()
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        
        to_encode.update({"exp": expire, "type": "access"})
        encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
        return encoded_jwt
    
    def create_refresh_token(self, data: dict):
        """Create JWT refresh token"""
        to_encode = data.copy()
        expire = datetime.utcnow() + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
        to_encode.update({"exp": expire, "type": "refresh"})
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
            user_id: str = payload.get("sub")
            if user_id is None:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid token"
                )
            
            return TokenData(user_id=user_id, scopes=payload.get("scopes", []))
            
        except jwt.ExpiredSignatureError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token has expired"
            )
        except jwt.JWTError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token"
            )
    
    def revoke_token(self, token: str):
        """Revoke a token"""
        self.blocked_tokens.add(token)
    
    def hash_password(self, password: str) -> str:
        """Hash password using SHA-256"""
        return hashlib.sha256(password.encode()).hexdigest()
    
    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """Verify password against hash"""
        return self.hash_password(plain_password) == hashed_password


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
                key = f"rate_limit:{client_ip}"
                
                if not security_manager.rate_limiter.check_rate_limit(key, max_requests, window):
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