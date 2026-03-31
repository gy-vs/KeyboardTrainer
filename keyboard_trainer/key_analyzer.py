"""
按键分析器模块

分析测试结果并识别薄弱按键。

Requirements: 1.3, 1.4, 1.5, 2.4, 2.5, 3.1, 3.2, 3.3
"""

from collections import defaultdict
from dataclasses import dataclass
from typing import Dict, List

from keyboard_trainer.models import (
    KeyStatistics,
    KeystrokeRecord,
    KeystrokeStatus,
    WeakKey,
)


@dataclass
class KeyAnalysisResult:
    """按键分析结果"""
    overall_accuracy: float
    overall_wpm: float
    overall_cpm: float
    duration: float
    per_key_statistics: Dict[str, KeyStatistics]


class KeyAnalyzer:
    """按键分析器，分析测试结果并识别薄弱按键"""
    
    ACCURACY_THRESHOLD = 0.90  # 准确率阈值
    RESPONSE_TIME_THRESHOLD = 500  # 响应时间阈值（毫秒）
    
    def __init__(self):
        """初始化按键分析器"""
        pass
    
    def analyze_keystrokes(self, keystrokes: List[KeystrokeRecord], duration: float = None) -> KeyAnalysisResult:
        """
        分析按键记录
        
        Args:
            keystrokes: 按键记录列表
            duration: 测试持续时间（秒），如果为 None 则从按键记录计算
            
        Returns:
            KeyAnalysisResult 包含整体和每键统计
        """
        if not keystrokes:
            return KeyAnalysisResult(
                overall_accuracy=0.0,
                overall_wpm=0.0,
                overall_cpm=0.0,
                duration=0.0,
                per_key_statistics={}
            )
        
        # 计算整体准确率
        correct_count = sum(1 for k in keystrokes if k.status == KeystrokeStatus.CORRECT)
        overall_accuracy = correct_count / len(keystrokes)
        
        # 计算持续时间
        if duration is None:
            if len(keystrokes) > 1:
                duration = (keystrokes[-1].timestamp - keystrokes[0].timestamp) / 1000  # 转换为秒
            else:
                duration = 0.0
        
        # 计算 WPM 和 CPM
        if duration > 0:
            duration_minutes = duration / 60
            overall_cpm = correct_count / duration_minutes
            overall_wpm = (correct_count / 5) / duration_minutes  # 标准：5 字符 = 1 词
        else:
            overall_cpm = 0.0
            overall_wpm = 0.0
        
        # 计算每键统计
        per_key_statistics = self._calculate_per_key_statistics(keystrokes)
        
        return KeyAnalysisResult(
            overall_accuracy=overall_accuracy,
            overall_wpm=overall_wpm,
            overall_cpm=overall_cpm,
            duration=duration,
            per_key_statistics=per_key_statistics
        )
    
    def _calculate_per_key_statistics(self, keystrokes: List[KeystrokeRecord]) -> Dict[str, KeyStatistics]:
        """计算每个按键的统计数据"""
        # 按期望字符分组
        key_data: Dict[str, Dict] = defaultdict(lambda: {
            'total': 0,
            'correct': 0,
            'response_times': []
        })
        
        for ks in keystrokes:
            key = ks.expected_char
            key_data[key]['total'] += 1
            if ks.status == KeystrokeStatus.CORRECT:
                key_data[key]['correct'] += 1
            key_data[key]['response_times'].append(ks.response_time)
        
        # 构建统计结果
        result = {}
        for key, data in key_data.items():
            accuracy = data['correct'] / data['total'] if data['total'] > 0 else 0.0
            avg_response_time = sum(data['response_times']) / len(data['response_times']) if data['response_times'] else 0.0
            
            result[key] = KeyStatistics(
                key=key,
                total_attempts=data['total'],
                correct_attempts=data['correct'],
                accuracy=accuracy,
                average_response_time=avg_response_time
            )
        
        return result
    
    def calculate_per_key_accuracy(self, keystrokes: List[KeystrokeRecord]) -> Dict[str, float]:
        """
        计算每个按键的准确率
        
        Args:
            keystrokes: 按键记录列表
            
        Returns:
            按键到准确率的映射
        """
        stats = self._calculate_per_key_statistics(keystrokes)
        return {key: s.accuracy for key, s in stats.items()}
    
    def calculate_per_key_speed(self, keystrokes: List[KeystrokeRecord]) -> Dict[str, float]:
        """
        计算每个按键的平均响应时间
        
        Args:
            keystrokes: 按键记录列表
            
        Returns:
            按键到平均响应时间（毫秒）的映射
        """
        stats = self._calculate_per_key_statistics(keystrokes)
        return {key: s.average_response_time for key, s in stats.items()}
    
    def identify_weak_keys(self, analysis: KeyAnalysisResult) -> List[WeakKey]:
        """
        识别薄弱按键
        
        准确率 < 90% 或响应时间 > 500ms 的按键被识别为薄弱按键
        
        Args:
            analysis: 按键分析结果
            
        Returns:
            薄弱按键列表
        """
        weak_keys = []
        
        for key, stats in analysis.per_key_statistics.items():
            if stats.accuracy < self.ACCURACY_THRESHOLD or stats.average_response_time > self.RESPONSE_TIME_THRESHOLD:
                # 计算严重程度评分
                severity = self._calculate_severity(stats)
                weak_keys.append(WeakKey(
                    key=key,
                    accuracy=stats.accuracy,
                    average_response_time=stats.average_response_time,
                    severity_score=severity
                ))
        
        return weak_keys
    
    def _calculate_severity(self, stats: KeyStatistics) -> float:
        """
        计算薄弱按键的严重程度评分
        
        评分越高表示越需要训练
        """
        # 准确率惩罚：准确率越低，惩罚越高
        accuracy_penalty = (1.0 - stats.accuracy) * 100
        
        # 响应时间惩罚：超过阈值的部分
        time_penalty = 0.0
        if stats.average_response_time > self.RESPONSE_TIME_THRESHOLD:
            time_penalty = (stats.average_response_time - self.RESPONSE_TIME_THRESHOLD) / 10
        
        return accuracy_penalty + time_penalty
    
    def rank_weak_keys(self, weak_keys: List[WeakKey]) -> List[WeakKey]:
        """
        按严重程度排序薄弱按键
        
        排序规则：
        1. 首先按准确率升序（准确率低的在前）
        2. 准确率相同时，按响应时间降序（响应时间高的在前）
        
        Args:
            weak_keys: 薄弱按键列表
            
        Returns:
            排序后的薄弱按键列表
        """
        return sorted(
            weak_keys,
            key=lambda wk: (wk.accuracy, -wk.average_response_time)
        )
