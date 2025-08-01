"""Utility functions for loading YAML configuration files into dataclasses."""

from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Type, TypeVar

import yaml

T = TypeVar("T")


def _load_yaml(path: Path | str) -> Dict:
    path = Path(path)
    with path.open("r", encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


def load_dataclass(path: Path | str, cls: Type[T]) -> T:
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
    def from_yaml(cls, path: Path | str) -> "AgentsConfig":
        raw = _load_yaml(path).get("agents", {})
        agents = {}
        for name, cfg in raw.items():
            # Добавляем model если его нет, используя default_tier
            if "model" not in cfg:
                cfg["model"] = "gpt-3.5-turbo"  # дефолтная модель
            agents[name] = AgentDefinition(**cfg)
        return cls(agents=agents)


def load_config(config_dir: Path | str | None = None) -> Dict[str, Dict]:
    """Load core YAML configuration files into a single dictionary.

    Parameters
    ----------
    config_dir: Path | str | None
        Directory containing configuration YAML files. Defaults to the
        directory of this module.

    Returns
    -------
    Dict[str, Dict]
        Aggregated configuration with keys for each YAML file found.
    """
    if config_dir is None:
        config_dir = Path(__file__).resolve().parent
    else:
        config_dir = Path(config_dir)

    files = {
        "agents": "agents.yaml",
        "llm_tiers": "llm_tiers.yaml",
        "instances": "instances.yaml",
        "pricing": "pricing.yaml",
        "proactive_mode": "proactive_mode.yaml",
    }

    config: Dict[str, Dict] = {}
    for key, filename in files.items():
        path = config_dir / filename
        try:
            data = _load_yaml(path)
        except FileNotFoundError:
            data = {}
        if key == "agents":
            config[key] = data.get("agents", {})
        else:
            config[key] = data
    return config
