"""
测试内容生成器模块
"""
import random
import pytest

from keyboard_trainer.content_generator import ContentGenerator


class TestContentGenerator:
    """测试内容生成器"""

    def setup_method(self):
        """设置测试环境，固定随机种子以获得可重复的结果"""
        random.seed(42)
        self.generator = ContentGenerator()

    def test_generate_basic_test_content_length(self):
        """测试生成基础测试内容的长度符合预期"""
        length = 200
        content = self.generator.generate_basic_test_content(length)

        assert len(content) >= length
        assert isinstance(content, str)
        assert len(content.split()) > 0

    def test_generate_basic_test_content_different_lengths(self):
        """测试生成不同长度的基础测试内容"""
        lengths = [150, 250, 550]

        for length in lengths:
            content = self.generator.generate_basic_test_content(length)
            assert len(content) >= length

    def test_filter_words_by_keys(self):
        """测试筛选包含指定按键的单词"""
        keys = ["x", "z"]
        words = self.generator.filter_words_by_keys(keys)

        assert len(words) > 0
        for word in words:
            assert "x" in word.lower() or "z" in word.lower()

    def test_filter_words_by_keys_case_insensitive(self):
        """测试按键筛选不区分大小写"""
        keys = ["X", "Z"]
        words = self.generator.filter_words_by_keys(keys)

        assert len(words) > 0
        for word in words:
            assert "x" in word.lower() or "z" in word.lower()

    def test_calculate_key_frequency(self):
        """测试计算文本中各按键的出现频率"""
        text = "The quick brown fox jumps over the lazy dog"
        freq = self.generator.calculate_key_frequency(text)

        assert freq["o"] >= 4
        assert freq["e"] >= 3
        assert freq["t"] >= 2
        assert freq["h"] >= 2
        assert freq["r"] >= 2
        assert freq["u"] >= 2

    def test_generate_training_content_no_weak_keys(self):
        """测试没有薄弱按键时生成基础内容"""
        content = self.generator.generate_training_content([], length=200)

        assert isinstance(content, str)
        assert len(content) >= 200

    def test_generate_training_content_with_weak_keys_length(self):
        """测试生成训练内容的长度符合预期"""
        weak_keys = ["x", "z"]
        length = 200
        content = self.generator.generate_training_content(weak_keys, length)

        assert len(content) >= length
        assert isinstance(content, str)

    def test_training_content_contains_higher_weak_key_frequency(self):
        """测试生成的训练内容确实包含更高比例的薄弱按键字符"""
        weak_keys = ["x", "z", "q"]

        random.seed(42)
        basic_content = self.generator.generate_basic_test_content(length=500)

        random.seed(42)
        training_content = self.generator.generate_training_content(weak_keys, length=500)

        basic_freq = self.generator.calculate_key_frequency(basic_content)
        training_freq = self.generator.calculate_key_frequency(training_content)

        basic_total = sum(basic_freq.values())
        training_total = sum(training_freq.values())

        weak_key_basic_count = sum(basic_freq.get(k, 0) for k in weak_keys)
        weak_key_training_count = sum(training_freq.get(k, 0) for k in weak_keys)

        weak_key_basic_ratio = weak_key_basic_count / basic_total if basic_total > 0 else 0
        weak_key_training_ratio = weak_key_training_count / training_total if training_total > 0 else 0

        assert weak_key_training_ratio > weak_key_basic_ratio, \
            f"训练内容中薄弱按键比例 ({weak_key_training_ratio:.2%}) 应高于基础内容 ({weak_key_basic_ratio:.2%})"

    def test_generate_training_content_nonexistent_weak_keys(self):
        """测试不存在包含薄弱按键的单词时回退到基础内容"""
        weak_keys = ["€", "£", "¥"]
        content = self.generator.generate_training_content(weak_keys, length=200)

        assert isinstance(content, str)
        assert len(content) >= 200

    def test_custom_word_database(self):
        """测试使用自定义单词库"""
        custom_words = ["test", "custom", "words", "database"]
        generator = ContentGenerator(word_database=custom_words)

        content = generator.generate_basic_test_content(length=50)

        for word in content.split():
            assert word in custom_words

    def test_generate_training_content_multiple_weak_keys(self):
        """测试多个薄弱按键都能获得更高频率"""
        weak_keys = ["j", "k", "q"]
        content = self.generator.generate_training_content(weak_keys, length=2000)
        freq = self.generator.calculate_key_frequency(content)

        total_chars = sum(freq.values())
        avg_freq = total_chars / 26

        weak_key_total = sum(freq.get(k, 0) for k in weak_keys)
        normal_key_avg = (total_chars - weak_key_total) / (26 - len(weak_keys))

        assert weak_key_total / len(weak_keys) >= normal_key_avg
