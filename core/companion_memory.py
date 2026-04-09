"""
Evans 记忆系统 - 结构化分层记忆
类别: facts(事实), events(事件), preferences(偏好), people(人物), emotions(情绪)
持久化到 data/memories.json
"""
import json
import time
import uuid
import os
import re
from typing import List, Dict, Any, Optional
from datetime import datetime
from collections import defaultdict

from utils.logger import setup_logger

logger = setup_logger("companion_memory")

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data")
MEMORY_FILE = os.path.join(DATA_DIR, "memories.json")

VALID_CATEGORIES = {"facts", "events", "preferences", "people", "emotions"}


class CompanionMemory:
    def __init__(self):
        os.makedirs(DATA_DIR, exist_ok=True)
        self.memories: Dict[str, Dict] = {}
        self._load()

    def _load(self):
        if os.path.exists(MEMORY_FILE):
            try:
                with open(MEMORY_FILE, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    self.memories = data if isinstance(data, dict) else {}
                logger.info(f"加载了 {len(self.memories)} 条记忆")
            except Exception as e:
                logger.error(f"加载记忆失败: {e}")
                self.memories = {}

    def _save(self):
        try:
            with open(MEMORY_FILE, "w", encoding="utf-8") as f:
                json.dump(self.memories, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"保存记忆失败: {e}")

    def add_memory(
        self,
        content: str,
        category: str = "facts",
        importance: float = 0.5,
        source: str = "conversation",
        metadata: Dict[str, Any] = None,
    ) -> Dict:
        if category not in VALID_CATEGORIES:
            category = "facts"
        mid = str(uuid.uuid4())[:8]
        entry = {
            "id": mid,
            "content": content,
            "category": category,
            "importance": min(1.0, max(0.0, importance)),
            "source": source,
            "metadata": metadata or {},
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat(),
            "access_count": 0,
            "tags": [],
        }
        self.memories[mid] = entry
        self._save()
        logger.info(f"新增记忆 [{category}]: {content[:40]}")
        return entry

    def get(self, memory_id: str) -> Optional[Dict]:
        m = self.memories.get(memory_id)
        if m:
            m["access_count"] = m.get("access_count", 0) + 1
            self._save()
        return m

    def delete(self, memory_id: str) -> bool:
        if memory_id in self.memories:
            del self.memories[memory_id]
            self._save()
            return True
        return False

    def search(self, query: str = "", category: str = "", limit: int = 50) -> List[Dict]:
        results = list(self.memories.values())
        if category and category in VALID_CATEGORIES:
            results = [m for m in results if m["category"] == category]
        if query:
            q = query.lower()
            results = [m for m in results if q in m["content"].lower()]
        results.sort(key=lambda m: m.get("importance", 0), reverse=True)
        return results[:limit]

    def get_recent(self, count: int = 10) -> List[Dict]:
        items = sorted(self.memories.values(), key=lambda m: m.get("created_at", ""), reverse=True)
        return items[:count]

    def get_by_category(self, category: str) -> List[Dict]:
        if category not in VALID_CATEGORIES:
            return []
        return [m for m in self.memories.values() if m["category"] == category]

    def get_statistics(self) -> Dict[str, Any]:
        cats = defaultdict(int)
        for m in self.memories.values():
            cats[m["category"]] += 1
        return {
            "total": len(self.memories),
            "by_category": dict(cats),
            "avg_importance": (
                sum(m["importance"] for m in self.memories.values()) / len(self.memories)
                if self.memories else 0
            ),
        }

    def get_context_for_chat(self, max_items: int = 8) -> str:
        """获取最近重要记忆作为聊天上下文"""
        items = sorted(
            self.memories.values(),
            key=lambda m: (m.get("importance", 0), m.get("created_at", "")),
            reverse=True,
        )[:max_items]
        if not items:
            return "暂无记忆"
        lines = []
        for m in items:
            lines.append(f"- [{m['category']}] {m['content']}")
        return "\n".join(lines)

    def extract_from_text(self, text: str) -> List[Dict]:
        """从对话文本中自动提取记忆（启发式）"""
        extracted = []
        # 偏好
        pref_patterns = [
            r"我(喜欢|爱|偏好|更喜欢|最爱)(.+?)([。，！？\n]|$)",
            r"我(不喜欢|讨厌|不爱|不想)(.+?)([。，！？\n]|$)",
        ]
        for pat in pref_patterns:
            for m in re.finditer(pat, text):
                content = m.group(1) + m.group(2)
                extracted.append({"content": content, "category": "preferences", "importance": 0.6})

        # 事件/计划
        event_patterns = [
            r"(明天|后天|下周|这周末|今晚)(.+?)([。，！？\n]|$)",
            r"我要去(.+?)([。，！？\n]|$)",
            r"我(做了|完成了|搞定了)(.+?)([。，！？\n]|$)",
        ]
        for pat in event_patterns:
            for m in re.finditer(pat, text):
                content = m.group(0).rstrip("。，！？\n")
                extracted.append({"content": content, "category": "events", "importance": 0.5})

        # 人物
        people_patterns = [
            r"(我(?:的)?(?:妈妈|爸爸|朋友|同事|老板|老师|同学|姐姐|哥哥|弟弟|妹妹|老公|老婆|男朋友|女朋友))(.{0,20})",
        ]
        for pat in people_patterns:
            for m in re.finditer(pat, text):
                content = m.group(0)
                extracted.append({"content": content, "category": "people", "importance": 0.7})

        # 事实
        fact_patterns = [
            r"我(?:是|在|有|住)(.+?)([。，！？\n]|$)",
            r"我的(.+?)是(.+?)([。，！？\n]|$)",
        ]
        for pat in fact_patterns:
            for m in re.finditer(pat, text):
                content = m.group(0).rstrip("。，！？\n")
                if len(content) > 4:
                    extracted.append({"content": content, "category": "facts", "importance": 0.6})

        return extracted
