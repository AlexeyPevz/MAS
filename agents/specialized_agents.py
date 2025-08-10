"""
Specialized agents for Root-MAS
Специализированные агенты для конкретных задач
"""
from dataclasses import dataclass
from typing import Dict, Any, List, Optional

from .base import BaseAgent


@dataclass
class ResearcherAgent(BaseAgent):
    """Агент-исследователь для поиска и анализа информации"""
    
    def __init__(self, model: str = "gpt-4o-mini", tier: str = "standard"):
        super().__init__("researcher", model, tier)
    
    async def research_topic(self, topic: str, max_results: int = 5) -> List[Dict[str, Any]]:
        """Исследовать тему"""
        # Ensure we have knowledge on the topic
        await self.ensure_knowledge(topic)
        
        # Search in knowledge graph
        knowledge_results = await self.query_knowledge_graph(topic)
        
        # Use tools if available
        try:
            from tools.researcher import search_and_store
            web_results = search_and_store(topic, max_results)
            
            return {
                "knowledge": knowledge_results,
                "web_search": web_results
            }
        except Exception:
            return knowledge_results


@dataclass
class FactCheckerAgent(BaseAgent):
    """Агент для проверки фактов"""
    
    def __init__(self, model: str = "gpt-4o", tier: str = "premium"):
        super().__init__("fact_checker", model, tier)
    
    async def verify_information(self, claim: str, sources: List[str]) -> Dict[str, Any]:
        """Проверить достоверность информации"""
        try:
            from tools.fact_checker import validate_sources, check_claim
            
            # Validate sources
            source_validation = validate_sources(sources)
            
            # Check claim
            claim_result = check_claim(claim, sources)
            
            return {
                "claim": claim,
                "verdict": claim_result["rating"],
                "confidence": claim_result["confidence"],
                "source_validation": source_validation
            }
        except Exception as e:
            return {
                "claim": claim,
                "verdict": "UNCERTAIN",
                "error": str(e)
            }


@dataclass  
class WorkflowBuilderAgent(BaseAgent):
    """Агент для создания n8n workflows"""
    
    def __init__(self, model: str = "gpt-4o-mini", tier: str = "standard"):
        super().__init__("workflow_builder", model, tier)
    
    async def create_workflow(self, description: str) -> Dict[str, Any]:
        """Создать workflow по описанию"""
        try:
            from tools.n8n_client import N8NClient
            
            client = N8NClient()
            
            # Generate workflow definition using LLM
            workflow_def = await self._generate_workflow_definition(description)
            
            # Create in n8n
            result = await client.create_workflow(workflow_def)
            
            return result
        except Exception as e:
            return {"error": str(e)}


@dataclass
class WebAppBuilderAgent(BaseAgent):
    """Агент для создания веб-приложений через GPT-Pilot"""
    
    def __init__(self, model: str = "gpt-4o", tier: str = "premium"):
        super().__init__("webapp_builder", model, tier)
    
    async def create_app(self, spec: str) -> Dict[str, Any]:
        """Создать веб-приложение по спецификации"""
        try:
            from tools.gpt_pilot import GPTPilotInterface
            
            pilot = GPTPilotInterface()
            
            # Start app generation
            result = await pilot.create_app(spec)
            
            return result
        except Exception as e:
            return {"error": str(e)}


@dataclass
class BudgetManagerAgent(BaseAgent):
    """Агент для управления бюджетом"""
    
    def __init__(self, model: str = "gpt-3.5-turbo", tier: str = "cheap"):
        super().__init__("budget_manager", model, tier)
    
    def get_budget_status(self) -> Dict[str, Any]:
        """Получить статус бюджета"""
        try:
            from tools.budget_manager import BudgetManager
            
            manager = BudgetManager()
            return manager.get_status()
        except Exception:
            return {"error": "Budget manager not available"}


# Export all specialized agents
__all__ = [
    'ResearcherAgent',
    'FactCheckerAgent', 
    'WorkflowBuilderAgent',
    'WebAppBuilderAgent',
    'BudgetManagerAgent'
]