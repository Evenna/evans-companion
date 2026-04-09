"""
Nexus Core 主程序
你的随身贾维斯，物理世界的AI指挥官

默认不再运行内置「手机充电 / 访客 / 家居」三段预制场景；需要旧演示请加 --demo。
实时摄像头 + Gemini 智脑请使用 Web：uvicorn server:app --host 0.0.0.0 --port 8000
"""
import argparse
import time
import sys
from pathlib import Path

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent))

from config import Config
from utils.logger import setup_logger
from utils.data_types import (
    TaskPlan, TaskPriority, Action, ActionType,
    Need, IntentType
)

from core.perception import PerceptionModule, MockAudioModule
from core.analysis import AnalysisModule
from core.decision import DecisionModule
from core.interaction import InteractionModule

from memory.omni_memory import OmniMemory
from memory.relation_graph import RelationGraph

from devices.device_manager import DeviceManager
from scheduler.task_scheduler import TaskScheduler

logger = setup_logger("main")

class NexusCore:
    """Nexus Core 主系统"""
    
    def __init__(self):
        logger.info("="*60)
        logger.info("Nexus Core 系统启动中...")
        logger.info("="*60)
        
        # 初始化配置
        Config.init_dirs()
        
        # 初始化核心模块
        self.perception = PerceptionModule(camera_index=Config.CAMERA_INDEX)
        self.audio = MockAudioModule()
        self.analysis = AnalysisModule()
        self.decision = DecisionModule()
        self.interaction = InteractionModule()
        
        # 初始化记忆系统
        self.memory = OmniMemory()
        self.relation_graph = RelationGraph()
        
        # 初始化设备管理
        self.device_manager = DeviceManager()
        self.device_manager.initialize_mock_devices()
        
        # 初始化任务调度
        self.scheduler = TaskScheduler(self.device_manager)
        
        # 系统状态
        self.is_running = False
        self.frame_count = 0
        
        logger.info("Nexus Core 系统初始化完成")
    
    def start(self):
        """启动系统"""
        logger.info("启动 Nexus Core...")
        
        # 启动感知模块
        if not self.perception.start():
            logger.error("感知模块启动失败")
            return False
        
        self.audio.start_listening()
        self.is_running = True
        
        logger.info("✓ Nexus Core 已启动")
        return True
    
    def stop(self):
        """停止系统"""
        logger.info("停止 Nexus Core...")
        
        self.is_running = False
        self.perception.stop()
        self.audio.stop_listening()
        
        logger.info("✓ Nexus Core 已停止")
    
    def run_loop(self, max_iterations: int = 10, infinite: bool = False):
        """主循环：感知→分析→决策→调度（无预制剧本）"""
        if infinite:
            logger.info("开始主循环 (持续运行，Ctrl+C 停止)...")
        else:
            logger.info(f"开始主循环 (最多 {max_iterations} 次迭代)...")

        iteration = 0

        while self.is_running and (infinite or iteration < max_iterations):
            iteration += 1
            logger.info(f"\n{'='*60}")
            if infinite:
                logger.info(f"迭代 {iteration}")
            else:
                logger.info(f"迭代 {iteration}/{max_iterations}")
            logger.info(f"{'='*60}")
            
            # 1. 感知
            perception_frame = self.perception.get_frame()
            if not perception_frame:
                logger.warning("未获取到感知帧")
                time.sleep(0.5)
                continue
            
            logger.info(f"感知: 检测到 {len(perception_frame.faces)} 个人脸")
            
            # 2. 分析
            analysis_result = self.analysis.analyze(perception_frame)
            logger.info(f"分析: {analysis_result.context_summary}")
            
            if analysis_result.intents:
                logger.info(f"识别到意图: {analysis_result.primary_intent.intent_type.value}")
            
            # 3. 决策
            decision_result = self.decision.decide(
                perception_frame,
                analysis_result,
                self.memory,
                self.relation_graph
            )
            
            if decision_result.primary_need:
                logger.info(f"识别到需求: {decision_result.primary_need.description}")
            
            # 4. 任务调度
            if decision_result.selected_plan:
                self.scheduler.submit_task(decision_result.selected_plan)
                logger.info(f"提交任务: {decision_result.selected_plan.task_description}")
            
            # 执行队列中的任务
            executed_task = self.scheduler.execute_next_task()
            if executed_task:
                logger.info(f"执行完成: {executed_task.task_description}")
            
            # 5. 记忆更新
            self._update_memory(perception_frame, analysis_result, decision_result)
            
            # 6. 输出交互
            if decision_result.selected_plan:
                self.interaction.generate_output(decision_result.selected_plan)
            
            # 等待
            time.sleep(1)
        
        logger.info(f"\n主循环结束，共执行 {iteration} 次迭代")

    def _update_memory(self, perception_frame, analysis_result, decision_result):
        """更新记忆"""
        # 存储感知帧到短期记忆
        self.memory.store_short_term({
            "type": "perception",
            "timestamp": perception_frame.timestamp,
            "faces": len(perception_frame.faces),
            "scene": perception_frame.scene_type
        })
        
        # 存储分析结果到中期记忆
        if analysis_result.primary_intent:
            self.memory.store_medium_term(
                {
                    "summary": analysis_result.context_summary,
                    "tags": [
                        "intent",
                        analysis_result.primary_intent.intent_type.value,
                    ],
                },
                importance=0.7,
            )
        
        # 更新关系图谱
        for person in analysis_result.identified_persons:
            self.relation_graph.update_person(person)
    
    def demo_scenario_1(self):
        """演示场景1: 手机充电任务"""
        logger.info("\n" + "="*60)
        logger.info("演示场景1: 手机充电任务")
        logger.info("="*60)
        
        # 模拟检测到手机电量低
        logger.info("检测到: 手机电量仅剩10%，且放在书架高处")
        
        # 创建任务计划
        task = TaskPlan(
            task_description="帮助用户将手机放到充电座",
            priority=TaskPriority.P1_HIGH,
            actions=[
                Action(
                    action_type=ActionType.SPEAK,
                    target="user",
                    parameters={"text": "检测到您的手机电量较低，我来帮您充电"}
                ),
                Action(
                    action_type=ActionType.DEVICE_CONTROL,
                    target="robot_arm_01",
                    parameters={
                        "command": "move",
                        "params": {"target": [100, 200, 150]}
                    },
                    expected_duration=2.0
                ),
                Action(
                    action_type=ActionType.DEVICE_CONTROL,
                    target="robot_arm_01",
                    parameters={
                        "command": "pick",
                        "params": {"object_id": "phone"}
                    },
                    expected_duration=1.0
                ),
                Action(
                    action_type=ActionType.DEVICE_CONTROL,
                    target="robot_arm_01",
                    parameters={
                        "command": "place",
                        "params": {"location": [50, 50, 10]}
                    },
                    expected_duration=1.0
                ),
                Action(
                    action_type=ActionType.SPEAK,
                    target="user",
                    parameters={"text": "手机已放置充电，预计1小时充满"}
                )
            ],
            estimated_duration=5.0,
            success_probability=0.9
        )
        
        # 提交并执行任务
        self.scheduler.submit_task(task)
        self.scheduler.execute_next_task()
        
        logger.info("✓ 场景1演示完成")
    
    def demo_scenario_2(self):
        """演示场景2: 访客身份识别"""
        logger.info("\n" + "="*60)
        logger.info("演示场景2: 访客身份识别")
        logger.info("="*60)
        
        logger.info("检测到: 有陌生人按门铃")
        
        # 创建任务计划
        task = TaskPlan(
            task_description="识别访客身份并提醒用户",
            priority=TaskPriority.P0_CRITICAL,
            actions=[
                Action(
                    action_type=ActionType.SPEAK,
                    target="user",
                    parameters={"text": "检测到门口有访客，正在识别身份..."}
                ),
                Action(
                    action_type=ActionType.NOTIFICATION,
                    target="user",
                    parameters={"message": "警告：此人可能是推销员，建议谨慎开门"}
                ),
                Action(
                    action_type=ActionType.RECORD,
                    target="system",
                    parameters={"data": {"event": "suspicious_visitor", "timestamp": time.time()}}
                )
            ],
            estimated_duration=2.0,
            success_probability=0.85
        )
        
        self.scheduler.submit_task(task)
        self.scheduler.execute_next_task()
        
        logger.info("✓ 场景2演示完成")
    
    def demo_scenario_3(self):
        """演示场景3: 智能家居联动"""
        logger.info("\n" + "="*60)
        logger.info("演示场景3: 智能家居联动（晨起场景）")
        logger.info("="*60)
        
        logger.info("检测到: 用户起床")
        
        # 创建任务计划
        task = TaskPlan(
            task_description="晨起智能家居联动",
            priority=TaskPriority.P2_NORMAL,
            actions=[
                Action(
                    action_type=ActionType.SPEAK,
                    target="user",
                    parameters={"text": "早上好！为您准备舒适的环境"}
                ),
                Action(
                    action_type=ActionType.DEVICE_CONTROL,
                    target="smart_curtain_01",
                    parameters={"command": "open"},
                    expected_duration=0.5
                ),
                Action(
                    action_type=ActionType.DEVICE_CONTROL,
                    target="smart_light_01",
                    parameters={
                        "command": "turn_on",
                        "params": {"brightness": 60}
                    },
                    expected_duration=0.2
                ),
                Action(
                    action_type=ActionType.SPEAK,
                    target="user",
                    parameters={"text": "今天天气晴朗，温度22度，适合外出"}
                )
            ],
            estimated_duration=3.0,
            success_probability=0.95
        )
        
        self.scheduler.submit_task(task)
        self.scheduler.execute_next_task()
        
        logger.info("✓ 场景3演示完成")
    
    def print_system_status(self):
        """打印系统状态"""
        logger.info("\n" + "="*60)
        logger.info("系统状态")
        logger.info("="*60)
        
        # 设备状态
        devices_status = self.device_manager.get_all_devices_status()
        logger.info(f"\n设备数量: {len(devices_status)}")
        for device_id, status in devices_status.items():
            logger.info(f"  - {device_id}: {status['status']} ({status['type']})")
        
        # 记忆统计
        memory_stats = self.memory.get_statistics()
        logger.info(f"\n记忆统计:")
        logger.info(f"  - 短期记忆: {memory_stats['short_term']}")
        logger.info(f"  - 中期记忆: {memory_stats['medium_term']}")
        logger.info(f"  - 长期记忆: {memory_stats['long_term']}")
        
        # 关系图谱
        graph_stats = self.relation_graph.get_statistics()
        logger.info(f"\n关系图谱:")
        logger.info(f"  - 人物数量: {graph_stats['total_persons']}")
        logger.info(f"  - 关系数量: {graph_stats['total_relations']}")
        
        # 任务队列
        logger.info(f"\n任务队列:")
        logger.info(f"  - 待执行任务: {self.scheduler.get_queue_size()}")
        logger.info(f"  - 历史任务: {len(self.scheduler.get_task_history())}")

def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description="Nexus Core CLI（默认：仅感知-分析-决策循环，无预制场景）"
    )
    parser.add_argument(
        "--demo",
        action="store_true",
        help="运行旧版三段预制演示（机械臂充电 / 访客 / 晨起家居）并跑 3 次主循环",
    )
    parser.add_argument(
        "-n",
        "--iterations",
        type=int,
        default=30,
        metavar="N",
        help="主循环迭代次数（非 --demo 时有效，默认 30；0 表示一直运行直到 Ctrl+C）",
    )
    args = parser.parse_args()

    print("\n" + "="*60)
    print("Nexus Core - 你的随身贾维斯")
    print("物理世界的AI指挥官")
    print("="*60 + "\n")

    if not args.demo:
        print(
            "提示：实时摄像头 + Gemini 画面分析请启动 Web 服务：\n"
            "  uvicorn server:app --host 0.0.0.0 --port 8000\n"
            "浏览器打开 http://127.0.0.1:8000\n"
        )

    nexus = NexusCore()

    if not nexus.start():
        print("系统启动失败")
        return

    try:
        if args.demo:
            print("\n【--demo】运行内置三段预制场景 + 主循环 3 次...\n")
            nexus.demo_scenario_1()
            time.sleep(1)
            nexus.demo_scenario_2()
            time.sleep(1)
            nexus.demo_scenario_3()
            time.sleep(1)
            nexus.print_system_status()
            print("\n主循环（3 次迭代）...")
            nexus.run_loop(max_iterations=3)
        else:
            inf = args.iterations == 0
            if inf:
                print("\n主循环：持续运行（Ctrl+C 停止）...\n")
            else:
                print(f"\n主循环：{args.iterations} 次迭代（感知→分析→决策，无预制任务）...\n")
            nexus.run_loop(max_iterations=max(args.iterations, 1), infinite=inf)

    except KeyboardInterrupt:
        print("\n用户中断")
    except Exception as e:
        print(f"\n系统异常: {e}")
        import traceback
        traceback.print_exc()
    finally:
        nexus.stop()
        print("\n系统已关闭")

if __name__ == "__main__":
    main()
