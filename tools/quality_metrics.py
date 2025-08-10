"""
Quality Metrics System for Root-MAS
Система оценки качества результатов работы агентов
"""
from typing import Dict, Any, List, Optional
from datetime import datetime, timezone
from dataclasses import dataclass, field
import json
from pathlib import Path
import statistics


@dataclass
class AgentMetrics:
    """Метрики производительности агента"""
    agent_name: str
    total_tasks: int = 0
    successful_tasks: int = 0
    failed_tasks: int = 0
    average_confidence: float = 0.0
    average_response_time: float = 0.0
    model_usage: Dict[str, int] = field(default_factory=dict)
    error_types: Dict[str, int] = field(default_factory=dict)
    
    @property
    def success_rate(self) -> float:
        if self.total_tasks == 0:
            return 0.0
        return self.successful_tasks / self.total_tasks
    
    @property
    def failure_rate(self) -> float:
        if self.total_tasks == 0:
            return 0.0
        return self.failed_tasks / self.total_tasks


@dataclass
class TaskResult:
    """Результат выполнения задачи"""
    task_id: str
    agent_name: str
    task_type: str
    status: str  # success, failure, partial
    confidence: float
    response_time: float
    model_used: str
    tier_used: str
    token_cost: float
    error: Optional[str] = None
    feedback: Optional[Dict[str, Any]] = None
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


class QualityMetricsManager:
    """Менеджер метрик качества"""
    
    def __init__(self, storage_path: str = "/workspace/data/metrics"):
        self.storage_path = Path(storage_path)
        self.storage_path.mkdir(parents=True, exist_ok=True)
        
        self.agent_metrics: Dict[str, AgentMetrics] = {}
        self.task_results: List[TaskResult] = []
        self.load_metrics()
    
    def record_task_result(self, result: TaskResult) -> None:
        """Записать результат выполнения задачи"""
        self.task_results.append(result)
        
        # Update agent metrics
        if result.agent_name not in self.agent_metrics:
            self.agent_metrics[result.agent_name] = AgentMetrics(result.agent_name)
        
        metrics = self.agent_metrics[result.agent_name]
        metrics.total_tasks += 1
        
        if result.status == "success":
            metrics.successful_tasks += 1
        elif result.status == "failure":
            metrics.failed_tasks += 1
            if result.error:
                metrics.error_types[result.error] = metrics.error_types.get(result.error, 0) + 1
        
        # Update averages
        metrics.average_confidence = self._calculate_average_confidence(result.agent_name)
        metrics.average_response_time = self._calculate_average_response_time(result.agent_name)
        
        # Track model usage
        model_key = f"{result.tier_used}:{result.model_used}"
        metrics.model_usage[model_key] = metrics.model_usage.get(model_key, 0) + 1
        
        # Save periodically
        if len(self.task_results) % 10 == 0:
            self.save_metrics()
    
    def get_agent_performance(self, agent_name: str) -> Dict[str, Any]:
        """Получить метрики производительности агента"""
        if agent_name not in self.agent_metrics:
            return {"error": "Agent not found"}
        
        metrics = self.agent_metrics[agent_name]
        recent_tasks = [r for r in self.task_results[-100:] if r.agent_name == agent_name]
        
        return {
            "agent_name": agent_name,
            "success_rate": metrics.success_rate,
            "failure_rate": metrics.failure_rate,
            "average_confidence": metrics.average_confidence,
            "average_response_time": metrics.average_response_time,
            "total_tasks": metrics.total_tasks,
            "recent_trend": self._calculate_trend(recent_tasks),
            "model_preferences": self._analyze_model_preferences(metrics),
            "common_errors": dict(sorted(metrics.error_types.items(), key=lambda x: x[1], reverse=True)[:5])
        }
    
    def get_model_performance(self, model: str, tier: str) -> Dict[str, Any]:
        """Анализ производительности конкретной модели"""
        model_tasks = [
            r for r in self.task_results 
            if r.model_used == model and r.tier_used == tier
        ]
        
        if not model_tasks:
            return {"error": "No data for this model"}
        
        success_tasks = [t for t in model_tasks if t.status == "success"]
        
        return {
            "model": model,
            "tier": tier,
            "total_uses": len(model_tasks),
            "success_rate": len(success_tasks) / len(model_tasks),
            "average_confidence": statistics.mean([t.confidence for t in success_tasks]) if success_tasks else 0,
            "average_response_time": statistics.mean([t.response_time for t in model_tasks]),
            "average_cost": statistics.mean([t.token_cost for t in model_tasks]),
            "cost_per_success": sum(t.token_cost for t in model_tasks) / max(len(success_tasks), 1)
        }
    
    def suggest_model_optimization(self, agent_name: str, task_type: str) -> Dict[str, Any]:
        """Предложить оптимальную модель для задачи"""
        # Analyze historical performance
        relevant_tasks = [
            r for r in self.task_results
            if r.agent_name == agent_name and r.task_type == task_type
        ]
        
        if not relevant_tasks:
            return {
                "suggestion": "Use default tier",
                "reasoning": "No historical data available"
            }
        
        # Group by model/tier combination
        model_stats = {}
        for task in relevant_tasks:
            key = f"{task.tier_used}:{task.model_used}"
            if key not in model_stats:
                model_stats[key] = {
                    "successes": 0,
                    "total": 0,
                    "total_cost": 0,
                    "total_time": 0
                }
            
            model_stats[key]["total"] += 1
            model_stats[key]["total_cost"] += task.token_cost
            model_stats[key]["total_time"] += task.response_time
            
            if task.status == "success":
                model_stats[key]["successes"] += 1
        
        # Calculate efficiency scores
        recommendations = []
        for model_key, stats in model_stats.items():
            if stats["total"] < 3:  # Skip if too few samples
                continue
            
            success_rate = stats["successes"] / stats["total"]
            avg_cost = stats["total_cost"] / stats["total"]
            avg_time = stats["total_time"] / stats["total"]
            
            # Efficiency score: balance success rate, cost, and time
            efficiency = success_rate * (1 / (avg_cost + 0.01)) * (1 / (avg_time + 0.1))
            
            tier, model = model_key.split(":", 1)
            recommendations.append({
                "tier": tier,
                "model": model,
                "success_rate": success_rate,
                "avg_cost": avg_cost,
                "avg_time": avg_time,
                "efficiency_score": efficiency,
                "sample_size": stats["total"]
            })
        
        # Sort by efficiency
        recommendations.sort(key=lambda x: x["efficiency_score"], reverse=True)
        
        if recommendations:
            best = recommendations[0]
            return {
                "suggestion": f"Use {best['tier']} tier with {best['model']}",
                "reasoning": f"Best efficiency score ({best['efficiency_score']:.2f}) based on {best['sample_size']} samples",
                "expected_success_rate": best['success_rate'],
                "expected_cost": best['avg_cost'],
                "alternatives": recommendations[1:3]  # Top 3 alternatives
            }
        else:
            return {
                "suggestion": "Use standard tier",
                "reasoning": "Insufficient data for optimization"
            }
    
    def _calculate_average_confidence(self, agent_name: str) -> float:
        """Рассчитать среднюю уверенность агента"""
        agent_tasks = [r for r in self.task_results if r.agent_name == agent_name and r.status == "success"]
        if not agent_tasks:
            return 0.0
        return statistics.mean([t.confidence for t in agent_tasks])
    
    def _calculate_average_response_time(self, agent_name: str) -> float:
        """Рассчитать среднее время ответа"""
        agent_tasks = [r for r in self.task_results if r.agent_name == agent_name]
        if not agent_tasks:
            return 0.0
        return statistics.mean([t.response_time for t in agent_tasks])
    
    def _calculate_trend(self, recent_tasks: List[TaskResult]) -> str:
        """Определить тренд производительности"""
        if len(recent_tasks) < 10:
            return "insufficient_data"
        
        # Split into halves and compare success rates
        mid = len(recent_tasks) // 2
        first_half = recent_tasks[:mid]
        second_half = recent_tasks[mid:]
        
        first_success_rate = sum(1 for t in first_half if t.status == "success") / len(first_half)
        second_success_rate = sum(1 for t in second_half if t.status == "success") / len(second_half)
        
        if second_success_rate > first_success_rate + 0.1:
            return "improving"
        elif second_success_rate < first_success_rate - 0.1:
            return "declining"
        else:
            return "stable"
    
    def _analyze_model_preferences(self, metrics: AgentMetrics) -> Dict[str, Any]:
        """Анализ предпочтений моделей"""
        if not metrics.model_usage:
            return {}
        
        total_uses = sum(metrics.model_usage.values())
        preferences = {}
        
        for model_key, count in metrics.model_usage.items():
            tier, model = model_key.split(":", 1)
            if tier not in preferences:
                preferences[tier] = {}
            preferences[tier][model] = {
                "usage_count": count,
                "usage_percentage": (count / total_uses) * 100
            }
        
        return preferences
    
    def save_metrics(self) -> None:
        """Сохранить метрики на диск"""
        # Save agent metrics
        metrics_file = self.storage_path / "agent_metrics.json"
        metrics_data = {
            name: {
                "total_tasks": m.total_tasks,
                "successful_tasks": m.successful_tasks,
                "failed_tasks": m.failed_tasks,
                "average_confidence": m.average_confidence,
                "average_response_time": m.average_response_time,
                "model_usage": m.model_usage,
                "error_types": m.error_types
            }
            for name, m in self.agent_metrics.items()
        }
        
        with open(metrics_file, "w") as f:
            json.dump(metrics_data, f, indent=2)
        
        # Save recent task results (last 1000)
        results_file = self.storage_path / "recent_results.json"
        recent_results = self.task_results[-1000:]
        results_data = [
            {
                "task_id": r.task_id,
                "agent_name": r.agent_name,
                "task_type": r.task_type,
                "status": r.status,
                "confidence": r.confidence,
                "response_time": r.response_time,
                "model_used": r.model_used,
                "tier_used": r.tier_used,
                "token_cost": r.token_cost,
                "error": r.error,
                "feedback": r.feedback,
                "timestamp": r.timestamp.isoformat()
            }
            for r in recent_results
        ]
        
        with open(results_file, "w") as f:
            json.dump(results_data, f, indent=2)
    
    def load_metrics(self) -> None:
        """Загрузить метрики с диска"""
        # Load agent metrics
        metrics_file = self.storage_path / "agent_metrics.json"
        if metrics_file.exists():
            with open(metrics_file, "r") as f:
                metrics_data = json.load(f)
            
            for name, data in metrics_data.items():
                self.agent_metrics[name] = AgentMetrics(
                    agent_name=name,
                    total_tasks=data.get("total_tasks", 0),
                    successful_tasks=data.get("successful_tasks", 0),
                    failed_tasks=data.get("failed_tasks", 0),
                    average_confidence=data.get("average_confidence", 0.0),
                    average_response_time=data.get("average_response_time", 0.0),
                    model_usage=data.get("model_usage", {}),
                    error_types=data.get("error_types", {})
                )
        
        # Load recent results
        results_file = self.storage_path / "recent_results.json"
        if results_file.exists():
            with open(results_file, "r") as f:
                results_data = json.load(f)
            
            for data in results_data:
                self.task_results.append(TaskResult(
                    task_id=data["task_id"],
                    agent_name=data["agent_name"],
                    task_type=data["task_type"],
                    status=data["status"],
                    confidence=data["confidence"],
                    response_time=data["response_time"],
                    model_used=data["model_used"],
                    tier_used=data["tier_used"],
                    token_cost=data["token_cost"],
                    error=data.get("error"),
                    feedback=data.get("feedback"),
                    timestamp=datetime.fromisoformat(data["timestamp"])
                ))


# Global instance
quality_metrics = QualityMetricsManager()