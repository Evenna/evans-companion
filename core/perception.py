"""感知模块：摄像头或模拟帧"""
import time
import uuid
from typing import Optional

from utils.data_types import PerceptionFrame, FaceInfo, AudioData, Emotion
from utils.logger import setup_logger

logger = setup_logger("perception")


class PerceptionModule:
    """图像感知；CAMERA_INDEX < 0 时使用模拟数据，无需摄像头"""

    def __init__(self, camera_index: int = 0):
        self.camera_index = camera_index
        self._running = False
        self._cap = None

    def start(self) -> bool:
        if self.camera_index < 0:
            logger.info("使用模拟感知（无摄像头）")
            self._running = True
            return True
        try:
            import cv2  # type: ignore

            self._cap = cv2.VideoCapture(self.camera_index)
            if not self._cap.isOpened():
                logger.error("无法打开摄像头，回退到模拟感知")
                self.camera_index = -1
                self._running = True
                return True
            self._running = True
            logger.info(f"摄像头已启动: index={self.camera_index}")
            return True
        except Exception as e:
            logger.warning(f"OpenCV 不可用 ({e})，使用模拟感知")
            self.camera_index = -1
            self._running = True
            return True

    def stop(self) -> None:
        self._running = False
        if self._cap is not None:
            try:
                self._cap.release()
            except Exception:
                pass
            self._cap = None

    def get_frame(self) -> Optional[PerceptionFrame]:
        if not self._running:
            return None
        if self.camera_index < 0 or self._cap is None:
            return self._mock_frame()
        try:
            import cv2  # type: ignore

            ok, _ = self._cap.read()
            if not ok:
                return self._mock_frame()
            # 演示：未做人脸检测，返回与模拟一致的结构
            return self._mock_frame()
        except Exception:
            return self._mock_frame()

    def _mock_frame(self) -> PerceptionFrame:
        return PerceptionFrame(
            timestamp=time.time(),
            frame_id=str(uuid.uuid4())[:8],
            scene_type="indoor",
            faces=[
                FaceInfo(face_id="demo_user_01", emotion=Emotion.NEUTRAL),
            ],
            objects=["phone", "book"],
            audio=AudioData(transcript=""),
        )


class MockAudioModule:
    """模拟麦克风"""

    def __init__(self):
        self._listening = False

    def start_listening(self) -> None:
        self._listening = True
        logger.info("模拟音频：开始监听")

    def stop_listening(self) -> None:
        self._listening = False
        logger.info("模拟音频：停止监听")
