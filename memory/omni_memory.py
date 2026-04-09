"""
OmniMem三层记忆系统
"""
import time
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field
from collections import deque

from utils.logger import setup_logger

logger = setup_logger("memory")

@dataclass
class MemoryItem:
    """记忆项"""
    memory_id: str
    content: Dict[str, Any]
    timestamp: float = field(default_factory=time.time)
    importance: float = 0.5  # 0-1
    access_count: int = 0
    last_access: float = field(default_factory=time.time)
    decay_rate: float = 0.95  # 衰减率

class OmniMemory:
    """三层记忆系统"""
    
    def __init__(
        self,
        short_term_size: int = 100,
        medium_term_size: int = 1000,
        decay_rate: float = 0.95
    ):
        # 短期记忆（工作记忆）- 最近的感知和决策
        self.short_term: deque = deque(maxlen=short_term_size)
        
        # 中期记忆（情景记忆）- 重要事件和交互
        self.medium_term: List[MemoryItem] = []
        self.medium_term_size = medium_term_size
        
        # 长期记忆（语义记忆）- 持久化的知识和习惯
        self.long_term: Dict[str, MemoryItem] = {}
        
        self.decay_rate = decay_rate
        self.memory_counter = 0
        
        logger.info("OmniMem记忆系统初始化完成")
    
    def store_short_term(self, content: Dict[str, Any]):
        """存储到短期记忆"""
        self.short_term.append({
            "timestamp": time.time(),
            "content": content
        })
    
    def store_medium_term(self, content: Dict[str, Any], importance: float = 0.5):
        """存储到中期记忆"""
        self.memory_counter += 1
        memory = MemoryItem(
            memory_id=f"mem_{self.memory_counter}",
            content=content,
            importance=importance
        )
        
        self.medium_term.append(memory)
        
        # 如果超过容量，移除重要性最低的记忆
        if len(self.medium_term) > self.medium_term_size:
            self.medium_term.sort(key=lambda m: m.importance)
            self.medium_term.pop(0)
        
        logger.debug(f"存储中期记忆: {memory.memory_id}")
    
    def store_long_term(self, key: str, content: Dict[str, Any], importance: float = 0.8):
        """存储到长期记忆"""
        memory = MemoryItem(
            memory_id=key,
            content=content,
            importance=importance
        )
        
        self.long_term[key] = memory
        logger.debug(f"存储长期记忆: {key}")
    
    def retrieve_recent(self, count: int = 10) -> List[Dict[str, Any]]:
        """检索最近的短期记忆"""
        recent = list(self.short_term)[-count:]
        return [item["content"] for item in recent]
    
    def retrieve_by_importance(self, threshold: float = 0.6, limit: int = 10) -> List[MemoryItem]:
        """按重要性检索中期记忆"""
        filtered = [m for m in self.medium_term if m.importance >= threshold]
        filtered.sort(key=lambda m: m.importance, reverse=True)
        return filtered[:limit]
    
    def retrieve_long_term(self, key: str) -> Optional[MemoryItem]:
        """检索长期记忆"""
        memory = self.long_term.get(key)
        if memory:
            memory.access_count += 1
            memory.last_access = time.time()
        return memory
    
    def decay_memories(self):
        """记忆衰减"""
        current_time = time.time()
        
        # 中期记忆衰减
        for memory in self.medium_term:
            time_elapsed = current_time - memory.last_access
            decay_factor = self.decay_rate ** (time_elapsed / 3600)  # 每小时衰减
            memory.importance *= decay_factor
        
        # 移除重要性过低的记忆
        self.medium_term = [m for m in self.medium_term if m.importance > 0.1]
        
        logger.debug(f"记忆衰减完成，中期记忆数: {len(self.medium_term)}")
    
    def get_statistics(self) -> Dict[str, int]:
        """获取记忆统计"""
        return {
            "short_term": len(self.short_term),
            "medium_term": len(self.medium_term),
            "long_term": len(self.long_term)
        }
