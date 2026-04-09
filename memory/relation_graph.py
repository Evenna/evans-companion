"""
关系图谱 - 人物关系网络
"""
import time
from typing import List, Dict, Optional, Set, Tuple
from dataclasses import dataclass, field

from utils.data_types import PersonIdentity, RelationType
from utils.logger import setup_logger

logger = setup_logger("relation_graph")

@dataclass
class RelationEdge:
    """关系边"""
    from_person: str  # person_id
    to_person: str    # person_id
    relation_type: RelationType
    strength: float = 0.5  # 关系强度 0-1
    created_at: float = field(default_factory=time.time)
    last_interaction: float = field(default_factory=time.time)
    interaction_count: int = 0
    notes: str = ""

class RelationGraph:
    """关系图谱"""
    
    def __init__(self):
        # 节点：person_id -> PersonIdentity
        self.nodes: Dict[str, PersonIdentity] = {}
        
        # 边：(from_id, to_id) -> RelationEdge
        self.edges: Dict[Tuple[str, str], RelationEdge] = {}
        
        # 邻接表（加速查询）
        self.adjacency: Dict[str, Set[str]] = {}
        
        logger.info("关系图谱初始化完成")
    
    def add_person(self, person: PersonIdentity) -> bool:
        """添加人物节点"""
        if person.person_id in self.nodes:
            logger.warning(f"人物已存在: {person.person_id}")
            return False
        
        self.nodes[person.person_id] = person
        self.adjacency[person.person_id] = set()
        
        logger.info(f"添加人物: {person.person_id} ({person.name or '未命名'})")
        return True
    
    def update_person(self, person: PersonIdentity):
        """更新人物信息"""
        if person.person_id not in self.nodes:
            self.add_person(person)
        else:
            self.nodes[person.person_id] = person
            logger.debug(f"更新人物: {person.person_id}")
    
    def get_person(self, person_id: str) -> Optional[PersonIdentity]:
        """获取人物信息"""
        return self.nodes.get(person_id)
    
    def add_relation(
        self,
        from_person: str,
        to_person: str,
        relation_type: RelationType,
        strength: float = 0.5,
        notes: str = ""
    ) -> bool:
        """添加关系边"""
        if from_person not in self.nodes or to_person not in self.nodes:
            logger.error("关系的人物节点不存在")
            return False
        
        edge_key = (from_person, to_person)
        
        if edge_key in self.edges:
            # 更新已有关系
            edge = self.edges[edge_key]
            edge.relation_type = relation_type
            edge.strength = strength
            edge.last_interaction = time.time()
            edge.interaction_count += 1
            if notes:
                edge.notes = notes
        else:
            # 创建新关系
            edge = RelationEdge(
                from_person=from_person,
                to_person=to_person,
                relation_type=relation_type,
                strength=strength,
                notes=notes
            )
            self.edges[edge_key] = edge
            
            # 更新邻接表
            self.adjacency[from_person].add(to_person)
        
        logger.info(f"添加关系: {from_person} -> {to_person} ({relation_type.value})")
        return True
    
    def get_relations(self, person_id: str) -> List[RelationEdge]:
        """获取某人的所有关系"""
        if person_id not in self.adjacency:
            return []
        
        relations = []
        for target_id in self.adjacency[person_id]:
            edge = self.edges.get((person_id, target_id))
            if edge:
                relations.append(edge)
        
        return relations
    
    def find_relation(self, from_person: str, to_person: str) -> Optional[RelationEdge]:
        """查找两人之间的关系"""
        return self.edges.get((from_person, to_person))
    
    def get_family_members(self, person_id: str) -> List[PersonIdentity]:
        """获取家庭成员"""
        family = []
        relations = self.get_relations(person_id)
        
        for edge in relations:
            if edge.relation_type == RelationType.FAMILY:
                person = self.nodes.get(edge.to_person)
                if person:
                    family.append(person)
        
        return family
    
    def get_trusted_persons(self, person_id: str, threshold: float = 0.7) -> List[PersonIdentity]:
        """获取信任的人"""
        trusted = []
        relations = self.get_relations(person_id)
        
        for edge in relations:
            if edge.strength >= threshold:
                person = self.nodes.get(edge.to_person)
                if person:
                    trusted.append(person)
        
        return trusted
    
    def remove_person(self, person_id: str) -> bool:
        """移除人物节点"""
        if person_id not in self.nodes:
            return False
        
        # 移除节点
        del self.nodes[person_id]
        
        # 移除相关的边
        edges_to_remove = []
        for edge_key in self.edges:
            if edge_key[0] == person_id or edge_key[1] == person_id:
                edges_to_remove.append(edge_key)
        
        for edge_key in edges_to_remove:
            del self.edges[edge_key]
        
        # 更新邻接表
        if person_id in self.adjacency:
            del self.adjacency[person_id]
        
        for neighbors in self.adjacency.values():
            neighbors.discard(person_id)
        
        logger.info(f"移除人物: {person_id}")
        return True
    
    def get_statistics(self) -> Dict[str, int]:
        """获取图谱统计"""
        return {
            "total_persons": len(self.nodes),
            "total_relations": len(self.edges),
            "family_relations": sum(1 for e in self.edges.values() if e.relation_type == RelationType.FAMILY),
            "friend_relations": sum(1 for e in self.edges.values() if e.relation_type == RelationType.FRIEND)
        }
