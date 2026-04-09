"""Nexus Core 共享数据类型"""
from __future__ import annotations

import time
import uuid
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional


# --- 枚举 ---


class IntentType(str, Enum):
    REQUEST = "request"
    QUERY = "query"
    NEED_COMFORT = "need_comfort"
    COMMAND = "command"


class RelationType(str, Enum):
    STRANGER = "stranger"
    FAMILY = "family"
    FRIEND = "friend"
    COLLEAGUE = "colleague"


class RiskLevel(int, Enum):
    LOW = 0
    MEDIUM = 1
    HIGH = 2
    CRITICAL = 3


class Emotion(str, Enum):
    NEUTRAL = "neutral"
    HAPPY = "happy"
    SAD = "sad"
    ANGRY = "angry"


class TaskPriority(int, Enum):
    P0_CRITICAL = 0
    P1_HIGH = 1
    P2_NORMAL = 2
    P3_LOW = 3


class TaskStatus(str, Enum):
    PENDING = "pending"
    EXECUTING = "executing"
    COMPLETED = "completed"
    FAILED = "failed"


class ActionType(str, Enum):
    SPEAK = "speak"
    DISPLAY = "display"
    DEVICE_CONTROL = "device_control"
    NOTIFICATION = "notification"
    RECORD = "record"


# --- 感知 ---


@dataclass
class AudioData:
    transcript: str = ""


@dataclass
class FaceInfo:
    face_id: str
    emotion: Emotion = Emotion.NEUTRAL


@dataclass
class PerceptionFrame:
    timestamp: float
    frame_id: str
    scene_type: str = "indoor"
    faces: List[FaceInfo] = field(default_factory=list)
    objects: List[str] = field(default_factory=list)
    audio: Optional[AudioData] = None


# --- 分析 ---


@dataclass
class Intent:
    intent_type: IntentType
    confidence: float
    source: str
    parameters: Dict[str, Any] = field(default_factory=dict)
    urgency: float = 0.0


@dataclass
class PersonIdentity:
    person_id: str
    name: Optional[str]
    relation: RelationType
    trust_level: float
    first_seen: float
    last_seen: float
    interaction_count: int = 0


@dataclass
class AnomalyDetection:
    anomaly_type: str
    description: str
    risk_level: RiskLevel
    confidence: float
    suggested_action: str = ""


@dataclass
class AnalysisResult:
    timestamp: float
    frame_id: str
    context_summary: str = ""
    intents: List[Intent] = field(default_factory=list)
    primary_intent: Optional[Intent] = None
    identified_persons: List[PersonIdentity] = field(default_factory=list)
    anomalies: List[AnomalyDetection] = field(default_factory=list)
    user_state: Dict[str, Any] = field(default_factory=dict)


# --- 决策 ---


@dataclass
class WorldState:
    timestamp: float = field(default_factory=time.time)
    user_activity: str = "unknown"
    user_mood: str = "neutral"
    environment_state: Dict[str, Any] = field(default_factory=dict)


@dataclass
class Need:
    need_type: str
    description: str
    confidence: float
    urgency: float
    source: str
    should_intervene: bool = False
    intervention_reason: str = ""


@dataclass
class Action:
    action_type: ActionType
    target: str
    parameters: Dict[str, Any] = field(default_factory=dict)
    expected_duration: float = 0.0


@dataclass
class TaskPlan:
    task_description: str
    priority: TaskPriority
    actions: List[Action] = field(default_factory=list)
    plan_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    status: TaskStatus = TaskStatus.PENDING
    estimated_duration: float = 0.0
    success_probability: float = 0.8


@dataclass
class DecisionResult:
    timestamp: float
    current_state: Optional[WorldState] = None
    recognized_needs: List[Need] = field(default_factory=list)
    primary_need: Optional[Need] = None
    task_plans: List[TaskPlan] = field(default_factory=list)
    selected_plan: Optional[TaskPlan] = None
    reasoning_chain: List[str] = field(default_factory=list)
    decision_confidence: float = 0.5


# 包内导出
__all__ = [
    "IntentType",
    "RelationType",
    "RiskLevel",
    "Emotion",
    "TaskPriority",
    "TaskStatus",
    "ActionType",
    "AudioData",
    "FaceInfo",
    "PerceptionFrame",
    "Intent",
    "PersonIdentity",
    "AnomalyDetection",
    "AnalysisResult",
    "WorldState",
    "Need",
    "Action",
    "TaskPlan",
    "DecisionResult",
]
