"""全局配置"""
from pathlib import Path


class Config:
    """运行时可调参数"""

    # 摄像头索引；-1 表示使用模拟帧，不打开真实设备
    CAMERA_INDEX: int = -1

    @staticmethod
    def init_dirs() -> None:
        """创建数据目录（日志、缓存等）"""
        base = Path(__file__).resolve().parent.parent / "data"
        base.mkdir(parents=True, exist_ok=True)
