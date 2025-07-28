from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict

from autogen.agentchat import ConversableAgent

from config_loader import AgentsConfig, AgentDefinition
from .base import BaseAgent


@dataclass
class MetaAgent(BaseAgent):
    def __init__(self, model: str):
        super().__init__("meta", model)


@dataclass
class CoordinationAgent(BaseAgent):
    def __init__(self, model: str):
        super().__init__("coordination", model)


@dataclass
class PromptBuilderAgent(BaseAgent):
    def __init__(self, model: str):
        super().__init__("prompt_builder", model)


@dataclass
class ModelSelectorAgent(BaseAgent):
    def __init__(self, model: str):
        super().__init__("model_selector", model)


@dataclass
class AgentBuilderAgent(BaseAgent):
    def __init__(self, model: str):
        super().__init__("agent_builder", model)


@dataclass
class InstanceFactoryAgent(BaseAgent):
    def __init__(self, model: str):
        super().__init__("instance_factory", model)


@dataclass
class ResearcherAgent(BaseAgent):
    def __init__(self, model: str):
        super().__init__("researcher", model)


@dataclass
class FactCheckerAgent(BaseAgent):
    def __init__(self, model: str):
        super().__init__("fact_checker", model)


@dataclass
class MultiToolAgent(BaseAgent):
    def __init__(self, model: str):
        super().__init__("multitool", model)


@dataclass
class WfBuilderAgent(BaseAgent):
    def __init__(self, model: str):
        super().__init__("wf_builder", model)


@dataclass
class WebAppBuilderAgent(BaseAgent):
    def __init__(self, model: str):
        super().__init__("webapp_builder", model)


@dataclass
class CommunicatorAgent(BaseAgent):
    def __init__(self, model: str):
        super().__init__("communicator", model)


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
