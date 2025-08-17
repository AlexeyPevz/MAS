"""
Knowledge Graph System for Root-MAS
Граф знаний для глубокого понимания связей между концепциями
"""
from typing import Dict, Any, List, Optional, Set, Tuple
from datetime import datetime, timezone
from dataclasses import dataclass, field
import json
import os
import networkx as nx
from pathlib import Path
import numpy as np
from collections import Counter
from collections import defaultdict

from .event_sourcing import event_logger, EventType


@dataclass
class Concept:
    """Концепция в графе знаний"""
    id: str
    name: str
    type: str  # entity, action, property, relation
    properties: Dict[str, Any] = field(default_factory=dict)
    embeddings: Optional[np.ndarray] = None
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    
    def similarity(self, other: 'Concept') -> float:
        """Вычислить семантическую близость с другой концепцией"""
        if self.embeddings is None or other.embeddings is None:
            return 0.0
        
        # Cosine similarity
        dot_product = np.dot(self.embeddings, other.embeddings)
        norm_a = np.linalg.norm(self.embeddings)
        norm_b = np.linalg.norm(other.embeddings)
        
        if norm_a == 0 or norm_b == 0:
            return 0.0
        
        return dot_product / (norm_a * norm_b)


@dataclass
class Relation:
    """Связь между концепциями"""
    source: str  # ID исходной концепции
    target: str  # ID целевой концепции
    type: str  # is_a, part_of, causes, requires, etc.
    weight: float = 1.0
    properties: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


class KnowledgeGraph:
    """Граф знаний системы"""
    
    def __init__(self, storage_path: str = None):
        if storage_path is None:
            storage_path = os.path.join(os.getenv("DATA_PATH", "data"), "knowledge_graph")
        self.storage_path = Path(storage_path)
        self.storage_path.mkdir(parents=True, exist_ok=True)
        
        self.graph = nx.DiGraph()
        self.concepts: Dict[str, Concept] = {}
        self.concept_index: Dict[str, Set[str]] = defaultdict(set)  # type -> concept_ids
        
        # Load existing graph
        self.load_graph()
    
    def add_concept(self, concept: Concept) -> str:
        """Добавить концепцию в граф"""
        # Store concept
        self.concepts[concept.id] = concept
        self.concept_index[concept.type].add(concept.id)
        
        # Add node to graph
        self.graph.add_node(
            concept.id,
            name=concept.name,
            type=concept.type,
            properties=concept.properties
        )
        
        # Find and create automatic relations
        self._infer_relations(concept)
        
        return concept.id
    
    def add_relation(self, relation: Relation) -> None:
        """Добавить связь между концепциями"""
        if relation.source not in self.concepts or relation.target not in self.concepts:
            raise ValueError("Both concepts must exist in the graph")
        
        # Add edge to graph
        self.graph.add_edge(
            relation.source,
            relation.target,
            type=relation.type,
            weight=relation.weight,
            properties=relation.properties
        )
    
    def get_concept(self, concept_id: str) -> Optional[Concept]:
        """Получить концепцию по ID"""
        return self.concepts.get(concept_id)
    
    def find_concepts(
        self, 
        name: Optional[str] = None,
        type: Optional[str] = None,
        properties: Optional[Dict[str, Any]] = None
    ) -> List[Concept]:
        """Найти концепции по критериям"""
        results = []
        
        # Filter by type first if provided
        if type:
            candidates = [self.concepts[cid] for cid in self.concept_index.get(type, [])]
        else:
            candidates = list(self.concepts.values())
        
        for concept in candidates:
            # Check name
            if name and name.lower() not in concept.name.lower():
                continue
            
            # Check properties
            if properties:
                match = True
                for key, value in properties.items():
                    if concept.properties.get(key) != value:
                        match = False
                        break
                if not match:
                    continue
            
            results.append(concept)
        
        return results
    
    def find_similar_concepts(
        self, 
        concept_id: str, 
        threshold: float = 0.7,
        limit: int = 10
    ) -> List[Tuple[Concept, float]]:
        """Найти похожие концепции"""
        base_concept = self.concepts.get(concept_id)
        if not base_concept or base_concept.embeddings is None:
            return []
        
        similarities = []
        
        for cid, concept in self.concepts.items():
            if cid == concept_id:
                continue
            
            similarity = base_concept.similarity(concept)
            if similarity >= threshold:
                similarities.append((concept, similarity))
        
        # Sort by similarity
        similarities.sort(key=lambda x: x[1], reverse=True)
        
        return similarities[:limit]
    
    def get_relations(
        self, 
        concept_id: str, 
        relation_type: Optional[str] = None,
        direction: str = "both"  # in, out, both
    ) -> List[Dict[str, Any]]:
        """Получить связи концепции"""
        relations = []
        
        # Outgoing relations
        if direction in ["out", "both"]:
            for _, target, data in self.graph.out_edges(concept_id, data=True):
                if relation_type and data.get("type") != relation_type:
                    continue
                
                relations.append({
                    "source": concept_id,
                    "target": target,
                    "type": data.get("type"),
                    "weight": data.get("weight", 1.0),
                    "properties": data.get("properties", {}),
                    "direction": "out"
                })
        
        # Incoming relations
        if direction in ["in", "both"]:
            for source, _, data in self.graph.in_edges(concept_id, data=True):
                if relation_type and data.get("type") != relation_type:
                    continue
                
                relations.append({
                    "source": source,
                    "target": concept_id,
                    "type": data.get("type"),
                    "weight": data.get("weight", 1.0),
                    "properties": data.get("properties", {}),
                    "direction": "in"
                })
        
        return relations
    
    def find_path(
        self, 
        source_id: str, 
        target_id: str,
        max_length: int = 5
    ) -> Optional[List[str]]:
        """Найти путь между концепциями"""
        try:
            path = nx.shortest_path(
                self.graph, 
                source_id, 
                target_id,
                weight="weight"
            )
            
            if len(path) > max_length:
                return None
            
            return path
        except nx.NetworkXNoPath:
            return None
    
    def get_subgraph(
        self, 
        concept_id: str, 
        depth: int = 2,
        max_nodes: int = 50
    ) -> nx.DiGraph:
        """Получить подграф вокруг концепции"""
        # BFS to get nodes within depth
        nodes = {concept_id}
        current_level = {concept_id}
        
        for _ in range(depth):
            next_level = set()
            for node in current_level:
                # Add neighbors
                next_level.update(self.graph.predecessors(node))
                next_level.update(self.graph.successors(node))
            
            nodes.update(next_level)
            current_level = next_level
            
            if len(nodes) >= max_nodes:
                break
        
        # Create subgraph
        return self.graph.subgraph(list(nodes)[:max_nodes])
    
    def _infer_relations(self, concept: Concept) -> None:
        """Автоматически вывести связи для новой концепции"""
        # Find similar concepts
        if concept.embeddings is not None:
            similar = self.find_similar_concepts(concept.id, threshold=0.8)
            
            for similar_concept, similarity in similar[:3]:
                # Create similarity relation
                self.add_relation(Relation(
                    source=concept.id,
                    target=similar_concept.id,
                    type="similar_to",
                    weight=similarity
                ))
        
        # Infer hierarchical relations based on name
        if " " in concept.name:
            # Check for "is a" patterns
            parts = concept.name.split()
            
            for other_id, other_concept in self.concepts.items():
                if other_id == concept.id:
                    continue
                
                # Check if this is a specialization
                if parts[-1] == other_concept.name:
                    self.add_relation(Relation(
                        source=concept.id,
                        target=other_id,
                        type="is_a",
                        weight=0.9
                    ))
                
                # Check if this contains the other
                if other_concept.name in concept.name:
                    self.add_relation(Relation(
                        source=concept.id,
                        target=other_id,
                        type="related_to",
                        weight=0.7
                    ))
    
    def query(self, sparql_like_query: str) -> List[Dict[str, Any]]:
        """Выполнить SPARQL-подобный запрос"""
        # Simple query parser
        # Format: SELECT ?x WHERE { ?x type "entity" . ?x property value }
        
        results = []
        
        # Parse query (simplified)
        if "WHERE" in sparql_like_query:
            conditions = sparql_like_query.split("WHERE")[1].strip()
            
            # Extract conditions
            type_filter = None
            property_filters = {}
            
            if "type" in conditions:
                # Extract type
                import re
                type_match = re.search(r'type\s+"([^"]+)"', conditions)
                if type_match:
                    type_filter = type_match.group(1)
            
            # Find matching concepts
            for concept in self.find_concepts(type=type_filter):
                results.append({
                    "id": concept.id,
                    "name": concept.name,
                    "type": concept.type,
                    "properties": concept.properties
                })
        
        return results
    
    def get_statistics(self) -> Dict[str, Any]:
        """Получить статистику графа"""
        return {
            "total_concepts": len(self.concepts),
            "total_relations": self.graph.number_of_edges(),
            "concept_types": {
                ctype: len(cids) 
                for ctype, cids in self.concept_index.items()
            },
            "relation_types": dict(
                Counter(nx.get_edge_attributes(self.graph, 'type').values())
            ),
            "avg_degree": sum(dict(self.graph.degree()).values()) / len(self.graph) if len(self.graph) > 0 else 0,
            "connected_components": nx.number_weakly_connected_components(self.graph),
            "density": nx.density(self.graph)
        }
    
    def visualize_subgraph(
        self, 
        concept_id: str, 
        depth: int = 2
    ) -> Dict[str, Any]:
        """Подготовить данные для визуализации подграфа"""
        subgraph = self.get_subgraph(concept_id, depth)
        
        nodes = []
        edges = []
        
        # Prepare nodes
        for node_id in subgraph.nodes():
            concept = self.concepts[node_id]
            nodes.append({
                "id": node_id,
                "label": concept.name,
                "type": concept.type,
                "properties": concept.properties
            })
        
        # Prepare edges
        for source, target, data in subgraph.edges(data=True):
            edges.append({
                "source": source,
                "target": target,
                "type": data.get("type", "related"),
                "weight": data.get("weight", 1.0)
            })
        
        return {
            "nodes": nodes,
            "edges": edges,
            "center": concept_id
        }
    
    def save_graph(self) -> None:
        """Сохранить граф на диск"""
        # Save concepts
        concepts_file = self.storage_path / "concepts.json"
        concepts_data = {
            cid: {
                "id": concept.id,
                "name": concept.name,
                "type": concept.type,
                "properties": concept.properties,
                "created_at": concept.created_at.isoformat(),
                "updated_at": concept.updated_at.isoformat()
            }
            for cid, concept in self.concepts.items()
        }
        
        with open(concepts_file, "w") as f:
            json.dump(concepts_data, f, indent=2)
        
        # Save graph structure
        graph_file = self.storage_path / "graph.json"
        graph_data = nx.node_link_data(self.graph)
        
        with open(graph_file, "w") as f:
            json.dump(graph_data, f, indent=2)
    
    def load_graph(self) -> None:
        """Загрузить граф с диска"""
        # Load concepts
        concepts_file = self.storage_path / "concepts.json"
        if concepts_file.exists():
            with open(concepts_file, "r") as f:
                concepts_data = json.load(f)
            
            for cid, data in concepts_data.items():
                concept = Concept(
                    id=data["id"],
                    name=data["name"],
                    type=data["type"],
                    properties=data.get("properties", {}),
                    created_at=datetime.fromisoformat(data["created_at"]),
                    updated_at=datetime.fromisoformat(data["updated_at"])
                )
                self.concepts[cid] = concept
                self.concept_index[concept.type].add(cid)
        
        # Load graph structure
        graph_file = self.storage_path / "graph.json"
        if graph_file.exists():
            with open(graph_file, "r") as f:
                graph_data = json.load(f)
            
            self.graph = nx.node_link_graph(graph_data)


# Global knowledge graph instance
knowledge_graph = KnowledgeGraph()


# Helper functions for agents
async def add_knowledge(
    concept_name: str,
    concept_type: str,
    properties: Optional[Dict[str, Any]] = None,
    relations: Optional[List[Tuple[str, str, str]]] = None  # [(target_name, relation_type, weight)]
) -> str:
    """Добавить знание в граф"""
    # Create concept
    concept = Concept(
        id=f"{concept_type}_{concept_name.lower().replace(' ', '_')}",
        name=concept_name,
        type=concept_type,
        properties=properties or {}
    )
    
    concept_id = knowledge_graph.add_concept(concept)
    
    # Add relations if provided
    if relations:
        for target_name, relation_type, weight in relations:
            # Find target concept
            targets = knowledge_graph.find_concepts(name=target_name)
            if targets:
                knowledge_graph.add_relation(Relation(
                    source=concept_id,
                    target=targets[0].id,
                    type=relation_type,
                    weight=weight
                ))
    
    # Log event
    await event_logger.log_system_event(
        EventType.MEMORY_STORED,
        {
            "concept_id": concept_id,
            "concept_name": concept_name,
            "concept_type": concept_type
        }
    )
    
    return concept_id


async def query_knowledge(
    query: str,
    concept_type: Optional[str] = None,
    max_depth: int = 3
) -> List[Dict[str, Any]]:
    """Запросить знания из графа"""
    # Find relevant concepts
    concepts = knowledge_graph.find_concepts(name=query, type=concept_type)
    
    results = []
    for concept in concepts[:5]:  # Limit to top 5
        # Get subgraph
        subgraph_data = knowledge_graph.visualize_subgraph(concept.id, depth=max_depth)
        
        # Get relations
        relations = knowledge_graph.get_relations(concept.id)
        
        results.append({
            "concept": {
                "id": concept.id,
                "name": concept.name,
                "type": concept.type,
                "properties": concept.properties
            },
            "relations": relations,
            "subgraph": subgraph_data
        })
    
    # Log event
    await event_logger.log_system_event(
        EventType.MEMORY_RETRIEVED,
        {
            "query": query,
            "results_count": len(results)
        }
    )
    
    return results