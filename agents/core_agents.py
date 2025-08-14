from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict

# Импорт AutoGen v0.4+ с поддержкой новых API
try:
    from autogen_agentchat.agents import AssistantAgent
    from autogen_ext.models.openai import OpenAIChatCompletionClient
    from autogen_core import CancellationToken
except ImportError:
    # Полностью изолированный fallback без внешних импортов
    class AssistantAgent:  # type: ignore
        def __init__(self, name, model_client=None, system_message="", *args, **kwargs):
            self.name = name
            self.model_client = model_client
            self.system_message = system_message
        async def on_messages(self, messages, cancellation_token=None):
            class _Resp:
                def __init__(self, content: str) -> None:
                    class _Msg:
                        def __init__(self, c: str) -> None:
                            self.content = c
                    self.chat_message = _Msg(content)
            return _Resp(content=f"[{self.name}] Mock response")

from config.config_loader import AgentsConfig, AgentDefinition
from .base import BaseAgent


@dataclass
class MetaAgent(BaseAgent):
    def __init__(self, model: str = "gpt-4o-mini", tier: str = "premium"):
        super().__init__("meta", model, tier)

    def create_plan(self, goal: str) -> list[str]:
        """Break down a user goal into simple tasks."""
        segments = [seg.strip() for seg in goal.split(".") if seg.strip()]
        return segments if segments else [goal]

    def escalate(self, message: str) -> Dict[str, str]:
        """Escalate a question to the user via Communicator."""
        return {"event": "OUTGOING_TO_TELEGRAM", "args": [message]}


@dataclass
class CoordinationAgent(BaseAgent):
    def __init__(self, model: str = "gpt-4o-mini", tier: str = "cheap"):
        super().__init__("coordination", model, tier)
        self.tasks: Dict[str, str] = {}

    def add_task(self, task: str, status: str = "pending") -> None:
        """Store a task with its status."""
        self.tasks[task] = status

    def list_tasks(self) -> Dict[str, str]:
        """Return current task queue."""
        return dict(self.tasks)


@dataclass
class PromptBuilderAgent(BaseAgent):
    def __init__(self, model: str = "gpt-4o-mini", tier: str = "standard"):
        super().__init__("prompt_builder", model, tier)

    def create_prompt(self, agent_name: str, content: str) -> None:
        from tools.prompt_builder import create_agent_prompt

        create_agent_prompt(agent_name, content)

    # Task-specific prompts -------------------------------------------------

    def create_task_prompt(self, agent_name: str, task: str, content: str) -> None:
        from tools.prompt_builder import create_task_prompt

        create_task_prompt(agent_name, task, content)

    def update_task_prompt(self, agent_name: str, task: str, content: str) -> None:
        from tools.prompt_builder import update_task_prompt

        update_task_prompt(agent_name, task, content)

    def audit_prompt(self, agent_name: str) -> str:
        from tools.prompt_builder import audit_prompt

        return audit_prompt(agent_name)


@dataclass
class ModelSelectorAgent(BaseAgent):
    def __init__(self, model: str = "gpt-4o-mini", tier: str = "cheap"):
        super().__init__("model_selector", model, tier)

    def pick(self, tier: str, attempt: int = 0) -> Dict[str, str]:
        from tools.llm_selector import pick_config

        _tier, model_cfg = pick_config(tier, attempt)
        return model_cfg


@dataclass
class AgentBuilderAgent(BaseAgent):
    def __init__(self, model: str = "gpt-4o-mini", tier: str = "cheap"):
        super().__init__("agent_builder", model, tier)

    def build(self, spec: Dict[str, Any]) -> None:
        try:
            from autogen import agentchat  # type: ignore
        except Exception as e:
            raise RuntimeError("Legacy autogen is not available; AgentBuilder requires migration or proper dependency") from e
        agentchat.build_from_spec(spec)


@dataclass
class InstanceFactoryAgent(BaseAgent):
    def __init__(self, model: str = "gpt-4o-mini", tier: str = "cheap"):
        super().__init__("instance_factory", model, tier)

    def deploy(self, directory: str, env: Dict[str, str]) -> None:
        from tools.instance_factory import deploy_instance

        deploy_instance(directory, env, "auto")


@dataclass
class ResearcherAgent(BaseAgent):
    def __init__(self, model: str = "gpt-4o-mini", tier: str = "standard"):
        super().__init__("researcher", model, tier)

    def web_search(self, query: str, max_results: int = 5) -> Any:
        from tools.researcher import web_search

        return web_search(query, max_results)


@dataclass
class FactCheckerAgent(BaseAgent):
    def __init__(self, model: str = "gpt-4o-mini", tier: str = "standard"):
        super().__init__("fact_checker", model, tier)

    def validate(self, facts: Any) -> bool:
        # In a full implementation this would cross-check sources.
        return bool(facts)


@dataclass
class MultiToolAgent(BaseAgent):
    def __init__(self, model: str = "gpt-4o-mini", tier: str = "cheap"):
        super().__init__("multitool", model, tier)

    def call_api(self, api_name: str, params: Dict[str, Any]) -> Any:
        from tools.multitool import call

        return call(api_name, params)


@dataclass
class WfBuilderAgent(BaseAgent):
    def __init__(self, model: str = "gpt-4o-mini", tier: str = "standard"):
        super().__init__("wf_builder", model, tier)

    def create_workflow(self, spec: str, url: str, api_key: str) -> Any:
        from tools.wf_builder import create_workflow

        return create_workflow(spec, url, api_key)


@dataclass
class WebAppBuilderAgent(BaseAgent):
    def __init__(self, model: str = "gpt-4o-mini", tier: str = "standard"):
        super().__init__("webapp_builder", model, tier)

    def create_app(self, spec: Dict[str, Any]) -> str:
        from tools.webapp_builder import create_app

        return create_app(spec)

    def status(self, job_id: str) -> Any:
        from tools.webapp_builder import check_status

        return check_status(job_id)


@dataclass
class CommunicatorAgent(BaseAgent):
    def __init__(self, model: str = "gpt-4o-mini", tier: str = "cheap"):
        super().__init__("communicator", model, tier)

    def forward(self, text: str) -> Dict[str, str]:
        """Prepare a message to be routed into the group chat."""
        return {"role": "user", "content": text}


@dataclass  
class BudgetManagerAgent(BaseAgent):
    def __init__(self, model: str = "gpt-4o-mini", tier: str = "cheap"):
        super().__init__("budget_manager", model, tier)
        self._costs: Dict[str, float] = {}
    
    def track_cost(self, agent_name: str, cost: float) -> None:
        """Track cost for an agent."""
        self._costs[agent_name] = self._costs.get(agent_name, 0) + cost
    
    def get_total_cost(self) -> float:
        """Get total cost across all agents."""
        return sum(self._costs.values())
    
    def get_agent_costs(self) -> Dict[str, float]:
        """Get cost breakdown by agent."""
        return dict(self._costs)


# Определение AGENT_CLASSES для использования в других модулях
AGENT_CLASSES = {
    "meta": MetaAgent,
    "coordination": CoordinationAgent,
    "prompt_builder": PromptBuilderAgent,
    "model_selector": ModelSelectorAgent,
    "agent_builder": AgentBuilderAgent,
    "instance_factory": InstanceFactoryAgent,
    "researcher": ResearcherAgent,
    "fact_checker": FactCheckerAgent,
    "multitool": MultiToolAgent,
    "multi_tool": MultiToolAgent,  # Добавлено: multi_tool
    "workflow_builder": WfBuilderAgent,  # Исправлено: workflow_builder вместо wf_builder
    "webapp_builder": WebAppBuilderAgent,
    "communicator": CommunicatorAgent,
    "budget_manager": BudgetManagerAgent,
}


def create_agents(config: AgentsConfig) -> Dict[str, AssistantAgent]:
    """Instantiate agents from configuration."""
    agents: Dict[str, AssistantAgent] = {}
    mapping = AGENT_CLASSES  # Используем AGENT_CLASSES вместо локального mapping
    for name, definition in config.agents.items():
        cls = mapping.get(name)
        if cls is None:
            continue
        
        # Используем tier из конфигурации агента
        tier = getattr(definition, 'default_tier', 'cheap')
        agents[name] = cls(definition.model, tier=tier)
    return agents
