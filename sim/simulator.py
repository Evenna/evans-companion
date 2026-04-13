"""
虚拟用户模拟器 - 林小晴的一天
完全独立运行，有自己的记忆和思考上下文
与 Evans 的交互通过 REST API / WebSocket 进行
"""
import asyncio
import json
import random
import time
from datetime import datetime, timedelta
from pathlib import Path
import os
import sys

# 加载虚拟用户档案
PROFILE_FILE = Path(__file__).parent / "virtual_user_profile.json"
with open(PROFILE_FILE, "r", encoding="utf-8") as f:
    PROFILE = json.load(f)

# Evans API 地址
EVANS_BASE = os.environ.get("EVANS_BASE", "http://127.0.0.1:8080")

# ─── 虚拟用户记忆（独立于 Evans） ──────────────────────────────

class VirtualMind:
    """虚拟用户的'大脑'，完全独立"""
    
    def __init__(self, profile):
        self.profile = profile
        self.short_term: list = []   # 当天短期记忆
        self.questions_asked: list = []  # 问过 Evans 的问题
        self.mood = "normal"
        self.energy = 80  # 精力值 0-100
        
    def think(self, prompt: str) -> str:
        """
        模拟用户思考：给定一个情境，生成用户可能的反应/回复
        这是虚拟用户的"内心独白"，不对 Evans 暴露
        """
        # 简化版：基于情绪和能量生成随机延迟表示"思考"
        think_delay = random.uniform(0.5, 2.0)
        time.sleep(think_delay)
        return ""
    
    def get_mood_context(self) -> str:
        """当前情绪上下文"""
        return f"情绪状态: {self.mood}，精力: {self.energy}/100"
    
    def decide_to_interact(self, context: str) -> bool:
        """决定是否要和 Evans 互动"""
        # 基于精力和情境决定
        if self.energy < 20:
            return random.random() < 0.1  # 太累很少互动
        if "工作压力大" in context or "焦虑" in self.mood:
            return random.random() < 0.7  # 压力大更想倾诉
        return random.random() < 0.4


# ─── 一天的时间线 ────────────────────────────────────────────

DAILY_SCENARIOS = [
    {
        "time": "07:30",
        "situation": "起床",
        "context": "刚睡醒，有点迷糊，昨晚熬夜了",
        "mood_before": "tired",
        "energy_delta": +10,
        "possible_actions": [
            ("text", "早上好呀，今天好困…昨晚追剧追太晚了"),
            ("text", "Evans，帮我看看今天天气怎么样"),
            ("text", "我今天嗓子有点不舒服"),
        ]
    },
    {
        "time": "07:50",
        "situation": "吃早餐",
        "context": "随便吃了点麦片，想起应该吃点有营养的",
        "mood_before": "neutral",
        "energy_delta": +5,
        "possible_actions": [
            ("text", "Evans，我早餐就吃了麦片，是不是不太够？"),
            ("text", "帮我记一下，我今天早餐只吃了麦片"),
        ]
    },
    {
        "time": "08:25",
        "situation": "出门上班",
        "context": "赶地铁，有点焦虑会不会迟到",
        "mood_before": "anxious",
        "energy_delta": -10,
        "possible_actions": [
            ("text", "Evans，我马上要迟到了，好焦虑"),
            ("text", "帮我设个提醒，下午3点要开评审会"),
        ]
    },
    {
        "time": "09:45",
        "situation": "到公司开始工作",
        "context": "看到待办清单很多，有点压力",
        "mood_before": "anxious",
        "energy_delta": -5,
        "possible_actions": [
            ("text", "Evans，我工作好多啊，想摆烂"),
            ("text", "帮我记一下：本周五之前要完成新功能需求文档"),
        ]
    },
    {
        "time": "11:30",
        "situation": "处理完一个任务",
        "context": "搞定了一个难题，有点开心",
        "mood_before": "happy",
        "energy_delta": +5,
        "possible_actions": [
            ("text", "Evans！我刚搞定了一个超难的需求评审，老板居然通过了！"),
            ("mood", "开心，想吃点好的奖励自己"),
        ]
    },
    {
        "time": "12:15",
        "situation": "午饭",
        "context": "和同事点外卖，在讨论吃什么",
        "mood_before": "neutral",
        "energy_delta": +15,
        "possible_actions": [
            ("text", "Evans，我和同事在纠结午饭吃什么，帮我选：麻辣香锅还是沙拉？"),
            ("text", "Evans，附近有什么好吃的不？"),
        ]
    },
    {
        "time": "14:00",
        "situation": "开会中",
        "context": "开了2小时会，很累，注意力涣散",
        "mood_before": "tired",
        "energy_delta": -15,
        "possible_actions": [
            ("text", "Evans，开会开得我头都大了…"),
            ("text", "Evans，有什么提神的方法吗"),
        ]
    },
    {
        "time": "15:00",
        "situation": "评审会",
        "context": "要给领导汇报，有点紧张",
        "mood_before": "anxious",
        "energy_delta": -5,
        "possible_actions": [
            ("text", "Evans，等下要给总监汇报，好紧张…"),
            ("text", "Evans，帮我整理一下刚才说的重点，我怕待会忘了"),
        ]
    },
    {
        "time": "16:30",
        "situation": "评审结束",
        "context": "汇报顺利，领导认可了",
        "mood_before": "happy",
        "energy_delta": +10,
        "possible_actions": [
            ("text", "Evans！汇报通过了！总监说方案很清晰！"),
            ("mood", "开心，想下班去吃顿好的"),
        ]
    },
    {
        "time": "18:45",
        "situation": "下班路上",
        "context": "还在地铁上，想锻炼但又很累",
        "mood_before": "neutral",
        "energy_delta": -5,
        "possible_actions": [
            ("text", "Evans，我今天不想去健身房了…"),
            ("text", "Evans，今天跑了3公里，感觉还不错"),
            ("mood", "纠结要不要去健身房"),
        ]
    },
    {
        "time": "19:30",
        "situation": "吃晚饭",
        "context": "随便吃了点，突然想喝奶茶",
        "mood_before": "neutral",
        "energy_delta": +5,
        "possible_actions": [
            ("text", "Evans，我好想喝奶茶…但又在减肥，好纠结"),
            ("text", "Evans，帮我记一下今晚吃了酸辣粉"),
        ]
    },
    {
        "time": "21:00",
        "situation": "在家放松",
        "context": "躺在沙发上刷手机，想起了前几天的事",
        "mood_before": "relaxed",
        "energy_delta": +10,
        "possible_actions": [
            ("text", "Evans，我突然想起来，我好像答应闺蜜下周末去逛街的"),
            ("text", "Evans，你还记得我说过想吃火锅吗？"),
            ("text", "Evans，跟我说说话呗，有点无聊"),
        ]
    },
    {
        "time": "22:15",
        "situation": "准备睡觉",
        "context": "洗漱完躺床上，想了想明天的工作",
        "mood_before": "anxious",
        "energy_delta": -10,
        "possible_actions": [
            ("text", "Evans，帮我设个闹钟，明天早上8点"),
            ("text", "Evans，帮我记一下明天要做的事：1. 整理周报 2. 回复客户邮件 3. 跟进设计方案"),
            ("text", "Evans，我最近老是很焦虑睡不好，是不是应该去看看医生"),
        ]
    },
]


# ─── 交互执行器 ──────────────────────────────────────────────

import requests


def send_to_evans(text: str) -> dict:
    """向 Evans 发送消息并获取回复"""
    try:
        resp = requests.post(
            f"{EVANS_BASE}/api/chat",
            json={"message": text},
            timeout=30
        )
        if resp.ok:
            return {"ok": True, "response": resp.json()}
        return {"ok": False, "error": f"{resp.status_code} {resp.reason}"}
    except Exception as e:
        return {"ok": False, "error": str(e)}


def send_mood_to_evans(mood: str) -> dict:
    """发送心情记录"""
    return send_to_evans(f"我现在心情怎么样？")


def print_divider(label: str):
    print(f"\n{'='*60}")
    print(f"  🕐 {label}")
    print('='*60)


def print_interaction(scenario: dict, action: tuple, evans_reply: dict):
    print(f"\n📍 场景: {scenario['situation']} ({scenario['time']})")
    print(f"   情绪: {scenario['mood_before']} | 精力: ", end="")
    
    if action[0] == "mood":
        print(f"→ 心情记录: {action[1]}")
        return
    
    print(f"→ {action[1][:50]}...")
    
    if evans_reply.get("ok"):
        r = evans_reply["response"]
        print(f"\n💬 林小晴: {action[1]}")
        print(f"💙 Evans: {r.get('response', '(无回复)')[:200]}")
        
        # 显示记忆/提醒创建情况
        memories = r.get("memories_to_add", [])
        reminders = r.get("reminders_to_create", [])
        if memories:
            print(f"   📝 Evans 记住了: {[m['content'] for m in memories]}")
        if reminders:
            print(f"   ⏰ Evans 要提醒: {[rem['text'] for rem in reminders]}")
    else:
        print(f"   ❌ 发送失败: {evans_reply.get('error')}")


# ─── 主模拟循环 ──────────────────────────────────────────────

def run_simulation():
    print("""
    ╔══════════════════════════════════════════╗
    ║   🌙 虚拟用户模拟 - 林小晴的一天        ║
    ║   林小晴: 28岁产品经理，北京独居        ║
    ║   Evans: AI 伴侣，部署在 VPS            ║
    ╚══════════════════════════════════════════╝
    """)
    
    print(f"📱 Evans API: {EVANS_BASE}")
    print(f"👤 虚拟用户: {PROFILE['name']}，{PROFILE['age']}岁，{PROFILE['occupation']}")
    print(f"😴 睡眠时间: {PROFILE['daily_schedule']['sleep']} | 🏃 运动目标: {PROFILE['preferences']['hobbies']}")
    
    # 测试 Evans 是否在线
    try:
        resp = requests.get(f"{EVANS_BASE}/api/stats", timeout=5)
        if resp.ok:
            print(f"✅ Evans 在线！记忆数: {resp.json().get('memory', {}).get('total', '?')}")
        else:
            print(f"⚠️ Evans 响应异常: {resp.status_code}")
    except Exception as e:
        print(f"❌ Evans 不在线: {e}")
        print("请确保 Evans 服务正在运行: cd evans-companion && uv run uvicorn server:app --port 8080")
        return
    
    input("\n按回车开始模拟一天... (Ctrl+C 退出)")
    
    mind = VirtualMind(PROFILE)
    
    for i, scenario in enumerate(DAILY_SCENARIOS):
        # 打印当前场景
        print_divider(f"{scenario['time']} - {scenario['situation']}")
        print(f"   情境: {scenario['context']}")
        print(f"   情绪: {scenario['mood_before']} → 精力变化: {scenario['energy_delta']:+d}")
        
        # 更新虚拟用户状态
        mind.mood = scenario["mood_before"]
        mind.energy = max(0, min(100, mind.energy + scenario["energy_delta"]))
        
        # 决定是否互动
        if not mind.decide_to_interact(scenario["context"]):
            print(f"   💭 林小晴选择不打扰，自己处理了")
            time.sleep(1)
            continue
        
        # 随机选择一个动作
        action = random.choice(scenario["possible_actions"])
        
        # 执行交互
        if action[0] == "text":
            evans_reply = send_to_evans(action[1])
        elif action[0] == "mood":
            evans_reply = send_mood_to_evans(action[1])
        else:
            continue
        
        print_interaction(scenario, action, evans_reply)
        
        # 模拟思考/停顿
        time.sleep(random.uniform(1, 2))
    
    # 一天结束总结
    print_divider("一天结束 - 23:30")
    print(f"""
    🌙 林小晴准备睡觉了
    📊 今日统计:
       - 向 Evans 提问: {len(mind.questions_asked)} 次
       - 最终情绪: {mind.mood}
       - 精力水平: {mind.energy}/100
    💭 感想: 今天过得挺充实的，工作有进展，
       但还是有点焦虑睡眠问题...
    """)


if __name__ == "__main__":
    run_simulation()
