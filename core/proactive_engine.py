"""
Evans 主动引擎 - 决定何时主动联系用户
"""
import time
import random
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta

from utils.logger import setup_logger

logger = setup_logger("proactive_engine")

GREETING_TEMPLATES = {
    "morning": [
        "早上好呀～今天天气不错，有什么安排吗？☀️",
        "早呀宝贝！新的一天，冲冲冲 💪",
        "早安～吃早餐了吗？别忘了吃点好的 🥐",
    ],
    "afternoon": [
        "下午好～该喝口水活动活动啦 💧",
        "嘿，下午了，进度怎么样？要不要聊两句？",
        "午后时光～需要我帮你做点什么吗？",
    ],
    "evening": [
        "晚上好～今天辛苦了，放松一下吧 🌙",
        "回来了呀～今天的你很棒，晚上想聊点什么？",
        "夜幕降临～吃晚饭了吗？别忘了好好吃饭 🍚",
    ],
    "check_in": [
        "好久没聊了，你还好吗？😊",
        "嘿，还在忙吗？记得休息一下哦",
        "想你了～最近怎么样？",
    ],
    "reminder_nudge": [
        "对了，你之前说 {reminder}，别忘了哦 ⏰",
        "提醒一下～{reminder} 快到了",
        "小提醒：{reminder} 📌",
    ],
    "emotional_support": [
        "感觉你最近有点累，要不要聊聊？我一直都在 💙",
        "不管发生什么，都有我在呢 🤗",
        "压力大的时候就深呼吸，有需要随时找我",
    ],
}


class ProactiveEngine:
    def __init__(self):
        self.last_interaction_time: float = time.time()
        self.last_proactive_time: float = 0
        self.proactivity_level: float = 0.5  # 0=沉默, 1=非常主动
        self.mood_trend: List[str] = []
        self.max_mood_history = 20

    def record_interaction(self):
        self.last_interaction_time = time.time()

    def record_mood(self, mood: str):
        self.mood_trend.append(mood)
        if len(self.mood_trend) > self.max_mood_history:
            self.mood_trend = self.mood_trend[-self.max_mood_history:]

    def should_reach_out(self) -> Optional[str]:
        """判断是否应该主动联系，返回消息模板类型或 None"""
        now = datetime.now()
        hour = now.hour
        gap = time.time() - self.last_interaction_time
        since_proactive = time.time() - self.last_proactive_time

        # 最少间隔30分钟才能再次主动
        if since_proactive < 1800:
            return None

        # 凌晨不打扰
        if 0 <= hour < 7:
            return None

        # 长时间无互动 (>4h)
        if gap > 14400 and self.proactivity_level >= 0.3:
            return "check_in"

        # 定时问候
        if since_proactive > 3600:  # 至少1小时前没主动过
            if hour == 8 and gap > 3600:
                return "morning"
            if hour == 14 and gap > 3600:
                return "afternoon"
            if hour == 19 and gap > 3600:
                return "evening"

        # 情绪支持：最近3次情绪中有2次负面
        if len(self.mood_trend) >= 3 and self.proactivity_level >= 0.5:
            recent = self.mood_trend[-3:]
            negative = sum(1 for m in recent if m in ("sad", "angry", "anxious", "tired"))
            if negative >= 2:
                return "emotional_support"

        return None

    def generate_message(self, msg_type: str, context: Dict[str, Any] = None) -> str:
        """生成主动消息"""
        templates = GREETING_TEMPLATES.get(msg_type, GREETING_TEMPLATES["check_in"])
        msg = random.choice(templates)

        if msg_type == "reminder_nudge" and context and context.get("reminder"):
            msg = msg.format(reminder=context["reminder"])

        self.last_proactive_time = time.time()
        return msg

    def get_status(self) -> Dict[str, Any]:
        gap = time.time() - self.last_interaction_time
        return {
            "last_interaction": self._format_gap(gap),
            "last_proactive": self._format_gap(time.time() - self.last_proactive_time),
            "proactivity_level": self.proactivity_level,
            "mood_trend": self.mood_trend[-5:],
            "current_mood": self.mood_trend[-1] if self.mood_trend else "unknown",
        }

    def _format_gap(self, seconds: float) -> str:
        if seconds < 60:
            return f"{int(seconds)}秒前"
        if seconds < 3600:
            return f"{int(seconds/60)}分钟前"
        if seconds < 86400:
            return f"{int(seconds/3600)}小时前"
        return f"{int(seconds/86400)}天前"
