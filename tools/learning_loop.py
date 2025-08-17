"""
Learning Loop System for Root-MAS
Система обучения с подкреплением на основе обратной связи
"""
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timezone, timedelta
from dataclasses import dataclass, field
import json
import os
import numpy as np
from pathlib import Path
import asyncio
from collections import defaultdict

from .quality_metrics import quality_metrics, TaskResult
from .event_sourcing import event_store, event_logger, EventType
from .prompt_builder import update_agent_prompt, audit_prompt


@dataclass
class Experience:
    """Единица опыта для обучения"""
    state: Dict[str, Any]  # Состояние до действия
    action: str  # Выбранное действие
    reward: float  # Полученная награда
    next_state: Dict[str, Any]  # Состояние после действия
    agent_name: str
    task_type: str
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


@dataclass
class LearningPolicy:
    """Политика обучения агента"""
    agent_name: str
    action_values: Dict[str, float] = field(default_factory=dict)  # Q-values
    action_counts: Dict[str, int] = field(default_factory=dict)
    exploration_rate: float = 0.1
    learning_rate: float = 0.1
    discount_factor: float = 0.95
    
    def get_best_action(self, available_actions: List[str]) -> str:
        """Получить лучшее действие согласно политике"""
        if not available_actions:
            return ""
        
        # Epsilon-greedy exploration
        if np.random.random() < self.exploration_rate:
            return np.random.choice(available_actions)
        
        # Choose best known action
        best_value = -float('inf')
        best_action = available_actions[0]
        
        for action in available_actions:
            value = self.action_values.get(action, 0.0)
            if value > best_value:
                best_value = value
                best_action = action
        
        return best_action
    
    def update(self, experience: Experience) -> None:
        """Обновить политику на основе опыта"""
        action = experience.action
        reward = experience.reward
        
        # Update count
        self.action_counts[action] = self.action_counts.get(action, 0) + 1
        
        # Q-learning update
        old_value = self.action_values.get(action, 0.0)
        
        # Get max Q-value for next state actions
        next_actions = experience.next_state.get('available_actions', [])
        if next_actions:
            max_next_value = max(
                self.action_values.get(a, 0.0) for a in next_actions
            )
        else:
            max_next_value = 0.0
        
        # Q-learning formula
        new_value = old_value + self.learning_rate * (
            reward + self.discount_factor * max_next_value - old_value
        )
        
        self.action_values[action] = new_value
        
        # Decay exploration rate
        self.exploration_rate = max(0.01, self.exploration_rate * 0.995)


class LearningLoop:
    """Основной цикл обучения системы"""
    
    def __init__(self, storage_path: str = None):
        if storage_path is None:
            storage_path = os.path.join(os.getenv("DATA_PATH", "data"), "learning")
        self.storage_path = Path(storage_path)
        self.storage_path.mkdir(parents=True, exist_ok=True)
        
        self.policies: Dict[str, LearningPolicy] = {}
        self.experience_buffer: List[Experience] = []
        self.performance_history: Dict[str, List[float]] = defaultdict(list)
        
        # Load existing policies
        self.load_policies()
        
        # Subscribe to relevant events
        event_store.subscribe(EventType.AGENT_TASK_COMPLETED, self._on_task_completed)
        event_store.subscribe(EventType.USER_FEEDBACK_PROVIDED, self._on_feedback_received)
    
    def get_policy(self, agent_name: str) -> LearningPolicy:
        """Получить или создать политику для агента"""
        if agent_name not in self.policies:
            self.policies[agent_name] = LearningPolicy(agent_name)
        return self.policies[agent_name]
    
    async def suggest_action(
        self, 
        agent_name: str, 
        state: Dict[str, Any], 
        available_actions: List[str]
    ) -> str:
        """Предложить действие на основе обученной политики"""
        policy = self.get_policy(agent_name)
        
        # Add available actions to state for learning
        state['available_actions'] = available_actions
        
        # Get best action
        action = policy.get_best_action(available_actions)
        
        # Log the suggestion
        await event_logger.log_system_event(
            EventType.AGENT_TASK_STARTED,
            {
                "agent": agent_name,
                "suggested_action": action,
                "exploration_rate": policy.exploration_rate
            }
        )
        
        return action
    
    async def record_experience(
        self,
        agent_name: str,
        task_type: str,
        state: Dict[str, Any],
        action: str,
        result: TaskResult,
        next_state: Optional[Dict[str, Any]] = None
    ) -> None:
        """Записать опыт для обучения"""
        # Calculate reward based on result
        reward = self._calculate_reward(result)
        
        # Create experience
        experience = Experience(
            state=state,
            action=action,
            reward=reward,
            next_state=next_state or {},
            agent_name=agent_name,
            task_type=task_type
        )
        
        # Add to buffer
        self.experience_buffer.append(experience)
        
        # Update policy immediately (online learning)
        policy = self.get_policy(agent_name)
        policy.update(experience)
        
        # Track performance
        self.performance_history[agent_name].append(reward)
        
        # Periodically train and save
        if len(self.experience_buffer) % 100 == 0:
            await self.train_policies()
            self.save_policies()
    
    def _calculate_reward(self, result: TaskResult) -> float:
        """Рассчитать награду на основе результата"""
        reward = 0.0
        
        # Base reward for success/failure
        if result.status == "success":
            reward += 1.0
        elif result.status == "failure":
            reward -= 1.0
        elif result.status == "partial":
            reward += 0.3
        
        # Bonus for high confidence
        if result.confidence > 0.8:
            reward += 0.2
        elif result.confidence < 0.5:
            reward -= 0.1
        
        # Penalty for slow response
        if result.response_time > 10.0:
            reward -= 0.2
        elif result.response_time < 2.0:
            reward += 0.1
        
        # Penalty for high cost
        if result.token_cost > 0.01:
            reward -= 0.3
        elif result.token_cost < 0.001:
            reward += 0.1
        
        return reward
    
    async def train_policies(self) -> None:
        """Обучить политики на накопленном опыте"""
        if len(self.experience_buffer) < 10:
            return
        
        # Group experiences by agent
        agent_experiences = defaultdict(list)
        for exp in self.experience_buffer[-1000:]:  # Last 1000 experiences
            agent_experiences[exp.agent_name].append(exp)
        
        # Train each agent's policy
        for agent_name, experiences in agent_experiences.items():
            policy = self.get_policy(agent_name)
            
            # Batch update
            for exp in experiences:
                policy.update(exp)
            
            # Check if policy improved
            if self._has_policy_improved(agent_name):
                await self._suggest_prompt_improvement(agent_name, policy)
    
    def _has_policy_improved(self, agent_name: str) -> bool:
        """Проверить улучшилась ли политика агента"""
        history = self.performance_history[agent_name]
        if len(history) < 100:
            return False
        
        # Compare recent performance with older
        recent_avg = np.mean(history[-50:])
        older_avg = np.mean(history[-100:-50])
        
        return recent_avg > older_avg * 1.1  # 10% improvement
    
    async def _suggest_prompt_improvement(
        self, 
        agent_name: str, 
        policy: LearningPolicy
    ) -> None:
        """Предложить улучшение промпта на основе обучения"""
        # Analyze top performing actions
        top_actions = sorted(
            policy.action_values.items(),
            key=lambda x: x[1],
            reverse=True
        )[:5]
        
        # Generate improvement suggestion
        suggestion = f"""
Based on learning analysis for {agent_name}:

Top performing strategies:
{chr(10).join(f'- {action}: {value:.2f} reward' for action, value in top_actions)}

Suggested prompt improvements:
1. Emphasize strategies similar to top performing actions
2. De-emphasize or modify approaches with negative rewards
3. Add specific examples based on successful patterns

Current exploration rate: {policy.exploration_rate:.2%}
Total experiences: {sum(policy.action_counts.values())}
"""
        
        # Log suggestion
        await event_logger.log_system_event(
            EventType.PROMPT_UPDATED,
            {
                "agent": agent_name,
                "suggestion": suggestion,
                "top_actions": dict(top_actions)
            }
        )
    
    async def _on_task_completed(self, event) -> None:
        """Обработчик завершения задачи"""
        # Extract task result from event
        task_id = event.data.get('task_id')
        agent_name = event.data.get('agent_name')
        
        # Get performance metrics
        performance = quality_metrics.get_agent_performance(agent_name)
        
        # Update learning based on performance
        if performance.get('recent_trend') == 'improving':
            # Increase exploitation
            policy = self.get_policy(agent_name)
            policy.exploration_rate *= 0.9
    
    async def _on_feedback_received(self, event) -> None:
        """Обработчик получения обратной связи от пользователя"""
        feedback = event.data.get('feedback')
        task_id = event.data.get('task_id')
        
        # Find related experience
        for exp in reversed(self.experience_buffer):
            if hasattr(exp, 'task_id') and exp.task_id == task_id:
                # Adjust reward based on feedback
                if feedback == 'positive':
                    exp.reward += 0.5
                elif feedback == 'negative':
                    exp.reward -= 0.5
                
                # Re-train policy with updated reward
                policy = self.get_policy(exp.agent_name)
                policy.update(exp)
                break
    
    def get_learning_report(self, agent_name: str) -> Dict[str, Any]:
        """Получить отчет об обучении агента"""
        policy = self.get_policy(agent_name)
        history = self.performance_history[agent_name]
        
        return {
            "agent_name": agent_name,
            "total_experiences": sum(policy.action_counts.values()),
            "exploration_rate": policy.exploration_rate,
            "top_actions": sorted(
                policy.action_values.items(),
                key=lambda x: x[1],
                reverse=True
            )[:10],
            "action_distribution": dict(policy.action_counts),
            "average_recent_reward": np.mean(history[-100:]) if history else 0,
            "learning_trend": self._calculate_trend(history),
            "convergence_status": self._check_convergence(policy)
        }
    
    def _calculate_trend(self, history: List[float]) -> str:
        """Рассчитать тренд обучения"""
        if len(history) < 20:
            return "insufficient_data"
        
        # Simple linear regression
        x = np.arange(len(history[-100:]))
        y = np.array(history[-100:])
        
        if len(y) == 0:
            return "no_data"
        
        # Calculate slope
        slope = np.polyfit(x, y, 1)[0]
        
        if slope > 0.01:
            return "improving"
        elif slope < -0.01:
            return "declining"
        else:
            return "stable"
    
    def _check_convergence(self, policy: LearningPolicy) -> str:
        """Проверить сходимость политики"""
        if policy.exploration_rate > 0.05:
            return "exploring"
        
        # Check if action values stabilized
        recent_updates = []  # Would need to track this
        
        return "converged" if policy.exploration_rate < 0.02 else "converging"
    
    def save_policies(self) -> None:
        """Сохранить политики на диск"""
        policies_file = self.storage_path / "policies.json"
        
        data = {
            agent_name: {
                "action_values": policy.action_values,
                "action_counts": policy.action_counts,
                "exploration_rate": policy.exploration_rate,
                "learning_rate": policy.learning_rate,
                "discount_factor": policy.discount_factor
            }
            for agent_name, policy in self.policies.items()
        }
        
        with open(policies_file, "w") as f:
            json.dump(data, f, indent=2)
        
        # Save performance history
        history_file = self.storage_path / "performance_history.json"
        with open(history_file, "w") as f:
            json.dump(dict(self.performance_history), f, indent=2)
    
    def load_policies(self) -> None:
        """Загрузить политики с диска"""
        policies_file = self.storage_path / "policies.json"
        
        if policies_file.exists():
            with open(policies_file, "r") as f:
                data = json.load(f)
            
            for agent_name, policy_data in data.items():
                policy = LearningPolicy(
                    agent_name=agent_name,
                    action_values=policy_data.get("action_values", {}),
                    action_counts=policy_data.get("action_counts", {}),
                    exploration_rate=policy_data.get("exploration_rate", 0.1),
                    learning_rate=policy_data.get("learning_rate", 0.1),
                    discount_factor=policy_data.get("discount_factor", 0.95)
                )
                self.policies[agent_name] = policy
        
        # Load performance history
        history_file = self.storage_path / "performance_history.json"
        if history_file.exists():
            with open(history_file, "r") as f:
                self.performance_history = defaultdict(list, json.load(f))


# Global learning loop instance
learning_loop = LearningLoop()