from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict

# Импорт AutoGen с поддержкой разных версий
try:
    from autogen.agentchat import ConversableAgent
except ImportError:
    try:
        from autogen_agentchat import ConversableAgent
    except ImportError:
        # Fallback для случая отсутствия autogen
        class ConversableAgent:
            def __init__(self, name, llm_config, system_message="", *args, **kwargs):
                self.name = name
                self.llm_config = llm_config
                self.system_message = system_message
            
            def generate_reply(self, messages=None, sender=None, config=None):
                return f"[{self.name}] Mock response"

from config_loader import AgentsConfig, AgentDefinition
from .base import BaseAgent


@dataclass
class MetaAgent(BaseAgent):
    def __init__(self, model: str, tier: str = "premium"):
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
    def __init__(self, model: str, tier: str = "cheap"):
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
    def __init__(self, model: str, tier: str = "standard"):
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
    def __init__(self, model: str, tier: str = "cheap"):
        super().__init__("model_selector", model, tier)

    def pick(self, tier: str, attempt: int = 0) -> Dict[str, str]:
        from tools.llm_selector import pick_config

        _tier, model_cfg = pick_config(tier, attempt)
        return model_cfg


@dataclass
class AgentBuilderAgent(BaseAgent):
    def __init__(self, model: str, tier: str = "cheap"):
        super().__init__("agent_builder", model, tier)

    def build(self, spec: Dict[str, Any]) -> None:
        from autogen import agentchat

        agentchat.build_from_spec(spec)


@dataclass
class InstanceFactoryAgent(BaseAgent):
    def __init__(self, model: str, tier: str = "cheap"):
        super().__init__("instance_factory", model, tier)

    def deploy(self, directory: str, env: Dict[str, str]) -> None:
        from tools.instance_factory import deploy_instance

        deploy_instance(directory, env, "auto")


@dataclass
class ResearcherAgent(BaseAgent):
    def __init__(self, model: str, tier: str = "standard"):
        super().__init__("researcher", model, tier)

    def web_search(self, query: str, max_results: int = 5) -> Any:
        from tools.researcher import web_search

        return web_search(query, max_results)


@dataclass
class FactCheckerAgent(BaseAgent):
    def __init__(self, model: str, tier: str = "standard"):
        super().__init__("fact_checker", model, tier)

    def validate(self, facts: Any) -> bool:
        # In a full implementation this would cross-check sources.
        return bool(facts)


@dataclass
class MultiToolAgent(BaseAgent):
    def __init__(self, model: str, tier: str = "cheap"):
        super().__init__("multitool", model, tier)

    def call_api(self, api_name: str, params: Dict[str, Any]) -> Any:
        from tools.multitool import call

        return call(api_name, params)


@dataclass
class WfBuilderAgent(BaseAgent):
    def __init__(self, model: str, tier: str = "standard"):
        super().__init__("wf_builder", model, tier)

    def create_workflow(self, spec: str, url: str, api_key: str) -> Any:
        from tools.wf_builder import create_workflow

        return create_workflow(spec, url, api_key)


@dataclass
class WebAppBuilderAgent(BaseAgent):
    def __init__(self, model: str, tier: str = "standard"):
        super().__init__("webapp_builder", model, tier)

    def create_app(self, spec: Dict[str, Any]) -> str:
        from tools.webapp_builder import create_app

        return create_app(spec)

    def status(self, job_id: str) -> Any:
        from tools.webapp_builder import check_status

        return check_status(job_id)


@dataclass
class CommunicatorAgent(BaseAgent):
    def __init__(self, model: str, tier: str = "cheap"):
        super().__init__("communicator", model, tier)

    def forward(self, text: str) -> Dict[str, str]:
        """Prepare a message to be routed into the group chat."""
        return {"role": "user", "content": text}


def create_agents(config: AgentsConfig) -> Dict[str, ConversableAgent]:
    """Instantiate agents from configuration."""
    agents: Dict[str, ConversableAgent] = {}
    mapping = {
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
    }
    for name, definition in config.agents.items():
        cls = mapping.get(name)
        if cls is None:
            continue
        
        # Используем tier из конфигурации агента
        tier = getattr(definition, 'default_tier', 'cheap')
        agents[name] = cls(definition.model, tier=tier)
    return agents
