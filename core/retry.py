"""
Retry mechanisms for external services
"""
import asyncio
import logging
from typing import TypeVar, Callable, Any, Union, Optional
from functools import wraps
import httpx
import aiohttp

logger = logging.getLogger(__name__)

T = TypeVar('T')


class RetryConfig:
    """Configuration for retry behavior"""
    def __init__(
        self,
        max_attempts: int = 3,
        initial_delay: float = 1.0,
        max_delay: float = 60.0,
        exponential_base: float = 2.0,
        jitter: bool = True
    ):
        self.max_attempts = max_attempts
        self.initial_delay = initial_delay
        self.max_delay = max_delay
        self.exponential_base = exponential_base
        self.jitter = jitter


# Default configurations for different services
RETRY_CONFIGS = {
    "llm": RetryConfig(max_attempts=3, initial_delay=2.0, max_delay=30.0),
    "redis": RetryConfig(max_attempts=5, initial_delay=0.5, max_delay=10.0),
    "http": RetryConfig(max_attempts=3, initial_delay=1.0, max_delay=20.0),
    "voice": RetryConfig(max_attempts=2, initial_delay=1.0, max_delay=10.0),
}


def calculate_delay(attempt: int, config: RetryConfig) -> float:
    """Calculate delay for exponential backoff with optional jitter"""
    delay = min(
        config.initial_delay * (config.exponential_base ** attempt),
        config.max_delay
    )
    
    if config.jitter:
        # Add random jitter (±25%)
        import random
        jitter_factor = 0.75 + random.random() * 0.5
        delay *= jitter_factor
    
    return delay


def is_retryable_exception(error: Exception) -> bool:
    """Determine if an exception is retryable"""
    # Network errors
    if isinstance(error, (
        asyncio.TimeoutError,
        ConnectionError,
        ConnectionResetError,
        ConnectionAbortedError,
    )):
        return True
    
    # HTTP client errors
    if isinstance(error, (httpx.TimeoutException, httpx.ConnectError)):
        return True
    
    if isinstance(error, aiohttp.ClientError):
        return True
    
    # HTTP status codes
    if hasattr(error, 'response'):
        if hasattr(error.response, 'status_code'):
            # Retry on 429 (rate limit), 502, 503, 504
            return error.response.status_code in [429, 502, 503, 504]
        elif hasattr(error.response, 'status'):
            return error.response.status in [429, 502, 503, 504]
    
    # OpenAI/LLM specific errors
    error_message = str(error).lower()
    if any(msg in error_message for msg in [
        "rate limit",
        "timeout",
        "connection",
        "temporarily unavailable",
        "service unavailable"
    ]):
        return True
    
    return False


def async_retry(
    config: Union[RetryConfig, str] = "http",
    on_retry: Optional[Callable[[Exception, int], None]] = None
):
    """Decorator for async functions with retry logic"""
    if isinstance(config, str):
        config = RETRY_CONFIGS.get(config, RETRY_CONFIGS["http"])
    
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @wraps(func)
        async def wrapper(*args, **kwargs) -> T:
            last_exception = None
            
            for attempt in range(config.max_attempts):
                try:
                    return await func(*args, **kwargs)
                    
                except Exception as e:
                    last_exception = e
                    
                    if not is_retryable_exception(e) or attempt == config.max_attempts - 1:
                        logger.error(
                            f"❌ {func.__name__} failed after {attempt + 1} attempts: {e}"
                        )
                        raise
                    
                    delay = calculate_delay(attempt, config)
                    logger.warning(
                        f"⚠️ {func.__name__} attempt {attempt + 1}/{config.max_attempts} "
                        f"failed: {e}. Retrying in {delay:.1f}s..."
                    )
                    
                    if on_retry:
                        on_retry(e, attempt)
                    
                    await asyncio.sleep(delay)
            
            raise last_exception
        
        return wrapper
    return decorator


def sync_retry(
    config: Union[RetryConfig, str] = "http",
    on_retry: Optional[Callable[[Exception, int], None]] = None
):
    """Decorator for sync functions with retry logic"""
    if isinstance(config, str):
        config = RETRY_CONFIGS.get(config, RETRY_CONFIGS["http"])
    
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @wraps(func)
        def wrapper(*args, **kwargs) -> T:
            last_exception = None
            
            for attempt in range(config.max_attempts):
                try:
                    return func(*args, **kwargs)
                    
                except Exception as e:
                    last_exception = e
                    
                    if not is_retryable_exception(e) or attempt == config.max_attempts - 1:
                        logger.error(
                            f"❌ {func.__name__} failed after {attempt + 1} attempts: {e}"
                        )
                        raise
                    
                    delay = calculate_delay(attempt, config)
                    logger.warning(
                        f"⚠️ {func.__name__} attempt {attempt + 1}/{config.max_attempts} "
                        f"failed: {e}. Retrying in {delay:.1f}s..."
                    )
                    
                    if on_retry:
                        on_retry(e, attempt)
                    
                    import time
                    time.sleep(delay)
            
            raise last_exception
        
        return wrapper
    return decorator


class RetryableHTTPClient:
    """HTTP client with built-in retry logic"""
    
    def __init__(self, config: RetryConfig = None):
        self.config = config or RETRY_CONFIGS["http"]
        self._client = None
    
    async def __aenter__(self):
        self._client = httpx.AsyncClient()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self._client:
            await self._client.aclose()
    
    @async_retry(config="http")
    async def get(self, url: str, **kwargs) -> httpx.Response:
        """GET request with retry"""
        return await self._client.get(url, **kwargs)
    
    @async_retry(config="http")
    async def post(self, url: str, **kwargs) -> httpx.Response:
        """POST request with retry"""
        return await self._client.post(url, **kwargs)
    
    @async_retry(config="http")
    async def put(self, url: str, **kwargs) -> httpx.Response:
        """PUT request with retry"""
        return await self._client.put(url, **kwargs)
    
    @async_retry(config="http")
    async def delete(self, url: str, **kwargs) -> httpx.Response:
        """DELETE request with retry"""
        return await self._client.delete(url, **kwargs)