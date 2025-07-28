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
    memory: str | None = None


@dataclass
class AgentsConfig:
    """Container for all agent definitions."""

    agents: Dict[str, AgentDefinition] = field(default_factory=dict)

    @classmethod
    def from_yaml(cls, path: Path) -> "AgentsConfig":
        raw = _load_yaml(path).get("agents", {})
        agents = {
            name: AgentDefinition(**cfg)
            for name, cfg in raw.items()
        }
        return cls(agents=agents)

