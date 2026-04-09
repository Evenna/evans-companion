"""
Nexus Core Web Server — Evans AI Companion
启动: uvicorn server:app --host 0.0.0.0 --port 8000 --reload
"""
from __future__ import annotations

import asyncio
import base64
import json
import os
import sys
import time
from collections import deque
from datetime import datetime
from pathlib import Path
from typing import Any, Deque, Dict, List, Optional

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from pydantic import BaseModel, Field
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

ROOT = Path(__file__).resolve().parent
load_dotenv(ROOT / ".env", override=True)
load_dotenv(Path.cwd() / ".env", override=True)
sys.path.insert(0, str(ROOT))

from services.gemini_brain import analyze_frame_jpeg, chat_response
from core.companion_memory import CompanionMemory
from core.reminder_engine import ReminderEngine, parse_natural_time
from core.proactive_engine import ProactiveEngine
from core.conversation import ConversationManager
from utils.logger import setup_logger

logger = setup_logger("nexus_server")

app = FastAPI(title="Evans AI Companion")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

STATIC = ROOT / "static"
if STATIC.exists():
    app.mount("/assets", StaticFiles(directory=STATIC), name="assets")
MOBILE_STATIC = STATIC / "mobile"
if MOBILE_STATIC.exists():
    app.mount("/mobile-assets", StaticFiles(directory=MOBILE_STATIC), name="mobile-assets")


@app.get("/")
async def index():
    return FileResponse(STATIC / "index.html")


@app.get("/m")
async def mobile_index():
    return FileResponse(MOBILE_STATIC / "index.html")


# ─── 核心组件 ────────────────────────────────────────────────────────────────

companion_memory = CompanionMemory()
reminder_engine = ReminderEngine()
proactive_engine = ProactiveEngine()
conversation_mgr = ConversationManager()


def _now_hms() -> str:
    return datetime.now().strftime("%H:%M:%S")


class RuntimeStore:
    """跨端共享状态"""

    def __init__(self) -> None:
        self.profile: Dict[str, Any] = {
            "name": "主用户",
            "group": "adult",
            "comm_style": "direct",
            "health": "正常",
            "proactive_level": 0.5,
            "learned_habits": [],
        }
        self.devices: Dict[str, Dict[str, Any]] = {
            "smart_light_main": {"name": "主灯", "type": "light", "on": False, "dim": 100},
            "smart_light_ambient": {"name": "氛围灯", "type": "light", "on": False, "dim": 60},
            "smart_speaker": {"name": "智能音箱", "type": "speaker", "on": False, "volume": 70},
            "ac_unit": {"name": "空调", "type": "climate", "on": False, "temperature": 26, "mode": "cool"},
            "robot_arm": {"name": "机械臂", "type": "robot", "on": False, "status": "idle"},
            "mobile_base": {"name": "移动底盘", "type": "robot", "on": False, "status": "idle"},
            "door_lock": {"name": "门锁", "type": "security", "locked": True},
            "camera_ptz": {"name": "云台摄像头", "type": "camera", "on": True, "angle": 0},
        }
        self.timeline: Deque[Dict[str, Any]] = deque(maxlen=300)
        self.memories: Deque[Dict[str, Any]] = deque(maxlen=120)
        self.last_result: Dict[str, Any] | None = None
        self.last_analyze_at: str = "-"
        self.analyze_count: int = 0
        self.last_scene: str = "等待分析"
        self.last_advice: str = "暂无建议"

    def add_timeline(self, t: str, detail: str, level: str = "info") -> None:
        self.timeline.appendleft({"ts": _now_hms(), "type": t, "detail": detail, "level": level})

    def apply_profile(self, patch: Dict[str, Any]) -> None:
        self.profile.update(patch)
        self.add_timeline("profile", f"画像更新: {', '.join(patch.keys())}")

    def apply_device_action(self, device_id: str, action: str, params: Dict[str, Any]) -> None:
        d = self.devices.get(device_id)
        if not d:
            raise KeyError(device_id)
        act = action.lower()
        if act == "on":
            d["on"] = True
        elif act == "off":
            d["on"] = False
        elif act == "dim":
            d["dim"] = int(params.get("level", d.get("dim", 60)))
        elif act == "temperature":
            d["temperature"] = int(params.get("value", d.get("temperature", 26)))
        elif act == "volume":
            d["volume"] = int(params.get("level", d.get("volume", 70)))
        elif act == "lock":
            d["locked"] = True
        elif act == "unlock":
            d["locked"] = False
        elif act in {"move_to", "patrol", "follow"}:
            d["on"] = True
            d["status"] = act
        elif act == "stop":
            d["on"] = False
            d["status"] = "idle"
        self.add_timeline("device", f"{d.get('name', device_id)} → {action}")

    def apply_analysis(self, data: Dict[str, Any]) -> None:
        self.last_result = data
        self.last_analyze_at = _now_hms()
        self.analyze_count += 1
        self.last_scene = data.get("layer2_fusion", {}).get("scene_label", "未知场景")
        self.last_advice = data.get("proactive_preview", "") or "继续观察"
        if self.last_scene:
            self.add_timeline("analysis", f"场景: {self.last_scene}")

        mem = data.get("memory_update", {})
        if mem.get("should_record"):
            entry = {
                "ts": _now_hms(),
                "summary": mem.get("event_summary", ""),
                "importance": mem.get("importance", 0.3),
            }
            self.memories.appendleft(entry)
            self.add_timeline("memory", f"记录记忆: {entry['summary'][:40]}")
        hint = mem.get("profile_hint", "")
        if hint:
            habits = self.profile.setdefault("learned_habits", [])
            if hint not in habits:
                habits.append(hint)
                if len(habits) > 20:
                    self.profile["learned_habits"] = habits[-20:]
            self.add_timeline("learn", f"学习到习惯: {hint[:40]}")

        for cmd in data.get("layer6_execution", {}).get("device_commands", []):
            did = cmd.get("device_id")
            if did in self.devices:
                try:
                    self.apply_device_action(did, cmd.get("action", ""), cmd.get("params") or {})
                except Exception:
                    pass

    def mobile_home(self) -> Dict[str, Any]:
        return {
            "status": "online",
            "last_analyze_at": self.last_analyze_at,
            "analyze_count": self.analyze_count,
            "scene": self.last_scene,
            "advice": self.last_advice,
            "profile": self.profile,
            "alerts": [x for x in list(self.timeline)[:10] if x["level"] in {"warn", "danger"}][:3],
        }


STORE = RuntimeStore()

# ─── WebSocket 连接管理 ─────────────────────────────────────────────────────

active_ws = None  # type: WebSocket | None


async def push_to_ws(data: Dict):
    """向前端推送消息"""
    global active_ws
    if active_ws:
        try:
            await active_ws.send_json(data)
        except Exception:
            active_ws = None


# ─── Request Models ──────────────────────────────────────────────────────────

class DeviceActionBody(BaseModel):
    device_id: str
    action: str
    params: Dict[str, Any] = Field(default_factory=dict)


class ProfilePatchBody(BaseModel):
    name: Optional[str] = None
    group: Optional[str] = None
    comm_style: Optional[str] = None
    health: Optional[str] = None
    proactive_level: Optional[float] = None


class ChatBody(BaseModel):
    message: str


class MemoryCreateBody(BaseModel):
    content: str
    category: str = "facts"
    importance: float = 0.5


class ReminderCreateBody(BaseModel):
    text: str
    time_text: str = ""
    category: str = "task"


class ReminderUpdateBody(BaseModel):
    text: Optional[str] = None
    time_text: Optional[str] = None
    status: Optional[str] = None
    category: Optional[str] = None


# ─── 原有 Mobile / Device API ───────────────────────────────────────────────

@app.get("/api/mobile/home")
async def mobile_home():
    return STORE.mobile_home()


@app.get("/api/mobile/timeline")
async def mobile_timeline(limit: int = 50):
    n = max(1, min(limit, 200))
    return {"items": list(STORE.timeline)[:n]}


@app.get("/api/mobile/devices")
async def mobile_devices():
    return {"devices": STORE.devices}


@app.post("/api/mobile/device/action")
async def mobile_device_action(body: DeviceActionBody):
    try:
        STORE.apply_device_action(body.device_id, body.action, body.params)
    except KeyError:
        raise HTTPException(status_code=404, detail="device not found")
    return {"ok": True, "devices": STORE.devices}


@app.get("/api/mobile/profile")
async def mobile_profile():
    return {"profile": STORE.profile}


@app.post("/api/mobile/profile")
async def mobile_profile_update(body: ProfilePatchBody):
    patch = {k: v for k, v in body.model_dump().items() if v is not None}
    if patch:
        STORE.apply_profile(patch)
    return {"ok": True, "profile": STORE.profile}


@app.get("/api/mobile/memory")
async def mobile_memory(limit: int = 50):
    n = max(1, min(limit, 120))
    return {"items": list(STORE.memories)[:n]}


@app.delete("/api/mobile/memory/{idx}")
async def mobile_memory_delete(idx: int):
    items = list(STORE.memories)
    if idx < 0 or idx >= len(items):
        raise HTTPException(status_code=404, detail="memory not found")
    removed = items.pop(idx)
    STORE.memories = deque(items, maxlen=STORE.memories.maxlen)
    STORE.add_timeline("memory", f"删除记忆: {removed.get('summary','')[:32]}")
    return {"ok": True}


@app.get("/api/mobile/latest")
async def mobile_latest():
    return {"result": STORE.last_result, "at": STORE.last_analyze_at}


# ─── Companion Chat API ─────────────────────────────────────────────────────

@app.post("/api/chat")
async def api_chat(body: ChatBody):
    """REST 方式的聊天接口"""
    user_msg = body.message.strip()
    if not user_msg:
        raise HTTPException(status_code=400, detail="消息不能为空")

    conversation_mgr.add_message("user", user_msg)
    proactive_engine.record_interaction()

    memory_ctx = companion_memory.get_context_for_chat()
    history = conversation_mgr.get_context()

    result = await asyncio.to_thread(
        chat_response,
        user_msg,
        history[:-1],  # 不含刚加的 user message（LLM需要的是历史）
        memory_context=memory_ctx,
    )

    # 存储助手回复
    conversation_mgr.add_message("assistant", result["response"])

    # 处理记忆
    for mem in result.get("memories_to_add", []):
        companion_memory.add_memory(
            content=mem.get("content", ""),
            category=mem.get("category", "facts"),
            importance=mem.get("importance", 0.5),
            source="conversation",
        )

    # 处理提醒
    for rem in result.get("reminders_to_create", []):
        reminder_engine.create_reminder(
            text=rem.get("text", ""),
            time_text=rem.get("time_text", ""),
        )

    # 记录情绪
    proactive_engine.record_mood(result.get("detected_mood", "neutral"))

    return result


# ─── Memory API ──────────────────────────────────────────────────────────────

@app.get("/api/memories")
async def api_memories(category: str = "", query: str = "", limit: int = 50):
    return {"items": companion_memory.search(query=query, category=category, limit=limit)}


@app.post("/api/memories")
async def api_memories_create(body: MemoryCreateBody):
    entry = companion_memory.add_memory(
        content=body.content,
        category=body.category,
        importance=body.importance,
        source="manual",
    )
    return {"ok": True, "memory": entry}


@app.delete("/api/memories/{memory_id}")
async def api_memories_delete(memory_id: str):
    ok = companion_memory.delete(memory_id)
    if not ok:
        raise HTTPException(status_code=404, detail="记忆不存在")
    return {"ok": True}


# ─── Reminder API ────────────────────────────────────────────────────────────

@app.get("/api/reminders")
async def api_reminders(status: str = ""):
    if status == "active":
        return {"items": reminder_engine.get_active()}
    return {"items": reminder_engine.get_all()}


@app.post("/api/reminders")
async def api_reminders_create(body: ReminderCreateBody):
    entry = reminder_engine.create_reminder(
        text=body.text,
        time_text=body.time_text,
        category=body.category,
    )
    return {"ok": True, "reminder": entry}


@app.put("/api/reminders/{reminder_id}")
async def api_reminders_update(reminder_id: str, body: ReminderUpdateBody):
    updates = {k: v for k, v in body.model_dump().items() if v is not None}
    if "time_text" in updates and updates["time_text"]:
        trigger = parse_natural_time(updates.pop("time_text"))
        if trigger:
            updates["trigger_time"] = trigger.isoformat()
    result = reminder_engine.update(reminder_id, updates)
    if not result:
        raise HTTPException(status_code=404, detail="提醒不存在")
    return {"ok": True, "reminder": result}


@app.delete("/api/reminders/{reminder_id}")
async def api_reminders_delete(reminder_id: str):
    ok = reminder_engine.delete(reminder_id)
    if not ok:
        raise HTTPException(status_code=404, detail="提醒不存在")
    return {"ok": True}


@app.post("/api/reminders/check")
async def api_reminders_check():
    due = reminder_engine.check_due()
    return {"due": due}


# ─── Stats & Proactive ──────────────────────────────────────────────────────

@app.get("/api/stats")
async def api_stats():
    return {
        "memory": companion_memory.get_statistics(),
        "reminders": {
            "total": len(reminder_engine.reminders),
            "active": len(reminder_engine.get_active()),
        },
        "proactive": proactive_engine.get_status(),
        "conversation": {
            "total_messages": len(conversation_mgr.history),
            "session_start": conversation_mgr.history[0]["timestamp"] if conversation_mgr.history else None,
        },
        "profile": STORE.profile,
    }


@app.get("/api/proactive/status")
async def api_proactive_status():
    return proactive_engine.get_status()


# ─── 后台任务：提醒检查 ──────────────────────────────────────────────────────

async def reminder_check_loop():
    """每30秒检查一次到期提醒"""
    while True:
        await asyncio.sleep(30)
        try:
            due = reminder_engine.check_due()
            for r in due:
                await push_to_ws({
                    "type": "reminder_due",
                    "reminder": r,
                    "message": f"⏰ 提醒：{r['text']}",
                })
        except Exception as e:
            logger.error(f"提醒检查失败: {e}")


@app.on_event("startup")
async def startup_event():
    asyncio.create_task(reminder_check_loop())


# ─── WebSocket 端点 ────────────────────────────────────────────────────────────

THROTTLE_SEC = float(os.environ.get("ANALYZE_THROTTLE_SEC", "1.5"))
MAX_IMAGE_BYTES = int(os.environ.get("MAX_IMAGE_BYTES", str(5 * 1024 * 1024)))


class NexusSession:
    MAX_MEMORY = 30

    def __init__(self):
        self.memory: Deque[Dict] = deque(maxlen=self.MAX_MEMORY)
        self.user_profile: Dict[str, Any] = dict(STORE.profile)
        self.event_log: List[Dict] = []
        self.analyze_count = 0
        self.session_start = datetime.now().isoformat()

    def add_memory(self, event: Dict) -> None:
        entry = {
            "time": datetime.now().strftime("%H:%M:%S"),
            "summary": event.get("event_summary", ""),
            "importance": event.get("importance", 0),
        }
        if entry["summary"]:
            self.memory.append(entry)

    def add_log(self, event_type: str, detail: str) -> None:
        self.event_log.append({
            "ts": datetime.now().strftime("%H:%M:%S"),
            "type": event_type,
            "detail": detail,
        })
        if len(self.event_log) > 200:
            self.event_log = self.event_log[-200:]

    def update_profile(self, hint: str) -> None:
        if hint and hint not in self.user_profile.get("learned_habits", []):
            habits = self.user_profile.setdefault("learned_habits", [])
            habits.append(hint)
            if len(habits) > 20:
                self.user_profile["learned_habits"] = habits[-20:]

    def to_dict(self) -> Dict:
        return {
            "profile": self.user_profile,
            "memory_count": len(self.memory),
            "memories": list(self.memory),
            "analyze_count": self.analyze_count,
            "session_start": self.session_start,
        }


@app.websocket("/ws")
async def ws_nexus(websocket: WebSocket):
    global active_ws
    await websocket.accept()
    active_ws = websocket
    session = NexusSession()
    last_analyze = 0.0

    logger.info("新 WebSocket 连接建立")
    session.add_log("system", "Evans 会话已启动")

    # 发送初始状态
    await websocket.send_json({
        "type": "session_init",
        "data": session.to_dict(),
        "stats": {
            "memory": companion_memory.get_statistics(),
            "reminders": {
                "total": len(reminder_engine.reminders),
                "active": len(reminder_engine.get_active()),
            },
        },
        "memories": companion_memory.get_recent(20),
        "reminders_list": reminder_engine.get_active(),
        "history": conversation_mgr.get_history(30),
    })

    try:
        while True:
            msg = await websocket.receive_json()
            mtype = msg.get("type")

            # ── ping ──
            if mtype == "ping":
                await websocket.send_json({"type": "pong", "t": time.time()})
                continue

            # ── 更新用户画像 ──
            if mtype == "update_profile":
                profile_data = msg.get("profile", {})
                session.user_profile.update(profile_data)
                STORE.apply_profile(profile_data)
                session.add_log("profile", f"用户画像已更新: {list(profile_data.keys())}")
                await websocket.send_json({"type": "profile_updated", "profile": session.user_profile})
                continue

            # ── 聊天消息 ──
            if mtype == "chat":
                user_text = (msg.get("text") or "").strip()
                if not user_text:
                    continue

                conversation_mgr.add_message("user", user_text)
                proactive_engine.record_interaction()

                await websocket.send_json({"type": "typing"})

                memory_ctx = companion_memory.get_context_for_chat()
                history = conversation_mgr.get_context(limit=10)

                result = await asyncio.wait_for(
                    asyncio.to_thread(
                        chat_response,
                        user_text,
                        history[:-1],
                        memory_context=memory_ctx,
                    ),
                    timeout=60.0,
                )

                conversation_mgr.add_message("assistant", result["response"])

                # 处理记忆
                new_memories = []
                for mem in result.get("memories_to_add", []):
                    entry = companion_memory.add_memory(
                        content=mem.get("content", ""),
                        category=mem.get("category", "facts"),
                        importance=mem.get("importance", 0.5),
                        source="conversation",
                    )
                    new_memories.append(entry)

                    # 也提取一下启发式记忆
                heuristic = companion_memory.extract_from_text(user_text)
                for h in heuristic:
                    entry = companion_memory.add_memory(**h, source="heuristic")
                    new_memories.append(entry)

                # 处理提醒
                new_reminders = []
                for rem in result.get("reminders_to_create", []):
                    entry = reminder_engine.create_reminder(
                        text=rem.get("text", ""),
                        time_text=rem.get("time_text", ""),
                    )
                    new_reminders.append(entry)

                # 启发式提醒提取
                rem_hint = reminder_engine.extract_from_text(user_text)
                if rem_hint:
                    entry = reminder_engine.create_reminder(**rem_hint)
                    new_reminders.append(entry)

                proactive_engine.record_mood(result.get("detected_mood", "neutral"))

                await websocket.send_json({
                    "type": "chat_response",
                    "response": result["response"],
                    "detected_mood": result.get("detected_mood", "neutral"),
                    "new_memories": new_memories,
                    "new_reminders": new_reminders,
                    "stats": {
                        "memory": companion_memory.get_statistics(),
                        "reminders": {
                            "total": len(reminder_engine.reminders),
                            "active": len(reminder_engine.get_active()),
                        },
                    },
                })
                continue

            # ── 图像分析请求 ──
            if mtype != "analyze":
                await websocket.send_json({"type": "error", "message": f"未知消息类型: {mtype}"})
                continue

            force = bool(msg.get("force"))
            now = time.time()
            if not force and now - last_analyze < THROTTLE_SEC:
                wait_ms = int((THROTTLE_SEC - (now - last_analyze)) * 1000)
                await websocket.send_json({"type": "throttle", "retry_after_ms": max(wait_ms, 50)})
                continue

            b64 = msg.get("image_base64") or ""
            if "," in b64:
                b64 = b64.split(",", 1)[1]
            try:
                raw_bytes = base64.b64decode(b64)
            except Exception as e:
                await websocket.send_json({"type": "error", "message": f"图片解码失败: {e}"})
                continue

            if len(raw_bytes) > MAX_IMAGE_BYTES:
                await websocket.send_json({"type": "error", "message": "图片过大"})
                continue

            user_text = (msg.get("text") or "").strip()
            sensors = msg.get("sensors") or {}

            last_analyze = time.time()
            session.analyze_count += 1

            session.add_log("analyze", f"第{session.analyze_count}次分析")

            await websocket.send_json({
                "type": "analyzing",
                "count": session.analyze_count,
                "ts": datetime.now().strftime("%H:%M:%S"),
            })

            try:
                data = await asyncio.wait_for(
                    asyncio.to_thread(
                        analyze_frame_jpeg,
                        raw_bytes,
                        user_text,
                        sensors=sensors,
                        session_memory=list(session.memory),
                        user_profile=session.user_profile,
                    ),
                    timeout=90.0,
                )

                mem_update = data.get("memory_update", {})
                if mem_update.get("should_record"):
                    session.add_memory(mem_update)
                    session.add_log("memory", f"记录事件: {mem_update.get('event_summary','')[:50]}")

                profile_hint = mem_update.get("profile_hint", "")
                if profile_hint:
                    session.update_profile(profile_hint)
                    session.add_log("learn", f"学习到用户习惯: {profile_hint[:50]}")

                exec_layer = data.get("layer6_execution", {})
                for cmd in exec_layer.get("device_commands", []):
                    session.add_log("device", f"指令→{cmd.get('device_id','?')}: {cmd.get('action','?')}")

                decision = data.get("layer4_decision", {})
                if decision.get("should_intervene"):
                    session.add_log("decision", f"主动介入: {decision.get('task_plan','')[:60]}")

                await websocket.send_json({
                    "type": "result",
                    "ok": True,
                    "data": data,
                    "session": session.to_dict(),
                    "log": session.event_log[-50:],
                })
                STORE.apply_analysis(data)

            except asyncio.TimeoutError:
                session.add_log("error", "AI分析超时(>90s)")
                await websocket.send_json({"type": "error", "message": "AI分析超时（>90s），请稍后重试"})
            except Exception as e:
                logger.exception("分析失败")
                session.add_log("error", str(e)[:100])
                await websocket.send_json({"type": "error", "message": str(e)})

    except WebSocketDisconnect:
        logger.info("WebSocket 断开，共分析 %d 次", session.analyze_count)
        if active_ws == websocket:
            active_ws = None
    except Exception as e:
        logger.exception("WebSocket 异常: %s", e)
        if active_ws == websocket:
            active_ws = None
