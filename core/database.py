"""
Database connection management with connection pooling
"""
import os
import logging
import asyncio
from typing import Optional, Dict, Any
from contextlib import asynccontextmanager
import redis.asyncio as aioredis
import asyncpg
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.pool import NullPool, QueuePool

from config.settings import (
    REDIS_HOST, REDIS_PORT, REDIS_DB,
    POSTGRES_HOST, POSTGRES_PORT, POSTGRES_USER, POSTGRES_PASSWORD, POSTGRES_DB,
    ENVIRONMENT
)

logger = logging.getLogger(__name__)


class DatabaseManager:
    """Manages database connections with pooling"""
    
    def __init__(self):
        self._redis_pool: Optional[aioredis.ConnectionPool] = None
        self._pg_pool: Optional[asyncpg.Pool] = None
        self._async_engine = None
        self._session_factory = None
        self._initialized = False
    
    async def initialize(self):
        """Initialize all database connections"""
        if self._initialized:
            return
        
        try:
            # Initialize Redis pool
            await self._init_redis_pool()
            
            # Initialize PostgreSQL pool
            await self._init_postgres_pool()
            
            # Initialize SQLAlchemy async engine
            await self._init_sqlalchemy()
            
            self._initialized = True
            logger.info("✅ Database connections initialized")
            
        except Exception as e:
            logger.error(f"❌ Failed to initialize database connections: {e}")
            raise
    
    async def _init_redis_pool(self):
        """Initialize Redis connection pool"""
        try:
            self._redis_pool = aioredis.ConnectionPool(
                host=REDIS_HOST,
                port=REDIS_PORT,
                db=REDIS_DB,
                max_connections=50,
                decode_responses=True
            )
            
            # Test connection
            async with aioredis.Redis(connection_pool=self._redis_pool) as redis:
                await redis.ping()
            
            logger.info(f"✅ Redis pool initialized ({REDIS_HOST}:{REDIS_PORT})")
            
        except Exception as e:
            logger.warning(f"⚠️ Redis pool initialization failed: {e}")
            # Don't fail completely if Redis is unavailable
    
    async def _init_postgres_pool(self):
        """Initialize PostgreSQL connection pool"""
        try:
            self._pg_pool = await asyncpg.create_pool(
                host=POSTGRES_HOST,
                port=POSTGRES_PORT,
                user=POSTGRES_USER,
                password=POSTGRES_PASSWORD,
                database=POSTGRES_DB,
                min_size=5,
                max_size=20,
                command_timeout=60
            )
            
            # Test connection
            async with self._pg_pool.acquire() as conn:
                await conn.fetchval('SELECT 1')
            
            logger.info(f"✅ PostgreSQL pool initialized ({POSTGRES_HOST}:{POSTGRES_PORT})")
            
        except Exception as e:
            logger.warning(f"⚠️ PostgreSQL pool initialization failed: {e}")
    
    async def _init_sqlalchemy(self):
        """Initialize SQLAlchemy async engine"""
        try:
            # Choose pool class based on environment
            poolclass = NullPool if ENVIRONMENT == "development" else QueuePool
            
            database_url = f"postgresql+asyncpg://{POSTGRES_USER}:{POSTGRES_PASSWORD}@{POSTGRES_HOST}:{POSTGRES_PORT}/{POSTGRES_DB}"
            
            self._async_engine = create_async_engine(
                database_url,
                poolclass=poolclass,
                pool_size=20,
                max_overflow=10,
                pool_pre_ping=True,
                echo=ENVIRONMENT == "development"
            )
            
            self._session_factory = async_sessionmaker(
                self._async_engine,
                class_=AsyncSession,
                expire_on_commit=False
            )
            
            logger.info("✅ SQLAlchemy async engine initialized")
            
        except Exception as e:
            logger.warning(f"⚠️ SQLAlchemy initialization failed: {e}")
    
    @asynccontextmanager
    async def get_redis(self):
        """Get Redis connection from pool"""
        if not self._redis_pool:
            raise RuntimeError("Redis pool not initialized")
        
        redis = aioredis.Redis(connection_pool=self._redis_pool)
        try:
            yield redis
        finally:
            await redis.close()
    
    @asynccontextmanager
    async def get_postgres(self):
        """Get PostgreSQL connection from pool"""
        if not self._pg_pool:
            raise RuntimeError("PostgreSQL pool not initialized")
        
        async with self._pg_pool.acquire() as conn:
            yield conn
    
    @asynccontextmanager
    async def get_session(self):
        """Get SQLAlchemy async session"""
        if not self._session_factory:
            raise RuntimeError("SQLAlchemy not initialized")
        
        async with self._session_factory() as session:
            try:
                yield session
                await session.commit()
            except Exception:
                await session.rollback()
                raise
    
    async def execute_query(self, query: str, *args) -> list:
        """Execute a query and return results"""
        async with self.get_postgres() as conn:
            return await conn.fetch(query, *args)
    
    async def execute_one(self, query: str, *args) -> Optional[Dict[str, Any]]:
        """Execute a query and return single result"""
        async with self.get_postgres() as conn:
            row = await conn.fetchrow(query, *args)
            return dict(row) if row else None
    
    async def redis_get(self, key: str) -> Optional[str]:
        """Get value from Redis"""
        async with self.get_redis() as redis:
            return await redis.get(key)
    
    async def redis_set(self, key: str, value: str, ttl: Optional[int] = None) -> bool:
        """Set value in Redis with optional TTL"""
        async with self.get_redis() as redis:
            if ttl:
                return await redis.setex(key, ttl, value)
            else:
                return await redis.set(key, value)
    
    async def redis_delete(self, key: str) -> bool:
        """Delete key from Redis"""
        async with self.get_redis() as redis:
            return await redis.delete(key) > 0
    
    async def health_check(self) -> Dict[str, str]:
        """Check health of all connections"""
        health = {}
        
        # Check Redis
        try:
            async with self.get_redis() as redis:
                await redis.ping()
            health['redis'] = 'healthy'
        except Exception as e:
            health['redis'] = f'unhealthy: {e}'
        
        # Check PostgreSQL
        try:
            async with self.get_postgres() as conn:
                await conn.fetchval('SELECT 1')
            health['postgres'] = 'healthy'
        except Exception as e:
            health['postgres'] = f'unhealthy: {e}'
        
        return health
    
    async def cleanup(self):
        """Cleanup all connections"""
        try:
            # Close Redis pool
            if self._redis_pool:
                await self._redis_pool.disconnect()
                logger.info("✅ Redis pool closed")
            
            # Close PostgreSQL pool
            if self._pg_pool:
                await self._pg_pool.close()
                logger.info("✅ PostgreSQL pool closed")
            
            # Dispose SQLAlchemy engine
            if self._async_engine:
                await self._async_engine.dispose()
                logger.info("✅ SQLAlchemy engine disposed")
            
            self._initialized = False
            
        except Exception as e:
            logger.error(f"❌ Error during database cleanup: {e}")


# Global database manager instance
db_manager = DatabaseManager()


async def get_db():
    """Dependency for database access"""
    if not db_manager._initialized:
        await db_manager.initialize()
    return db_manager