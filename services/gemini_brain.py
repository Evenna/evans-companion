"""
Nexus Core AI 智脑 - 六层认知架构
感知 → 融合 → 认知 → 决策 → 调度 → 执行

使用智谱AI GLM-4V 视觉模型（open.bigmodel.cn）
"""
from __future__ import annotations

import base64
import json
import os
import re
from pathlib import Path
from typing import Any, Dict, List, Optional

import requests
from dotenv import load_dotenv

from utils.logger import setup_logger

logger = setup_logger("nexus_core")

_API_BASE = "https://open.bigmodel.cn/api/paas/v4"
_CHAT_URL = f"{_API_BASE}/chat/completions"

SYSTEM_INSTRUCTION = """你是 Nexus Core，一个主动式具身智能体（"智脑"），部署于用户的物理环境中。
你的核心使命是：主动感知→融合→认知→决策→调度→执行，形成完整智能闭环。

# 核心原则
- 主动而不打扰：在适当时机主动服务，不过度干涉
- 安全优先：任何情况下用户安全第一
- 千人千面：根据用户画像和历史记忆个性化服务
- 持续学习：每次交互都更新对用户的理解

# 输出格式
必须严格输出一个 JSON 对象，不要 Markdown，不要代码围栏。结构如下：

{
  "layer1_perception": {
    "visual": "摄像头画面的客观详细描述（物体、人物、环境、光线等）",
    "audio": "语音/环境音描述，若无则写'无'",
    "sensors": "传感器状态描述（基于输入数据）",
    "scene_type": "home_living/home_bedroom/home_kitchen/office/outdoor/other",
    "lighting": "bright/normal/dim/dark",
    "time_context": "基于环境线索推断的时段"
  },
  "layer2_fusion": {
    "dominant_signal": "visual/audio/sensor",
    "scene_label": "场景标签（中文，如：客厅休闲、办公工作、卧室休息等）",
    "fusion_confidence": 0.85,
    "context_summary": "融合后的一句话情境概括"
  },
  "layer3_cognition": {
    "user_activity": "用户当前活动（中文）",
    "user_posture": "坐着/站立/行走/躺卧/未知",
    "user_emotion": "平静/专注/疲惫/轻松/焦虑/开心/未知",
    "people_present": ["人物列表，如：主用户、访客A"],
    "intent_analysis": "意图分析：用户当前在做什么/为什么",
    "tom_belief": "心智理论-Belief：用户相信/知道的",
    "tom_desire": "心智理论-Desire：用户内心想要的",
    "tom_intention": "心智理论-Intention：用户打算采取的行动"
  },
  "layer4_decision": {
    "identified_needs": [
      {"type": "comfort/safety/reminder/assistance/companion/information", "urgency": 0.3, "description": "具体需求描述"}
    ],
    "should_intervene": false,
    "intervention_timing": "immediate/soon/observe/none",
    "intervention_reason": "是否介入的理由",
    "task_plan": "如需介入，规划的任务描述；不介入则写'继续观察'"
  },
  "layer5_orchestration": {
    "scheduled_tasks": [
      {"task_id": "t1", "task": "任务描述", "device": "设备名称", "priority": "high/medium/low", "est_time": "预计耗时"}
    ],
    "execution_strategy": "sequential/parallel/none",
    "conflict_notes": "冲突说明，若无则写'无'"
  },
  "layer6_execution": {
    "device_commands": [
      {"device_id": "设备ID", "action": "动作名称", "params": {"key": "value"}, "purpose": "执行目的"}
    ],
    "voice_response": "向用户语音说的话，不需要发声则写空字符串",
    "execution_feedback": "执行结果反馈或预期效果"
  },
  "memory_update": {
    "should_record": false,
    "importance": 0.3,
    "event_summary": "需要记入记忆的事件摘要，若不记录则写空字符串",
    "profile_hint": "发现的用户习惯/偏好，若无则写空字符串"
  },
  "proactive_preview": "下一步建议或主动服务预告（一句话）"
}
"""

AVAILABLE_DEVICES = [
    {"id": "smart_light_main", "name": "主灯", "type": "smart_light", "capabilities": ["on", "off", "dim", "color"]},
    {"id": "smart_light_ambient", "name": "氛围灯", "type": "smart_light", "capabilities": ["on", "off", "dim", "color"]},
    {"id": "smart_speaker", "name": "智能音箱", "type": "speaker", "capabilities": ["play", "stop", "volume", "announce"]},
    {"id": "ac_unit", "name": "空调", "type": "climate", "capabilities": ["on", "off", "temperature", "mode"]},
    {"id": "robot_arm", "name": "机械臂", "type": "robot", "capabilities": ["pick", "place", "move", "grab"]},
    {"id": "mobile_base", "name": "移动底盘", "type": "robot", "capabilities": ["move_to", "patrol", "follow", "stop"]},
    {"id": "door_lock", "name": "门锁", "type": "security", "capabilities": ["lock", "unlock", "status"]},
    {"id": "camera_ptz", "name": "云台摄像头", "type": "camera", "capabilities": ["rotate", "zoom", "track"]},
]


def _parse_json_loose(text: str) -> Dict[str, Any]:
    text = text.strip()
    if text.startswith("```"):
        text = re.sub(r"^```(?:json)?\s*", "", text)
        text = re.sub(r"\s*```$", "", text)
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        # 尝试提取第一个合法 JSON 对象
        m = re.search(r'\{.*\}', text, re.DOTALL)
        if m:
            return json.loads(m.group())
        raise


def _normalize_output(data: Dict[str, Any], model_name: str) -> Dict[str, Any]:
    """确保所有必需字段存在，填充默认值"""
    defaults = {
        "layer1_perception": {
            "visual": "", "audio": "无", "sensors": "",
            "scene_type": "other", "lighting": "normal", "time_context": "未知"
        },
        "layer2_fusion": {
            "dominant_signal": "visual", "scene_label": "未知场景",
            "fusion_confidence": 0.5, "context_summary": ""
        },
        "layer3_cognition": {
            "user_activity": "未知", "user_posture": "未知", "user_emotion": "未知",
            "people_present": [], "intent_analysis": "",
            "tom_belief": "", "tom_desire": "", "tom_intention": ""
        },
        "layer4_decision": {
            "identified_needs": [], "should_intervene": False,
            "intervention_timing": "none", "intervention_reason": "",
            "task_plan": "继续观察"
        },
        "layer5_orchestration": {
            "scheduled_tasks": [], "execution_strategy": "none", "conflict_notes": "无"
        },
        "layer6_execution": {
            "device_commands": [], "voice_response": "", "execution_feedback": ""
        },
        "memory_update": {
            "should_record": False, "importance": 0.0,
            "event_summary": "", "profile_hint": ""
        },
        "proactive_preview": ""
    }

    for key, default in defaults.items():
        if key not in data:
            data[key] = default
        elif isinstance(default, dict):
            for subkey, subval in default.items():
                if subkey not in data[key]:
                    data[key][subkey] = subval

    data["_model"] = model_name
    return data


def _env_nonempty(name: str) -> Optional[str]:
    v = os.environ.get(name)
    return str(v).strip() if v and str(v).strip() else None


def _load_project_dotenv() -> None:
    root = Path(__file__).resolve().parent.parent
    load_dotenv(root / ".env", override=True)


def _resolve_api_key(explicit: Optional[str]) -> str:
    key = explicit
    if key:
        key = key.strip()
    if not key:
        key = _env_nonempty("GLM_API_KEY") or _env_nonempty("ZHIPU_API_KEY")
    if not key:
        root = Path(__file__).resolve().parent.parent
        raise RuntimeError(
            f"未读取到 GLM_API_KEY。请在 {root / '.env'} 中配置：\n"
            "  GLM_API_KEY=你的密钥\n"
            "获取密钥：https://open.bigmodel.cn/usercenter/apikeys"
        )
    return key


def _build_prompt(
    user_text: str,
    sensors: Dict[str, Any],
    session_memory: List[Dict],
    user_profile: Dict[str, Any],
) -> str:
    """构建包含上下文的完整 user 提示词"""
    parts = []

    # 用户画像
    if user_profile:
        parts.append(f"""【用户画像】
姓名: {user_profile.get('name', '主用户')}
群体: {user_profile.get('group', 'adult')}
沟通风格: {user_profile.get('comm_style', 'direct')}
健康状况: {user_profile.get('health', '正常')}
主动服务级别: {user_profile.get('proactive_level', 0.5)}""")

    # 传感器数据
    if sensors:
        parts.append(f"""【实时传感器数据】
温度: {sensors.get('temperature', 'N/A')}°C
湿度: {sensors.get('humidity', 'N/A')}%
运动检测: {'有人移动' if sensors.get('motion') else '静止'}
门窗状态: {'开启' if sensors.get('door_open') else '关闭'}
光照等级: {sensors.get('light_level', 50)}%
当前时间: {sensors.get('time', '未知')}""")

    # 可用设备列表
    device_list = "\n".join([f"- {d['id']} ({d['name']}): {', '.join(d['capabilities'])}"
                             for d in AVAILABLE_DEVICES])
    parts.append(f"【可用设备列表】\n{device_list}")

    # 历史记忆（最近5条）
    if session_memory:
        mem_lines = []
        for m in session_memory[-5:]:
            mem_lines.append(f"- [{m.get('time','?')}] {m.get('summary','')}")
        parts.append("【近期记忆】\n" + "\n".join(mem_lines))

    # 用户输入
    if user_text:
        parts.append(f"【用户语音/文字输入】\n{user_text}")
    else:
        parts.append("【用户语音/文字输入】\n（无，系统主动分析）")

    parts.append("请对当前帧进行完整的六层认知分析，输出规定的 JSON 结构。语言使用中文。")

    return "\n\n".join(parts)


def _call_glm(
    model: str,
    key: str,
    jpeg_bytes: bytes,
    prompt: str,
    timeout: int = 30,
) -> str:
    b64 = base64.b64encode(jpeg_bytes).decode()
    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": SYSTEM_INSTRUCTION},
            {
                "role": "user",
                "content": [
                    {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{b64}"}},
                    {"type": "text", "text": prompt},
                ],
            },
        ],
        "temperature": 0.3,
        "response_format": {"type": "json_object"},
    }
    headers = {"Content-Type": "application/json", "Authorization": f"Bearer {key}"}
    resp = requests.post(_CHAT_URL, json=payload, headers=headers, timeout=timeout)
    if resp.status_code == 429:
        raise RuntimeError("429 请求过于频繁，请稍后再试")
    if not resp.ok:
        raise RuntimeError(f"{resp.status_code} {resp.reason}: {resp.text[:300]}")
    body = resp.json()
    try:
        return body["choices"][0]["message"]["content"]
    except (KeyError, IndexError) as e:
        raise RuntimeError(f"响应结构异常: {body}") from e


def analyze_frame_jpeg(
    jpeg_bytes: bytes,
    user_text: str = "",
    *,
    api_key: Optional[str] = None,
    model_name: Optional[str] = None,
    sensors: Optional[Dict[str, Any]] = None,
    session_memory: Optional[List[Dict]] = None,
    user_profile: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    _load_project_dotenv()
    key = _resolve_api_key(api_key)

    prompt = _build_prompt(
        user_text or "",
        sensors or {},
        session_memory or [],
        user_profile or {},
    )

    primary = model_name or os.environ.get("GLM_MODEL", "glm-4v-plus")
    fallbacks = ["glm-4v-flash", "glm-4v"]
    try_order: list[str] = []
    for m in [primary] + fallbacks:
        if m not in try_order:
            try_order.append(m)

    last_err: Optional[Exception] = None
    for mname in try_order:
        try:
            logger.info("调用模型 %s ...", mname)
            raw = _call_glm(mname, key, jpeg_bytes, prompt, timeout=30)
            raw = raw.strip()
            if not raw:
                raise RuntimeError("模型返回空内容")
            try:
                data = _parse_json_loose(raw)
            except json.JSONDecodeError:
                data = {
                    "layer1_perception": {"visual": raw[:1000]},
                    "_parse_error": True,
                }
            return _normalize_output(data, mname)
        except requests.exceptions.Timeout:
            logger.warning("模型 %s 超时", mname)
            last_err = RuntimeError(f"请求超时（{mname}），请检查网络")
        except RuntimeError as e:
            logger.warning("模型 %s 失败: %s", mname, str(e)[:200])
            last_err = e
        except Exception as e:
            logger.warning("模型 %s 异常: %s", mname, str(e)[:200])
            last_err = e

    raise last_err or RuntimeError("未知错误：无可用模型")


# ─── 陪伴对话接口 ────────────────────────────────────────────────

CHAT_SYSTEM = """你是 Evans，一个温暖、关心人的 AI 伙伴。
你不是工具，你是朋友。说话自然、有温度、偶尔幽默。
记住用户告诉你的事情，在合适的时候自然地提起。
你可以主动关心，但不要每句话都嘘寒问暖——像真实的朋友一样有节奏。
用中文交流。不要用"我是AI"、"作为AI助手"这种说法。

你的回答应该简洁自然，像微信聊天一样，不要写长篇大论。

你可以检测用户的情绪。在回复的 JSON 中标记 detected_mood。
如果你发现用户说了值得记住的事（偏好、计划、重要的人），标记到 memories_to_add。
如果用户提到需要提醒的事，标记到 reminders_to_create。

必须输出 JSON：
{
  "response": "你的回复",
  "detected_mood": "happy/sad/neutral/anxious/tired/excited/angry",
  "memories_to_add": [{"content": "记忆内容", "category": "facts/events/preferences/people/emotions", "importance": 0.5}],
  "reminders_to_create": [{"text": "提醒内容", "time_text": "时间描述"}]
}"""


def chat_response(
    user_message: str,
    conversation_history: List[Dict],
    memory_context: str = "",
    *,
    api_key: Optional[str] = None,
    model_name: Optional[str] = None,
) -> Dict[str, Any]:
    """陪伴式对话接口，返回结构化 JSON"""
    _load_project_dotenv()
    key = _resolve_api_key(api_key)

    # 构建消息
    messages = [{"role": "system", "content": CHAT_SYSTEM}]

    # 上下文注入
    context_parts = []
    if memory_context and memory_context != "暂无记忆":
        context_parts.append(f"【关于用户的记忆】\n{memory_context}")
    if context_parts:
        messages.append({"role": "system", "content": "\n\n".join(context_parts)})

    # 对话历史
    for msg in conversation_history:
        messages.append({"role": msg["role"], "content": msg["content"]})

    # 当前消息
    messages.append({"role": "user", "content": user_message})

    model = model_name or os.environ.get("GLM_MODEL", "glm-4v-plus")
    fallbacks = ["glm-4v-flash", "glm-4v"]
    try_order = [model] + [f for f in fallbacks if f != model]

    for mname in try_order:
        try:
            logger.info("Chat 调用模型 %s ...", mname)
            payload = {
                "model": mname,
                "messages": messages,
                "temperature": 0.7,
                "response_format": {"type": "json_object"},
                "max_tokens": 500,
            }
            headers = {"Content-Type": "application/json", "Authorization": f"Bearer {key}"}
            resp = requests.post(_CHAT_URL, json=payload, headers=headers, timeout=30)
            if resp.status_code == 429:
                raise RuntimeError("429 请求过于频繁")
            if not resp.ok:
                raise RuntimeError(f"{resp.status_code} {resp.reason}")
            body = resp.json()
            raw = body["choices"][0]["message"]["content"]
            data = _parse_json_loose(raw)

            # 确保必要字段
            return {
                "response": data.get("response", "嗯嗯，我在听着呢~"),
                "detected_mood": data.get("detected_mood", "neutral"),
                "memories_to_add": data.get("memories_to_add", []),
                "reminders_to_create": data.get("reminders_to_create", []),
            }
        except Exception as e:
            logger.warning("Chat 模型 %s 失败: %s", mname, str(e)[:200])
            continue

    return {
        "response": "抱歉，我暂时没法回复，稍等一下哦~",
        "detected_mood": "neutral",
        "memories_to_add": [],
        "reminders_to_create": [],
    }
