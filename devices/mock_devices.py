"""
模拟设备实现
"""
import time
from typing import Dict, Any, List
from devices.rma_protocol import IRMADevice, DeviceType, DeviceStatus
from utils.logger import setup_logger

logger = setup_logger("mock_devices")

class MockRobotArm(IRMADevice):
    """模拟机械臂"""
    
    def __init__(self, device_id: str, name: str):
        self.device_id = device_id
        self.name = name
        self.status = DeviceStatus.IDLE
        self.position = [0, 0, 0]  # x, y, z
        self.gripper_open = True
        logger.info(f"机械臂初始化: {name}")
    
    def get_id(self) -> str:
        return self.device_id
    
    def get_type(self) -> DeviceType:
        return DeviceType.ROBOT_ARM
    
    def get_status(self) -> DeviceStatus:
        return self.status
    
    def get_capabilities(self) -> List[str]:
        return ["move", "pick", "place", "rotate"]
    
    def execute_command(self, command: str, parameters: Dict[str, Any]) -> bool:
        """执行命令"""
        logger.info(f"[{self.name}] 执行命令: {command}, 参数: {parameters}")
        
        self.status = DeviceStatus.BUSY
        
        try:
            if command == "move":
                target = parameters.get("target", [0, 0, 0])
                self._move_to(target)
            elif command == "pick":
                object_id = parameters.get("object_id")
                self._pick_object(object_id)
            elif command == "place":
                location = parameters.get("location", [0, 0, 0])
                self._place_object(location)
            else:
                logger.warning(f"未知命令: {command}")
                return False
            
            self.status = DeviceStatus.IDLE
            return True
            
        except Exception as e:
            logger.error(f"命令执行失败: {e}")
            self.status = DeviceStatus.ERROR
            return False
    
    def _move_to(self, target: List[float]):
        """移动到目标位置"""
        logger.info(f"[{self.name}] 移动到位置: {target}")
        time.sleep(0.5)  # 模拟移动时间
        self.position = target
    
    def _pick_object(self, object_id: str):
        """抓取物体"""
        logger.info(f"[{self.name}] 抓取物体: {object_id}")
        time.sleep(0.3)
        self.gripper_open = False
    
    def _place_object(self, location: List[float]):
        """放置物体"""
        logger.info(f"[{self.name}] 放置物体到: {location}")
        time.sleep(0.3)
        self.gripper_open = True
    
    def get_state(self) -> Dict[str, Any]:
        return {
            "position": self.position,
            "gripper_open": self.gripper_open,
            "status": self.status.value
        }
    
    def reset(self) -> bool:
        self.position = [0, 0, 0]
        self.gripper_open = True
        self.status = DeviceStatus.IDLE
        logger.info(f"[{self.name}] 已重置")
        return True

class MockVacuum(IRMADevice):
    """模拟扫地机器人"""
    
    def __init__(self, device_id: str, name: str):
        self.device_id = device_id
        self.name = name
        self.status = DeviceStatus.IDLE
        self.is_cleaning = False
        self.battery = 100
        logger.info(f"扫地机器人初始化: {name}")
    
    def get_id(self) -> str:
        return self.device_id
    
    def get_type(self) -> DeviceType:
        return DeviceType.VACUUM
    
    def get_status(self) -> DeviceStatus:
        return self.status
    
    def get_capabilities(self) -> List[str]:
        return ["start_cleaning", "stop_cleaning", "return_home"]
    
    def execute_command(self, command: str, parameters: Dict[str, Any]) -> bool:
        logger.info(f"[{self.name}] 执行命令: {command}")
        
        try:
            if command == "start_cleaning":
                self.status = DeviceStatus.BUSY
                self.is_cleaning = True
                logger.info(f"[{self.name}] 开始清扫")
                time.sleep(1)
            elif command == "stop_cleaning":
                self.is_cleaning = False
                self.status = DeviceStatus.IDLE
                logger.info(f"[{self.name}] 停止清扫")
            elif command == "return_home":
                self.is_cleaning = False
                self.status = DeviceStatus.BUSY
                logger.info(f"[{self.name}] 返回充电座")
                time.sleep(0.5)
                self.status = DeviceStatus.IDLE
            else:
                return False
            
            return True
            
        except Exception as e:
            logger.error(f"命令执行失败: {e}")
            self.status = DeviceStatus.ERROR
            return False
    
    def get_state(self) -> Dict[str, Any]:
        return {
            "is_cleaning": self.is_cleaning,
            "battery": self.battery,
            "status": self.status.value
        }
    
    def reset(self) -> bool:
        self.is_cleaning = False
        self.battery = 100
        self.status = DeviceStatus.IDLE
        return True

class MockSmartLight(IRMADevice):
    """模拟智能灯"""
    
    def __init__(self, device_id: str, name: str):
        self.device_id = device_id
        self.name = name
        self.status = DeviceStatus.IDLE
        self.is_on = False
        self.brightness = 0
        logger.info(f"智能灯初始化: {name}")
    
    def get_id(self) -> str:
        return self.device_id
    
    def get_type(self) -> DeviceType:
        return DeviceType.SMART_LIGHT
    
    def get_status(self) -> DeviceStatus:
        return self.status
    
    def get_capabilities(self) -> List[str]:
        return ["turn_on", "turn_off", "set_brightness"]
    
    def execute_command(self, command: str, parameters: Dict[str, Any]) -> bool:
        logger.info(f"[{self.name}] 执行命令: {command}, 参数: {parameters}")
        
        try:
            if command == "turn_on":
                self.is_on = True
                self.brightness = parameters.get("brightness", 100)
                logger.info(f"[{self.name}] 开灯，亮度: {self.brightness}%")
            elif command == "turn_off":
                self.is_on = False
                self.brightness = 0
                logger.info(f"[{self.name}] 关灯")
            elif command == "set_brightness":
                brightness = parameters.get("brightness", 50)
                self.brightness = max(0, min(100, brightness))
                logger.info(f"[{self.name}] 设置亮度: {self.brightness}%")
            else:
                return False
            
            return True
            
        except Exception as e:
            logger.error(f"命令执行失败: {e}")
            return False
    
    def get_state(self) -> Dict[str, Any]:
        return {
            "is_on": self.is_on,
            "brightness": self.brightness,
            "status": self.status.value
        }
    
    def reset(self) -> bool:
        self.is_on = False
        self.brightness = 0
        return True

class MockSmartCurtain(IRMADevice):
    """模拟智能窗帘"""
    
    def __init__(self, device_id: str, name: str):
        self.device_id = device_id
        self.name = name
        self.status = DeviceStatus.IDLE
        self.position = 0  # 0=关闭, 100=完全打开
        logger.info(f"智能窗帘初始化: {name}")
    
    def get_id(self) -> str:
        return self.device_id
    
    def get_type(self) -> DeviceType:
        return DeviceType.SMART_CURTAIN
    
    def get_status(self) -> DeviceStatus:
        return self.status
    
    def get_capabilities(self) -> List[str]:
        return ["open", "close", "set_position"]
    
    def execute_command(self, command: str, parameters: Dict[str, Any]) -> bool:
        logger.info(f"[{self.name}] 执行命令: {command}")
        
        try:
            self.status = DeviceStatus.BUSY
            
            if command == "open":
                self.position = 100
                logger.info(f"[{self.name}] 打开窗帘")
                time.sleep(0.5)
            elif command == "close":
                self.position = 0
                logger.info(f"[{self.name}] 关闭窗帘")
                time.sleep(0.5)
            elif command == "set_position":
                position = parameters.get("position", 50)
                self.position = max(0, min(100, position))
                logger.info(f"[{self.name}] 设置位置: {self.position}%")
                time.sleep(0.3)
            else:
                return False
            
            self.status = DeviceStatus.IDLE
            return True
            
        except Exception as e:
            logger.error(f"命令执行失败: {e}")
            self.status = DeviceStatus.ERROR
            return False
    
    def get_state(self) -> Dict[str, Any]:
        return {
            "position": self.position,
            "status": self.status.value
        }
    
    def reset(self) -> bool:
        self.position = 0
        self.status = DeviceStatus.IDLE
        return True
