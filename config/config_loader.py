"""Utility functions for loading YAML configuration files into dataclasses."""

from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Type, TypeVar

import yaml

T = TypeVar("T")


def _load_yaml(path: Path) -> Dict:
    with path.open("r", encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


def load_dataclass(path: Path, cls: Type[T]) -> T:
    """Load a YAML file and populate the given dataclass type."""

    data = _load_yaml(path)
    # Для LlmTiers нужно извлечь данные из секции 'tiers'
    if cls == LlmTiers and 'tiers' in data:
        tiers_data = data['tiers']
        return cls(**tiers_data)
    return cls(**data)


@dataclass
class LlmTiers:
    """Configuration for language model tiers."""

    cheap: List[str] = field(default_factory=list)
    standard: List[str] = field(default_factory=list)
    premium: List[str] = field(default_factory=list)


@dataclass
class AgentDefinition:
    """Single agent configuration entry."""

    role: str
    model: str
    description: str = ""
    default_tier: str = "standard"
    memory: str | None = None


@dataclass
class AgentsConfig:
    """Container for all agent definitions."""

    agents: Dict[str, AgentDefinition] = field(default_factory=dict)

    @classmethod
    def from_yaml(cls, path: Path) -> "AgentsConfig":
        raw = _load_yaml(path).get("agents", {})
        agents = {}
        for name, cfg in raw.items():
            # Добавляем model если его нет, используя default_tier
            if "model" not in cfg:
                cfg["model"] = "gpt-3.5-turbo"  # дефолтная модель
            agents[name] = AgentDefinition(**cfg)
        return cls(agents=agents)

