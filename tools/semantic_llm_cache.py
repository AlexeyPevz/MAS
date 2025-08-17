"""
Семантическое кэширование LLM для Root-MAS
Находит похожие запросы даже если они сформулированы по-разному
"""
from typing import Dict, Any, Optional, List, Tuple
import hashlib
import json
import os
import time
from datetime import datetime, timezone
from dataclasses import dataclass, field
import asyncio
from collections import OrderedDict
# import pickle  # Removed - using JSON instead for security
import logging

# Опциональные импорты
try:
    import redis.asyncio as redis
    REDIS_ASYNC_AVAILABLE = True
except ImportError:
    REDIS_ASYNC_AVAILABLE = False
    redis = None

try:
    import numpy as np
    NUMPY_AVAILABLE = True
except ImportError:
    NUMPY_AVAILABLE = False
    np = None

# Импорты из существующей системы
try:
    from memory.chroma_store import ChromaStore
    CHROMA_AVAILABLE = True
except ImportError:
    CHROMA_AVAILABLE = False
    ChromaStore = None

try:
    from tools.quality_metrics import quality_metrics
except ImportError:
    quality_metrics = None

logger = logging.getLogger(__name__)

@dataclass
class SemanticCacheEntry:
    """Запись в семантическом кэше"""
    key: str
    query: str
    response: Any
    embedding: Optional[List[float]] = None
    created_at: float = field(default_factory=time.time)
    ttl: int = 86400  # 24 часа по умолчанию
    hits: int = 0
    last_accessed: float = field(default_factory=time.time)
    model: str = ""
    tokens_saved: int = 0
    cost_saved: float = 0.0
    similarity_score: float = 1.0  # Для отслеживания качества матчей
    
    def to_dict(self) -> dict:
        """Конвертация в словарь для JSON"""
        return {
            'key': self.key,
            'query': self.query,
            'response': self.response,
            'embedding': self.embedding,
            'created_at': self.created_at,
            'ttl': self.ttl,
            'hits': self.hits,
            'last_accessed': self.last_accessed,
            'model': self.model,
            'tokens_saved': self.tokens_saved,
            'cost_saved': self.cost_saved,
            'similarity_score': self.similarity_score
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> 'SemanticCacheEntry':
        """Создание из словаря"""
        return cls(**data)

class SemanticLLMCache:
    """Семантический кэш с использованием ChromaDB"""
    
    def __init__(
        self,
        redis_url: str = None,
        chroma_collection: str = "llm_cache", 
        similarity_threshold: float = 0.92,
        local_cache_size: int = 1000,
        default_ttl: int = 86400
    ):
        # Используем redis_url из аргументов или строим из env
        if redis_url is None:
            redis_host = os.getenv('REDIS_HOST', 'localhost')
            redis_port = os.getenv('REDIS_PORT', '6379')
            redis_url = f"redis://{redis_host}:{redis_port}"
        
        self.redis_url = redis_url
        self.redis_client = None
        self.similarity_threshold = similarity_threshold
        self.local_cache_size = local_cache_size
        self.default_ttl = default_ttl
        
        # ChromaDB для семантического поиска
        self._use_semantic = CHROMA_AVAILABLE and NUMPY_AVAILABLE
        self._use_redis = REDIS_ASYNC_AVAILABLE
        
        if self._use_semantic:
            try:
                self.chroma_store = ChromaStore()
                self.collection_name = chroma_collection
            except Exception as e:
                logger.warning(f"⚠️ Disabling semantic search (Chroma init failed: {e})")
                self._use_semantic = False
                self.chroma_store = None
                self.collection_name = None
        else:
            self.chroma_store = None
            self.collection_name = None
            logger.warning("⚠️ Semantic search disabled (ChromaDB or NumPy not available)")
            
        if not self._use_redis:
            logger.warning("⚠️ Redis persistence disabled")
        
        # Локальный LRU кэш
        self.local_cache: OrderedDict[str, SemanticCacheEntry] = OrderedDict()
        
        # Статистика
        self.stats = {
            "hits": 0,
            "misses": 0,
            "semantic_hits": 0,
            "exact_hits": 0,
            "total_tokens_saved": 0,
            "total_cost_saved": 0.0,
            "avg_similarity": 0.0
        }
        
    async def initialize(self):
        """Инициализация подключений"""
        # Redis
        if self._use_redis:
            try:
                self.redis_client = await redis.from_url(self.redis_url)
                await self.redis_client.ping()
            except Exception as e:
                logger.warning(f"⚠️ Redis connection failed: {e}")
                self.redis_client = None
                self._use_redis = False
        
        # ChromaDB инициализируется в ChromaMemoryStore
        mode = []
        if self._use_redis:
            mode.append("Redis")
        if self._use_semantic:
            mode.append("Semantic")
        if not mode:
            mode.append("Local-only")
            
        logger.info(f"Semantic LLM cache initialized ({', '.join(mode)} mode)")
        
    async def get_or_compute(
        self,
        query: str,
        compute_func: callable,
        agent_name: str = "unknown",
        ttl: Optional[int] = None,
        model: str = "gpt-4o-mini",
        estimated_tokens: int = 0,
        metadata: Optional[Dict] = None
    ) -> Tuple[Any, bool, float]:
        """Получить из кэша или вычислить с семантическим поиском"""
        
        # 1. Точный поиск в локальном кэше
        exact_key = self._generate_key(query)
        local_result = self._check_local_cache(exact_key)
        if local_result is not None:
            self.stats["hits"] += 1
            self.stats["exact_hits"] += 1
            return local_result.response, True, 1.0
        
        # 2. Семантический поиск в ChromaDB
        semantic_results = await self._semantic_search(query, agent_name)
        
        if semantic_results:
            best_match = semantic_results[0]
            if best_match['score'] >= self.similarity_threshold:
                # Нашли похожий запрос
                cached_entry = await self._get_cached_entry(best_match['key'])
                
                if cached_entry:
                    self.stats["hits"] += 1
                    self.stats["semantic_hits"] += 1
                    self._update_similarity_stats(best_match['score'])
                    
                    # Сохраняем в локальный кэш для быстрого доступа
                    self.local_cache[exact_key] = SemanticCacheEntry(
                        key=exact_key,
                        query=query,
                        response=cached_entry.response,
                        similarity_score=best_match['score'],
                        model=model,
                        tokens_saved=estimated_tokens
                    )
                    
                    return cached_entry.response, True, best_match['score']
        
        # 3. Не нашли - вычисляем
        self.stats["misses"] += 1
        logger.info(f"Cache miss for query: {query[:50]}...")
        
        result = await compute_func()
        
        # 4. Сохраняем результат
        await self._save_to_cache(
            query=query,
            response=result,
            agent_name=agent_name,
            ttl=ttl or self.default_ttl,
            model=model,
            estimated_tokens=estimated_tokens,
            metadata=metadata
        )
        
        return result, False, 0.0
    
    async def _semantic_search(
        self, 
        query: str, 
        agent_name: str,
        top_k: int = 5
    ) -> List[Dict[str, Any]]:
        """Семантический поиск похожих запросов"""
        if not self._use_semantic or not self.chroma_store:
            return []
            
        try:
            # Формируем метаданные для фильтрации
            where_clause = {"agent_name": agent_name} if agent_name else None
            
            # Ищем в ChromaDB
            results = self.chroma_store.query(
                collection_name=self.collection_name,
                query_texts=[query],
                n_results=top_k,
                where=where_clause
            )
            
            if not results or not results['ids'] or not results['ids'][0]:
                return []
            
            # Преобразуем результаты
            similar_queries = []
            for i in range(len(results['ids'][0])):
                similar_queries.append({
                    'key': results['ids'][0][i],
                    'query': results['documents'][0][i] if results['documents'] else "",
                    'score': 1 - results['distances'][0][i],  # Преобразуем расстояние в similarity
                    'metadata': results['metadatas'][0][i] if results['metadatas'] else {}
                })
            
            return similar_queries
            
        except Exception as e:
            logger.error(f"Semantic search error: {e}")
            return []
    
    def _check_local_cache(self, key: str) -> Optional[SemanticCacheEntry]:
        """Проверка локального кэша"""
        if key in self.local_cache:
            entry = self.local_cache[key]
            if time.time() - entry.created_at < entry.ttl:
                # Обновляем позицию в LRU
                self.local_cache.move_to_end(key)
                entry.hits += 1
                entry.last_accessed = time.time()
                return entry
            else:
                # Истек срок
                del self.local_cache[key]
        return None
    
    async def _get_cached_entry(self, key: str) -> Optional[SemanticCacheEntry]:
        """Получение записи из Redis"""
        if not self.redis_client:
            return None
        try:
            data = await self.redis_client.get(f"llm_cache:{key}")
            if data:
                json_data = json.loads(data)
                return SemanticCacheEntry.from_dict(json_data)
        except Exception as e:
            logger.error(f"Redis get error: {e}")
        return None
    
    async def _save_to_cache(
        self,
        query: str,
        response: Any,
        agent_name: str,
        ttl: int,
        model: str,
        estimated_tokens: int,
        metadata: Optional[Dict]
    ):
        """Сохранение в все уровни кэша"""
        key = self._generate_key(query)
        
        # Считаем экономию
        cost_saved = estimated_tokens * self._get_model_cost(model)
        
        # Создаем запись
        entry = SemanticCacheEntry(
            key=key,
            query=query,
            response=response,
            ttl=ttl,
            model=model,
            tokens_saved=estimated_tokens,
            cost_saved=cost_saved
        )
        
        # 1. Сохраняем в Redis
        if self.redis_client:
            try:
                await self.redis_client.setex(
                    f"llm_cache:{key}",
                    ttl,
                    json.dumps(entry.to_dict())
                )
            except Exception as e:
                logger.error(f"Redis save error: {e}")
        
        # 2. Сохраняем в ChromaDB для семантического поиска
        try:
            cache_metadata = {
                "agent_name": agent_name,
                "model": model,
                "timestamp": time.time(),
                "ttl": ttl
            }
            if metadata:
                cache_metadata.update(metadata)
            
            self.chroma_store.add(
                collection_name=self.collection_name,
                documents=[query],
                metadatas=[cache_metadata],
                ids=[key]
            )
        except Exception as e:
            logger.error(f"ChromaDB save error: {e}")
        
        # 3. Добавляем в локальный кэш
        self._add_to_local_cache(entry)
        
        # Обновляем статистику
        self.stats["total_tokens_saved"] += estimated_tokens
        self.stats["total_cost_saved"] += cost_saved
    
    def _add_to_local_cache(self, entry: SemanticCacheEntry):
        """Добавление в локальный LRU кэш"""
        # Удаляем старые записи если нужно
        while len(self.local_cache) >= self.local_cache_size:
            oldest_key = next(iter(self.local_cache))
            del self.local_cache[oldest_key]
        
        self.local_cache[entry.key] = entry
    
    def _generate_key(self, text: str) -> str:
        """Генерация ключа для текста"""
        return hashlib.sha256(text.encode()).hexdigest()[:16]
    
    def _get_model_cost(self, model: str) -> float:
        """Стоимость за токен для разных моделей"""
        costs = {
            "gpt-4o": 0.00001,
            "gpt-4o-mini": 0.0000015,
            "gpt-3.5-turbo": 0.0000015,
            "claude-3-opus": 0.000015,
            "claude-3-sonnet": 0.000003,
            "claude-3-haiku": 0.0000025
        }
        return costs.get(model, 0.000002)
    
    def _update_similarity_stats(self, score: float):
        """Обновление статистики similarity scores"""
        alpha = 0.1  # Скользящее среднее
        self.stats["avg_similarity"] = (
            alpha * score + 
            (1 - alpha) * self.stats["avg_similarity"]
        )
    
    async def clear_expired(self):
        """Очистка истекших записей"""
        current_time = time.time()
        
        # Очистка локального кэша
        expired_keys = [
            key for key, entry in self.local_cache.items()
            if current_time - entry.created_at > entry.ttl
        ]
        
        for key in expired_keys:
            del self.local_cache[key]
        
        logger.info(f"Cleared {len(expired_keys)} expired entries from local cache")
    
    def get_stats(self) -> Dict[str, Any]:
        """Получение расширенной статистики"""
        total_requests = self.stats["hits"] + self.stats["misses"]
        hit_rate = self.stats["hits"] / max(total_requests, 1)
        semantic_hit_rate = self.stats["semantic_hits"] / max(self.stats["hits"], 1)
        
        return {
            "hit_rate": f"{hit_rate * 100:.2f}%",
            "semantic_hit_rate": f"{semantic_hit_rate * 100:.2f}%",
            "exact_hit_rate": f"{(self.stats['exact_hits'] / max(self.stats['hits'], 1)) * 100:.2f}%",
            "total_requests": total_requests,
            "cache_hits": self.stats["hits"],
            "semantic_hits": self.stats["semantic_hits"],
            "exact_hits": self.stats["exact_hits"],
            "avg_similarity_score": f"{self.stats['avg_similarity']:.3f}",
            "tokens_saved": self.stats["total_tokens_saved"],
            "money_saved": f"${self.stats['total_cost_saved']:.2f}",
            "local_cache_size": len(self.local_cache),
            "similarity_threshold": self.similarity_threshold
        }

# Глобальный экземпляр кэша (может быть отключён через env)
_ENABLE_SEM_CACHE = os.getenv("SEMANTIC_CACHE_ENABLED", "true").lower() not in {"0", "false", "no"}
semantic_cache = SemanticLLMCache() if _ENABLE_SEM_CACHE else SemanticLLMCache()

# Декоратор для автоматического кэширования
def cached_llm_call(
    agent_name: str = "unknown",
    ttl: Optional[int] = None,
    include_metadata: bool = True
):
    """Декоратор для семантического кэширования вызовов LLM"""
    def decorator(func):
        async def wrapper(*args, **kwargs):
            # Извлекаем query из аргументов
            query = None
            if args and isinstance(args[0], str):
                query = args[0]
            elif 'messages' in kwargs and kwargs['messages']:
                # Для generate_reply
                last_message = kwargs['messages'][-1]
                query = last_message.get('content', '') if isinstance(last_message, dict) else str(last_message)
            elif 'query' in kwargs:
                query = kwargs['query']
            
            if not query:
                # Не можем кэшировать без query
                return await func(*args, **kwargs)
            
            # Метаданные
            metadata = {}
            if include_metadata:
                metadata['function'] = func.__name__
                metadata['module'] = func.__module__
            
            # Модель
            model = kwargs.get('model', 'gpt-4o-mini')
            
            # Оценка токенов
            estimated_tokens = len(query.split()) * 2  # Грубая оценка
            
            # Используем кэш
            result, from_cache, similarity = await semantic_cache.get_or_compute(
                query=query,
                compute_func=lambda: func(*args, **kwargs),
                agent_name=agent_name,
                ttl=ttl,
                model=model,
                estimated_tokens=estimated_tokens,
                metadata=metadata
            )
            
            if from_cache and similarity < 1.0:
                logger.info(f"Semantic cache hit with similarity {similarity:.3f}")
            
            return result
            
        return wrapper
    return decorator