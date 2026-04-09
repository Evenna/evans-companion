"""
分析模块 - 场景理解、意图识别、关系分析
"""
import requests
import json
import os
from typing import List, Optional, Dict, Any
from abc import ABC, abstractmethod

from utils.data_types import (
    PerceptionFrame, AnalysisResult, Intent, IntentType,
    PersonIdentity, RelationType, AnomalyDetection, RiskLevel
)
from utils.logger import setup_logger

logger = setup_logger("analysis")

class IAnalysisModule(ABC):
    """分析模块接口"""
    
    @abstractmethod
    def analyze(self, perception_frame: PerceptionFrame) -> AnalysisResult:
        """分析感知帧"""
        pass

class AnalysisModule(IAnalysisModule):
    """分析模块实现"""
    
    def __init__(self):
        self.llm_api_url = "http://v2.open.venus.oa.com/llmproxy/chat/completions"
        self.llm_model = "server:269246"
        self.llm_api_key = os.environ.get('LLM_API_KEY', '')
        
        # 已知人物数据库（简化版）
        self.known_persons: Dict[str, PersonIdentity] = {}
        
        logger.info("分析模块初始化完成")
    
    def analyze(self, perception_frame: PerceptionFrame) -> AnalysisResult:
        """分析感知帧"""
        result = AnalysisResult(
            timestamp=perception_frame.timestamp,
            frame_id=perception_frame.frame_id
        )
        
        # 1. 场景理解
        context_summary = self._understand_scene(perception_frame)
        result.context_summary = context_summary
        
        # 2. 意图识别
        intents = self._recognize_intent(perception_frame, context_summary)
        result.intents = intents
        if intents:
            result.primary_intent = intents[0]
        
        # 3. 人物识别与关系分析
        identified_persons = self._analyze_persons(perception_frame)
        result.identified_persons = identified_persons
        
        # 4. 异常检测
        anomalies = self._detect_anomalies(perception_frame, context_summary)
        result.anomalies = anomalies
        
        # 5. 用户状态估计
        result.user_state = self._estimate_user_state(perception_frame, intents)
        
        logger.info(f"分析完成 - 场景: {context_summary}, 意图数: {len(intents)}, 人物数: {len(identified_persons)}")
        
        return result
    
    def _understand_scene(self, frame: PerceptionFrame) -> str:
        """场景理解"""
        # 构建场景描述
        scene_desc = f"场景类型: {frame.scene_type}, "
        scene_desc += f"检测到 {len(frame.faces)} 个人脸, "
        scene_desc += f"{len(frame.objects)} 个物体"
        
        if frame.audio and frame.audio.transcript:
            scene_desc += f", 语音内容: {frame.audio.transcript}"
        
        # 调用LLM进行场景理解
        try:
            prompt = f"""请分析以下场景并给出简洁的理解（不超过50字）：
{scene_desc}

请直接输出场景理解结果，格式：用户正在[活动]，环境[状态]"""
            
            understanding = self._call_llm(prompt).strip()
            if understanding:
                return understanding
            return scene_desc

        except Exception as e:
            logger.error(f"场景理解失败: {e}")
            return scene_desc
    
    def _recognize_intent(self, frame: PerceptionFrame, context: str) -> List[Intent]:
        """意图识别"""
        intents = []
        
        # 如果有语音输入，识别显式意图
        if frame.audio and frame.audio.transcript:
            transcript = frame.audio.transcript.lower()
            
            # 简单规则匹配
            if any(word in transcript for word in ["帮我", "请", "能不能"]):
                intents.append(Intent(
                    intent_type=IntentType.REQUEST,
                    confidence=0.8,
                    source="audio",
                    parameters={"text": frame.audio.transcript}
                ))
            elif "?" in transcript or "吗" in transcript:
                intents.append(Intent(
                    intent_type=IntentType.QUERY,
                    confidence=0.7,
                    source="audio",
                    parameters={"text": frame.audio.transcript}
                ))
        
        # 基于场景推理隐式意图
        if len(frame.faces) > 0:
            # 检测到人脸，可能需要识别身份
            face = frame.faces[0]
            if face.emotion.value in ["sad", "angry"]:
                intents.append(Intent(
                    intent_type=IntentType.NEED_COMFORT,
                    confidence=0.6,
                    source="vision",
                    urgency=0.7
                ))
        
        return intents
    
    def _analyze_persons(self, frame: PerceptionFrame) -> List[PersonIdentity]:
        """人物识别与关系分析"""
        identified = []
        
        for face in frame.faces:
            # 简化版：基于face_id查找已知人物
            person_id = face.face_id
            
            if person_id in self.known_persons:
                person = self.known_persons[person_id]
                person.last_seen = frame.timestamp
                person.interaction_count += 1
            else:
                # 新人物
                person = PersonIdentity(
                    person_id=person_id,
                    name=None,
                    relation=RelationType.STRANGER,
                    trust_level=0.0,
                    first_seen=frame.timestamp,
                    last_seen=frame.timestamp,
                    interaction_count=1
                )
                self.known_persons[person_id] = person
            
            identified.append(person)
        
        return identified
    
    def _detect_anomalies(self, frame: PerceptionFrame, context: str) -> List[AnomalyDetection]:
        """异常检测"""
        anomalies = []
        
        # 检测陌生人
        for face in frame.faces:
            if (
                face.face_id not in self.known_persons
                or self.known_persons[face.face_id].relation == RelationType.STRANGER
            ):
                anomalies.append(AnomalyDetection(
                    anomaly_type="unknown_person",
                    description="检测到陌生人",
                    risk_level=RiskLevel.LOW,
                    confidence=0.7,
                    suggested_action="询问身份"
                ))
        
        return anomalies
    
    def _estimate_user_state(self, frame: PerceptionFrame, intents: List[Intent]) -> Dict[str, Any]:
        """用户状态估计"""
        state = {
            "is_present": len(frame.faces) > 0,
            "activity": "unknown",
            "mood": "neutral",
            "needs_attention": len(intents) > 0
        }
        
        if frame.faces:
            face = frame.faces[0]
            state["mood"] = face.emotion.value
        
        return state
    
    def _call_llm(self, prompt: str, max_tokens: int = 200) -> str:
        """调用LLM API"""
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.llm_api_key}"
        }
        
        payload = {
            "model": self.llm_model,
            "messages": [
                {"role": "user", "content": prompt}
            ],
            "max_tokens": max_tokens,
            "temperature": 0.7
        }
        
        try:
            response = requests.post(
                self.llm_api_url,
                headers=headers,
                json=payload,
                timeout=10
            )
            response.raise_for_status()
            
            result = response.json()
            return result["choices"][0]["message"]["content"]
            
        except Exception as e:
            logger.error(f"LLM调用失败: {e}")
            return ""
