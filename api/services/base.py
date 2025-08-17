"""
Base service class for all services
"""
from typing import Any, Dict, Optional
import logging
from abc import ABC, abstractmethod


class BaseService(ABC):
    """Base service with common functionality"""
    
    def __init__(self):
        self.logger = logging.getLogger(self.__class__.__name__)
        self._initialized = False
    
    async def initialize(self) -> None:
        """Initialize service resources"""
        if self._initialized:
            return
        
        await self._setup()
        self._initialized = True
        self.logger.info(f"✅ {self.__class__.__name__} initialized")
    
    @abstractmethod
    async def _setup(self) -> None:
        """Setup service specific resources"""
        pass
    
    async def cleanup(self) -> None:
        """Cleanup service resources"""
        if not self._initialized:
            return
        
        await self._teardown()
        self._initialized = False
        self.logger.info(f"✅ {self.__class__.__name__} cleaned up")
    
    async def _teardown(self) -> None:
        """Teardown service specific resources"""
        pass
    
    def validate_input(self, data: Dict[str, Any], required_fields: list) -> bool:
        """Validate input data has required fields"""
        for field in required_fields:
            if field not in data:
                raise ValueError(f"Missing required field: {field}")
        return True