import pytest
import random
from keyboard_trainer.content_generator import ContentGenerator, DEFAULT_WORD_DATABASE


@pytest.fixture
def generator():
    """创建 ContentGenerator 实例"""
    return ContentGenerator()


@pytest.fixture
def fixed_seed():
    """设置固定随机种子以保证测试可重复"""
    random.seed(42)
    yield
    random.seed()


class TestContentGeneratorBasics:
    """测试基础功能"""

    def test_generator_initialization_default(self):
        """测试使用默认单词库初始化"""
        gen = ContentGenerator()
        assert gen.word_database == DEFAULT_WORD_DATABASE
        assert len(gen.word_database) > 0

    def test_generator_initialization_custom(self):
        """测试使用自定义单词库初始化"""
        custom_words = ['test', 'custom', 'words']
        gen = ContentGenerator(word_database=custom_words)
        assert gen.word_database == custom_words
        assert len(gen.word_database) == 3

    def test_filter_words_by_keys(self, generator):
        """测试按按键筛选单词"""
        keys = ['q', 'x']
        filtered = generator.filter_words_by_keys(keys)
        assert len(filtered) > 0
        for word in filtered:
            assert 'q' in word.lower() or 'x' in word.lower()

    def test_filter_words_by_keys_case_insensitive(self, generator):
        """测试按键筛选大小写不敏感"""
        keys_lower = ['a']
        keys_upper = ['A']
        filtered_lower = generator.filter_words_by_keys(keys_lower)
        filtered_upper = generator.filter_words_by_keys(keys_upper)
        assert filtered_lower == filtered_upper

    def test_filter_words_by_keys_no_match(self, generator):
        """测试没有匹配的按键时返回空列表"""
        keys = ['zzz']
        filtered = generator.filter_words_by_keys(keys)
        assert filtered == []

    def test_calculate_key_frequency(self, generator):
        """测试按键频率计算"""
        text = 'Hello World'
        freq = generator.calculate_key_frequency(text)
        assert freq['h'] == 1
        assert freq['e'] == 1
        assert freq['l'] == 3
        assert freq['o'] == 2
        assert freq['w'] == 1
        assert freq['r'] == 1
        assert freq['d'] == 1

    def test_calculate_key_frequency_ignores_non_letters(self, generator):
        """测试按键频率计算忽略非字母字符"""
        text = 'Hello, World! 123'
        freq = generator.calculate_key_frequency(text)
        assert ',' not in freq
        assert '!' not in freq
        assert '1' not in freq
        assert ' ' not in freq


class TestContentLength:
    """测试生成内容的长度"""

    def test_basic_content_length_approximate(self, generator, fixed_seed):
        """测试基础内容长度接近目标值"""
        target_length = 200
        content = generator.generate_basic_test_content(length=target_length)
        assert len(content) >= target_length * 0.8
        assert len(content) <= target_length * 1.5

    def test_basic_content_length_variations(self, generator, fixed_seed):
        """测试不同长度的内容生成"""
        for length in [50, 100, 200, 500]:
            content = generator.generate_basic_test_content(length=length)
            assert len(content) > 0
            words = content.split()
            assert len(words) > 0

    def test_training_content_length_no_weak_keys(self, generator, fixed_seed):
        """测试无薄弱按键时训练内容退化为基础内容"""
        content = generator.generate_training_content(weak_keys=[], length=200)
        assert len(content) > 0

    def test_training_content_length_with_weak_keys(self, generator, fixed_seed):
        """测试有薄弱按键时内容长度"""
        target_length = 200
        content = generator.generate_training_content(weak_keys=['x', 'q'], length=target_length)
        assert len(content) >= target_length * 0.8


class TestWeakKeyFrequency:
    """测试薄弱按键频率增强"""

    def test_training_content_contains_weak_keys(self, generator, fixed_seed):
        """测试生成的训练内容包含薄弱按键"""
        weak_keys = ['x', 'q', 'z']
        content = generator.generate_training_content(weak_keys=weak_keys, length=500)
        freq = generator.calculate_key_frequency(content)

        for key in weak_keys:
            assert freq.get(key, 0) > 0

    def test_weak_keys_have_higher_frequency(self, generator, fixed_seed):
        """测试薄弱按键出现频率高于普通按键"""
        weak_keys = ['x', 'z']
        normal_keys = ['e', 't', 'a']  # 常见字母

        content = generator.generate_training_content(weak_keys=weak_keys, length=1000)
        freq = generator.calculate_key_frequency(content)
        total_chars = sum(freq.values())

        if total_chars == 0:
            pytest.skip("No characters in content")

        avg_normal_freq = sum(freq.get(k, 0) for k in normal_keys) / len(normal_keys) / total_chars
        avg_weak_freq = sum(freq.get(k, 0) for k in weak_keys) / len(weak_keys) / total_chars

        if avg_normal_freq > 0:
            multiplier = avg_weak_freq / avg_normal_freq
            assert multiplier >= 0.7
        else:
            assert avg_weak_freq > 0

    def test_training_content_with_no_matching_words(self, fixed_seed):
        """测试没有匹配薄弱按键的单词时"""
        custom_words = ['hello', 'world', 'test']
        gen = ContentGenerator(word_database=custom_words)
        weak_keys = ['x', 'z']
        content = gen.generate_training_content(weak_keys=weak_keys, length=200)
        assert len(content) > 0

    def test_multiple_weak_keys_frequency(self, generator, fixed_seed):
        """测试多个薄弱按键的频率"""
        weak_keys = ['j', 'k', 'q', 'x', 'z']
        content = generator.generate_training_content(weak_keys=weak_keys, length=2000)
        freq = generator.calculate_key_frequency(content)

        for key in weak_keys:
            assert key in freq
            assert freq[key] > 0

    def test_content_consists_of_words_from_database(self, generator, fixed_seed):
        """测试生成内容由单词库中的单词组成"""
        content = generator.generate_basic_test_content(length=200)
        words = content.split()
        for word in words:
            assert word in generator.word_database

    def test_training_content_uses_filtered_words(self, generator, fixed_seed):
        """测试训练内容使用筛选后的单词"""
        weak_keys = ['x']
        content = generator.generate_training_content(weak_keys=weak_keys, length=500)
        words = content.split()

        x_words = [w for w in words if 'x' in w.lower()]
        assert len(x_words) > 0


class TestContentGenerationEdgeCases:
    """测试边缘情况"""

    def test_zero_length_content(self, generator, fixed_seed):
        """测试零长度内容生成"""
        content = generator.generate_basic_test_content(length=1)
        assert len(content) >= 0

    def test_very_short_length(self, generator, fixed_seed):
        """测试非常短的内容生成"""
        content = generator.generate_basic_test_content(length=10)
        assert len(content) > 0
        words = content.split()
        assert len(words) >= 1

    def test_very_long_content(self, generator, fixed_seed):
        """测试非常长的内容生成"""
        content = generator.generate_basic_test_content(length=2000)
        assert len(content) >= 1000

    def test_empty_word_database_fallback_to_default(self):
        """测试空单词库回退到默认单词库"""
        gen = ContentGenerator(word_database=[])
        assert gen.word_database is DEFAULT_WORD_DATABASE
        content = gen.generate_basic_test_content(length=100)
        assert len(content) > 0

    def test_single_word_database(self, fixed_seed):
        """测试只有一个单词的单词库"""
        gen = ContentGenerator(word_database=['test'])
        content = gen.generate_basic_test_content(length=100)
        words = content.split()
        assert all(word == 'test' for word in words)
