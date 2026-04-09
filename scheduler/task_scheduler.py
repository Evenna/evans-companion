"""
任务调度器
"""
import time
import queue
from typing import Dict, List, Optional
from threading import Lock

from utils.data_types import TaskPlan, TaskPriority, TaskStatus, Action
from devices.device_manager import DeviceManager
from utils.logger import setup_logger

logger = setup_logger("task_scheduler")

class TaskScheduler:
    """任务调度器"""
    
    def __init__(self, device_manager: DeviceManager):
        self.device_manager = device_manager
        
        # 优先级队列
        self.task_queue = queue.PriorityQueue()
        
        # 正在执行的任务
        self.executing_tasks: Dict[str, TaskPlan] = {}
        
        # 任务历史
        self.task_history: List[TaskPlan] = []
        
        # 设备锁（防止冲突）
        self.device_locks: Dict[str, Lock] = {}
        
        logger.info("任务调度器初始化完成")
    
    def submit_task(self, task: TaskPlan) -> bool:
        """提交任务"""
        try:
            # 优先级队列：数字越小优先级越高
            priority_value = task.priority.value
            self.task_queue.put((priority_value, time.time(), task))
            
            logger.info(f"任务已提交: {task.task_description} (优先级: P{priority_value})")
            return True
            
        except Exception as e:
            logger.error(f"任务提交失败: {e}")
            return False
    
    def execute_next_task(self) -> Optional[TaskPlan]:
        """执行下一个任务"""
        if self.task_queue.empty():
            return None
        
        try:
            # 从队列取出任务
            _, _, task = self.task_queue.get_nowait()
            
            logger.info(f"开始执行任务: {task.task_description}")
            
            # 执行任务
            success = self._execute_task(task)
            
            if success:
                task.status = TaskStatus.COMPLETED
                logger.info(f"任务完成: {task.task_description}")
            else:
                task.status = TaskStatus.FAILED
                logger.error(f"任务失败: {task.task_description}")
            
            # 记录历史
            self.task_history.append(task)
            
            return task
            
        except queue.Empty:
            return None
        except Exception as e:
            logger.error(f"任务执行异常: {e}")
            return None
    
    def _execute_task(self, task: TaskPlan) -> bool:
        """执行任务（内部方法）"""
        task.status = TaskStatus.EXECUTING
        self.executing_tasks[task.plan_id] = task
        
        try:
            # 执行每个动作
            for action in task.actions:
                success = self._execute_action(action)
                if not success:
                    logger.error(f"动作执行失败: {action.action_type.value}")
                    return False
                
                # 模拟动作耗时
                if action.expected_duration > 0:
                    time.sleep(min(action.expected_duration, 2))  # 最多等待2秒
            
            return True
            
        except Exception as e:
            logger.error(f"任务执行异常: {e}")
            return False
        
        finally:
            # 清理
            if task.plan_id in self.executing_tasks:
                del self.executing_tasks[task.plan_id]
    
    def _execute_action(self, action: Action) -> bool:
        """执行单个动作"""
        from utils.data_types import ActionType
        
        logger.info(f"执行动作: {action.action_type.value} -> {action.target}")
        
        if action.action_type == ActionType.SPEAK:
            # 语音输出
            text = action.parameters.get("text", "")
            logger.info(f"[语音输出] {text}")
            return True
        
        elif action.action_type == ActionType.DEVICE_CONTROL:
            # 设备控制
            device_id = action.target
            command = action.parameters.get("command")
            params = action.parameters.get("params", {})
            
            return self.device_manager.execute_device_command(
                device_id, command, params
            )
        
        elif action.action_type == ActionType.NOTIFICATION:
            # 通知
            message = action.parameters.get("message", "")
            logger.info(f"[通知] {message}")
            return True
        
        elif action.action_type == ActionType.RECORD:
            # 记录
            data = action.parameters.get("data", {})
            logger.info(f"[记录] {data}")
            return True
        
        else:
            logger.warning(f"未知动作类型: {action.action_type}")
            return False
    
    def get_queue_size(self) -> int:
        """获取队列大小"""
        return self.task_queue.qsize()
    
    def get_executing_tasks(self) -> List[TaskPlan]:
        """获取正在执行的任务"""
        return list(self.executing_tasks.values())
    
    def get_task_history(self, limit: int = 10) -> List[TaskPlan]:
        """获取任务历史"""
        return self.task_history[-limit:]
    
    def clear_queue(self):
        """清空队列"""
        while not self.task_queue.empty():
            try:
                self.task_queue.get_nowait()
            except queue.Empty:
                break
        logger.info("任务队列已清空")
