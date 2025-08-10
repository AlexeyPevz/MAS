"""
Centralized Error Handler for Root-MAS
Централизованная обработка ошибок с классификацией и восстановлением
"""
from typing import Dict, Any, Optional, Callable, Type
from datetime import datetime, timezone
import logging
import traceback
from enum import Enum
from dataclasses import dataclass
import asyncio


class ErrorSeverity(Enum):
    """Уровни критичности ошибок"""
    LOW = "low"          # Можно игнорировать
    MEDIUM = "medium"    # Требует внимания
    HIGH = "high"        # Нужно исправить
    CRITICAL = "critical"  # Система не может продолжать работу


class ErrorCategory(Enum):
    """Категории ошибок"""
    LLM_ERROR = "llm_error"              # Ошибки LLM API
    MEMORY_ERROR = "memory_error"        # Ошибки работы с памятью
    NETWORK_ERROR = "network_error"      # Сетевые ошибки
    VALIDATION_ERROR = "validation_error"  # Ошибки валидации
    PERMISSION_ERROR = "permission_error"  # Ошибки доступа
    CONFIGURATION_ERROR = "config_error"   # Ошибки конфигурации
    AGENT_ERROR = "agent_error"          # Ошибки агентов
    UNKNOWN_ERROR = "unknown_error"      # Неизвестные ошибки


@dataclass
class ErrorContext:
    """Контекст ошибки"""
    error: Exception
    severity: ErrorSeverity
    category: ErrorCategory
    agent_name: Optional[str] = None
    task_id: Optional[str] = None
    user_id: Optional[str] = None
    timestamp: datetime = None
    traceback: str = ""
    recovery_attempted: bool = False
    recovery_successful: bool = False
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now(timezone.utc)
        if not self.traceback:
            self.traceback = traceback.format_exc()


class ErrorHandler:
    """Централизованный обработчик ошибок"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.error_handlers: Dict[Type[Exception], Callable] = {}
        self.recovery_strategies: Dict[ErrorCategory, Callable] = {}
        self.error_history: list[ErrorContext] = []
        
        # Register default handlers
        self._register_default_handlers()
    
    def _register_default_handlers(self):
        """Регистрация обработчиков по умолчанию"""
        # LLM errors
        self.register_handler(
            ConnectionError,
            self._handle_connection_error,
            ErrorCategory.NETWORK_ERROR
        )
        
        # Memory errors
        self.register_handler(
            MemoryError,
            self._handle_memory_error,
            ErrorCategory.MEMORY_ERROR
        )
        
        # Permission errors
        self.register_handler(
            PermissionError,
            self._handle_permission_error,
            ErrorCategory.PERMISSION_ERROR
        )
        
        # Validation errors
        self.register_handler(
            ValueError,
            self._handle_validation_error,
            ErrorCategory.VALIDATION_ERROR
        )
    
    def register_handler(
        self, 
        error_type: Type[Exception], 
        handler: Callable,
        category: ErrorCategory = ErrorCategory.UNKNOWN_ERROR
    ):
        """Регистрация обработчика для типа ошибки"""
        self.error_handlers[error_type] = (handler, category)
    
    def register_recovery_strategy(
        self,
        category: ErrorCategory,
        strategy: Callable
    ):
        """Регистрация стратегии восстановления"""
        self.recovery_strategies[category] = strategy
    
    async def handle_error(
        self,
        error: Exception,
        agent_name: Optional[str] = None,
        task_id: Optional[str] = None,
        user_id: Optional[str] = None,
        **kwargs
    ) -> ErrorContext:
        """Обработать ошибку"""
        # Classify error
        severity, category = self._classify_error(error)
        
        # Create context
        context = ErrorContext(
            error=error,
            severity=severity,
            category=category,
            agent_name=agent_name,
            task_id=task_id,
            user_id=user_id
        )
        
        # Log error
        self._log_error(context)
        
        # Store in history
        self.error_history.append(context)
        
        # Try specific handler
        handler_result = await self._run_specific_handler(error, context)
        if handler_result:
            return context
        
        # Try recovery strategy
        if severity in [ErrorSeverity.MEDIUM, ErrorSeverity.HIGH]:
            recovery_result = await self._attempt_recovery(context)
            context.recovery_attempted = True
            context.recovery_successful = recovery_result
        
        # Notify if critical
        if severity == ErrorSeverity.CRITICAL:
            await self._notify_critical_error(context)
        
        return context
    
    def _classify_error(self, error: Exception) -> tuple[ErrorSeverity, ErrorCategory]:
        """Классифицировать ошибку"""
        # Check registered handlers
        for error_type, (handler, category) in self.error_handlers.items():
            if isinstance(error, error_type):
                severity = self._determine_severity(error, category)
                return severity, category
        
        # Default classification
        if isinstance(error, (ConnectionError, TimeoutError)):
            return ErrorSeverity.MEDIUM, ErrorCategory.NETWORK_ERROR
        elif isinstance(error, MemoryError):
            return ErrorSeverity.HIGH, ErrorCategory.MEMORY_ERROR
        elif isinstance(error, PermissionError):
            return ErrorSeverity.HIGH, ErrorCategory.PERMISSION_ERROR
        elif isinstance(error, ValueError):
            return ErrorSeverity.LOW, ErrorCategory.VALIDATION_ERROR
        else:
            return ErrorSeverity.MEDIUM, ErrorCategory.UNKNOWN_ERROR
    
    def _determine_severity(self, error: Exception, category: ErrorCategory) -> ErrorSeverity:
        """Определить критичность ошибки"""
        # Critical errors
        if category in [ErrorCategory.CONFIGURATION_ERROR]:
            return ErrorSeverity.CRITICAL
        
        # High severity
        if category in [ErrorCategory.PERMISSION_ERROR, ErrorCategory.MEMORY_ERROR]:
            return ErrorSeverity.HIGH
        
        # Check error message for patterns
        error_msg = str(error).lower()
        if any(word in error_msg for word in ['critical', 'fatal', 'emergency']):
            return ErrorSeverity.CRITICAL
        elif any(word in error_msg for word in ['error', 'failed', 'unable']):
            return ErrorSeverity.HIGH
        elif any(word in error_msg for word in ['warning', 'retry', 'timeout']):
            return ErrorSeverity.MEDIUM
        
        return ErrorSeverity.LOW
    
    def _log_error(self, context: ErrorContext):
        """Логировать ошибку"""
        log_message = (
            f"[{context.severity.value.upper()}] {context.category.value}: "
            f"{type(context.error).__name__}: {str(context.error)}"
        )
        
        if context.agent_name:
            log_message += f" | Agent: {context.agent_name}"
        if context.task_id:
            log_message += f" | Task: {context.task_id}"
        
        if context.severity == ErrorSeverity.CRITICAL:
            self.logger.critical(log_message)
        elif context.severity == ErrorSeverity.HIGH:
            self.logger.error(log_message)
        elif context.severity == ErrorSeverity.MEDIUM:
            self.logger.warning(log_message)
        else:
            self.logger.info(log_message)
        
        # Log traceback for high/critical errors
        if context.severity in [ErrorSeverity.HIGH, ErrorSeverity.CRITICAL]:
            self.logger.debug(f"Traceback:\n{context.traceback}")
    
    async def _run_specific_handler(self, error: Exception, context: ErrorContext) -> bool:
        """Запустить специфический обработчик"""
        for error_type, (handler, _) in self.error_handlers.items():
            if isinstance(error, error_type):
                try:
                    if asyncio.iscoroutinefunction(handler):
                        await handler(error, context)
                    else:
                        handler(error, context)
                    return True
                except Exception as e:
                    self.logger.error(f"Error in error handler: {e}")
        return False
    
    async def _attempt_recovery(self, context: ErrorContext) -> bool:
        """Попытаться восстановиться после ошибки"""
        strategy = self.recovery_strategies.get(context.category)
        if not strategy:
            return False
        
        try:
            if asyncio.iscoroutinefunction(strategy):
                return await strategy(context)
            else:
                return strategy(context)
        except Exception as e:
            self.logger.error(f"Recovery strategy failed: {e}")
            return False
    
    async def _notify_critical_error(self, context: ErrorContext):
        """Уведомить о критической ошибке"""
        # Send to monitoring system
        try:
            from tools.callbacks import outgoing_to_telegram
            
            message = (
                f"🚨 КРИТИЧЕСКАЯ ОШИБКА!\n\n"
                f"Категория: {context.category.value}\n"
                f"Ошибка: {type(context.error).__name__}\n"
                f"Описание: {str(context.error)}\n"
            )
            
            if context.agent_name:
                message += f"Агент: {context.agent_name}\n"
            
            outgoing_to_telegram(message)
        except Exception:
            pass  # Don't fail on notification error
    
    # Default handlers
    def _handle_connection_error(self, error: ConnectionError, context: ErrorContext):
        """Обработка сетевых ошибок"""
        self.logger.info(f"Handling connection error: {error}")
        # Could implement retry logic here
    
    def _handle_memory_error(self, error: MemoryError, context: ErrorContext):
        """Обработка ошибок памяти"""
        self.logger.error(f"Memory error occurred: {error}")
        # Could implement memory cleanup here
    
    def _handle_permission_error(self, error: PermissionError, context: ErrorContext):
        """Обработка ошибок доступа"""
        self.logger.error(f"Permission denied: {error}")
        # Could request elevated permissions
    
    def _handle_validation_error(self, error: ValueError, context: ErrorContext):
        """Обработка ошибок валидации"""
        self.logger.warning(f"Validation error: {error}")
        # Could suggest valid values
    
    def get_error_statistics(self) -> Dict[str, Any]:
        """Получить статистику ошибок"""
        if not self.error_history:
            return {"total_errors": 0}
        
        total = len(self.error_history)
        by_category = {}
        by_severity = {}
        recovery_rate = 0
        
        for error in self.error_history:
            # Count by category
            cat = error.category.value
            by_category[cat] = by_category.get(cat, 0) + 1
            
            # Count by severity
            sev = error.severity.value
            by_severity[sev] = by_severity.get(sev, 0) + 1
            
            # Recovery rate
            if error.recovery_attempted and error.recovery_successful:
                recovery_rate += 1
        
        return {
            "total_errors": total,
            "by_category": by_category,
            "by_severity": by_severity,
            "recovery_rate": recovery_rate / total if total > 0 else 0,
            "recent_errors": [
                {
                    "error": type(e.error).__name__,
                    "category": e.category.value,
                    "severity": e.severity.value,
                    "timestamp": e.timestamp.isoformat()
                }
                for e in self.error_history[-10:]  # Last 10 errors
            ]
        }


# Global error handler instance
error_handler = ErrorHandler()


# Decorator for automatic error handling
def handle_errors(
    severity: ErrorSeverity = ErrorSeverity.MEDIUM,
    category: ErrorCategory = ErrorCategory.UNKNOWN_ERROR
):
    """Декоратор для автоматической обработки ошибок"""
    def decorator(func):
        async def async_wrapper(*args, **kwargs):
            try:
                return await func(*args, **kwargs)
            except Exception as e:
                # Extract context from function arguments
                agent_name = kwargs.get('agent_name')
                task_id = kwargs.get('task_id')
                
                # Handle error
                context = await error_handler.handle_error(
                    e,
                    agent_name=agent_name,
                    task_id=task_id
                )
                
                # Re-raise if critical
                if context.severity == ErrorSeverity.CRITICAL:
                    raise
                
                # Return None for other errors
                return None
        
        def sync_wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                # Extract context
                agent_name = kwargs.get('agent_name')
                task_id = kwargs.get('task_id')
                
                # Handle error synchronously
                asyncio.create_task(
                    error_handler.handle_error(
                        e,
                        agent_name=agent_name,
                        task_id=task_id
                    )
                )
                
                # Re-raise if critical
                if severity == ErrorSeverity.CRITICAL:
                    raise
                
                return None
        
        return async_wrapper if asyncio.iscoroutinefunction(func) else sync_wrapper
    return decorator