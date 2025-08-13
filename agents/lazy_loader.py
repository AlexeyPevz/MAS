"""
Lazy Agent Loader
================

Загружает агентов только при первом обращении к ним.
Значительно ускоряет время запуска системы.
"""

import logging
from typing import Dict, Any, Optional, Type
from functools import lru_cache

logger = logging.getLogger(__name__)


class LazyAgentLoader:
    """Ленивая загрузка агентов для оптимизации времени запуска."""
    
    def __init__(self):
        self._agents: Dict[str, Any] = {}
        self._agent_classes: Dict[str, Type] = {}
        self._configs: Dict[str, Dict] = {}
        self._initialized = False
        
    def register_agent_class(self, name: str, agent_class: Type, config: Dict[str, Any]):
        """Регистрирует класс агента без создания экземпляра."""
        self._agent_classes[name] = agent_class
        self._configs[name] = config
        logger.debug(f"Registered agent class: {name}")
        
    def get_agent(self, name: str) -> Optional[Any]:
        """Получает агента, создавая его при первом обращении."""
        if name not in self._agent_classes:
            logger.warning(f"Agent {name} not registered")
            return None
            
        if name not in self._agents:
            logger.info(f"🔄 Lazy loading agent: {name}")
            try:
                agent_class = self._agent_classes[name]
                config = self._configs[name]
                
                # Создаем агента
                if hasattr(agent_class, 'from_config'):
                    agent = agent_class.from_config(config)
                else:
                    agent = agent_class(**config)
                    
                self._agents[name] = agent
                logger.info(f"✅ Agent {name} loaded successfully")
                
            except Exception as e:
                logger.error(f"❌ Failed to load agent {name}: {e}")
                return None
                
        return self._agents[name]
    
    def get_loaded_agents(self) -> Dict[str, Any]:
        """Возвращает только загруженные агенты."""
        return self._agents.copy()
    
    def get_all_agent_names(self) -> list[str]:
        """Возвращает имена всех зарегистрированных агентов."""
        return list(self._agent_classes.keys())
    
    def is_agent_loaded(self, name: str) -> bool:
        """Проверяет, загружен ли агент."""
        return name in self._agents
    
    def preload_essential_agents(self, essential_names: list[str]):
        """Предзагружает критически важные агенты."""
        logger.info(f"🚀 Preloading essential agents: {essential_names}")
        for name in essential_names:
            self.get_agent(name)
    
    def clear_cache(self):
        """Очищает кэш загруженных агентов."""
        self._agents.clear()
        logger.info("Cache cleared")
    
    @property
    def stats(self) -> Dict[str, int]:
        """Статистика загрузки."""
        return {
            "registered": len(self._agent_classes),
            "loaded": len(self._agents),
            "pending": len(self._agent_classes) - len(self._agents)
        }


# Глобальный экземпляр
agent_loader = LazyAgentLoader()


def register_core_agents():
    """Регистрирует основные агенты без их создания."""
    from agents.core_agents import (
        MetaAgent, BudgetManager, Coordinator, 
        ModelSelector, Communicator
    )
    
    # Регистрируем классы без создания экземпляров
    agent_loader.register_agent_class(
        "meta",
        MetaAgent,
        {"model": "gpt-4o-mini", "tier": "premium"}
    )
    
    agent_loader.register_agent_class(
        "budget_manager",
        BudgetManager,
        {"model": "gpt-4o-mini", "tier": "standard"}
    )
    
    agent_loader.register_agent_class(
        "coordinator",
        Coordinator,
        {"model": "gpt-4o-mini", "tier": "standard"}
    )
    
    agent_loader.register_agent_class(
        "model_selector",
        ModelSelector,
        {"model": "gpt-4o-mini", "tier": "standard"}
    )
    
    agent_loader.register_agent_class(
        "communicator", 
        Communicator,
        {"model": "gpt-4o-mini", "tier": "premium"}
    )
    
    logger.info("✅ Core agents registered")


def register_specialized_agents():
    """Регистрирует специализированные агенты."""
    from agents.specialized_agents import (
        AgentBuilder, InstanceFactory, PromptBuilder,
        WorkflowBuilder, FactChecker, Researcher,
        Multitool, WebappBuilder
    )
    
    specialized = {
        "agent_builder": (AgentBuilder, {"model": "gpt-4o", "tier": "premium"}),
        "instance_factory": (InstanceFactory, {"model": "gpt-4o-mini", "tier": "standard"}),
        "prompt_builder": (PromptBuilder, {"model": "gpt-4o-mini", "tier": "standard"}),
        "workflow_builder": (WorkflowBuilder, {"model": "gpt-4o-mini", "tier": "standard"}),
        "fact_checker": (FactChecker, {"model": "gpt-4o-mini", "tier": "standard"}),
        "researcher": (Researcher, {"model": "gpt-4o-mini", "tier": "standard"}),
        "multitool": (Multitool, {"model": "gpt-4o-mini", "tier": "premium"}),
        "webapp_builder": (WebappBuilder, {"model": "gpt-4o", "tier": "premium"}),
    }
    
    for name, (cls, config) in specialized.items():
        agent_loader.register_agent_class(name, cls, config)
    
    logger.info("✅ Specialized agents registered")