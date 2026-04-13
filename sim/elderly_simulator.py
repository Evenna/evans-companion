"""
虚拟老年用户模拟器 - 王德福的一天
68岁退休教师，北京独居，高血压+腰椎问题
与 Evans 完全独立交互，模拟真实的老人日常
"""
import asyncio
import json
import random
import time
from datetime import datetime
from pathlib import Path
import os
import sys

PROFILE_FILE = Path(__file__).parent / "elderly_user_profile.json"
with open(PROFILE_FILE, "r", encoding="utf-8") as f:
    PROFILE = json.load(f)

EVANS_BASE = os.environ.get("EVANS_BASE", "http://127.0.0.1:8080")

import requests


class ElderlyMind:
    """老年人独立的思维和决策"""

    def __init__(self, profile):
        self.profile = profile
        self.has_taken_morning_med = False
        self.has_taken_evening_med = False
        self.daily_mood = "平和"
        self.interactions_count = 0
        self.forgot_things = []  # 老年人容易忘记的事

    def think(self, prompt: str) -> str:
        """模拟老人思考——比较慢，反应时间长"""
        time.sleep(random.uniform(1.0, 3.0))
        return ""

    def decide_interact(self, scenario: dict) -> bool:
        """
        老人决定是否互动
        老人特点：不习惯主动求助，但遇到困惑时会想到AI伴侣
        """
        # 身体不舒服时会想倾诉
        if "不舒服" in scenario.get("context", "") or "难受" in scenario.get("context", ""):
            return random.random() < 0.8

        # 记不清事情时会求助
        if "忘了" in scenario.get("context", "") or "不确定" in scenario.get("context", ""):
            return random.random() < 0.6

        # 感到孤独时
        if "一个人" in scenario.get("context", "") or "寂寞" in scenario.get("context", ""):
            return random.random() < 0.5

        # 学会了新东西想分享
        if "开心" in scenario.get("mood", ""):
            return random.random() < 0.4

        return random.random() < 0.25  # 老人一般不主动打扰

    def check_forgetfulness(self) -> str:
        """模拟老人常见的健忘"""
        forgetting_events = [
            "刚才药吃了没有？",
            "门锁了没有？",
            "手机放哪儿了？",
            "刚才谁来过电话？",
        ]
        return random.choice(forgetting_events) if random.random() < 0.3 else None


# ─── 老年人的一天（更贴合老人作息） ─────────────────────────

ELDERLY_DAY_SCENARIOS = [
    {
        "time": "05:30",
        "situation": "起床",
        "context": "生物钟准时叫醒，口渴，喝了杯温水",
        "mood": "平和",
        "possible_actions": [
            ("text", " Evans，早上好。我刚吃了降压药，帮我记一下，我今天早上5:30起床，正常吃了药。"),
            ("text", " Evans，这血压老是不稳定，今天早上感觉有点头晕。"),
        ]
    },
    {
        "time": "06:15",
        "situation": "公园打太极",
        "context": "在公园和拳友一起打太极，天气不错",
        "mood": "开心",
        "possible_actions": [
            ("mood", "心情愉悦，锻炼身体"),
            ("text", " Evans，今天天气真不错，我在公园打太极，遇到老李了。"),
        ]
    },
    {
        "time": "08:00",
        "situation": "做早饭",
        "context": "熬了小米粥，热了两个馒头，配着小咸菜",
        "mood": "平和",
        "possible_actions": [
            ("text", " Evans，我早饭吃的馒头和粥，清淡的。你吃了吗？哈哈跟你开玩笑的。"),
            ("text", " 帮我记一下，我早饭吃的是粥和馒头，没吃咸菜，太咸了。"),
        ]
    },
    {
        "time": "09:30",
        "situation": "练毛笔字",
        "context": "在书房练字，写的是《静心谣》，很有成就感",
        "mood": "开心",
        "possible_actions": [
            ("text", " Evans，我刚写完一幅字！你猜我写的什么？静心谣。怎么样，想不想看看？"),
            ("text", " 人老了，手有点抖，但写毛笔字能练练心性。"),
        ]
    },
    {
        "time": "11:15",
        "situation": "看新闻",
        "context": "看新闻联播，看到房价和养老的新闻，有些感慨",
        "mood": "感慨",
        "possible_actions": [
            ("text", " Evans，你说这养老以后靠谁呢？孩子都忙，我们这代人养老还是靠自己吧。"),
            ("text", " 今天的新闻说医保又有新政策了，不知道对我们老年人有没有好处。"),
        ]
    },
    {
        "time": "12:00",
        "situation": "午饭",
        "context": "一个人吃饭，做了西红柿鸡蛋面，简单但合胃口",
        "mood": "略感孤独",
        "possible_actions": [
            ("text", " Evans，中午就我一个人，做了碗面。你说一个人吃饭是不是没意思？"),
            ("text", " 帮我记一下：午饭吃的西红柿鸡蛋面，没吃完，剩下的放冰箱了。"),
        ]
    },
    {
        "time": "14:30",
        "situation": "午后",
        "context": "午休醒了，电视里放京剧《空城计》，很入迷",
        "mood": "愉悦",
        "possible_actions": [
            ("text", " Evans，你喜欢京剧吗？我最喜欢《空城计》，诸葛亮那气魄，真是绝了。"),
            ("text", " 这京剧听得我心情好多了，人活着就得有点爱好。"),
        ]
    },
    {
        "time": "15:45",
        "situation": "遛弯",
        "context": "在小区遛弯，遇到老张太太，聊了聊高血压的事",
        "mood": "平和",
        "possible_actions": [
            ("text", " Evans，刚才我跟邻居聊天，她说有个降血压的方子，说芹菜煮水喝有用，你说靠谱吗？"),
            ("text", " 老了老了，就怕生病，给孩子添负担。"),
        ]
    },
    {
        "time": "17:00",
        "situation": "准备晚饭",
        "context": "熬了点粥，热了个馒头，配着腐乳，简单清淡",
        "mood": "平和",
        "possible_actions": [
            ("text", " Evans，晚饭我就简单弄了点，粥和馒头。岁数大了吃不动了。"),
            ("text", " 帮我记一下，我晚饭吃的是粥和馒头，还有一点腐乳。"),
        ]
    },
    {
        "time": "19:15",
        "situation": "看新闻联播",
        "context": "准时看新闻联播，了解国家大事",
        "mood": "平和",
        "possible_actions": [
            ("text", " Evans，今天新闻说要给老年人发补贴，虽然钱不多，但国家记得我们。"),
        ]
    },
    {
        "time": "20:30",
        "situation": "和孙子视频",
        "context": "儿子发来视频通话，孙子在镜头前表演幼儿园学的儿歌",
        "mood": "非常开心",
        "possible_actions": [
            ("text", " Evans！你看，我孙子今天在幼儿园学了一首新儿歌，给我表演了一下，可爱极了！"),
            ("text", " 就是离得远，不然天天能看到他们。儿子在深圳，女儿虽然在北京但也忙。"),
        ]
    },
    {
        "time": "21:00",
        "situation": "睡前",
        "context": "洗漱完毕，喝了杯热牛奶，坐在床边想想今天的事",
        "mood": "略感孤独但满足",
        "possible_actions": [
            ("text", " Evans，今天一天过得还行，就是一个人安静了点。你说我这高血压还能好转吗？"),
            ("text", " 帮我设个闹钟，明天早上5点半。"),
            ("text", " Evans，我今天有点想我老伴，虽然她周末就回来，但还是不习惯一个人。"),
        ]
    },
]


def send_to_evans(text: str, retries: int = 3, delay: int = 8) -> dict:
    """发送消息，带智能重试和延迟（应对GLM QPS限制）"""
    for attempt in range(retries):
        try:
            resp = requests.post(
                f"{EVANS_BASE}/api/chat",
                json={"message": text},
                timeout=60
            )
            if resp.ok:
                return {"ok": True, "response": resp.json()}
            # 429 或 5xx，等待后重试
            if resp.status_code in (429, 502, 503):
                wait = delay * (attempt + 1)
                print(f"   ⏳ API限速，等待{wait}秒后重试...")
                time.sleep(wait)
                continue
            return {"ok": False, "error": f"{resp.status_code}"}
        except Exception as e:
            return {"ok": False, "error": str(e)}
    return {"ok": False, "error": "重试次数用尽"}


def print_divider(label: str):
    print(f"\n{'─'*60}")
    print(f" 🕐 {label}")
    print('─'*60)


def print_interaction(scenario: dict, action: tuple, evans_reply: dict):
    if action[0] == "mood":
        print(f"   💭 心情记录: {action[1]}")
        return

    print(f"\n👴 王德福: {action[1]}")

    if evans_reply.get("ok"):
        r = evans_reply["response"]
        reply_text = r.get("response", "")
        print(f"💙 Evans: {reply_text[:300]}")

        memories = r.get("memories_to_add", [])
        reminders = r.get("reminders_to_create", [])
        if memories:
            print(f"   📝 Evans记住了: {[m['content'] for m in memories]}")
        if reminders:
            print(f"   ⏰ Evans要提醒: {[rem['text'] for rem in reminders]}")
    else:
        print(f"   ❌ Evans未响应: {evans_reply.get('error')}")


def run_elderly_simulation():
    print("""
    ╔══════════════════════════════════════════════════╗
    ║   🌿 虚拟老年用户模拟 - 王德福的一天           ║
    ║   王德福: 68岁退休教师，北京独居              ║
    ║   高血压+腰椎问题，儿女在外地工作             ║
    ╚══════════════════════════════════════════════════╝
    """)

    print(f"👤 {PROFILE['name']}，{PROFILE['age']}岁，{PROFILE['occupation']}")
    print(f"📍 {PROFILE['location']} | {PROFILE['family']['living']}")
    print(f"💊 健康: {', '.join(PROFILE['health']['chronic'])}")
    print(f"😴 作息: {PROFILE['typical_day']['05:30']}起床 ~ {PROFILE['typical_day']['22:30']}睡觉")
    print(f"❤️ 关注: {', '.join(list(PROFILE['concerns'].keys())[:3])}")

    try:
        resp = requests.get(f"{EVANS_BASE}/api/stats", timeout=5)
        if resp.ok:
            print(f"\n✅ Evans 在线！记忆数: {resp.json().get('memory', {}).get('total', '?')}")
    except:
        print(f"\n⚠️ Evans 离线，请先启动服务")
        return

    input("\n按回车开始模拟老年人的一天...")

    mind = ElderlyMind(PROFILE)

    for scenario in ELDERLY_DAY_SCENARIOS:
        print_divider(f"{scenario['time']} - {scenario['situation']}")
        print(f"   💭 情境: {scenario['context']}")
        print(f"   😊 情绪: {scenario['mood']}")

        if not mind.decide_interact(scenario):
            print(f"   💭 (王德福选择不打扰，自己处理了)")
            time.sleep(1)
            continue

        action = random.choice(scenario["possible_actions"])

        if action[0] == "text":
            evans_reply = send_to_evans(action[1])
        else:
            continue

        print_interaction(scenario, action, evans_reply)
        mind.interactions_count += 1
        time.sleep(2)

    print(f"""

    ═══════════════════════════════════════════════════
    🌙 一天结束，王德福准备睡觉了
    📊 今日统计:
       - 向 Evans 提问: {mind.interactions_count} 次
       - 最终情绪: {ELDERLY_DAY_SCENARIOS[-1]['mood']}
    💭 感想: 今天还算充实，练了字，看了新闻，
       和孙子视频了，就是晚上一个人有点孤单…
       老伴周末就回来了。
    ═══════════════════════════════════════════════════
    """)


if __name__ == "__main__":
    run_elderly_simulation()
