
import pytest
from keyboard_trainer.key_analyzer import KeyAnalyzer, KeyAnalysisResult
from keyboard_trainer.models import KeystrokeRecord, KeystrokeStatus, KeyStatistics, WeakKey


class TestKeyAnalyzer:
    @pytest.fixture
    def analyzer(self):
        return KeyAnalyzer()

    @pytest.fixture
    def sample_keystrokes(self):
        return [
            KeystrokeRecord('a', 'a', 1000.0, 150.0, KeystrokeStatus.CORRECT),
            KeystrokeRecord('a', 'a', 1200.0, 200.0, KeystrokeStatus.CORRECT),
            KeystrokeRecord('a', 'b', 1400.0, 180.0, KeystrokeStatus.INCORRECT),
            KeystrokeRecord('b', 'b', 1600.0, 250.0, KeystrokeStatus.CORRECT),
            KeystrokeRecord('b', 'b', 1800.0, 220.0, KeystrokeStatus.CORRECT),
            KeystrokeRecord('x', 'x', 2000.0, 600.0, KeystrokeStatus.CORRECT),
            KeystrokeRecord('y', 'y', 2200.0, 400.0, KeystrokeStatus.CORRECT),
            KeystrokeRecord('z', 'a', 2400.0, 550.0, KeystrokeStatus.INCORRECT),
        ]

    def test_analyze_keystrokes_empty_list(self, analyzer):
        result = analyzer.analyze_keystrokes([])
        assert isinstance(result, KeyAnalysisResult)
        assert result.overall_accuracy == 0.0
        assert result.overall_wpm == 0.0
        assert result.overall_cpm == 0.0
        assert result.per_key_statistics == {}

    def test_analyze_keystrokes_calculates_statistics(self, analyzer, sample_keystrokes):
        result = analyzer.analyze_keystrokes(sample_keystrokes, duration=60.0)

        assert isinstance(result, KeyAnalysisResult)
        assert result.duration == 60.0

        correct_count = sum(1 for k in sample_keystrokes if k.status == KeystrokeStatus.CORRECT)
        assert result.overall_accuracy == correct_count / len(sample_keystrokes)

    def test_calculate_per_key_statistics(self, analyzer, sample_keystrokes):
        stats = analyzer._calculate_per_key_statistics(sample_keystrokes)

        assert 'a' in stats
        assert 'b' in stats
        assert 'x' in stats
        assert 'y' in stats
        assert 'z' in stats

        a_stats = stats['a']
        assert a_stats.total_attempts == 3
        assert a_stats.correct_attempts == 2
        assert a_stats.accuracy == 2 / 3
        assert a_stats.average_response_time == (150 + 200 + 180) / 3

        b_stats = stats['b']
        assert b_stats.total_attempts == 2
        assert b_stats.correct_attempts == 2
        assert b_stats.accuracy == 1.0
        assert b_stats.average_response_time == (250 + 220) / 2

    def test_calculate_per_key_accuracy(self, analyzer, sample_keystrokes):
        accuracies = analyzer.calculate_per_key_accuracy(sample_keystrokes)

        assert 'a' in accuracies
        assert accuracies['a'] == 2 / 3
        assert accuracies['b'] == 1.0

    def test_calculate_per_key_speed(self, analyzer, sample_keystrokes):
        speeds = analyzer.calculate_per_key_speed(sample_keystrokes)

        assert 'a' in speeds
        assert 'b' in speeds

    def test_identify_weak_keys_low_accuracy(self, analyzer):
        stats = {
            'a': KeyStatistics('a', 10, 8, 0.80, 400),
            'b': KeyStatistics('b', 10, 10, 1.0, 400),
        }
        analysis = KeyAnalysisResult(
            overall_accuracy=0.90,
            overall_wpm=50.0,
            overall_cpm=250.0,
            duration=60.0,
            per_key_statistics=stats
        )

        weak_keys = analyzer.identify_weak_keys(analysis)

        assert len(weak_keys) == 1
        assert weak_keys[0].key == 'a'

    def test_identify_weak_keys_high_response_time(self, analyzer):
        stats = {
            'a': KeyStatistics('a', 10, 10, 1.0, 600),
            'b': KeyStatistics('b', 10, 10, 1.0, 400),
        }
        analysis = KeyAnalysisResult(
            overall_accuracy=1.0,
            overall_wpm=50.0,
            overall_cpm=250.0,
            duration=60.0,
            per_key_statistics=stats
        )

        weak_keys = analyzer.identify_weak_keys(analysis)

        assert len(weak_keys) == 1
        assert weak_keys[0].key == 'a'

    def test_identify_weak_keys_with_sample_data(self, analyzer, sample_keystrokes):
        analysis = analyzer.analyze_keystrokes(sample_keystrokes, duration=60.0)
        weak_keys = analyzer.identify_weak_keys(analysis)

        weak_key_chars = [wk.key for wk in weak_keys]
        assert 'a' in weak_key_chars
        assert 'x' in weak_key_chars
        assert 'z' in weak_key_chars

    def test_calculate_severity(self, analyzer):
        stats_low_accuracy = KeyStatistics('a', 10, 8, 0.80, 400)
        severity1 = analyzer._calculate_severity(stats_low_accuracy)
        assert severity1 == pytest.approx(20.0)

        stats_high_time = KeyStatistics('a', 10, 10, 1.0, 600)
        severity2 = analyzer._calculate_severity(stats_high_time)
        assert severity2 == pytest.approx(10.0)

        stats_both = KeyStatistics('a', 10, 8, 0.80, 600)
        severity3 = analyzer._calculate_severity(stats_both)
        assert severity3 == pytest.approx(30.0)

    def test_rank_weak_keys(self, analyzer):
        weak_keys = [
            WeakKey('a', 0.70, 400, 30.0),
            WeakKey('b', 0.90, 600, 20.0),
            WeakKey('c', 0.70, 500, 35.0),
        ]

        ranked = analyzer.rank_weak_keys(weak_keys)

        assert ranked[0].key == 'c'
        assert ranked[1].key == 'a'
        assert ranked[2].key == 'b'

    def test_analyze_keystrokes_duration_from_keystrokes(self, analyzer, sample_keystrokes):
        result = analyzer.analyze_keystrokes(sample_keystrokes)

        expected_duration = (sample_keystrokes[-1].timestamp - sample_keystrokes[0].timestamp) / 1000
        assert result.duration == expected_duration

    def test_analyze_keystrokes_single_keystroke(self, analyzer):
        keystroke = KeystrokeRecord('a', 'a', 1000.0, 150.0, KeystrokeStatus.CORRECT)
        result = analyzer.analyze_keystrokes([keystroke])

        assert result.overall_accuracy == 1.0
        assert result.duration == 0.0
        assert 'a' in result.per_key_statistics

