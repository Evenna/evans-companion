"""
Evans 提醒系统 - 自然语言时间解析 + CRUD
"""
import json
import time
import uuid
import os
import re
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
# dateutil is optional; parse_natural_time uses regex

from utils.logger import setup_logger

logger = setup_logger("reminder_engine")

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data")
REMINDER_FILE = os.path.join(DATA_DIR, "reminders.json")


def parse_natural_time(text: str) -> Optional[datetime]:
    """简单的中文自然语言时间解析"""
    now = datetime.now()
    text = text.strip()

    # X分钟后
    m = re.search(r"(\d+)\s*分钟(后|之后)", text)
    if m:
        return now + timedelta(minutes=int(m.group(1)))

    # X小时后
    m = re.search(r"(\d+)\s*小时(后|之后)", text)
    if m:
        return now + timedelta(hours=int(m.group(1)))

    # 明天
    if "明天" in text:
        target = now + timedelta(days=1)
        hm = _extract_hm(text)
        if hm:
            return target.replace(hour=hm[0], minute=hm[1], second=0, microsecond=0)
        return target.replace(hour=9, minute=0, second=0, microsecond=0)

    # 后天
    if "后天" in text:
        target = now + timedelta(days=2)
        hm = _extract_hm(text)
        if hm:
            return target.replace(hour=hm[0], minute=hm[1], second=0, microsecond=0)
        return target.replace(hour=9, minute=0, second=0, microsecond=0)

    # 下周一~日
    weekday_map = {"一": 0, "二": 1, "三": 2, "四": 3, "五": 4, "六": 5, "日": 6, "天": 6}
    m = re.search(r"下周([一二三四五六日天])", text)
    if m:
        wd = weekday_map.get(m.group(1), 0)
        days_ahead = wd - now.weekday()
        if days_ahead <= 0:
            days_ahead += 7
        target = now + timedelta(days=days_ahead)
        hm = _extract_hm(text)
        if hm:
            return target.replace(hour=hm[0], minute=hm[1], second=0, microsecond=0)
        return target.replace(hour=9, minute=0, second=0, microsecond=0)

    # 每天/每晚/每早
    if text.startswith("每天") or text.startswith("每晚") or text.startswith("每早"):
        hm = _extract_hm(text)
        if hm:
            target = now.replace(hour=hm[0], minute=hm[1], second=0, microsecond=0)
            if target <= now:
                target += timedelta(days=1)
            return target
        return None

    # 今天 + 时间
    if "今天" in text or "今晚" in text:
        hm = _extract_hm(text)
        if hm:
            target = now.replace(hour=hm[0], minute=hm[1], second=0, microsecond=0)
            return target
        return None

    # 纯时间 HH:MM
    hm = _extract_hm(text)
    if hm:
        target = now.replace(hour=hm[0], minute=hm[1], second=0, microsecond=0)
        if target <= now:
            target += timedelta(days=1)
        return target

    return None


def _extract_hm(text: str) -> Optional[tuple]:
    """从文本中提取小时:分钟"""
    # 下午3点 / 上午9点半 / 晚上8点
    m = re.search(
        r"(上午|下午|晚上|傍晚|早上|早晨|中午|凌晨)?\s*(\d{1,2})[点时:：](\d{1,2})?(?:分|半)?",
        text,
    )
    if m:
        period = m.group(1) or ""
        hour = int(m.group(2))
        minute = int(m.group(3)) if m.group(3) else 0
        if "半" in text[text.find(m.group(0)) : text.find(m.group(0)) + len(m.group(0)) + 2]:
            minute = 30
        if period in ("下午", "晚上", "傍晚") and hour < 12:
            hour += 12
        if period == "凌晨" and hour == 12:
            hour = 0
        return (hour, minute)
    return None


def detect_recurrence(text: str) -> Optional[str]:
    """检测重复模式"""
    if text.startswith("每天"):
        return "daily"
    if text.startswith("每周"):
        return "weekly"
    if text.startswith("每月"):
        return "monthly"
    return None


class ReminderEngine:
    def __init__(self):
        os.makedirs(DATA_DIR, exist_ok=True)
        self.reminders: Dict[str, Dict] = {}
        self._load()

    def _load(self):
        if os.path.exists(REMINDER_FILE):
            try:
                with open(REMINDER_FILE, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    self.reminders = data if isinstance(data, dict) else {}
                logger.info(f"加载了 {len(self.reminders)} 条提醒")
            except Exception as e:
                logger.error(f"加载提醒失败: {e}")
                self.reminders = {}

    def _save(self):
        try:
            with open(REMINDER_FILE, "w", encoding="utf-8") as f:
                json.dump(self.reminders, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"保存提醒失败: {e}")

    def create_reminder(
        self,
        text: str,
        time_text: str = "",
        category: str = "task",
        trigger_time: Optional[datetime] = None,
    ) -> Dict:
        rid = str(uuid.uuid4())[:8]
        recurrence = detect_recurrence(time_text or text)

        if trigger_time is None:
            trigger_time = parse_natural_time(time_text or text)

        entry = {
            "id": rid,
            "text": text,
            "trigger_time": trigger_time.isoformat() if trigger_time else None,
            "recurrence": recurrence,
            "category": category,
            "status": "active",
            "created_at": datetime.now().isoformat(),
            "fired_at": None,
            "raw_time_text": time_text,
        }
        self.reminders[rid] = entry
        self._save()
        logger.info(f"创建提醒: {text[:30]} @ {trigger_time}")
        return entry

    def update(self, reminder_id: str, updates: Dict) -> Optional[Dict]:
        r = self.reminders.get(reminder_id)
        if not r:
            return None
        r.update(updates)
        r["updated_at"] = datetime.now().isoformat()
        self._save()
        return r

    def delete(self, reminder_id: str) -> bool:
        if reminder_id in self.reminders:
            del self.reminders[reminder_id]
            self._save()
            return True
        return False

    def mark_done(self, reminder_id: str) -> Optional[Dict]:
        return self.update(reminder_id, {"status": "done", "fired_at": datetime.now().isoformat()})

    def check_due(self) -> List[Dict]:
        """返回所有到期的提醒"""
        now = datetime.now()
        due = []
        for r in list(self.reminders.values()):
            if r["status"] != "active" or not r.get("trigger_time"):
                continue
            try:
                trigger = datetime.fromisoformat(r["trigger_time"])
            except Exception:
                continue
            if trigger <= now:
                due.append(r)
                # 处理重复
                if r.get("recurrence") == "daily":
                    r["trigger_time"] = (trigger + timedelta(days=1)).isoformat()
                elif r.get("recurrence") == "weekly":
                    r["trigger_time"] = (trigger + timedelta(weeks=1)).isoformat()
                elif r.get("recurrence") == "monthly":
                    r["trigger_time"] = (trigger + timedelta(days=30)).isoformat()
                else:
                    r["status"] = "done"
                    r["fired_at"] = now.isoformat()
        if due:
            self._save()
        return due

    def get_active(self) -> List[Dict]:
        return [
            r for r in self.reminders.values()
            if r["status"] == "active"
        ]

    def get_all(self) -> List[Dict]:
        return list(self.reminders.values())

    def extract_from_text(self, text: str) -> Optional[Dict]:
        """从文本中提取提醒意图"""
        patterns = [
            r"(?:提醒我|记着|别忘了|记得)(.+?)(?:[。，！？\n]|$)",
            r"(?:明天|后天|今晚|今天|下周|每天|每晚|每早|N分钟后|\d+小时后)(.+?)(?:[。，！？\n]|$)",
        ]
        for pat in patterns:
            m = re.search(pat, text)
            if m:
                reminder_text = m.group(0).strip()
                trigger = parse_natural_time(reminder_text)
                if trigger:
                    return {"text": reminder_text, "trigger_time": trigger}
        return None
