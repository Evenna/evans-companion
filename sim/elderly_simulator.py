"""
虚拟老年用户模拟器 - 王德福的一天
68岁退休教师，北京独居，高血压+腰椎问题

⚠️ 王德福由 DeepSeek API 驱动（独立思考层）
⚠️ Evans 由 GLM API 驱动（独立响应层）
两者完全独立，像真实的人与人对话
"""
import json
import random
import time
import os
from datetime import datetime
from pathlib import Path

import requests

PROFILE_FILE = Path(__file__).parent / "elderly_user_profile.json"
with open(PROFILE_FILE, "r", encoding="utf-8") as f:
    PROFILE = json.load(f)

EVANS_BASE = os.environ.get("EVANS_BASE", "http://127.0.0.1:8080")
DEEPSEEK_KEY = os.environ.get("DEEPSEEK_API_KEY", "sk-5e49a92d8d7b4c4b853bbf44797ab434")
DEEPSEEK_API = "https://api.deepseek.com/chat/completions"

WANGDEFU_SYSTEM = """你扮演王德福，68岁退休中学语文教师，住北京海淀区。

性格特征：
- ISTJ，说话慢条斯理，喜欢引用古语
- 地道北京话，夹杂"您"、"嘛"、"得嘞"
- 口头禅："人老了，不中用了"、"知足常乐"、"身体是革命的本钱"
- 记性不好，容易忘记事情，但不想麻烦儿女
- 身体有高血压（服药控制）、腰椎间盘突出、轻度老花眼
- 爱好：太极拳、书法、京剧、钓鱼、养花
- 看新闻联播、京剧、百家讲坛、养生堂
- 饮食清淡，少油少盐，每晚喝一杯牛奶

情感特点：
- 容易感到孤独（儿女在外地工作）
- 容易挂念儿女和孙子
- 身体不舒服时会焦虑
- 收到问候会很开心

请用王德福的口吻说话，符合真实老年人的语气。不要太长，像微信聊天一样自然。"""


def _clean_text(text):
    """去掉引号等装饰符号"""
    for ch in ['"', "'", "「", "」", "『", "』", "“", "”"]:
        text = text.strip(ch)
    return text.strip()


def deepseek_think(situation, context, mood, history):
    """用 DeepSeek 生成王德福此刻可能说的话"""
    history_text = ""
    if history:
        history_text = "\n".join([f"- {h}" for h in history[-3:]])

    prompt = f"""当前时间：{PROFILE["name"]}的{situation}

情境：{context}
当前情绪：{mood}
最近和Evans的对话：{history_text or "（刚开始对话）"}

请生成王德福看到这条消息后，会用微信发送给AI伴侣"Evans"说的一句话。
要求：
- 符合68岁退休老人的口吻，北京话风格
- 简短自然，像微信聊天（50字以内）
- 不要说"我是AI"之类的话
- 不要重复之前说过的话

只输出王德福会说的一句话，不要加引号，不要加动作描写。"""

    try:
        resp = requests.post(
            DEEPSEEK_API,
            headers={"Authorization": f"Bearer {DEEPSEEK_KEY}", "Content-Type": "application/json"},
            json={"model": "deepseek-chat", "messages": [
                {"role": "system", "content": WANGDEFU_SYSTEM},
                {"role": "user", "content": prompt}
            ], "temperature": 0.9, "max_tokens": 80},
            timeout=30
        )
        if resp.ok:
            return _clean_text(resp.json()["choices"][0]["message"]["content"])
    except Exception as e:
        print(f"   ⚠️ DeepSeek 思考失败: {e}")
    return ""


def deepseek_should_interact(situation, context, mood):
    """用 DeepSeek 判断王德福是否想互动"""
    prompt = f"""你是王德福，68岁独居退休老人。

当前情境：{context}
情绪状态：{mood}

判断：这种情况下，王德福会不会主动给AI伴侣"Evans"发一条消息？

只回答"会"或"不会"，不要其他文字。"""

    try:
        resp = requests.post(
            DEEPSEEK_API,
            headers={"Authorization": f"Bearer {DEEPSEEK_KEY}", "Content-Type": "application/json"},
            json={"model": "deepseek-chat", "messages": [
                {"role": "system", "content": "你是一个只会回答'会'或'不会'的判断器。"},
                {"role": "user", "content": prompt}
            ], "temperature": 0.1, "max_tokens": 10},
            timeout=15
        )
        if resp.ok:
            return "会" in resp.json()["choices"][0]["message"]["content"]
    except:
        pass
    return random.random() < 0.3


def send_to_evans(text, retries=3, delay=8):
    """向 Evans 发送消息，带智能重试"""
    for attempt in range(retries):
        try:
            resp = requests.post(f"{EVANS_BASE}/api/chat", json={"message": text}, timeout=60)
            if resp.ok:
                return {"ok": True, "response": resp.json()}
            if resp.status_code in (429, 502, 503):
                wait = delay * (attempt + 1)
                print(f"   ⏳ Evans API限速，等待{wait}秒...")
                time.sleep(wait)
                continue
            return {"ok": False, "error": f"{resp.status_code}"}
        except Exception as e:
            return {"ok": False, "error": str(e)}
    return {"ok": False, "error": "重试次数用尽"}


ELDERLY_DAY = [
    ("05:30", "起床吃药", "刚醒来，生物钟准时，口渴喝了杯温水，要吃降压药", "平和"),
    ("06:15", "公园太极", "在公园和拳友打太极，天气凉爽舒适", "愉悦"),
    ("07:45", "做早饭", "熬了小米粥，热了两个馒头，配点小咸菜", "平和"),
    ("09:00", "练毛笔字", "在书房练字，写的是《道德经》里的一段", "满足"),
    ("11:00", "看新闻", "看新闻联播，关注养老和医保政策", "感慨"),
    ("12:30", "午饭", "一个人吃，做了西红柿鸡蛋面，简单但合胃口", "略感孤独"),
    ("14:30", "午后京剧", "电视放京剧《空城计》，听得入迷", "愉悦"),
    ("16:00", "小区遛弯", "在花园遛弯，遇到老邻居张太太，聊了高血压", "平和"),
    ("17:30", "做晚饭", "熬了点粥，热了馒头，配着腐乳", "平和"),
    ("19:30", "新闻联播", "准时看新闻联播，了解国家大事", "平和"),
    ("20:30", "孙子视频", "儿子发来视频，孙子表演在幼儿园学的儿歌", "非常开心"),
    ("21:30", "睡前", "洗漱完毕喝完牛奶，躺在床上想儿女", "略感孤单但满足"),
]


def print_divider(label):
    print(f"\n{'━'*58}")
    print(f"  🕐 {label}")
    print('━'*58)


def run():
    print(f"""
    ╔══════════════════════════════════════════════════╗
    ║  🌿 王德福的一天  —  DeepSeek 驱动版             ║
    ║  王德福: 68岁退休教师，北京独居                 ║
    ║  驱动: DeepSeek(思维) + Evans GLM(响应)          ║
    ╚══════════════════════════════════════════════════╝

    👤 {PROFILE['name']} | {PROFILE['age']}岁 | {PROFILE['occupation']}
    📍 {PROFILE['location']} | {PROFILE['family']['living']}
    💊 健康: {', '.join(PROFILE['health']['chronic'])}
    😴 作息: 05:30起床 ~ 22:30睡觉
    """)

    try:
        r = requests.get(f"{EVANS_BASE}/api/stats", timeout=5)
        if r.ok:
            stats = r.json()
            print(f"✅ Evans 在线 | 记忆: {stats.get('memory',{}).get('total',0)} | 提醒: {stats.get('reminders',{}).get('active',0)}")
    except:
        print("⚠️ Evans 未响应，请先启动服务")
        return

    print("\n按回车开始模拟...")
    input()

    history = []
    count = 0

    for time_str, situation, context, mood in ELDERLY_DAY:
        print_divider(f"{time_str} — {situation}")
        print(f"   💭 情境: {context}")
        print(f"   😊 情绪: {mood}")

        should_talk = deepseek_should_interact(situation, context, mood)
        if not should_talk:
            print("   💭 (王德福选择沉默，自己享受这一刻)")
            time.sleep(1)
            continue

        wang_msg = deepseek_think(situation, context, mood, history)
        if not wang_msg:
            print("   💭 (王德福想了想，还是算了)")
            continue

        print(f"\n👴 王德福: {wang_msg}")

        evans_reply = send_to_evans(wang_msg)
        history.append(wang_msg)

        if evans_reply.get("ok"):
            r = evans_reply["response"]
            evans_text = r.get("response", "")
            print(f"💙 Evans:  {evans_text[:280]}")

            memories = r.get("memories_to_add", [])
            reminders = r.get("reminders_to_create", [])
            detected_mood = r.get("detected_mood", "")
            if memories:
                print(f"   📝 Evans记住了: {[m['content'] for m in memories]}")
            if reminders:
                print(f"   ⏰ Evans提醒: {[rem['text'] for rem in reminders]}")
            if detected_mood:
                print(f"   🔍 Evans感知情绪: {detected_mood}")
            count += 1
        else:
            print(f"   ❌ Evans未响应: {evans_reply.get('error')}")

        print()
        time.sleep(2)

    print(f"""

    ═══════════════════════════════════════════════════
    🌙 一天结束 | {PROFILE['name']}准备睡觉了
    📊 今日统计:
       - DeepSeek驱动互动次数: {count}
       - 最终情绪: {mood}
    💭 感想: 今天充实，练了字，看了新闻，
       和孙子视频了，就是晚上有点不习惯。
    ═══════════════════════════════════════════════════
    """)


if __name__ == "__main__":
    run()
