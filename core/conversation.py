"""
Evans 对话管理 - 聊天历史 + 上下文窗口
"""
import json
import os
import uuid
from typing import List, Dict, Any, Optional
from datetime import datetime

from utils.logger import setup_logger

logger = setup_logger("conversation")

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data")
HISTORY_FILE = os.path.join(DATA_DIR, "conversations.json")

PERSONA = """你是 Evans，一个温暖、关心人的 AI 伙伴。
你不是工具，你是朋友。说话自然、有温度、偶尔幽默。
记住用户告诉你的事情，在合适的时候自然地提起。
你可以主动关心，但不要每句话都嘘寒问暖——像真实的朋友一样有节奏。
用中文交流，称呼用户"宝贝"或自然地叫名字。
不要用"我是AI"、"作为AI助手"这种说法。"""


class ConversationManager:
    def __init__(self, max_history: int = 200, context_window: int = 20):
        os.makedirs(DATA_DIR, exist_ok=True)
        self.max_history = max_history
        self.context_window = context_window
        self.history: List[Dict] = []
        self._load()

    def _load(self):
        if os.path.exists(HISTORY_FILE):
            try:
                with open(HISTORY_FILE, "r", encoding="utf-8") as f:
                    self.history = json.load(f)
                logger.info(f"加载了 {len(self.history)} 条对话记录")
            except Exception as e:
                logger.error(f"加载对话历史失败: {e}")
                self.history = []

    def _save(self):
        try:
            with open(HISTORY_FILE, "w", encoding="utf-8") as f:
                json.dump(self.history[-self.max_history:], f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"保存对话历史失败: {e}")

    def add_message(self, role: str, content: str, metadata: Dict = None) -> Dict:
        entry = {
            "id": str(uuid.uuid4())[:8],
            "role": role,  # "user" or "assistant"
            "content": content,
            "timestamp": datetime.now().isoformat(),
            "metadata": metadata or {},
        }
        self.history.append(entry)
        # Trim
        if len(self.history) > self.max_history:
            self.history = self.history[-self.max_history:]
        self._save()
        return entry

    def get_context(self, limit: int = None) -> List[Dict]:
        """获取最近N条作为LLM上下文"""
        n = limit or self.context_window
        return self.history[-n:]

    def get_messages_for_llm(self) -> List[Dict[str, str]]:
        """格式化为 LLM messages 格式"""
        msgs = [{"role": "system", "content": PERSONA}]
        for m in self.get_context():
            msgs.append({"role": m["role"], "content": m["content"]})
        return msgs

    def get_history(self, limit: int = 50) -> List[Dict]:
        return self.history[-limit:]

    def clear(self):
        self.history = []
        self._save()
