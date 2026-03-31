"""
报告生成器模块

生成熟练度和进步报告。

Requirements: 2.1, 2.2, 7.1, 7.2, 7.3, 7.4, 7.6
"""

from typing import List, Optional

from keyboard_trainer.data_store import DataStore
from keyboard_trainer.key_analyzer import KeyAnalyzer, KeyAnalysisResult
from keyboard_trainer.models import (
    ProficiencyReport,
    ProgressReport,
    TestResult,
    WeakKey,
)


class ReportGenerator:
    """报告生成器，生成熟练度和进步报告"""
    
    def __init__(self, data_store: Optional[DataStore] = None):
        """
        初始化报告生成器
        
        Args:
            data_store: 数据存储实例
        """
        self.data_store = data_store
        self.key_analyzer = KeyAnalyzer()
    
    def generate_proficiency_report(self, test_result: TestResult) -> ProficiencyReport:
        """
        生成熟练度报告
        
        Args:
            test_result: 测试结果
            
        Returns:
            ProficiencyReport 熟练度报告
        """
        # 分析按键数据
        analysis = self.key_analyzer.analyze_keystrokes(
            test_result.keystrokes,
            test_result.duration
        )
        
        # 识别薄弱按键
        weak_keys = self.key_analyzer.identify_weak_keys(analysis)
        weak_keys = self.key_analyzer.rank_weak_keys(weak_keys)
        
        # 计算整体评级
        overall_grade = self._calculate_grade(test_result.accuracy, test_result.wpm)
        
        # 生成建议
        recommendations = self._generate_recommendations(test_result, weak_keys)
        
        return ProficiencyReport(
            test_result=test_result,
            weak_keys=weak_keys,
            overall_grade=overall_grade,
            recommendations=recommendations
        )
    
    def generate_progress_report(self, current: TestResult, baseline: TestResult) -> ProgressReport:
        """
        生成进步程度报告
        
        Args:
            current: 当前测试结果
            baseline: 基准测试结果
            
        Returns:
            ProgressReport 进步报告
        """
        # 计算提升百分比
        wpm_improvement = self.calculate_wpm_improvement(current.wpm, baseline.wpm)
        accuracy_improvement = self.calculate_accuracy_improvement(current.accuracy, baseline.accuracy)
        
        # 分析按键数据
        current_analysis = self.key_analyzer.analyze_keystrokes(
            current.keystrokes,
            current.duration
        )
        baseline_analysis = self.key_analyzer.analyze_keystrokes(
            baseline.keystrokes,
            baseline.duration
        )
        
        # 识别改善的按键
        improved_keys = self.identify_improved_keys(current_analysis, baseline_analysis)
        
        # 识别仍然薄弱的按键
        current_weak = self.key_analyzer.identify_weak_keys(current_analysis)
        still_weak_keys = [wk.key for wk in current_weak]
        
        # 生成总结
        conclusion = self._generate_conclusion(
            wpm_improvement, accuracy_improvement, improved_keys, still_weak_keys
        )
        
        return ProgressReport(
            current_result=current,
            baseline_result=baseline,
            wpm_improvement=wpm_improvement,
            accuracy_improvement=accuracy_improvement,
            improved_keys=improved_keys,
            still_weak_keys=still_weak_keys,
            conclusion=conclusion
        )
    
    def calculate_wpm_improvement(self, current_wpm: float, baseline_wpm: float) -> float:
        """
        计算 WPM 提升百分比
        
        Args:
            current_wpm: 当前 WPM
            baseline_wpm: 基准 WPM
            
        Returns:
            提升百分比
        """
        if baseline_wpm == 0:
            return 0.0 if current_wpm == 0 else 100.0
        return ((current_wpm - baseline_wpm) / baseline_wpm) * 100
    
    def calculate_accuracy_improvement(self, current_acc: float, baseline_acc: float) -> float:
        """
        计算准确率提升百分比
        
        Args:
            current_acc: 当前准确率
            baseline_acc: 基准准确率
            
        Returns:
            提升百分比
        """
        if baseline_acc == 0:
            return 0.0 if current_acc == 0 else 100.0
        return ((current_acc - baseline_acc) / baseline_acc) * 100
    
    def identify_improved_keys(
        self, 
        current: KeyAnalysisResult, 
        baseline: KeyAnalysisResult
    ) -> List[str]:
        """
        识别已改善的按键
        
        按键从薄弱状态变为正常状态即为改善
        
        Args:
            current: 当前分析结果
            baseline: 基准分析结果
            
        Returns:
            改善的按键列表
        """
        # 获取基准测试中的薄弱按键
        baseline_weak = self.key_analyzer.identify_weak_keys(baseline)
        baseline_weak_keys = {wk.key for wk in baseline_weak}
        
        # 获取当前测试中的薄弱按键
        current_weak = self.key_analyzer.identify_weak_keys(current)
        current_weak_keys = {wk.key for wk in current_weak}
        
        # 改善的按键 = 之前薄弱但现在不薄弱的按键
        improved = baseline_weak_keys - current_weak_keys
        return list(improved)
    
    def _calculate_grade(self, accuracy: float, wpm: float) -> str:
        """计算整体评级"""
        # 综合评分 = 准确率权重 60% + WPM 权重 40%
        accuracy_score = accuracy * 100
        wpm_score = min(wpm / 60 * 100, 100)  # 60 WPM 为满分
        
        total_score = accuracy_score * 0.6 + wpm_score * 0.4
        
        if total_score >= 90:
            return "A"
        elif total_score >= 80:
            return "B"
        elif total_score >= 70:
            return "C"
        elif total_score >= 60:
            return "D"
        else:
            return "F"
    
    def _generate_recommendations(
        self, 
        test_result: TestResult, 
        weak_keys: List[WeakKey]
    ) -> List[str]:
        """生成改进建议"""
        recommendations = []
        
        if test_result.accuracy < 0.9:
            recommendations.append("建议放慢速度，专注于准确性")
        
        if test_result.wpm < 30:
            recommendations.append("建议多加练习以提高打字速度")
        
        if weak_keys:
            weak_key_str = ", ".join([wk.key for wk in weak_keys[:5]])
            recommendations.append(f"建议针对以下按键进行专项训练: {weak_key_str}")
        
        if not recommendations:
            recommendations.append("表现优秀！继续保持")
        
        return recommendations
    
    def _generate_conclusion(
        self,
        wpm_improvement: float,
        accuracy_improvement: float,
        improved_keys: List[str],
        still_weak_keys: List[str]
    ) -> str:
        """生成总结结论"""
        parts = []
        
        if wpm_improvement > 0:
            parts.append(f"打字速度提升了 {wpm_improvement:.1f}%")
        elif wpm_improvement < 0:
            parts.append(f"打字速度下降了 {abs(wpm_improvement):.1f}%")
        
        if accuracy_improvement > 0:
            parts.append(f"准确率提升了 {accuracy_improvement:.1f}%")
        elif accuracy_improvement < 0:
            parts.append(f"准确率下降了 {abs(accuracy_improvement):.1f}%")
        
        if improved_keys:
            parts.append(f"以下按键已改善: {', '.join(improved_keys)}")
        
        if still_weak_keys:
            parts.append(f"仍需加强练习: {', '.join(still_weak_keys[:5])}")
        
        if not parts:
            return "测试结果与基准相当，继续保持练习"
        
        return "。".join(parts) + "。"
