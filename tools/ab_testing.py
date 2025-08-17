"""
A/B Testing System for Prompts
Система A/B тестирования для оптимизации промптов
"""
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timezone
from dataclasses import dataclass, field
import json
import random
import hashlib
from pathlib import Path
import statistics
try:
    from scipy import stats  # type: ignore
    _SCIPY_AVAILABLE = True
except Exception:
    stats = None  # type: ignore
    _SCIPY_AVAILABLE = False
import asyncio

from .quality_metrics import quality_metrics, TaskResult
from .event_sourcing import event_logger, EventType


@dataclass
class PromptVariant:
    """Вариант промпта для тестирования"""
    id: str
    name: str
    content: str
    agent_name: str
    task_type: Optional[str] = None
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    
    def get_hash(self) -> str:
        """Получить хеш содержимого для версионирования"""
        return hashlib.md5(self.content.encode()).hexdigest()[:8]


@dataclass
class ExperimentResult:
    """Результат эксперимента"""
    variant_id: str
    task_id: str
    success: bool
    confidence: float
    response_time: float
    token_cost: float
    user_satisfaction: Optional[float] = None  # 1-5 scale
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


@dataclass
class Experiment:
    """A/B эксперимент"""
    id: str
    name: str
    agent_name: str
    task_type: Optional[str]
    control_variant: PromptVariant
    test_variants: List[PromptVariant]
    traffic_split: Dict[str, float]  # variant_id -> percentage
    status: str = "running"  # running, paused, completed
    start_date: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    end_date: Optional[datetime] = None
    min_sample_size: int = 100
    confidence_level: float = 0.95
    
    def is_active(self) -> bool:
        """Проверить активен ли эксперимент"""
        return self.status == "running" and (
            self.end_date is None or datetime.now(timezone.utc) < self.end_date
        )


class ABTestingManager:
    """Менеджер A/B тестирования"""
    
    def __init__(self, storage_path: str = None):
        if storage_path is None:
            import os
            base = os.getenv("DATA_PATH", "data")
            storage_path = str(Path(base) / "ab_tests")
        self.storage_path = Path(storage_path)
        self.storage_path.mkdir(parents=True, exist_ok=True)
        
        self.experiments: Dict[str, Experiment] = {}
        self.results: Dict[str, List[ExperimentResult]] = {}
        self.variant_cache: Dict[str, PromptVariant] = {}
        
        # Load existing experiments
        self.load_experiments()
    
    def create_experiment(
        self,
        name: str,
        agent_name: str,
        control_prompt: str,
        test_prompts: List[Tuple[str, str]],  # [(name, content)]
        task_type: Optional[str] = None,
        traffic_split: Optional[Dict[str, float]] = None,
        min_sample_size: int = 100
    ) -> str:
        """Создать новый эксперимент"""
        experiment_id = f"exp_{agent_name}_{int(datetime.now(timezone.utc).timestamp())}"
        
        # Create control variant
        control = PromptVariant(
            id=f"{experiment_id}_control",
            name="Control",
            content=control_prompt,
            agent_name=agent_name,
            task_type=task_type
        )
        
        # Create test variants
        test_variants = []
        for i, (variant_name, content) in enumerate(test_prompts):
            variant = PromptVariant(
                id=f"{experiment_id}_test_{i}",
                name=variant_name,
                content=content,
                agent_name=agent_name,
                task_type=task_type
            )
            test_variants.append(variant)
            self.variant_cache[variant.id] = variant
        
        # Set traffic split
        if traffic_split is None:
            # Equal split
            num_variants = len(test_variants) + 1
            equal_split = 1.0 / num_variants
            traffic_split = {control.id: equal_split}
            for variant in test_variants:
                traffic_split[variant.id] = equal_split
        
        # Create experiment
        experiment = Experiment(
            id=experiment_id,
            name=name,
            agent_name=agent_name,
            task_type=task_type,
            control_variant=control,
            test_variants=test_variants,
            traffic_split=traffic_split,
            min_sample_size=min_sample_size
        )
        
        self.experiments[experiment_id] = experiment
        self.results[experiment_id] = []
        self.variant_cache[control.id] = control
        
        # Save
        self.save_experiments()
        
        return experiment_id
    
    def get_variant_for_task(
        self, 
        agent_name: str, 
        task_type: Optional[str] = None,
        user_id: Optional[str] = None
    ) -> Optional[PromptVariant]:
        """Получить вариант промпта для задачи"""
        # Find active experiments for agent
        active_experiments = [
            exp for exp in self.experiments.values()
            if exp.agent_name == agent_name 
            and exp.is_active()
            and (exp.task_type is None or exp.task_type == task_type)
        ]
        
        if not active_experiments:
            return None
        
        # Use first matching experiment
        experiment = active_experiments[0]
        
        # Deterministic assignment based on user_id
        if user_id:
            hash_value = int(hashlib.md5(f"{experiment.id}:{user_id}".encode()).hexdigest(), 16)
            assignment = hash_value % 100 / 100.0
        else:
            assignment = random.random()
        
        # Select variant based on traffic split
        cumulative = 0.0
        for variant_id, percentage in experiment.traffic_split.items():
            cumulative += percentage
            if assignment < cumulative:
                return self.variant_cache.get(variant_id)
        
        # Fallback to control
        return experiment.control_variant
    
    def record_result(
        self,
        experiment_id: str,
        variant_id: str,
        task_result: TaskResult,
        user_satisfaction: Optional[float] = None
    ) -> None:
        """Записать результат эксперимента"""
        result = ExperimentResult(
            variant_id=variant_id,
            task_id=task_result.task_id,
            success=task_result.status == "success",
            confidence=task_result.confidence,
            response_time=task_result.response_time,
            token_cost=task_result.token_cost,
            user_satisfaction=user_satisfaction
        )
        
        if experiment_id not in self.results:
            self.results[experiment_id] = []
        
        self.results[experiment_id].append(result)
        
        # Check if experiment should be stopped
        self._check_experiment_completion(experiment_id)
        
        # Save periodically
        if len(self.results[experiment_id]) % 10 == 0:
            self.save_experiments()
    
    def _check_experiment_completion(self, experiment_id: str) -> None:
        """Проверить нужно ли завершить эксперимент"""
        experiment = self.experiments.get(experiment_id)
        if not experiment or not experiment.is_active():
            return
        
        results = self.results.get(experiment_id, [])
        
        # Check minimum sample size
        variant_counts = {}
        for result in results:
            variant_counts[result.variant_id] = variant_counts.get(result.variant_id, 0) + 1
        
        min_count = min(variant_counts.values()) if variant_counts else 0
        
        if min_count >= experiment.min_sample_size:
            # Perform statistical analysis
            analysis = self.analyze_experiment(experiment_id)
            
            # Check if we have statistical significance
            if analysis.get("has_winner"):
                experiment.status = "completed"
                experiment.end_date = datetime.now(timezone.utc)
                
                # Log completion
                asyncio.create_task(event_logger.log_system_event(
                    EventType.PROMPT_UPDATED,
                    {
                        "experiment_id": experiment_id,
                        "winner": analysis.get("winner"),
                        "improvement": analysis.get("improvement")
                    }
                ))
    
    def analyze_experiment(self, experiment_id: str) -> Dict[str, Any]:
        """Анализировать результаты эксперимента"""
        experiment = self.experiments.get(experiment_id)
        if not experiment:
            return {"error": "Experiment not found"}
        
        results = self.results.get(experiment_id, [])
        if not results:
            return {"error": "No results yet"}
        
        # Group results by variant
        variant_results = {}
        for result in results:
            if result.variant_id not in variant_results:
                variant_results[result.variant_id] = []
            variant_results[result.variant_id].append(result)
        
        # Calculate metrics for each variant
        variant_metrics = {}
        for variant_id, variant_results_list in variant_results.items():
            metrics = self._calculate_variant_metrics(variant_results_list)
            variant_metrics[variant_id] = metrics
        
        # Perform statistical tests
        control_id = experiment.control_variant.id
        control_metrics = variant_metrics.get(control_id, {})
        
        best_variant = control_id
        best_improvement = 0.0
        has_winner = False
        
        for variant in experiment.test_variants:
            test_metrics = variant_metrics.get(variant.id, {})
            
            # Compare success rates
            if "success_rate" in control_metrics and "success_rate" in test_metrics:
                # Chi-square test for success rates
                control_successes = control_metrics["success_count"]
                control_total = control_metrics["total_count"]
                test_successes = test_metrics["success_count"]
                test_total = test_metrics["total_count"]
                
                # Perform chi-square test
                observed = [[control_successes, control_total - control_successes],
                           [test_successes, test_total - test_successes]]
                
                try:
                    if _SCIPY_AVAILABLE and stats is not None:
                        chi2, p_value = stats.chi2_contingency(observed)[:2]
                        significant = p_value < (1 - experiment.confidence_level)
                    else:
                        # Fallback: simple heuristic significance when sample sizes are large and delta is notable
                        total = control_total + test_total
                        delta = abs(test_metrics["success_rate"] - control_metrics["success_rate"]) if total > 0 else 0
                        significant = (total >= max(50, experiment.min_sample_size)) and (delta >= 0.1)

                    if significant:
                        improvement = (test_metrics["success_rate"] - control_metrics["success_rate"]) / max(control_metrics["success_rate"], 1e-9)
                        if improvement > best_improvement:
                            best_improvement = improvement
                            best_variant = variant.id
                            has_winner = True
                except Exception:
                    pass  # Not enough data or computation unavailable
        
        return {
            "experiment_id": experiment_id,
            "status": experiment.status,
            "control_metrics": control_metrics,
            "variant_metrics": variant_metrics,
            "has_winner": has_winner,
            "winner": best_variant if has_winner else None,
            "improvement": best_improvement if has_winner else 0.0,
            "sample_sizes": {
                vid: len(vresults) 
                for vid, vresults in variant_results.items()
            }
        }
    
    def _calculate_variant_metrics(self, results: List[ExperimentResult]) -> Dict[str, Any]:
        """Рассчитать метрики для варианта"""
        if not results:
            return {}
        
        success_count = sum(1 for r in results if r.success)
        total_count = len(results)
        
        confidences = [r.confidence for r in results if r.success]
        response_times = [r.response_time for r in results]
        costs = [r.token_cost for r in results]
        satisfactions = [r.user_satisfaction for r in results if r.user_satisfaction is not None]
        
        metrics = {
            "total_count": total_count,
            "success_count": success_count,
            "success_rate": success_count / total_count,
            "avg_confidence": statistics.mean(confidences) if confidences else 0,
            "avg_response_time": statistics.mean(response_times),
            "avg_cost": statistics.mean(costs),
            "cost_per_success": sum(costs) / max(success_count, 1)
        }
        
        if satisfactions:
            metrics["avg_satisfaction"] = statistics.mean(satisfactions)
        
        return metrics
    
    def get_winning_prompt(self, agent_name: str, task_type: Optional[str] = None) -> Optional[str]:
        """Получить победивший промпт для агента"""
        # Find completed experiments
        completed = [
            exp for exp in self.experiments.values()
            if exp.agent_name == agent_name 
            and exp.status == "completed"
            and (exp.task_type is None or exp.task_type == task_type)
        ]
        
        if not completed:
            return None
        
        # Get most recent completed experiment
        latest = max(completed, key=lambda e: e.end_date or e.start_date)
        
        # Get analysis
        analysis = self.analyze_experiment(latest.id)
        
        if analysis.get("has_winner"):
            winner_id = analysis.get("winner")
            winner_variant = self.variant_cache.get(winner_id)
            if winner_variant:
                return winner_variant.content
        
        return None
    
    def save_experiments(self) -> None:
        """Сохранить эксперименты на диск"""
        # Save experiments
        experiments_file = self.storage_path / "experiments.json"
        experiments_data = {}
        
        for exp_id, experiment in self.experiments.items():
            experiments_data[exp_id] = {
                "id": experiment.id,
                "name": experiment.name,
                "agent_name": experiment.agent_name,
                "task_type": experiment.task_type,
                "control_variant": {
                    "id": experiment.control_variant.id,
                    "name": experiment.control_variant.name,
                    "content": experiment.control_variant.content
                },
                "test_variants": [
                    {
                        "id": v.id,
                        "name": v.name,
                        "content": v.content
                    }
                    for v in experiment.test_variants
                ],
                "traffic_split": experiment.traffic_split,
                "status": experiment.status,
                "start_date": experiment.start_date.isoformat(),
                "end_date": experiment.end_date.isoformat() if experiment.end_date else None,
                "min_sample_size": experiment.min_sample_size,
                "confidence_level": experiment.confidence_level
            }
        
        with open(experiments_file, "w") as f:
            json.dump(experiments_data, f, indent=2)
        
        # Save results
        results_file = self.storage_path / "results.json"
        results_data = {}
        
        for exp_id, results in self.results.items():
            results_data[exp_id] = [
                {
                    "variant_id": r.variant_id,
                    "task_id": r.task_id,
                    "success": r.success,
                    "confidence": r.confidence,
                    "response_time": r.response_time,
                    "token_cost": r.token_cost,
                    "user_satisfaction": r.user_satisfaction,
                    "timestamp": r.timestamp.isoformat()
                }
                for r in results
            ]
        
        with open(results_file, "w") as f:
            json.dump(results_data, f, indent=2)
    
    def load_experiments(self) -> None:
        """Загрузить эксперименты с диска"""
        # Load experiments
        experiments_file = self.storage_path / "experiments.json"
        if experiments_file.exists():
            with open(experiments_file, "r") as f:
                experiments_data = json.load(f)
            
            for exp_id, data in experiments_data.items():
                # Recreate variants
                control = PromptVariant(
                    id=data["control_variant"]["id"],
                    name=data["control_variant"]["name"],
                    content=data["control_variant"]["content"],
                    agent_name=data["agent_name"],
                    task_type=data.get("task_type")
                )
                
                test_variants = []
                for v_data in data["test_variants"]:
                    variant = PromptVariant(
                        id=v_data["id"],
                        name=v_data["name"],
                        content=v_data["content"],
                        agent_name=data["agent_name"],
                        task_type=data.get("task_type")
                    )
                    test_variants.append(variant)
                    self.variant_cache[variant.id] = variant
                
                # Create experiment
                experiment = Experiment(
                    id=data["id"],
                    name=data["name"],
                    agent_name=data["agent_name"],
                    task_type=data.get("task_type"),
                    control_variant=control,
                    test_variants=test_variants,
                    traffic_split=data["traffic_split"],
                    status=data["status"],
                    start_date=datetime.fromisoformat(data["start_date"]),
                    end_date=datetime.fromisoformat(data["end_date"]) if data["end_date"] else None,
                    min_sample_size=data.get("min_sample_size", 100),
                    confidence_level=data.get("confidence_level", 0.95)
                )
                
                self.experiments[exp_id] = experiment
                self.variant_cache[control.id] = control
        
        # Load results
        results_file = self.storage_path / "results.json"
        if results_file.exists():
            with open(results_file, "r") as f:
                results_data = json.load(f)
            
            for exp_id, results_list in results_data.items():
                self.results[exp_id] = []
                for r_data in results_list:
                    result = ExperimentResult(
                        variant_id=r_data["variant_id"],
                        task_id=r_data["task_id"],
                        success=r_data["success"],
                        confidence=r_data["confidence"],
                        response_time=r_data["response_time"],
                        token_cost=r_data["token_cost"],
                        user_satisfaction=r_data.get("user_satisfaction"),
                        timestamp=datetime.fromisoformat(r_data["timestamp"])
                    )
                    self.results[exp_id].append(result)


# Global A/B testing manager
ab_testing = ABTestingManager()