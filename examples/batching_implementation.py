"""
Система батчинга для эффективной обработки групповых запросов в Root-MAS
"""
from typing import List, Dict, Any, Optional, Callable, Tuple
import asyncio
from dataclasses import dataclass, field
from datetime import datetime, timezone
import time
from collections import defaultdict
import json
from autogen_agentchat.agents import AssistantAgent
from autogen_agentchat.messages import TextMessage
from autogen_core import CancellationToken

@dataclass
class BatchRequest:
    """Отдельный запрос в батче"""
    id: str
    content: str
    user_id: str
    priority: int = 1
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: float = field(default_factory=time.time)
    callback: Optional[asyncio.Future] = None

@dataclass 
class BatchResult:
    """Результат обработки батча"""
    batch_id: str
    total_requests: int
    successful: int
    failed: int
    processing_time: float
    results: Dict[str, Any]
    cost_estimate: float

class BatchProcessor:
    """Процессор для батчевой обработки запросов"""
    
    def __init__(
        self,
        batch_size: int = 10,
        batch_timeout: float = 1.0,  # секунды
        max_batch_size: int = 50
    ):
        self.batch_size = batch_size
        self.batch_timeout = batch_timeout
        self.max_batch_size = max_batch_size
        
        # Очереди для разных приоритетов
        self.queues = {
            1: asyncio.Queue(),  # Низкий приоритет
            2: asyncio.Queue(),  # Средний
            3: asyncio.Queue()   # Высокий
        }
        
        # Активные батчи
        self.active_batches: Dict[str, List[BatchRequest]] = {}
        
        # Статистика
        self.stats = {
            "total_batches": 0,
            "total_requests": 0,
            "avg_batch_size": 0,
            "avg_processing_time": 0
        }
        
        # Запускаем обработчики
        self.processors = []
        
    async def start(self):
        """Запуск обработчиков батчей"""
        for priority in [3, 2, 1]:  # От высокого к низкому
            processor = asyncio.create_task(
                self._batch_processor(priority)
            )
            self.processors.append(processor)
    
    async def stop(self):
        """Остановка обработчиков"""
        for processor in self.processors:
            processor.cancel()
    
    async def add_request(
        self,
        content: str,
        user_id: str,
        priority: int = 1,
        metadata: Optional[Dict] = None
    ) -> Any:
        """Добавление запроса в батч"""
        request = BatchRequest(
            id=f"{user_id}_{time.time()}",
            content=content,
            user_id=user_id,
            priority=min(max(priority, 1), 3),  # 1-3
            metadata=metadata or {},
            callback=asyncio.Future()
        )
        
        # Добавляем в соответствующую очередь
        await self.queues[request.priority].put(request)
        
        # Ждем результат
        return await request.callback
    
    async def _batch_processor(self, priority: int):
        """Обработчик батчей для конкретного приоритета"""
        queue = self.queues[priority]
        
        while True:
            batch = []
            batch_start_time = time.time()
            
            try:
                # Собираем батч
                while len(batch) < self.batch_size:
                    timeout = self.batch_timeout - (time.time() - batch_start_time)
                    
                    if timeout <= 0:
                        break
                    
                    try:
                        request = await asyncio.wait_for(
                            queue.get(),
                            timeout=timeout
                        )
                        batch.append(request)
                        
                        # Проверяем максимальный размер
                        if len(batch) >= self.max_batch_size:
                            break
                            
                    except asyncio.TimeoutError:
                        break
                
                # Обрабатываем батч если есть запросы
                if batch:
                    await self._process_batch(batch, priority)
                    
            except Exception as e:
                print(f"Error in batch processor: {e}")
                # Отменяем все запросы в батче с ошибкой
                for req in batch:
                    if req.callback and not req.callback.done():
                        req.callback.set_exception(e)
    
    async def _process_batch(
        self, 
        batch: List[BatchRequest], 
        priority: int
    ):
        """Обработка одного батча"""
        batch_id = f"batch_{priority}_{time.time()}"
        start_time = time.time()
        
        try:
            # Группируем по типам задач для оптимизации
            grouped = self._group_requests(batch)
            
            # Обрабатываем каждую группу
            results = {}
            for task_type, requests in grouped.items():
                group_results = await self._process_group(
                    task_type, 
                    requests
                )
                results.update(group_results)
            
            # Возвращаем результаты
            for request in batch:
                if request.id in results:
                    request.callback.set_result(results[request.id])
                else:
                    request.callback.set_exception(
                        Exception("No result for request")
                    )
            
            # Обновляем статистику
            processing_time = time.time() - start_time
            self._update_stats(len(batch), processing_time)
            
        except Exception as e:
            # Ошибка всего батча
            for request in batch:
                if not request.callback.done():
                    request.callback.set_exception(e)
    
    def _group_requests(
        self, 
        batch: List[BatchRequest]
    ) -> Dict[str, List[BatchRequest]]:
        """Группировка запросов по типам"""
        grouped = defaultdict(list)
        
        for request in batch:
            # Определяем тип задачи из метаданных или контента
            task_type = request.metadata.get("task_type", "general")
            grouped[task_type].append(request)
        
        return grouped
    
    async def _process_group(
        self,
        task_type: str,
        requests: List[BatchRequest]
    ) -> Dict[str, Any]:
        """Обработка группы однотипных запросов"""
        # Здесь была бы реальная обработка через LLM
        # Для примера - простая имитация
        results = {}
        
        # Формируем единый промпт для всей группы
        combined_prompt = self._create_batch_prompt(task_type, requests)
        
        # Вызов к LLM (имитация)
        await asyncio.sleep(0.1)  # Имитация вызова API
        
        # Парсим результаты для каждого запроса
        for i, request in enumerate(requests):
            results[request.id] = {
                "response": f"Batch response for {task_type}: {request.content[:50]}...",
                "batch_position": i,
                "processing_time": 0.1
            }
        
        return results
    
    def _create_batch_prompt(
        self,
        task_type: str,
        requests: List[BatchRequest]
    ) -> str:
        """Создание единого промпта для батча"""
        if task_type == "classification":
            return self._create_classification_prompt(requests)
        elif task_type == "summarization":
            return self._create_summarization_prompt(requests)
        else:
            return self._create_general_prompt(requests)
    
    def _create_classification_prompt(
        self,
        requests: List[BatchRequest]
    ) -> str:
        """Промпт для классификации"""
        prompt = """Классифицируй следующие тексты.
Для каждого текста определи категорию и уверенность (0-1).

Тексты:
"""
        for i, req in enumerate(requests):
            prompt += f"{i+1}. {req.content}\n"
        
        prompt += "\nОтветь в формате JSON: [{category, confidence}, ...]"
        return prompt
    
    def _create_summarization_prompt(
        self,
        requests: List[BatchRequest]
    ) -> str:
        """Промпт для суммаризации"""
        prompt = """Создай краткие резюме для следующих текстов.

Тексты:
"""
        for i, req in enumerate(requests):
            prompt += f"\n--- Текст {i+1} ---\n{req.content}\n"
        
        prompt += "\nДля каждого текста создай резюме в 1-2 предложения."
        return prompt
    
    def _create_general_prompt(
        self,
        requests: List[BatchRequest]
    ) -> str:
        """Общий промпт для разных задач"""
        prompt = "Обработай следующие запросы:\n\n"
        
        for i, req in enumerate(requests):
            prompt += f"Запрос {i+1}: {req.content}\n"
            
        return prompt
    
    def _update_stats(self, batch_size: int, processing_time: float):
        """Обновление статистики"""
        self.stats["total_batches"] += 1
        self.stats["total_requests"] += batch_size
        
        # Скользящее среднее
        alpha = 0.1
        self.stats["avg_batch_size"] = (
            alpha * batch_size + 
            (1 - alpha) * self.stats["avg_batch_size"]
        )
        self.stats["avg_processing_time"] = (
            alpha * processing_time + 
            (1 - alpha) * self.stats["avg_processing_time"]
        )

# Умный батчер с динамическим размером
class AdaptiveBatchProcessor(BatchProcessor):
    """Батч-процессор с адаптивным размером батча"""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.performance_history = []
        self.optimal_batch_sizes = {
            1: self.batch_size,
            2: self.batch_size,
            3: self.batch_size
        }
    
    async def _process_batch(
        self, 
        batch: List[BatchRequest], 
        priority: int
    ):
        """Обработка с измерением производительности"""
        start_time = time.time()
        
        # Обрабатываем
        await super()._process_batch(batch, priority)
        
        # Измеряем производительность
        processing_time = time.time() - start_time
        throughput = len(batch) / processing_time
        
        # Сохраняем историю
        self.performance_history.append({
            "batch_size": len(batch),
            "priority": priority,
            "throughput": throughput,
            "time": processing_time
        })
        
        # Адаптируем размер батча
        self._adapt_batch_size(priority)
    
    def _adapt_batch_size(self, priority: int):
        """Адаптация размера батча на основе производительности"""
        # Анализируем последние 10 батчей
        recent = [
            h for h in self.performance_history[-10:]
            if h["priority"] == priority
        ]
        
        if len(recent) < 3:
            return
        
        # Находим оптимальный размер
        best_throughput = 0
        best_size = self.batch_size
        
        for size in range(5, self.max_batch_size, 5):
            size_data = [h for h in recent if abs(h["batch_size"] - size) < 3]
            
            if size_data:
                avg_throughput = sum(h["throughput"] for h in size_data) / len(size_data)
                
                if avg_throughput > best_throughput:
                    best_throughput = avg_throughput
                    best_size = size
        
        # Применяем новый размер
        self.optimal_batch_sizes[priority] = best_size

# Интеграция с FastAPI
from fastapi import FastAPI, BackgroundTasks
from pydantic import BaseModel

app = FastAPI()
batch_processor = AdaptiveBatchProcessor(
    batch_size=10,
    batch_timeout=0.5,
    max_batch_size=100
)

class BatchRequestModel(BaseModel):
    content: str
    priority: int = 1
    task_type: str = "general"

@app.on_event("startup")
async def startup():
    await batch_processor.start()

@app.on_event("shutdown")
async def shutdown():
    await batch_processor.stop()

@app.post("/api/v1/batch/process")
async def process_batch_request(
    request: BatchRequestModel,
    user_id: str
):
    """Обработка запроса через батчинг"""
    result = await batch_processor.add_request(
        content=request.content,
        user_id=user_id,
        priority=request.priority,
        metadata={"task_type": request.task_type}
    )
    
    return result

@app.post("/api/v1/batch/bulk")
async def process_bulk_requests(
    requests: List[BatchRequestModel],
    user_id: str,
    background_tasks: BackgroundTasks
):
    """Массовая обработка запросов"""
    if len(requests) > 100:
        # Для очень больших запросов - в фоне
        background_tasks.add_task(
            _process_bulk_background,
            requests,
            user_id
        )
        return {
            "status": "processing",
            "count": len(requests),
            "message": "Large batch processing started"
        }
    
    # Для небольших - сразу
    tasks = []
    for req in requests:
        task = batch_processor.add_request(
            content=req.content,
            user_id=user_id,
            priority=req.priority,
            metadata={"task_type": req.task_type}
        )
        tasks.append(task)
    
    results = await asyncio.gather(*tasks, return_exceptions=True)
    
    return {
        "status": "completed",
        "results": results,
        "stats": batch_processor.stats
    }

async def _process_bulk_background(
    requests: List[BatchRequestModel],
    user_id: str
):
    """Фоновая обработка больших батчей"""
    # Здесь была бы логика сохранения результатов
    pass

@app.get("/api/v1/batch/stats")
async def get_batch_stats():
    """Статистика батчинга"""
    return {
        "stats": batch_processor.stats,
        "optimal_sizes": batch_processor.optimal_batch_sizes,
        "queue_sizes": {
            p: q.qsize() for p, q in batch_processor.queues.items()
        }
    }