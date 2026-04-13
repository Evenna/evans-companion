"""
Evans 记忆系统 - 语义检索升级版
支持 GLM Embedding-3（优先）+ GLM Chat 模型语义排序（fallback）+ 关键词匹配（保底）
"""
import json
import time
import uuid
import os
import re
from typing import List, Dict, Any, Optional
from datetime import datetime
from collections import defaultdict
from pathlib import Path

import requests
import numpy as np
from dotenv import load_dotenv

from utils.logger import setup_logger

logger = setup_logger("companion_memory")

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data")
MEMORY_FILE = os.path.join(DATA_DIR, "memories.json")

VALID_CATEGORIES = {"facts", "events", "preferences", "people", "emotions"}

_EMBED_API = "https://open.bigmodel.cn/api/paas/v4/embeddings"
_EMBED_MODEL = "embedding-3"
_CHAT_API = "https://open.bigmodel.cn/api/paas/v4/chat/completions"

# ─── 向量工具 ────────────────────────────────────────────────

def _cosine_sim(a: List[float], b: List[float]) -> float:
    """计算两个向量的余弦相似度"""
    a = np.array(a, dtype=np.float32)
    b = np.array(b, dtype=np.float32)
    norm_a = np.linalg.norm(a)
    norm_b = np.linalg.norm(b)
    if norm_a < 1e-8 or norm_b < 1e-8:
        return 0.0
    return float(np.dot(a, b) / (norm_a * norm_b))


def _load_dotenv_() -> None:
    root = Path(__file__).resolve().parent.parent
    load_dotenv(root / ".env", override=True)


def _get_api_key() -> str:
    root = Path(__file__).resolve().parent.parent
    load_dotenv(root / ".env", override=True)
    key = os.environ.get("GLM_API_KEY") or os.environ.get("ZHIPU_API_KEY")
    if not key:
        raise RuntimeError("未配置 GLM_API_KEY")
    return key


# ─── Embedding 缓存 ───────────────────────────────────────────

_embedding_cache: Dict[str, List[float]] = {}
_embed_available: Optional[bool] = None  # None=未检测过


def get_embedding(text: str, api_key: Optional[str] = None) -> Optional[List[float]]:
    """获取文本的 embedding 向量。失败返回 None（不降级到零向量）"""
    global _embed_available
    cache_key = text[:200]
    if cache_key in _embedding_cache:
        return _embedding_cache[cache_key]

    key = api_key or _get_api_key()
    payload = {"model": _EMBED_MODEL, "input": text}
    headers = {"Authorization": f"Bearer {key}", "Content-Type": "application/json"}

    try:
        resp = requests.post(_EMBED_API, json=payload, headers=headers, timeout=15)
        if resp.status_code == 429:
            if _embed_available is None:
                _embed_available = False
                logger.warning("GLM Embedding API 429（余额不足），语义搜索暂时不可用")
            return None
        if resp.status_code == 400:
            # 模型不存在
            if _embed_available is None:
                _embed_available = False
                logger.warning("GLM Embedding 模型不可用")
            return None
        if not resp.ok:
            if _embed_available is None:
                _embed_available = False
            return None

        data = resp.json()
        vector = data["data"][0]["embedding"]
        if _embed_available is None:
            _embed_available = True
        _embedding_cache[cache_key] = vector
        return vector
    except Exception as e:
        if _embed_available is None:
            _embed_available = False
            logger.warning(f"Embedding API 请求失败: {e}")
        return None


def _semantic_rank_with_chat(
    query: str,
    candidates: List[Dict],
    api_key: str,
    top_k: int = 5,
) -> List[tuple]:
    """
    用 GLM Chat 模型对候选记忆做语义排序。
    每次请求只比 top_k 条，避免 token 浪费。
    """
    if not candidates:
        return []

    # 限制候选数量避免 token 溢出
    candidates = candidates[:20]

    mem_texts = "\n".join(
        f"[{i}] {m['content']}" for i, m in enumerate(candidates)
    )

    prompt = f"""你是一个记忆检索助手。用户问：「{query}」

以下是候选记忆列表：
{mem_texts}

请找出最相关的3条记忆，输出 JSON 格式：
{{"top_ids": [记忆序号列表，按相关度从高到低]}}

注意：只输出 JSON，不要其他文字。"""

    payload = {
        "model": "glm-4-flash",  # text-only, not rate-limited like glm-4-plus
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.1,
        "max_tokens": 100,
    }
    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}

    try:
        resp = requests.post(_CHAT_API, json=payload, headers=headers, timeout=15)
        if not resp.ok:
            return []
        raw = resp.json()["choices"][0]["message"]["content"]
        # 去掉可能的 markdown 代码围栏
        raw = raw.strip()
        if raw.startswith("```"):
            raw = raw.split("```", 2)[1]
            raw = raw.lstrip("json\n")
        data = json.loads(raw)
        indices = data.get("top_ids", [])
        return [(i, candidates[i]) for i in indices if i < len(candidates)]
    except Exception as e:
        logger.warning(f"Chat 语义排序失败: {e}")
        return []


# ─── 主类 ────────────────────────────────────────────────

class CompanionMemory:
    def __init__(self):
        os.makedirs(DATA_DIR, exist_ok=True)
        self.memories: Dict[str, Dict] = {}
        self._load()
        logger.info(f"记忆系统初始化，共 {len(self.memories)} 条记忆，embedding={_embed_available}")

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

        # Write Guard 预检
        guard = self.write_guard(content, category)
        if guard["action"] == "NOOP":
            logger.info(f"Write Guard 拦截: {guard['reason']}")
            return self.memories.get(guard.get("existing_id", "")) or {}

        if guard["action"] == "UPDATE" and guard["merge_with"]:
            # 合并到已有记忆，更新重要性
            mid = guard["merge_with"]
            self.memories[mid]["importance"] = max(
                self.memories[mid].get("importance", 0), importance
            )
            self.memories[mid]["updated_at"] = datetime.now().isoformat()
            self._save()
            logger.info(f"合并记忆 id={mid}")
            return self.memories[mid]

        # 生成 embedding（异步，不阻塞）
        embedding = None
        try:
            embedding = get_embedding(content)
        except Exception as e:
            logger.warning(f"生成 embedding 失败: {e}")

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
            "embedding": embedding,
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

    def search(
        self,
        query: str = "",
        category: str = "",
        limit: int = 50,
        use_semantic: bool = True,
    ) -> List[Dict]:
        """
        搜索记忆。

        优先级策略：
        1. Embedding 可用 → embedding cosine similarity + importance 加权
        2. Embedding 不可用，Chat 可用 → GLM chat 语义排序
        3. 降级 → 关键词匹配 + importance 排序
        """
        results = list(self.memories.values())

        # 分类过滤
        if category and category in VALID_CATEGORIES:
            results = [m for m in results if m["category"] == category]

        if not query:
            results.sort(key=lambda m: m.get("importance", 0), reverse=True)
            return results[:limit]

        # ── 策略 1：Embedding cosine similarity ──
        if use_semantic and _embed_available is not False:
            query_emb = get_embedding(query)
            if query_emb:
                scored = []
                for m in results:
                    emb = m.get("embedding")
                    if emb:
                        sim = _cosine_sim(query_emb, emb)
                        # 综合语义相似度 + 重要性
                        score = sim * 0.7 + m.get("importance", 0) * 0.3
                    else:
                        # 无 embedding，降级用关键词
                        score = 0.3 if query.lower() in m["content"].lower() else 0.0
                    scored.append((score, m))

                scored.sort(key=lambda x: x[0], reverse=True)
                logger.info(f"语义搜索[{query[:20]}]: 命中 {len(scored)} 条")
                return [m for _, m in scored[:limit]]

        # ── 策略 2：Chat 模型语义排序（Embedding 不可用时） ──
        if use_semantic and len(results) <= 50:
            try:
                key = _get_api_key()
                ranked = _semantic_rank_with_chat(query, results, key, top_k=limit)
                if ranked:
                    logger.info(f"Chat 语义排序[{query[:20]}]: 命中 {len(ranked)} 条")
                    # 剩余未进入 top 的，按 importance 补足
                    ranked_ids = {id(m) for _, m in ranked}
                    others = [
                        (m.get("importance", 0), m)
                        for m in results
                        if id(m) not in ranked_ids
                    ]
                    others.sort(key=lambda x: x[0], reverse=True)
                    all_results = [m for _, m in ranked] + [m for _, m in others[:limit - len(ranked)]]
                    return all_results
            except Exception as e:
                logger.warning(f"Chat 语义排序失败: {e}")

        # ── 策略 3：关键词 + importance 降级 ──
        q = query.lower()
        results = [m for m in results if q in m["content"].lower()]
        results.sort(key=lambda m: m.get("importance", 0), reverse=True)
        logger.info(f"关键词搜索[{query[:20]}]: 命中 {len(results)} 条")
        return results[:limit]

    def get_recent(self, count: int = 10) -> List[Dict]:
        items = sorted(
            self.memories.values(),
            key=lambda m: m.get("created_at", ""),
            reverse=True,
        )
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

    def get_context_for_chat(self, max_items: int = 8, query: str = "") -> str:
        """
        获取聊天用记忆上下文。
        有 query 时自动选择最优搜索策略。
        """
        items = self.search(query=query, limit=max_items, use_semantic=True)

        if not items:
            return "暂无记忆"

        lines = []
        cat_emoji = {
            "facts": "📌", "events": "📅", "preferences": "❤️",
            "people": "👤", "emotions": "💭"
        }
        for m in items:
            emoji = cat_emoji.get(m["category"], "📝")
            lines.append(f"- {emoji} {m['content']}")
        return "\n".join(lines)

    def extract_from_text(self, text: str) -> List[Dict]:
        """从对话文本中自动提取记忆（启发式）"""
        extracted = []

        pref_patterns = [
            r"我(喜欢|爱|偏好|更喜欢|最爱)(.+?)([。，！？\n]|$)",
            r"我(不喜欢|讨厌|不爱|不想)(.+?)([。，！？\n]|$)",
        ]
        for pat in pref_patterns:
            for m in re.finditer(pat, text):
                content = m.group(1) + m.group(2)
                extracted.append({"content": content, "category": "preferences", "importance": 0.6})

        event_patterns = [
            r"(明天|后天|下周|这周末|今晚)(.+?)([。，！？\n]|$)",
            r"我要去(.+?)([。，！？\n]|$)",
            r"我(做了|完成了|搞定了)(.+?)([。，！？\n]|$)",
        ]
        for pat in event_patterns:
            for m in re.finditer(pat, text):
                content = m.group(0).rstrip("。，！？\n")
                extracted.append({"content": content, "category": "events", "importance": 0.5})

        people_patterns = [
            r"(我(?:的)?(?:妈妈|爸爸|朋友|同事|老板|老师|同学|姐姐|哥哥|弟弟|妹妹|老公|老婆|男朋友|女朋友))(.{0,20})",
        ]
        for pat in people_patterns:
            for m in re.finditer(pat, text):
                content = m.group(0)
                extracted.append({"content": content, "category": "people", "importance": 0.7})

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

    # ─── Write Guard ─────────────────────────────────────────

    def write_guard(self, content: str, category: str) -> Dict[str, Any]:
        """预检记忆内容，防止重复写入。"""
        result = {
            "action": "ADD",
            "reason": "",
            "merge_with": None,
            "existing_id": None,
        }

        if not content or len(content.strip()) < 2:
            result["action"] = "NOOP"
            result["reason"] = "内容太短"
            return result

        content_lower = content.strip().lower()

        for mid, mem in self.memories.items():
            if mem["content"].strip().lower() == content_lower:
                result["action"] = "NOOP"
                result["reason"] = f"完全重复 id={mid}"
                result["existing_id"] = mid
                return result

            # 语义相似度检查（需要 embedding）
            if _embed_available and mem.get("embedding"):
                emb = get_embedding(content)
                if emb:
                    sim = _cosine_sim(emb, mem["embedding"])
                    if sim > 0.95:
                        result["action"] = "UPDATE"
                        result["merge_with"] = mid
                        result["reason"] = f"高度相似({sim:.2f})，合并"
                        return result

        return result

    # ─── 批量补全 embedding ────────────────────────────────

    def rebuild_embeddings(self) -> int:
        """为没有 embedding 的记忆补全向量"""
        if _embed_available is False:
            logger.warning("Embedding API 不可用，跳过补全")
            return 0

        count = 0
        for mid, mem in self.memories.items():
            if mem.get("embedding"):
                continue
            try:
                emb = get_embedding(mem["content"])
                if emb:
                    mem["embedding"] = emb
                    count += 1
                    time.sleep(0.2)  # 避免 429
            except Exception as e:
                logger.warning(f"补全 {mid} 失败: {e}")
        if count > 0:
            self._save()
            logger.info(f"补全了 {count} 条 embedding")
        return count

    # ─── 快照与回滚 ───────────────────────────────────────

    def snapshot(self) -> str:
        """创建快照，返回快照 ID"""
        snap_id = datetime.now().strftime("%Y%m%d_%H%M%S")
        snap_file = os.path.join(DATA_DIR, f"snapshot_{snap_id}.json")
        with open(snap_file, "w", encoding="utf-8") as f:
            json.dump(self.memories, f, ensure_ascii=False, indent=2)
        logger.info(f"快照 {snap_id}: {len(self.memories)} 条")
        return snap_id

    def rollback(self, snap_id: str) -> int:
        """回滚到指定快照"""
        snap_file = os.path.join(DATA_DIR, f"snapshot_{snap_id}.json")
        if not os.path.exists(snap_file):
            logger.error(f"快照不存在: {snap_id}")
            return 0
        with open(snap_file, "r", encoding="utf-8") as f:
            self.memories = json.load(f)
        self._save()
        logger.info(f"已回滚到 {snap_id}")
        return len(self.memories)

    def list_snapshots(self) -> List[Dict[str, str]]:
        """列出所有快照"""
        return sorted(
            [
                {"id": f.replace("snapshot_", "").replace(".json", ""), "file": f}
                for f in os.listdir(DATA_DIR)
                if f.startswith("snapshot_") and f.endswith(".json")
            ],
            key=lambda x: x["id"],
            reverse=True,
        )
