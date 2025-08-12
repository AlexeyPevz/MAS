"""
Продвинутая система кэширования LLM результатов для Root-MAS
"""
from typing import Dict, Any, Optional, List, Tuple
import hashlib
import json
import time
from datetime import datetime, timedelta
from dataclasses import dataclass, field
import asyncio
import redis.asyncio as redis
from collections import OrderedDict
import pickle

@dataclass
class CacheEntry:
    """Запись в кэше"""
    key: str
    value: Any
    created_at: float
    ttl: int  # Time to live в секундах
    hits: int = 0
    last_accessed: float = field(default_factory=time.time)
    model: str = ""
    tokens_saved: int = 0
    cost_saved: float = 0.0

class LLMCache:
    """Многоуровневая система кэширования для LLM"""
    
    def __init__(
        self,
        redis_url: str = "redis://localhost:6379",
        local_cache_size: int = 1000,
        default_ttl: int = 3600  # 1 час
    ):
        self.redis_url = redis_url
        self.redis_client = None
        self.local_cache_size = local_cache_size
        self.default_ttl = default_ttl
        
        # Локальный LRU кэш для супер-быстрого доступа
        self.local_cache: OrderedDict[str, CacheEntry] = OrderedDict()
        
        # Статистика
        self.stats = {
            "hits": 0,
            "misses": 0,
            "local_hits": 0,
            "redis_hits": 0,
            "total_tokens_saved": 0,
            "total_cost_saved": 0.0
        }
        
    async def initialize(self):
        """Инициализация подключений"""
        self.redis_client = await redis.from_url(self.redis_url)
        
    async def get_or_compute(
        self,
        key: str,
        compute_func: callable,
        ttl: Optional[int] = None,
        model: str = "gpt-4o-mini",
        estimated_tokens: int = 0
    ) -> Tuple[Any, bool]:
        """Получить из кэша или вычислить"""
        # 1. Проверяем локальный кэш
        if key in self.local_cache:
            entry = self.local_cache[key]
            if time.time() - entry.created_at < entry.ttl:
                # Обновляем позицию в LRU
                self.local_cache.move_to_end(key)
                entry.hits += 1
                entry.last_accessed = time.time()
                
                self.stats["hits"] += 1
                self.stats["local_hits"] += 1
                
                return entry.value, True
            else:
                # Истек срок - удаляем
                del self.local_cache[key]
        
        # 2. Проверяем Redis
        redis_value = await self._get_from_redis(key)
        if redis_value is not None:
            self.stats["hits"] += 1
            self.stats["redis_hits"] += 1
            
            # Сохраняем в локальный кэш
            await self._add_to_local_cache(
                key, redis_value, ttl or self.default_ttl, model, estimated_tokens
            )
            
            return redis_value, True
        
        # 3. Вычисляем значение
        self.stats["misses"] += 1
        result = await compute_func()
        
        # 4. Сохраняем в кэши
        await self._save_to_caches(
            key, result, ttl or self.default_ttl, model, estimated_tokens
        )
        
        return result, False
    
    async def _get_from_redis(self, key: str) -> Optional[Any]:
        """Получение из Redis"""
        try:
            value = await self.redis_client.get(f"llm_cache:{key}")
            if value:
                return pickle.loads(value)
        except Exception as e:
            print(f"Redis error: {e}")
        return None
    
    async def _save_to_caches(
        self, 
        key: str, 
        value: Any, 
        ttl: int,
        model: str,
        estimated_tokens: int
    ):
        """Сохранение в оба кэша"""
        # Сохраняем в Redis
        try:
            await self.redis_client.setex(
                f"llm_cache:{key}",
                ttl,
                pickle.dumps(value)
            )
        except Exception as e:
            print(f"Redis save error: {e}")
        
        # Сохраняем в локальный кэш
        await self._add_to_local_cache(key, value, ttl, model, estimated_tokens)
    
    async def _add_to_local_cache(
        self,
        key: str,
        value: Any,
        ttl: int,
        model: str,
        estimated_tokens: int
    ):
        """Добавление в локальный LRU кэш"""
        # Удаляем старые записи если нужно
        while len(self.local_cache) >= self.local_cache_size:
            oldest_key = next(iter(self.local_cache))
            del self.local_cache[oldest_key]
        
        # Считаем сэкономленные средства
        cost_per_token = self._get_model_cost(model)
        cost_saved = estimated_tokens * cost_per_token
        
        # Добавляем новую запись
        entry = CacheEntry(
            key=key,
            value=value,
            created_at=time.time(),
            ttl=ttl,
            model=model,
            tokens_saved=estimated_tokens,
            cost_saved=cost_saved
        )
        
        self.local_cache[key] = entry
        
        # Обновляем статистику
        self.stats["total_tokens_saved"] += estimated_tokens
        self.stats["total_cost_saved"] += cost_saved
    
    def _get_model_cost(self, model: str) -> float:
        """Стоимость за токен для разных моделей"""
        costs = {
            "gpt-4o": 0.00001,
            "gpt-4o-mini": 0.0000015,
            "gpt-3.5-turbo": 0.0000015,
            "claude-3-opus": 0.000015,
            "claude-3-sonnet": 0.000003
        }
        return costs.get(model, 0.000002)
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """Получение статистики кэша"""
        hit_rate = self.stats["hits"] / max(
            self.stats["hits"] + self.stats["misses"], 1
        )
        
        return {
            "hit_rate": f"{hit_rate * 100:.2f}%",
            "total_requests": self.stats["hits"] + self.stats["misses"],
            "cache_hits": self.stats["hits"],
            "local_hits": self.stats["local_hits"],
            "redis_hits": self.stats["redis_hits"],
            "tokens_saved": self.stats["total_tokens_saved"],
            "money_saved": f"${self.stats['total_cost_saved']:.2f}",
            "local_cache_size": len(self.local_cache)
        }

# Интеллектуальный кэш с семантическим поиском
class SemanticLLMCache(LLMCache):
    """Кэш с семантическим поиском похожих запросов"""
    
    def __init__(self, *args, similarity_threshold: float = 0.95, **kwargs):
        super().__init__(*args, **kwargs)
        self.similarity_threshold = similarity_threshold
        self.embeddings_cache = {}
        
    async def get_or_compute_semantic(
        self,
        query: str,
        compute_func: callable,
        get_embedding_func: callable,
        **kwargs
    ) -> Tuple[Any, bool, float]:
        """Поиск с учетом семантической близости"""
        
        # 1. Получаем embedding запроса
        query_embedding = await get_embedding_func(query)
        
        # 2. Ищем похожие запросы в кэше
        similar_key, similarity = await self._find_similar(query_embedding)
        
        if similar_key and similarity >= self.similarity_threshold:
            # Нашли похожий запрос
            result, from_cache = await self.get_or_compute(
                similar_key,
                compute_func,
                **kwargs
            )
            return result, True, similarity
        
        # 3. Не нашли - вычисляем
        key = self._generate_key(query)
        result, from_cache = await self.get_or_compute(
            key,
            compute_func,
            **kwargs
        )
        
        # Сохраняем embedding
        self.embeddings_cache[key] = query_embedding
        
        return result, from_cache, 1.0
    
    async def _find_similar(
        self, 
        query_embedding: List[float]
    ) -> Tuple[Optional[str], float]:
        """Поиск похожего запроса по embedding"""
        import numpy as np
        
        best_key = None
        best_similarity = 0.0
        
        for key, embedding in self.embeddings_cache.items():
            # Косинусное сходство
            similarity = np.dot(query_embedding, embedding) / (
                np.linalg.norm(query_embedding) * np.linalg.norm(embedding)
            )
            
            if similarity > best_similarity:
                best_similarity = similarity
                best_key = key
        
        return best_key, best_similarity
    
    def _generate_key(self, text: str) -> str:
        """Генерация ключа для текста"""
        return hashlib.sha256(text.encode()).hexdigest()

# Декоратор для автоматического кэширования
def cached_llm_call(
    cache: LLMCache,
    ttl: Optional[int] = None,
    key_prefix: str = "",
    include_model: bool = True
):
    """Декоратор для кэширования вызовов LLM"""
    def decorator(func):
        async def wrapper(*args, **kwargs):
            # Генерируем ключ из аргументов
            key_parts = [key_prefix] if key_prefix else []
            
            # Добавляем аргументы в ключ
            for arg in args:
                if isinstance(arg, (str, int, float, bool)):
                    key_parts.append(str(arg))
            
            # Добавляем kwargs
            for k, v in sorted(kwargs.items()):
                if isinstance(v, (str, int, float, bool)):
                    key_parts.append(f"{k}={v}")
            
            # Если нужно включить модель
            if include_model and "model" in kwargs:
                model = kwargs["model"]
            else:
                model = "gpt-4o-mini"
            
            cache_key = hashlib.sha256(
                ":".join(key_parts).encode()
            ).hexdigest()
            
            # Оцениваем количество токенов
            estimated_tokens = len(" ".join(key_parts)) // 4
            
            # Используем кэш
            result, from_cache = await cache.get_or_compute(
                cache_key,
                lambda: func(*args, **kwargs),
                ttl=ttl,
                model=model,
                estimated_tokens=estimated_tokens
            )
            
            return result
            
        return wrapper
    return decorator

# Пример использования в вашем проекте
class CachedAgentSystem:
    """Система агентов с кэшированием"""
    
    def __init__(self):
        self.cache = SemanticLLMCache(
            redis_url="redis://localhost:6379",
            local_cache_size=5000,
            default_ttl=7200  # 2 часа
        )
        self.initialized = False
        
    async def initialize(self):
        """Инициализация системы"""
        await self.cache.initialize()
        self.initialized = True
        
    @cached_llm_call(
        cache=lambda self: self.cache,
        ttl=3600,
        key_prefix="research"
    )
    async def research_task(self, query: str, model: str = "gpt-4o-mini") -> str:
        """Исследовательская задача с кэшированием"""
        # Здесь был бы реальный вызов к LLM
        # Для примера возвращаем заглушку
        await asyncio.sleep(1)  # Имитация вызова API
        return f"Research results for: {query}"
    
    async def get_cache_report(self) -> Dict[str, Any]:
        """Отчет по использованию кэша"""
        stats = self.cache.get_cache_stats()
        
        # Добавляем топ кэшированных запросов
        top_queries = sorted(
            self.cache.local_cache.items(),
            key=lambda x: x[1].hits,
            reverse=True
        )[:10]
        
        stats["top_cached_queries"] = [
            {
                "key": entry.key[:16] + "...",
                "hits": entry.hits,
                "tokens_saved": entry.tokens_saved,
                "cost_saved": f"${entry.cost_saved:.4f}"
            }
            for _, entry in top_queries
        ]
        
        return stats

# Интеграция с FastAPI
from fastapi import FastAPI, Depends

app = FastAPI()
agent_system = CachedAgentSystem()

@app.on_event("startup")
async def startup():
    await agent_system.initialize()

@app.get("/api/v1/cache/stats")
async def get_cache_stats():
    """Получение статистики кэширования"""
    return await agent_system.get_cache_report()

@app.post("/api/v1/cache/clear")
async def clear_cache(pattern: Optional[str] = None):
    """Очистка кэша"""
    if pattern:
        # Очистка по паттерну
        keys_to_remove = [
            k for k in agent_system.cache.local_cache.keys()
            if pattern in k
        ]
        for key in keys_to_remove:
            del agent_system.cache.local_cache[key]
        
        return {"cleared": len(keys_to_remove)}
    else:
        # Полная очистка
        size = len(agent_system.cache.local_cache)
        agent_system.cache.local_cache.clear()
        return {"cleared": size}