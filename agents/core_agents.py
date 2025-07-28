from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict

try:
    from autogen.agentchat import ConversableAgent
except Exception:  # pragma: no cover - optional dependency
    from agents.base import ConversableAgent  # type: ignore

from config_loader import AgentsConfig, AgentDefinition
from .base import BaseAgent


@dataclass
class MetaAgent(BaseAgent):
    def __init__(self, model: str):
        super().__init__("meta", model)

    def create_plan(self, goal: str) -> list[str]:
        """Break down a user goal into simple tasks."""
        segments = [seg.strip() for seg in goal.split(".") if seg.strip()]
        return segments if segments else [goal]

    def escalate(self, message: str) -> Dict[str, str]:
        """Escalate a question to the user via Communicator."""
        return {"event": "OUTGOING_TO_TELEGRAM", "args": [message]}


@dataclass
class CoordinationAgent(BaseAgent):
    def __init__(self, model: str):
        super().__init__("coordination", model)
        self.tasks: Dict[str, str] = {}

    def add_task(self, task: str, status: str = "pending") -> None:
        """Store a task with its status."""
        self.tasks[task] = status

    def list_tasks(self) -> Dict[str, str]:
        """Return current task queue."""
        return dict(self.tasks)


@dataclass
class PromptBuilderAgent(BaseAgent):
    def __init__(self, model: str):
        super().__init__("prompt_builder", model)

    def create_prompt(self, agent_name: str, content: str) -> None:
        from tools.prompt_builder import create_agent_prompt

        create_agent_prompt(agent_name, content)

    def audit_prompt(self, agent_name: str) -> str:
        from tools.prompt_builder import audit_prompt

        return audit_prompt(agent_name)


@dataclass
class ModelSelectorAgent(BaseAgent):
    def __init__(self, model: str):
        super().__init__("model_selector", model)

    def pick(self, tier: str, attempt: int = 0) -> Dict[str, str]:
        from tools.llm_selector import pick_config

        _tier, model_cfg = pick_config(tier, attempt)
        return model_cfg


@dataclass
class AgentBuilderAgent(BaseAgent):
    def __init__(self, model: str):
        super().__init__("agent_builder", model)

    def build(self, spec: Dict[str, Any]) -> None:
        from autogen import agentchat

        agentchat.build_from_spec(spec)


@dataclass
class InstanceFactoryAgent(BaseAgent):
    def __init__(self, model: str):
        super().__init__("instance_factory", model)

    def deploy(self, directory: str, env: Dict[str, str]) -> None:
        from tools.instance_factory import deploy_instance

        deploy_instance(directory, env, "auto")


@dataclass
class ResearcherAgent(BaseAgent):
    def __init__(self, model: str):
        super().__init__("researcher", model)

    def web_search(self, query: str, max_results: int = 5) -> Any:
        from tools.researcher import web_search

        return web_search(query, max_results)


@dataclass
class FactCheckerAgent(BaseAgent):
    def __init__(self, model: str):
        super().__init__("fact_checker", model)

    def validate(self, facts: Any) -> bool:
        # In a full implementation this would cross-check sources.
        return bool(facts)


@dataclass
class MultiToolAgent(BaseAgent):
    def __init__(self, model: str):
        super().__init__("multitool", model)

    def call_api(self, api_name: str, params: Dict[str, Any]) -> Any:
        from tools.multitool import call_api

        return call_api(api_name, params)


@dataclass
class WfBuilderAgent(BaseAgent):
    def __init__(self, model: str):
        super().__init__("wf_builder", model)

    def create_workflow(self, spec: str, url: str, api_key: str) -> Any:
        from tools.wf_builder import create_workflow

        return create_workflow(spec, url, api_key)


@dataclass
class WebAppBuilderAgent(BaseAgent):
    def __init__(self, model: str):
        super().__init__("webapp_builder", model)

    def create_app(self, spec: Dict[str, Any]) -> str:
        from tools.webapp_builder import create_app

        return create_app(spec)

    def status(self, job_id: str) -> Any:
        from tools.webapp_builder import check_status

        return check_status(job_id)


@dataclass
class CommunicatorAgent(BaseAgent):
    def __init__(self, model: str):
        super().__init__("communicator", model)

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
        "wf_builder": WfBuilderAgent,
        "webapp_builder": WebAppBuilderAgent,
        "communicator": CommunicatorAgent,
    }
    for name, definition in config.agents.items():
        cls = mapping.get(name)
        if cls is None:
            continue
        agents[name] = cls(definition.model)
    return agents
