
import pytest
import random
from unittest.mock import patch
from keyboard_trainer.content_generator import ContentGenerator


class TestContentGenerator:
    @pytest.fixture
    def generator(self):
        return ContentGenerator(word_database=[
            'apple', 'banana', 'cherry', 'date', 'elderberry',
            'fig', 'grape', 'honeydew', 'kiwi', 'lemon',
            'mango', 'orange', 'peach', 'pear', 'pineapple',
            'quick', 'brown', 'fox', 'jumps', 'lazy', 'dog',
            'xylophone', 'zebra', 'yellow', 'violet'
        ])

    @pytest.fixture
    def simple_generator(self):
        return ContentGenerator(word_database=[
            'ax', 'bx', 'cx', 'ay', 'by', 'cy',
            'normal', 'test', 'word'
        ])

    def test_generate_basic_test_content_length(self, generator):
        content = generator.generate_basic_test_content(length=100)
        assert len(content) >= 100

    def test_generate_basic_test_content_uses_word_database(self, generator):
        content = generator.generate_basic_test_content(length=50)
        words = content.split()
        for word in words:
            assert word in generator.word_database

    def test_generate_training_content_no_weak_keys(self, generator):
        with patch.object(generator, 'generate_basic_test_content') as mock_basic:
            mock_basic.return_value = 'basic content'
            content = generator.generate_training_content([], length=100)
            mock_basic.assert_called_once_with(100)
            assert content == 'basic content'

    def test_filter_words_by_keys(self, simple_generator):
        words = simple_generator.filter_words_by_keys(['x', 'y'])
        expected = {'ax', 'bx', 'cx', 'ay', 'by', 'cy'}
        assert set(words) == expected

    def test_filter_words_by_keys_case_insensitive(self, simple_generator):
        words = simple_generator.filter_words_by_keys(['X', 'Y'])
        expected = {'ax', 'bx', 'cx', 'ay', 'by', 'cy'}
        assert set(words) == expected

    def test_calculate_key_frequency(self, generator):
        text = 'Apple Banana Cherry'
        freq = generator.calculate_key_frequency(text)
        assert freq['a'] == 4
        assert freq['p'] == 2
        assert freq['l'] == 1
        assert freq['e'] == 2
        assert freq['b'] == 1
        assert freq['n'] == 2
        assert freq['c'] == 1
        assert freq['h'] == 1
        assert freq['r'] == 2
        assert freq['y'] == 1

    def test_calculate_key_frequency_ignores_non_letters(self, generator):
        text = 'Hello! World? 123'
        freq = generator.calculate_key_frequency(text)
        assert '!' not in freq
        assert '?' not in freq
        assert '1' not in freq
        assert '2' not in freq
        assert '3' not in freq

    def test_generate_training_content_includes_weak_keys(self, simple_generator):
        weak_keys = ['x', 'y']
        
        with patch('random.random', return_value=0.5):
            content = simple_generator.generate_training_content(weak_keys, length=50)
        
        freq = simple_generator.calculate_key_frequency(content)
        assert 'x' in freq or 'y' in freq

    def test_generate_training_content_length(self, simple_generator):
        weak_keys = ['x']
        content = simple_generator.generate_training_content(weak_keys, length=100)
        assert len(content) >= 90

    def test_init_with_default_database(self):
        generator = ContentGenerator()
        assert len(generator.word_database) > 0
        assert 'the' in generator.word_database
        assert 'quick' in generator.word_database

    def test_filter_words_by_keys_empty_result(self, simple_generator):
        words = simple_generator.filter_words_by_keys(['z'])
        assert len(words) == 0

    def test_generate_training_content_no_weak_key_words(self, simple_generator):
        with patch.object(simple_generator, 'generate_basic_test_content') as mock_basic:
            mock_basic.return_value = 'fallback content'
            content = simple_generator.generate_training_content(['z'], length=100)
            mock_basic.assert_called_once()
            assert content == 'fallback content'

    @pytest.mark.parametrize('length', [50, 100, 200, 500])
    def test_generate_content_various_lengths(self, generator, length):
        content = generator.generate_basic_test_content(length=length)
        assert len(content) >= length - 10

    def test_generate_training_content_high_probability_for_weak_words(self, simple_generator):
        weak_keys = ['x']
        
        weak_word_count = 0
        total_count = 100
        
        for _ in range(total_count):
            with patch('random.random', return_value=0.5):
                content = simple_generator.generate_training_content(weak_keys, length=20)
                words = content.split()
                if words:
                    if words[0] in ['ax', 'bx', 'cx']:
                        weak_word_count += 1
        
        assert weak_word_count > total_count * 0.5

