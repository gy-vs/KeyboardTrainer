"""
Keyboard Trainer - 键盘练习工具

一个基于 Python GUI 的键盘练习桌面应用工具，帮助用户通过基础测试、
针对性训练和进阶测试三个模块来提升打字技能。
"""

__version__ = "1.0.0"
__author__ = "Keyboard Trainer Team"

# 导出核心数据模型
from keyboard_trainer.models import (
    TestType,
    KeystrokeStatus,
    FingerPosition,
    KeystrokeRecord,
    KeyStatistics,
    WeakKey,
    TestResult,
    ProficiencyReport,
    ProgressReport,
    TrainingSession,
    TrainingProgress,
    FileLoadResult,
    FileInfo,
)
