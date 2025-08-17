"""
Federated Learning System for Root-MAS
Система федеративного обучения для обмена знаниями между экземплярами
"""
from typing import Dict, Any, List, Optional, Set
from datetime import datetime, timezone, timedelta
from dataclasses import dataclass, field
import json
import os
import hashlib
import asyncio
import aiohttp
from pathlib import Path
import numpy as np
from collections import defaultdict
import jwt

from .learning_loop import LearningPolicy
from .knowledge_graph import Concept, knowledge_graph
from .quality_metrics import AgentMetrics


@dataclass
class FederatedNode:
    """Узел в федеративной сети"""
    node_id: str
    name: str
    endpoint: str
    public_key: str
    specialization: List[str] = field(default_factory=list)  # Области экспертизы
    trust_score: float = 1.0
    last_sync: Optional[datetime] = None
    is_active: bool = True


@dataclass
class KnowledgePacket:
    """Пакет знаний для обмена"""
    packet_id: str
    source_node: str
    timestamp: datetime
    knowledge_type: str  # policy, concept, metric, prompt
    data: Dict[str, Any]
    signature: str  # Цифровая подпись для верификации
    privacy_level: int = 1  # 1-public, 2-anonymized, 3-encrypted


@dataclass
class FederationRequest:
    """Запрос на обмен знаниями"""
    request_id: str
    requester_node: str
    knowledge_domain: str
    specific_agents: Optional[List[str]] = None
    min_confidence: float = 0.7
    max_age_days: int = 30


class FederatedLearningHub:
    """Центральный хаб федеративного обучения"""
    
    def __init__(self, node_id: str, storage_path: str = None):
        if storage_path is None:
            storage_path = os.path.join(os.getenv("DATA_PATH", "data"), "federation")
        self.node_id = node_id
        self.storage_path = Path(storage_path)
        self.storage_path.mkdir(parents=True, exist_ok=True)
        
        self.nodes: Dict[str, FederatedNode] = {}
        self.knowledge_cache: Dict[str, KnowledgePacket] = {}
        self.pending_requests: Dict[str, FederationRequest] = {}
        
        # Crypto keys for secure communication
        self.private_key = self._load_or_generate_key()
        self.public_key = self._get_public_key()
        
        # Load configuration
        self.load_federation_config()
    
    def _load_or_generate_key(self) -> str:
        """Загрузить или сгенерировать приватный ключ"""
        key_file = self.storage_path / "private_key.pem"
        if key_file.exists():
            return key_file.read_text()
        
        # Generate new key pair (simplified for demo)
        import secrets
        key = secrets.token_urlsafe(32)
        key_file.write_text(key)
        key_file.chmod(0o600)
        return key
    
    def _get_public_key(self) -> str:
        """Получить публичный ключ"""
        # In real implementation, derive from private key
        return hashlib.sha256(self.private_key.encode()).hexdigest()
    
    async def join_federation(self, hub_endpoint: str, specialization: List[str]) -> bool:
        """Присоединиться к федерации"""
        registration_data = {
            "node_id": self.node_id,
            "public_key": self.public_key,
            "specialization": specialization,
            "endpoint": f"http://localhost:8000/federation",  # Our endpoint
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{hub_endpoint}/register",
                    json=registration_data
                ) as response:
                    if response.status == 200:
                        # Get list of other nodes
                        nodes_data = await response.json()
                        for node_data in nodes_data.get("nodes", []):
                            node = FederatedNode(**node_data)
                            self.nodes[node.node_id] = node
                        return True
        except Exception as e:
            print(f"Failed to join federation: {e}")
        
        return False
    
    def prepare_knowledge_for_sharing(
        self, 
        knowledge_type: str,
        privacy_level: int = 2
    ) -> List[KnowledgePacket]:
        """Подготовить знания для обмена"""
        packets = []
        
        if knowledge_type == "policy":
            # Share learning policies
            from .learning_loop import learning_loop
            
            for agent_name, policy in learning_loop.policies.items():
                # Anonymize if needed
                if privacy_level >= 2:
                    data = self._anonymize_policy(policy)
                else:
                    data = {
                        "agent_type": agent_name.split("_")[0],  # Generic type
                        "action_values": policy.action_values,
                        "exploration_rate": policy.exploration_rate,
                        "total_experiences": sum(policy.action_counts.values())
                    }
                
                packet = KnowledgePacket(
                    packet_id=f"{self.node_id}_{knowledge_type}_{agent_name}_{int(datetime.now(timezone.utc).timestamp())}",
                    source_node=self.node_id,
                    timestamp=datetime.now(timezone.utc),
                    knowledge_type=knowledge_type,
                    data=data,
                    signature=self._sign_data(data),
                    privacy_level=privacy_level
                )
                packets.append(packet)
        
        elif knowledge_type == "concept":
            # Share knowledge graph concepts
            stats = knowledge_graph.get_statistics()
            
            # Share only aggregate statistics
            data = {
                "total_concepts": stats["total_concepts"],
                "concept_types": stats["concept_types"],
                "density": stats["density"],
                "top_concepts": self._get_top_concepts(10)
            }
            
            packet = KnowledgePacket(
                packet_id=f"{self.node_id}_{knowledge_type}_graph_{int(datetime.now(timezone.utc).timestamp())}",
                source_node=self.node_id,
                timestamp=datetime.now(timezone.utc),
                knowledge_type=knowledge_type,
                data=data,
                signature=self._sign_data(data),
                privacy_level=privacy_level
            )
            packets.append(packet)
        
        elif knowledge_type == "metric":
            # Share performance metrics
            from .quality_metrics import quality_metrics
            
            # Aggregate metrics across all agents
            aggregated = {
                "avg_success_rate": 0.0,
                "total_tasks": 0,
                "model_distribution": defaultdict(int)
            }
            
            agent_count = 0
            for agent_name in quality_metrics.agent_metrics:
                metrics = quality_metrics.get_agent_performance(agent_name)
                if metrics and "error" not in metrics:
                    aggregated["avg_success_rate"] += metrics.get("success_rate", 0)
                    aggregated["total_tasks"] += metrics.get("total_tasks", 0)
                    agent_count += 1
                    
                    # Model preferences
                    for tier, models in metrics.get("model_preferences", {}).items():
                        for model, stats in models.items():
                            aggregated["model_distribution"][f"{tier}:{model}"] += stats.get("usage_count", 0)
            
            if agent_count > 0:
                aggregated["avg_success_rate"] /= agent_count
            
            packet = KnowledgePacket(
                packet_id=f"{self.node_id}_{knowledge_type}_aggregate_{int(datetime.now(timezone.utc).timestamp())}",
                source_node=self.node_id,
                timestamp=datetime.now(timezone.utc),
                knowledge_type=knowledge_type,
                data=aggregated,
                signature=self._sign_data(aggregated),
                privacy_level=privacy_level
            )
            packets.append(packet)
        
        return packets
    
    def _anonymize_policy(self, policy: LearningPolicy) -> Dict[str, Any]:
        """Анонимизировать политику обучения"""
        # Group actions by category
        action_categories = defaultdict(list)
        
        for action, value in policy.action_values.items():
            # Extract action type (simplified)
            action_type = action.split("_")[0] if "_" in action else "general"
            action_categories[action_type].append(value)
        
        # Return aggregated statistics
        return {
            "action_categories": {
                cat: {
                    "count": len(values),
                    "avg_value": np.mean(values) if values else 0,
                    "std_value": np.std(values) if len(values) > 1 else 0
                }
                for cat, values in action_categories.items()
            },
            "exploration_rate": policy.exploration_rate,
            "maturity": "converged" if policy.exploration_rate < 0.02 else "learning"
        }
    
    def _get_top_concepts(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Получить топ концепций по связям"""
        concept_scores = []
        
        for concept_id, concept in knowledge_graph.concepts.items():
            relations = knowledge_graph.get_relations(concept_id)
            score = len(relations)
            
            concept_scores.append({
                "type": concept.type,
                "relation_count": score,
                "properties_count": len(concept.properties)
            })
        
        # Sort by score and return top
        concept_scores.sort(key=lambda x: x["relation_count"], reverse=True)
        return concept_scores[:limit]
    
    def _sign_data(self, data: Dict[str, Any]) -> str:
        """Подписать данные"""
        # Simplified signature
        data_str = json.dumps(data, sort_keys=True)
        return hashlib.sha256(f"{self.private_key}:{data_str}".encode()).hexdigest()
    
    def _verify_signature(self, packet: KnowledgePacket, public_key: str) -> bool:
        """Проверить подпись пакета"""
        data_str = json.dumps(packet.data, sort_keys=True)
        expected_signature = hashlib.sha256(f"{public_key}:{data_str}".encode()).hexdigest()
        return packet.signature == expected_signature
    
    async def share_knowledge(self, target_node_id: Optional[str] = None) -> int:
        """Поделиться знаниями с федерацией"""
        packets = []
        
        # Prepare different types of knowledge
        for knowledge_type in ["policy", "concept", "metric"]:
            packets.extend(self.prepare_knowledge_for_sharing(knowledge_type))
        
        shared_count = 0
        
        # Send to specific node or broadcast
        target_nodes = [self.nodes[target_node_id]] if target_node_id else self.nodes.values()
        
        for node in target_nodes:
            if not node.is_active:
                continue
            
            try:
                async with aiohttp.ClientSession() as session:
                    for packet in packets:
                        async with session.post(
                            f"{node.endpoint}/receive_knowledge",
                            json=packet.__dict__
                        ) as response:
                            if response.status == 200:
                                shared_count += 1
            except Exception as e:
                print(f"Failed to share with {node.node_id}: {e}")
                node.is_active = False
        
        return shared_count
    
    async def request_knowledge(
        self, 
        knowledge_domain: str,
        specific_agents: Optional[List[str]] = None
    ) -> List[KnowledgePacket]:
        """Запросить знания из федерации"""
        request = FederationRequest(
            request_id=f"{self.node_id}_req_{int(datetime.now(timezone.utc).timestamp())}",
            requester_node=self.node_id,
            knowledge_domain=knowledge_domain,
            specific_agents=specific_agents
        )
        
        received_packets = []
        
        for node in self.nodes.values():
            if not node.is_active:
                continue
            
            # Check if node has relevant specialization
            if knowledge_domain not in node.specialization:
                continue
            
            try:
                async with aiohttp.ClientSession() as session:
                    async with session.post(
                        f"{node.endpoint}/request_knowledge",
                        json=request.__dict__
                    ) as response:
                        if response.status == 200:
                            packets_data = await response.json()
                            for packet_data in packets_data:
                                packet = KnowledgePacket(**packet_data)
                                
                                # Verify signature
                                if self._verify_signature(packet, node.public_key):
                                    received_packets.append(packet)
                                    node.trust_score = min(node.trust_score * 1.01, 2.0)
                                else:
                                    node.trust_score *= 0.9
            except Exception as e:
                print(f"Failed to request from {node.node_id}: {e}")
                node.is_active = False
        
        return received_packets
    
    async def integrate_federated_knowledge(self, packets: List[KnowledgePacket]) -> Dict[str, int]:
        """Интегрировать полученные знания"""
        integration_stats = {
            "policies_updated": 0,
            "concepts_added": 0,
            "metrics_incorporated": 0
        }
        
        for packet in packets:
            if packet.knowledge_type == "policy":
                # Merge policy insights
                success = await self._merge_policy_insights(packet.data)
                if success:
                    integration_stats["policies_updated"] += 1
            
            elif packet.knowledge_type == "concept":
                # Enhance knowledge graph
                success = await self._enhance_knowledge_graph(packet.data)
                if success:
                    integration_stats["concepts_added"] += 1
            
            elif packet.knowledge_type == "metric":
                # Update benchmarks
                success = await self._update_benchmarks(packet.data)
                if success:
                    integration_stats["metrics_incorporated"] += 1
        
        return integration_stats
    
    async def _merge_policy_insights(self, policy_data: Dict[str, Any]) -> bool:
        """Объединить инсайты политик"""
        try:
            from .learning_loop import learning_loop
            
            # Extract valuable patterns
            if "action_categories" in policy_data:
                for category, stats in policy_data["action_categories"].items():
                    if stats["avg_value"] > 0.5 and stats["count"] > 10:
                        # This category performs well in other nodes
                        # Boost exploration in this direction
                        for agent_name, policy in learning_loop.policies.items():
                            # Find similar actions
                            for action in policy.action_values:
                                if category in action:
                                    # Slightly boost value
                                    current = policy.action_values[action]
                                    policy.action_values[action] = current * 1.1
            
            return True
        except Exception:
            return False
    
    async def _enhance_knowledge_graph(self, graph_data: Dict[str, Any]) -> bool:
        """Улучшить граф знаний"""
        try:
            # Add trending concept types
            if "concept_types" in graph_data:
                for concept_type, count in graph_data["concept_types"].items():
                    if count > 10:  # Popular concept type
                        # Create placeholder for exploration
                        await add_knowledge(
                            concept_name=f"federated_{concept_type}_insight",
                            concept_type=concept_type,
                            properties={"source": "federation", "importance": count}
                        )
            
            return True
        except Exception:
            return False
    
    async def _update_benchmarks(self, metrics_data: Dict[str, Any]) -> bool:
        """Обновить бенчмарки производительности"""
        try:
            # Store federation benchmarks
            benchmark_file = self.storage_path / "federation_benchmarks.json"
            
            if benchmark_file.exists():
                with open(benchmark_file, "r") as f:
                    benchmarks = json.load(f)
            else:
                benchmarks = {}
            
            # Update with new data
            timestamp = datetime.now(timezone.utc).isoformat()
            benchmarks[timestamp] = metrics_data
            
            # Keep only last 100 entries
            if len(benchmarks) > 100:
                sorted_keys = sorted(benchmarks.keys())
                for old_key in sorted_keys[:-100]:
                    del benchmarks[old_key]
            
            with open(benchmark_file, "w") as f:
                json.dump(benchmarks, f, indent=2)
            
            return True
        except Exception:
            return False
    
    async def sync_with_federation(self) -> Dict[str, Any]:
        """Полная синхронизация с федерацией"""
        sync_stats = {
            "knowledge_shared": 0,
            "knowledge_received": 0,
            "nodes_synced": 0,
            "integration_stats": {}
        }
        
        # Share our knowledge
        shared = await self.share_knowledge()
        sync_stats["knowledge_shared"] = shared
        
        # Request knowledge in our specialization areas
        received_packets = []
        for domain in ["ai_agents", "automation", "optimization"]:
            packets = await self.request_knowledge(domain)
            received_packets.extend(packets)
        
        sync_stats["knowledge_received"] = len(received_packets)
        
        # Integrate received knowledge
        if received_packets:
            integration = await self.integrate_federated_knowledge(received_packets)
            sync_stats["integration_stats"] = integration
        
        # Update last sync time
        for node in self.nodes.values():
            if node.is_active:
                node.last_sync = datetime.now(timezone.utc)
                sync_stats["nodes_synced"] += 1
        
        # Save state
        self.save_federation_state()
        
        return sync_stats
    
    def get_federation_status(self) -> Dict[str, Any]:
        """Получить статус федерации"""
        active_nodes = [n for n in self.nodes.values() if n.is_active]
        
        return {
            "node_id": self.node_id,
            "total_nodes": len(self.nodes),
            "active_nodes": len(active_nodes),
            "trusted_nodes": len([n for n in active_nodes if n.trust_score > 1.2]),
            "specializations": list(set(
                spec for node in active_nodes 
                for spec in node.specialization
            )),
            "last_sync": max(
                (n.last_sync for n in self.nodes.values() if n.last_sync),
                default=None
            ),
            "knowledge_packets_cached": len(self.knowledge_cache)
        }
    
    def save_federation_state(self) -> None:
        """Сохранить состояние федерации"""
        state_file = self.storage_path / "federation_state.json"
        
        state = {
            "node_id": self.node_id,
            "nodes": {
                node_id: {
                    "node_id": node.node_id,
                    "name": node.name,
                    "endpoint": node.endpoint,
                    "public_key": node.public_key,
                    "specialization": node.specialization,
                    "trust_score": node.trust_score,
                    "last_sync": node.last_sync.isoformat() if node.last_sync else None,
                    "is_active": node.is_active
                }
                for node_id, node in self.nodes.items()
            }
        }
        
        with open(state_file, "w") as f:
            json.dump(state, f, indent=2)
    
    def load_federation_config(self) -> None:
        """Загрузить конфигурацию федерации"""
        state_file = self.storage_path / "federation_state.json"
        
        if state_file.exists():
            with open(state_file, "r") as f:
                state = json.load(f)
            
            for node_data in state.get("nodes", {}).values():
                if "last_sync" in node_data and node_data["last_sync"]:
                    node_data["last_sync"] = datetime.fromisoformat(node_data["last_sync"])
                
                node = FederatedNode(**node_data)
                self.nodes[node.node_id] = node


# Global federation hub
import platform
node_id = f"mas_{platform.node()}_{hashlib.md5(platform.machine().encode()).hexdigest()[:8]}"
federation_hub = FederatedLearningHub(node_id)