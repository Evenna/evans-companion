"""
RMA机器人操控抽象层协议 - 统一设备控制接口
"""
from abc import ABC, abstractmethod
from typing import Dict, Any, List
from enum import Enum

class DeviceType(Enum):
    """设备类型"""
    ROBOT_ARM = "robot_arm"
    VACUUM = "vacuum"
    SMART_LIGHT = "smart_light"
    SMART_CURTAIN = "smart_curtain"
    MOBILE_BASE = "mobile_base"

class DeviceStatus(Enum):
    """设备状态"""
    IDLE = "idle"
    BUSY = "busy"
    ERROR = "error"
    OFFLINE = "offline"

class IRMADevice(ABC):
    """RMA设备接口"""
    
    @abstractmethod
    def get_id(self) -> str:
        """获取设备ID"""
        pass
    
    @abstractmethod
    def get_type(self) -> DeviceType:
        """获取设备类型"""
        pass
    
    @abstractmethod
    def get_status(self) -> DeviceStatus:
        """获取设备状态"""
        pass
    
    @abstractmethod
    def get_capabilities(self) -> List[str]:
        """获取设备能力列表"""
        pass
    
    @abstractmethod
    def execute_command(self, command: str, parameters: Dict[str, Any]) -> bool:
        """执行命令"""
        pass
    
    @abstractmethod
    def get_state(self) -> Dict[str, Any]:
        """获取设备状态信息"""
        pass
    
    @abstractmethod
    def reset(self) -> bool:
        """重置设备"""
        pass
