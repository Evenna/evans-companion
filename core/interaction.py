"""
交互模块 - 输出生成、设备控制
"""
import time
from typing import Optional, Dict, Any
from abc import ABC, abstractmethod

from utils.data_types import DecisionResult, Action, ActionType, TaskPlan
from utils.logger import setup_logger

logger = setup_logger("interaction")

class IInteractionModule(ABC):
    """交互模块接口"""
    
    @abstractmethod
    def execute(self, decision: DecisionResult) -> bool:
        """执行决策"""
        pass

class InteractionModule(IInteractionModule):
    """交互模块实现"""
    
    def __init__(self):
        self.tts_enabled = True
        self.device_manager = None  # 将在后续设置
        
        logger.info("交互模块初始化完成")
    
    def set_device_manager(self, device_manager):
        """设置设备管理器"""
        self.device_manager = device_manager

    def generate_output(self, plan: TaskPlan) -> bool:
        """根据任务计划输出（与 execute 等价，供主循环调用）"""
        dr = DecisionResult(timestamp=time.time(), selected_plan=plan)
        return self.execute(dr)
    
    def execute(self, decision: DecisionResult) -> bool:
        """执行决策"""
        if not decision.selected_plan:
            return True
        
        plan = decision.selected_plan
        logger.info(f"开始执行任务: {plan.task_description}")
        
        success = True
        for action in plan.actions:
            try:
                self._execute_action(action)
                time.sleep(0.1)  # 短暂延迟
            except Exception as e:
                logger.error(f"动作执行失败: {action.action_type.value}, 错误: {e}")
                success = False
        
        logger.info(f"任务执行{'成功' if success else '失败'}")
        return success
    
    def _execute_action(self, action: Action):
        """执行单个动作"""
        if action.action_type == ActionType.SPEAK:
            self._speak(action.parameters.get("text", ""))
        
        elif action.action_type == ActionType.DISPLAY:
            self._display(action.parameters.get("content", ""))
        
        elif action.action_type == ActionType.DEVICE_CONTROL:
            self._control_device(
                action.target,
                action.parameters.get("command", "")
            )
        
        elif action.action_type == ActionType.NOTIFICATION:
            self._send_notification(
                action.target,
                action.parameters.get("message", "")
            )
        
        elif action.action_type == ActionType.RECORD:
            self._record_event(action.parameters)
    
    def _speak(self, text: str):
        """语音输出"""
        logger.info(f"[语音输出] {text}")
        print(f"🔊 Nexus Core: {text}")
        
        # 实际TTS实现（可选）
        # if self.tts_enabled:
        #     import pyttsx3
        #     engine = pyttsx3.init()
        #     engine.say(text)
        #     engine.runAndWait()
    
    def _display(self, content: str):
        """屏幕显示"""
        logger.info(f"[屏幕显示] {content}")
        print(f"📺 显示: {content}")
    
    def _control_device(self, device_id: str, command: str):
        """控制设备"""
        logger.info(f"[设备控制] {device_id}: {command}")
        print(f"🤖 控制设备 {device_id}: {command}")
        
        if self.device_manager:
            self.device_manager.send_command(device_id, command)
    
    def _send_notification(self, target: str, message: str):
        """发送通知"""
        logger.info(f"[通知] 发送给{target}: {message}")
        print(f"📬 通知 [{target}]: {message}")
    
    def _record_event(self, event_data: Dict[str, Any]):
        """记录事件"""
        logger.info(f"[记录事件] {event_data}")
        print(f"📝 记录: {event_data}")
