"""
设备管理器
"""
from typing import Dict, List, Optional
from devices.rma_protocol import IRMADevice, DeviceType, DeviceStatus
from devices.mock_devices import MockRobotArm, MockVacuum, MockSmartLight, MockSmartCurtain
from utils.logger import setup_logger

logger = setup_logger("device_manager")

class DeviceManager:
    """设备管理器"""
    
    def __init__(self):
        self.devices: Dict[str, IRMADevice] = {}
        logger.info("设备管理器初始化完成")
    
    def register_device(self, device: IRMADevice) -> bool:
        """注册设备"""
        device_id = device.get_id()
        
        if device_id in self.devices:
            logger.warning(f"设备已存在: {device_id}")
            return False
        
        self.devices[device_id] = device
        logger.info(f"注册设备: {device_id} ({device.get_type().value})")
        return True
    
    def unregister_device(self, device_id: str) -> bool:
        """注销设备"""
        if device_id not in self.devices:
            logger.warning(f"设备不存在: {device_id}")
            return False
        
        del self.devices[device_id]
        logger.info(f"注销设备: {device_id}")
        return True
    
    def get_device(self, device_id: str) -> Optional[IRMADevice]:
        """获取设备"""
        return self.devices.get(device_id)
    
    def get_devices_by_type(self, device_type: DeviceType) -> List[IRMADevice]:
        """按类型获取设备"""
        return [d for d in self.devices.values() if d.get_type() == device_type]
    
    def get_idle_devices(self) -> List[IRMADevice]:
        """获取空闲设备"""
        return [d for d in self.devices.values() if d.get_status() == DeviceStatus.IDLE]
    
    def get_device_by_capability(self, capability: str) -> List[IRMADevice]:
        """按能力查找设备"""
        return [d for d in self.devices.values() if capability in d.get_capabilities()]
    
    def execute_device_command(
        self,
        device_id: str,
        command: str,
        parameters: Dict = None
    ) -> bool:
        """执行设备命令"""
        device = self.get_device(device_id)
        
        if not device:
            logger.error(f"设备不存在: {device_id}")
            return False
        
        if device.get_status() == DeviceStatus.OFFLINE:
            logger.error(f"设备离线: {device_id}")
            return False
        
        if parameters is None:
            parameters = {}
        
        return device.execute_command(command, parameters)
    
    def get_all_devices_status(self) -> Dict[str, Dict]:
        """获取所有设备状态"""
        status = {}
        for device_id, device in self.devices.items():
            status[device_id] = {
                "type": device.get_type().value,
                "status": device.get_status().value,
                "state": device.get_state()
            }
        return status
    
    def reset_all_devices(self):
        """重置所有设备"""
        for device in self.devices.values():
            device.reset()
        logger.info("所有设备已重置")
    
    def initialize_mock_devices(self):
        """初始化模拟设备"""
        # 机械臂
        robot_arm = MockRobotArm("robot_arm_01", "桌面机械臂")
        self.register_device(robot_arm)
        
        # 扫地机器人
        vacuum = MockVacuum("vacuum_01", "扫地机器人")
        self.register_device(vacuum)
        
        # 智能灯
        light = MockSmartLight("smart_light_01", "客厅智能灯")
        self.register_device(light)
        
        # 智能窗帘
        curtain = MockSmartCurtain("smart_curtain_01", "卧室智能窗帘")
        self.register_device(curtain)
        
        logger.info(f"初始化了 {len(self.devices)} 个模拟设备")
