"""
测试数据存储模块
"""
import sqlite3
from datetime import datetime
import pytest

from keyboard_trainer.data_store import DataStore
from keyboard_trainer.models import (
    KeyStatistics,
    KeystrokeRecord,
    KeystrokeStatus,
    TestResult,
    TestType,
    WeakKey,
)


class TestDataStore:
    """测试数据存储"""

    @pytest.fixture
    def data_store(self):
        """创建使用内存数据库的测试数据存储"""
        store = DataStore(":memory:")
        yield store
        store.close()

    def test_database_initialization(self, data_store):
        """测试数据库初始化和表结构创建"""
        conn = data_store._get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT name FROM sqlite_master 
            WHERE type='table' AND name IN 
            ('test_results', 'key_statistics', 'keystroke_records', 'weak_keys')
        """)
        tables = {row[0] for row in cursor.fetchall()}

        required_tables = {'test_results', 'key_statistics', 'keystroke_records', 'weak_keys'}
        assert required_tables.issubset(tables)

    def test_save_and_get_test_result_consistency(self, data_store):
        """测试测试结果的保存和读取（save/get 往返一致性）"""
        test_id = "test-001"
        timestamp = datetime.now()

        key_statistics = {
            "a": KeyStatistics(
                key="a",
                total_attempts=10,
                correct_attempts=9,
                accuracy=0.9,
                average_response_time=200.0,
            ),
            "b": KeyStatistics(
                key="b",
                total_attempts=5,
                correct_attempts=4,
                accuracy=0.8,
                average_response_time=300.0,
            ),
        }

        keystrokes = [
            KeystrokeRecord(
                expected_char="a",
                actual_char="a",
                timestamp=1000.0,
                response_time=200.0,
                status=KeystrokeStatus.CORRECT,
            ),
            KeystrokeRecord(
                expected_char="b",
                actual_char="b",
                timestamp=2000.0,
                response_time=300.0,
                status=KeystrokeStatus.CORRECT,
            ),
        ]

        test_result = TestResult(
            id=test_id,
            test_type=TestType.BASIC,
            timestamp=timestamp,
            duration=60.0,
            total_characters=15,
            correct_characters=13,
            wpm=40.0,
            cpm=200.0,
            accuracy=0.8667,
            key_statistics=key_statistics,
            keystrokes=keystrokes,
        )

        assert data_store.save_test_result(test_result) is True

        history = data_store.get_test_history(limit=10)
        assert len(history) == 1

        saved_result = history[0]
        assert saved_result.id == test_id
        assert saved_result.test_type == TestType.BASIC
        assert saved_result.duration == 60.0
        assert saved_result.total_characters == 15
        assert saved_result.correct_characters == 13
        assert saved_result.wpm == 40.0
        assert saved_result.cpm == 200.0
        assert saved_result.accuracy == 0.8667

        assert "a" in saved_result.key_statistics
        assert "b" in saved_result.key_statistics
        assert saved_result.key_statistics["a"].total_attempts == 10
        assert saved_result.key_statistics["a"].correct_attempts == 9
        assert saved_result.key_statistics["a"].accuracy == 0.9
        assert saved_result.key_statistics["a"].average_response_time == 200.0

        assert len(saved_result.keystrokes) == 2
        assert saved_result.keystrokes[0].expected_char == "a"
        assert saved_result.keystrokes[0].actual_char == "a"
        assert saved_result.keystrokes[0].status == KeystrokeStatus.CORRECT

    def test_get_latest_basic_test(self, data_store):
        """测试获取最近的基础测试结果"""
        test_id_1 = "test-001"
        test_id_2 = "test-002"

        test_result_1 = TestResult(
            id=test_id_1,
            test_type=TestType.BASIC,
            timestamp=datetime(2024, 1, 1),
            duration=60.0,
            total_characters=100,
            correct_characters=90,
            wpm=40.0,
            cpm=200.0,
            accuracy=0.9,
            key_statistics={},
        )

        test_result_2 = TestResult(
            id=test_id_2,
            test_type=TestType.BASIC,
            timestamp=datetime(2024, 1, 2),
            duration=60.0,
            total_characters=100,
            correct_characters=95,
            wpm=45.0,
            cpm=225.0,
            accuracy=0.95,
            key_statistics={},
        )

        data_store.save_test_result(test_result_1)
        data_store.save_test_result(test_result_2)

        latest = data_store.get_latest_basic_test()
        assert latest is not None
        assert latest.id == test_id_2

    def test_get_latest_basic_test_none(self, data_store):
        """测试没有基础测试时返回 None"""
        assert data_store.get_latest_basic_test() is None

    def test_save_and_get_weak_keys(self, data_store):
        """测试薄弱按键的保存和获取"""
        weak_keys = [
            WeakKey(
                key="x",
                accuracy=0.75,
                average_response_time=550.0,
                severity_score=30.0,
            ),
            WeakKey(
                key="z",
                accuracy=0.80,
                average_response_time=600.0,
                severity_score=30.0,
            ),
        ]

        assert data_store.save_weak_keys(weak_keys) is True

        saved_weak_keys = data_store.get_weak_keys()
        assert len(saved_weak_keys) == 2

        keys = {wk.key for wk in saved_weak_keys}
        assert keys == {"x", "z"}

        x_key = next(wk for wk in saved_weak_keys if wk.key == "x")
        z_key = next(wk for wk in saved_weak_keys if wk.key == "z")

        assert x_key.accuracy == 0.75
        assert x_key.average_response_time == 550.0
        assert z_key.accuracy == 0.80
        assert z_key.average_response_time == 600.0

    def test_save_weak_keys_replaces_existing(self, data_store):
        """测试保存新的薄弱按键会替换现有记录"""
        weak_keys_1 = [
            WeakKey(key="x", accuracy=0.75, average_response_time=550.0, severity_score=30.0),
        ]

        weak_keys_2 = [
            WeakKey(key="z", accuracy=0.80, average_response_time=600.0, severity_score=30.0),
        ]

        data_store.save_weak_keys(weak_keys_1)
        data_store.save_weak_keys(weak_keys_2)

        saved_weak_keys = data_store.get_weak_keys()
        assert len(saved_weak_keys) == 1
        assert saved_weak_keys[0].key == "z"

    def test_validate_data_integrity_valid(self, data_store):
        """测试数据完整性验证通过"""
        test_result = TestResult(
            id="test-001",
            test_type=TestType.BASIC,
            timestamp=datetime.now(),
            duration=60.0,
            total_characters=100,
            correct_characters=90,
            wpm=40.0,
            cpm=200.0,
            accuracy=0.9,
            key_statistics={
                "a": KeyStatistics(
                    key="a",
                    total_attempts=10,
                    correct_attempts=9,
                    accuracy=0.9,
                    average_response_time=200.0,
                ),
            },
            keystrokes=[
                KeystrokeRecord(
                    expected_char="a",
                    actual_char="a",
                    timestamp=1000.0,
                    response_time=200.0,
                    status=KeystrokeStatus.CORRECT,
                ),
            ],
        )

        data_store.save_test_result(test_result)

        assert data_store.validate_data_integrity() is True

    def test_validate_data_integrity_missing_tables(self):
        """测试缺少表时数据完整性验证失败"""
        conn = sqlite3.connect(":memory:")
        conn.close()

        store = DataStore(":memory:")
        cursor = store._get_connection().cursor()
        cursor.execute("DROP TABLE weak_keys")
        store._get_connection().commit()

        assert store.validate_data_integrity() is False
        store.close()

    def test_get_test_history_limit(self, data_store):
        """测试获取测试历史的数量限制"""
        for i in range(5):
            test_result = TestResult(
                id=f"test-{i:03d}",
                test_type=TestType.BASIC,
                timestamp=datetime.now(),
                duration=60.0,
                total_characters=100,
                correct_characters=90,
                wpm=40.0,
                cpm=200.0,
                accuracy=0.9,
                key_statistics={},
            )
            data_store.save_test_result(test_result)

        history = data_store.get_test_history(limit=3)
        assert len(history) == 3

    def test_save_test_result_with_weak_keys(self, data_store):
        """测试保存测试结果时自动识别并保存薄弱按键"""
        key_statistics = {
            "x": KeyStatistics(
                key="x",
                total_attempts=10,
                correct_attempts=7,
                accuracy=0.7,
                average_response_time=600.0,
            ),
            "a": KeyStatistics(
                key="a",
                total_attempts=10,
                correct_attempts=9,
                accuracy=0.9,
                average_response_time=200.0,
            ),
        }

        test_result = TestResult(
            id="test-001",
            test_type=TestType.BASIC,
            timestamp=datetime.now(),
            duration=60.0,
            total_characters=20,
            correct_characters=16,
            wpm=40.0,
            cpm=200.0,
            accuracy=0.8,
            key_statistics=key_statistics,
        )

        assert data_store.save_test_result(test_result) is True

        weak_keys = data_store.get_weak_keys()
        assert len(weak_keys) >= 1
        assert any(wk.key == "x" for wk in weak_keys)

    def test_close_connection(self, data_store):
        """测试关闭数据库连接"""
        data_store.close()
        assert data_store._connection is None

    def test_backup_corrupted_data(self, data_store, tmp_path):
        """测试备份损坏的数据"""
        test_db_path = str(tmp_path / "test.db")
        store = DataStore(test_db_path)
        backup_path = store.backup_corrupted_data()

        assert backup_path != ""
        assert backup_path.startswith(test_db_path)
        store.close()
