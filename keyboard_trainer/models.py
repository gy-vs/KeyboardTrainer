"""
核心数据模型

包含键盘练习工具的所有数据类型定义，包括枚举、数据类和类型别名。

Requirements: 1.2, 1.7
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional


class TestType(Enum):
    """
    测试类型枚举
    
    定义系统支持的三种测试模式。
    """
    BASIC = "basic"        # 基础测试
    TRAINING = "training"  # 针对性训练
    ADVANCED = "advanced"  # 进阶测试（自定义文章）


class KeystrokeStatus(Enum):
    """
    按键状态枚举
    
    表示单次按键的结果状态。
    """
    CORRECT = "correct"      # 正确输入
    INCORRECT = "incorrect"  # 错误输入
    MISSED = "missed"        # 漏输入


class FingerPosition(Enum):
    """
    手指位置枚举
    
    用于虚拟键盘的手指位置指南，帮助用户学习正确的触打指法。
    """
    LEFT_PINKY = "left_pinky"      # 左手小指
    LEFT_RING = "left_ring"        # 左手无名指
    LEFT_MIDDLE = "left_middle"    # 左手中指
    LEFT_INDEX = "left_index"      # 左手食指
    LEFT_THUMB = "left_thumb"      # 左手拇指
    RIGHT_THUMB = "right_thumb"    # 右手拇指
    RIGHT_INDEX = "right_index"    # 右手食指
    RIGHT_MIDDLE = "right_middle"  # 右手中指
    RIGHT_RING = "right_ring"      # 右手无名指
    RIGHT_PINKY = "right_pinky"    # 右手小指


@dataclass
class KeystrokeRecord:
    """
    按键记录
    
    记录单次按键的详细信息，用于后续分析和统计。
    
    Attributes:
        expected_char: 期望输入的字符
        actual_char: 实际输入的字符
        timestamp: 按键时间戳（Unix 时间戳，秒）
        response_time: 响应时间（毫秒），从上一个按键到当前按键的时间间隔
        status: 按键状态（正确/错误/漏输入）
    """
    expected_char: str
    actual_char: str
    timestamp: float
    response_time: float  # 毫秒
    status: KeystrokeStatus


@dataclass
class KeyStatistics:
    """
    单个按键的统计数据
    
    汇总某个按键在测试中的表现数据。
    
    Attributes:
        key: 按键字符
        total_attempts: 总尝试次数
        correct_attempts: 正确次数
        accuracy: 准确率（0.0 - 1.0）
        average_response_time: 平均响应时间（毫秒）
    """
    key: str
    total_attempts: int
    correct_attempts: int
    accuracy: float  # 0.0 - 1.0
    average_response_time: float  # 毫秒
    
    @property
    def is_weak(self) -> bool:
        """
        判断是否为薄弱按键
        
        根据准确率阈值（90%）和响应时间阈值（500ms）判断。
        
        Returns:
            如果准确率低于 90% 或响应时间高于 500ms，返回 True
        """
        return self.accuracy < 0.90 or self.average_response_time > 500


@dataclass
class WeakKey:
    """
    薄弱按键
    
    表示需要重点训练的按键，包含其统计数据和严重程度评分。
    
    Attributes:
        key: 按键字符
        accuracy: 准确率（0.0 - 1.0）
        average_response_time: 平均响应时间（毫秒）
        severity_score: 综合严重程度评分（越高越需要训练）
    """
    key: str
    accuracy: float
    average_response_time: float
    severity_score: float  # 综合严重程度评分


@dataclass
class TestResult:
    """
    测试结果
    
    包含一次完整测试的所有数据，用于持久化存储和报告生成。
    
    Attributes:
        id: 唯一标识符
        test_type: 测试类型
        timestamp: 测试完成时间
        duration: 测试持续时间（秒）
        total_characters: 总字符数
        correct_characters: 正确字符数
        wpm: 每分钟词数 (Words Per Minute)
        cpm: 每分钟字符数 (Characters Per Minute)
        accuracy: 整体准确率（0.0 - 1.0）
        key_statistics: 每个按键的统计数据
        keystrokes: 所有按键记录
    """
    id: str
    test_type: TestType
    timestamp: datetime
    duration: float  # 秒
    total_characters: int
    correct_characters: int
    wpm: float
    cpm: float
    accuracy: float
    key_statistics: Dict[str, KeyStatistics]
    keystrokes: List[KeystrokeRecord] = field(default_factory=list)


@dataclass
class ProficiencyReport:
    """
    熟练度报告
    
    基于测试结果生成的熟练度分析报告。
    
    Attributes:
        test_result: 关联的测试结果
        weak_keys: 识别出的薄弱按键列表
        overall_grade: 整体评级（A, B, C, D, F）
        recommendations: 改进建议列表
    """
    test_result: TestResult
    weak_keys: List[WeakKey]
    overall_grade: str  # A, B, C, D, F
    recommendations: List[str]


@dataclass
class ProgressReport:
    """
    进步程度报告
    
    比较当前测试与基准测试的进步情况。
    
    Attributes:
        current_result: 当前测试结果
        baseline_result: 基准测试结果（通常是最近的基础测试）
        wpm_improvement: WPM 提升百分比
        accuracy_improvement: 准确率提升百分比
        improved_keys: 已改善的按键列表
        still_weak_keys: 仍然薄弱的按键列表
        conclusion: 总结结论
    """
    current_result: TestResult
    baseline_result: TestResult
    wpm_improvement: float  # 百分比
    accuracy_improvement: float  # 百分比
    improved_keys: List[str]
    still_weak_keys: List[str]
    conclusion: str


@dataclass
class TrainingSession:
    """
    训练会话
    
    记录一次针对性训练的会话数据。
    
    Attributes:
        id: 唯一标识符
        start_time: 开始时间
        target_weak_keys: 目标薄弱按键列表
        content: 训练内容文本
        current_position: 当前位置索引
        keystrokes: 按键记录列表
    """
    id: str
    start_time: datetime
    target_weak_keys: List[str]
    content: str
    current_position: int
    keystrokes: List[KeystrokeRecord] = field(default_factory=list)


@dataclass
class TrainingProgress:
    """
    训练进度
    
    表示当前训练会话的进度信息。
    
    Attributes:
        total_characters: 总字符数
        completed_characters: 已完成字符数
        current_accuracy: 当前准确率
        weak_key_improvements: 各薄弱按键的改善情况
    """
    total_characters: int
    completed_characters: int
    current_accuracy: float
    weak_key_improvements: Dict[str, float]


@dataclass
class FileLoadResult:
    """
    文件加载结果
    
    表示文件加载操作的结果。
    
    Attributes:
        success: 是否成功
        content: 文件内容（成功时）
        error_message: 错误消息（失败时）
        file_info: 文件信息（成功时）
    """
    success: bool
    content: Optional[str]
    error_message: Optional[str]
    file_info: Optional['FileInfo']


@dataclass
class FileInfo:
    """
    文件信息
    
    表示用户导入文件的基本信息。
    
    Attributes:
        path: 文件路径
        name: 文件名
        size: 文件大小（字节）
        character_count: 字符数
    """
    path: str
    name: str
    size: int
    character_count: int
