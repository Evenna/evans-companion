"""
决策模块 - 主动需求识别、任务规划、世界模型
"""
import time
from typing import List, Optional, Dict, Any
from abc import ABC, abstractmethod

from utils.data_types import (
    AnalysisResult, DecisionResult, Need, TaskPlan, Action,
    WorldState, TaskPriority, ActionType
)
from utils.logger import setup_logger

logger = setup_logger("decision")

class IDecisionModule(ABC):
    """决策模块接口"""
    
    @abstractmethod
    def decide(self, analysis_result: AnalysisResult, **kwargs) -> DecisionResult:
        """做出决策"""
        pass

class DecisionModule(IDecisionModule):
    """决策模块实现"""
    
    def __init__(self):
        self.world_state = WorldState()
        self.decision_history: List[DecisionResult] = []
        
        logger.info("决策模块初始化完成")
    
    def decide(
        self,
        perception_frame,
        analysis_result: AnalysisResult,
        memory=None,
        relation_graph=None,
    ) -> DecisionResult:
        """做出决策（memory / relation_graph 预留扩展）"""
        _ = (perception_frame, memory, relation_graph)
        result = DecisionResult(timestamp=time.time())
        
        # 1. 更新世界状态
        self._update_world_state(analysis_result)
        result.current_state = self.world_state
        
        # 2. 主动需求识别（ToM心智理论）
        needs = self._recognize_needs(analysis_result)
        result.recognized_needs = needs
        if needs:
            result.primary_need = needs[0]
        
        # 3. 任务规划（ReAct框架）
        if result.primary_need and result.primary_need.should_intervene:
            task_plans = self._plan_tasks(result.primary_need, analysis_result)
            result.task_plans = task_plans
            if task_plans:
                result.selected_plan = task_plans[0]
        
        # 4. 生成推理链（CoT）
        result.reasoning_chain = self._generate_reasoning_chain(
            analysis_result, needs, result.selected_plan
        )
        
        # 5. 决策置信度
        result.decision_confidence = self._calculate_confidence(result)
        
        # 保存决策历史
        self.decision_history.append(result)
        if len(self.decision_history) > 100:
            self.decision_history.pop(0)
        
        logger.info(f"决策完成 - 需求: {len(needs)}, 计划: {len(result.task_plans)}")
        
        return result
    
    def _update_world_state(self, analysis: AnalysisResult):
        """更新世界状态"""
        self.world_state.timestamp = analysis.timestamp
        
        # 更新用户状态
        if analysis.user_state.get("is_present"):
            self.world_state.user_activity = analysis.user_state.get("activity", "unknown")
            self.world_state.user_mood = analysis.user_state.get("mood", "neutral")
        
        # 更新环境状态
        self.world_state.environment_state["scene"] = analysis.context_summary
        self.world_state.environment_state["person_count"] = len(analysis.identified_persons)
    
    def _recognize_needs(self, analysis: AnalysisResult) -> List[Need]:
        """主动需求识别（基于ToM心智理论）"""
        needs = []
        
        # 基于意图识别需求
        for intent in analysis.intents:
            need = Need(
                need_type=intent.intent_type.value,
                description=f"用户意图: {intent.intent_type.value}",
                confidence=intent.confidence,
                urgency=intent.urgency,
                source="intent_analysis"
            )
            
            # 判断是否需要主动介入
            if intent.urgency > 0.6 or intent.intent_type.value.startswith("need_"):
                need.should_intervene = True
                need.intervention_reason = "检测到高紧急度需求或隐式需求"
            
            needs.append(need)
        
        # 基于异常检测识别安全需求
        for anomaly in analysis.anomalies:
            if anomaly.risk_level.value >= 2:  # MEDIUM及以上
                need = Need(
                    need_type="safety_alert",
                    description=anomaly.description,
                    confidence=anomaly.confidence,
                    urgency=0.8,
                    source="anomaly_detection",
                    should_intervene=True,
                    intervention_reason=f"检测到{anomaly.risk_level.name}风险"
                )
                needs.append(need)
        
        # ToM推理：基于用户情绪推断需求
        user_mood = self.world_state.user_mood
        if user_mood in ["sad", "angry"]:
            need = Need(
                need_type="emotional_support",
                description=f"用户情绪{user_mood}，可能需要情感支持",
                confidence=0.6,
                urgency=0.5,
                source="tom_reasoning",
                should_intervene=True,
                intervention_reason="ToM推理：用户情绪低落"
            )
            needs.append(need)
        
        # 按紧急度排序
        needs.sort(key=lambda x: x.urgency, reverse=True)
        
        return needs
    
    def _plan_tasks(self, need: Need, analysis: AnalysisResult) -> List[TaskPlan]:
        """任务规划（ReAct框架）"""
        plans = []
        
        # 根据需求类型生成任务计划
        if need.need_type == "request":
            plan = self._plan_request_task(need, analysis)
            if plan:
                plans.append(plan)
        
        elif need.need_type == "safety_alert":
            plan = self._plan_safety_task(need, analysis)
            if plan:
                plans.append(plan)
        
        elif need.need_type == "emotional_support":
            plan = self._plan_comfort_task(need, analysis)
            if plan:
                plans.append(plan)
        
        elif need.need_type == "need_comfort":
            plan = self._plan_comfort_task(need, analysis)
            if plan:
                plans.append(plan)
        
        return plans
    
    def _plan_request_task(self, need: Need, analysis: AnalysisResult) -> Optional[TaskPlan]:
        """规划请求任务"""
        plan = TaskPlan(
            task_description=need.description,
            priority=TaskPriority.P2_NORMAL
        )
        
        # 动作序列
        plan.actions = [
            Action(
                action_type=ActionType.SPEAK,
                target="user",
                parameters={"text": "我明白了，让我来帮您处理"},
                expected_duration=2.0
            ),
            Action(
                action_type=ActionType.RECORD,
                target="memory",
                parameters={"event": need.description},
                expected_duration=0.5
            )
        ]
        
        plan.estimated_duration = sum(a.expected_duration for a in plan.actions)
        plan.success_probability = 0.8
        
        return plan
    
    def _plan_safety_task(self, need: Need, analysis: AnalysisResult) -> Optional[TaskPlan]:
        """规划安全任务"""
        plan = TaskPlan(
            task_description=need.description,
            priority=TaskPriority.P0_CRITICAL
        )
        
        plan.actions = [
            Action(
                action_type=ActionType.SPEAK,
                target="user",
                parameters={"text": f"注意：{need.description}"},
                expected_duration=2.0
            ),
            Action(
                action_type=ActionType.NOTIFICATION,
                target="family",
                parameters={"message": need.description, "level": "warning"},
                expected_duration=1.0
            )
        ]
        
        plan.estimated_duration = sum(a.expected_duration for a in plan.actions)
        plan.success_probability = 0.9
        
        return plan
    
    def _plan_comfort_task(self, need: Need, analysis: AnalysisResult) -> Optional[TaskPlan]:
        """规划安慰任务"""
        plan = TaskPlan(
            task_description="提供情感支持",
            priority=TaskPriority.P1_HIGH
        )
        
        plan.actions = [
            Action(
                action_type=ActionType.SPEAK,
                target="user",
                parameters={"text": "我注意到您似乎有些不开心，需要我陪您聊聊吗？"},
                expected_duration=3.0
            )
        ]
        
        plan.estimated_duration = 3.0
        plan.success_probability = 0.7
        
        return plan
    
    def _generate_reasoning_chain(
        self, 
        analysis: AnalysisResult, 
        needs: List[Need],
        plan: Optional[TaskPlan]
    ) -> List[str]:
        """生成推理链（CoT）"""
        chain = []
        
        chain.append(f"观察：{analysis.context_summary}")
        
        if analysis.intents:
            chain.append(f"意图识别：检测到{len(analysis.intents)}个意图")
        
        if needs:
            chain.append(f"需求分析：识别到{len(needs)}个需求，主要需求为{needs[0].need_type}")
        
        if plan:
            chain.append(f"决策：执行{plan.task_description}，包含{len(plan.actions)}个动作")
        else:
            chain.append("决策：当前无需主动介入")
        
        return chain
    
    def _calculate_confidence(self, result: DecisionResult) -> float:
        """计算决策置信度"""
        if not result.primary_need:
            return 0.5
        
        confidence = result.primary_need.confidence
        
        if result.selected_plan:
            confidence = (confidence + result.selected_plan.success_probability) / 2
        
        return confidence
