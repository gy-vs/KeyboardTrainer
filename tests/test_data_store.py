import pytest
import sqlite3
import os
from datetime import datetime
from unittest.mock import patch, MagicMock
from keyboard_trainer.data_store import DataStore
from keyboard_trainer.models import (
    KeyStatistics,
    KeystrokeRecord,
    KeystrokeStatus,
    TestResult,
    TestType,
    WeakKey,
)


@pytest.fixture
def memory_db():
    """创建内存数据库实例"""
    db = DataStore(':memory:')
    yield db
    db.close()


@pytest.fixture
def sample_test_result():
    """创建示例测试结果"""
    key_statistics = {
        'a': KeyStatistics('a', 10, 9, 0.9, 200.0),
        'b': KeyStatistics('b', 10, 7, 0.7, 600.0),
    }
    keystrokes = [
        KeystrokeRecord('a', 'a', 1000.0, 200.0, KeystrokeStatus.CORRECT),
        KeystrokeRecord('b', 'x', 1001.0, 250.0, KeystrokeStatus.INCORRECT),
    ]
    return TestResult(
        id='test_001',
        test_type=TestType.BASIC,
        timestamp=datetime.now(),
        duration=60.0,
        total_characters=20,
        correct_characters=16,
        wpm=30.0,
        cpm=150.0,
        accuracy=0.8,
        key_statistics=key_statistics,
        keystrokes=keystrokes
    )


class TestDatabaseInitialization:
    """测试数据库初始化和表结构"""

    def test_database_connection_established(self, memory_db):
        """测试数据库连接成功建立"""
        assert memory_db._connection is not None

    def test_all_tables_created(self, memory_db):
        """测试所有必需表已创建"""
        cursor = memory_db._connection.cursor()
        cursor.execute("""
            SELECT name FROM sqlite_master 
            WHERE type='table' AND name IN 
            ('test_results', 'key_statistics', 'keystroke_records', 'weak_keys')
        """)
        tables = {row[0] for row in cursor.fetchall()}
        required_tables = {'test_results', 'key_statistics', 'keystroke_records', 'weak_keys'}
        assert required_tables.issubset(tables)

    def test_table_structures(self, memory_db):
        """测试表结构正确性"""
        cursor = memory_db._connection.cursor()

        cursor.execute("PRAGMA table_info(test_results)")
        columns = {row[1] for row in cursor.fetchall()}
        expected = {'id', 'test_type', 'timestamp', 'duration', 'total_characters',
                    'correct_characters', 'wpm', 'cpm', 'accuracy'}
        assert expected.issubset(columns)

        cursor.execute("PRAGMA table_info(key_statistics)")
        columns = {row[1] for row in cursor.fetchall()}
        expected = {'test_result_id', 'key_char', 'total_attempts', 'correct_attempts',
                    'accuracy', 'average_response_time'}
        assert expected.issubset(columns)

        cursor.execute("PRAGMA table_info(keystroke_records)")
        columns = {row[1] for row in cursor.fetchall()}
        expected = {'test_result_id', 'expected_char', 'actual_char', 'timestamp',
                    'response_time', 'status'}
        assert expected.issubset(columns)

        cursor.execute("PRAGMA table_info(weak_keys)")
        columns = {row[1] for row in cursor.fetchall()}
        expected = {'key_char', 'accuracy', 'average_response_time', 'severity_score', 'identified_at'}
        assert expected.issubset(columns)

    def test_foreign_keys_configured(self, memory_db):
        """测试外键约束已配置"""
        cursor = memory_db._connection.cursor()
        cursor.execute("PRAGMA foreign_key_list(key_statistics)")
        fks = cursor.fetchall()
        assert len(fks) > 0
        assert fks[0][2] == 'test_results'
        assert fks[0][3] == 'test_result_id'

    def test_close_connection(self, memory_db):
        """测试关闭数据库连接"""
        memory_db.close()
        assert memory_db._connection is None

    def test_ensure_directory_creates_path(self, tmp_path):
        """测试数据库目录创建"""
        db_path = str(tmp_path / 'data' / 'test.db')
        db = DataStore(db_path)
        assert os.path.exists(os.path.dirname(db_path))
        db.close()


class TestTestResultPersistence:
    """测试测试结果的保存和读取"""

    def test_save_test_result_success(self, memory_db, sample_test_result):
        """测试成功保存测试结果"""
        success = memory_db.save_test_result(sample_test_result)
        assert success is True

        cursor = memory_db._connection.cursor()
        cursor.execute("SELECT COUNT(*) FROM test_results")
        assert cursor.fetchone()[0] == 1

    def test_save_test_result_key_statistics_saved(self, memory_db, sample_test_result):
        """测试按键统计数据保存"""
        memory_db.save_test_result(sample_test_result)

        cursor = memory_db._connection.cursor()
        cursor.execute("SELECT COUNT(*) FROM key_statistics")
        assert cursor.fetchone()[0] == 2

    def test_save_test_result_keystrokes_saved(self, memory_db, sample_test_result):
        """测试按键记录保存"""
        memory_db.save_test_result(sample_test_result)

        cursor = memory_db._connection.cursor()
        cursor.execute("SELECT COUNT(*) FROM keystroke_records")
        assert cursor.fetchone()[0] == 2

    def test_save_and_get_roundtrip(self, memory_db, sample_test_result):
        """测试保存和读取的往返一致性"""
        memory_db.save_test_result(sample_test_result)
        history = memory_db.get_test_history(limit=10)

        assert len(history) == 1
        loaded = history[0]
        assert loaded.id == sample_test_result.id
        assert loaded.test_type == sample_test_result.test_type
        assert loaded.duration == sample_test_result.duration
        assert loaded.total_characters == sample_test_result.total_characters
        assert loaded.correct_characters == sample_test_result.correct_characters
        assert loaded.wpm == sample_test_result.wpm
        assert loaded.cpm == sample_test_result.cpm
        assert loaded.accuracy == sample_test_result.accuracy

    def test_key_statistics_roundtrip(self, memory_db, sample_test_result):
        """测试按键统计数据往返一致性"""
        memory_db.save_test_result(sample_test_result)
        history = memory_db.get_test_history(limit=10)
        loaded = history[0]

        assert 'a' in loaded.key_statistics
        assert 'b' in loaded.key_statistics
        assert loaded.key_statistics['a'].total_attempts == 10
        assert loaded.key_statistics['a'].correct_attempts == 9
        assert loaded.key_statistics['a'].accuracy == 0.9
        assert loaded.key_statistics['a'].average_response_time == 200.0

    def test_keystrokes_roundtrip(self, memory_db, sample_test_result):
        """测试按键记录往返一致性"""
        memory_db.save_test_result(sample_test_result)
        history = memory_db.get_test_history(limit=10)
        loaded = history[0]

        assert len(loaded.keystrokes) == 2
        assert loaded.keystrokes[0].expected_char == 'a'
        assert loaded.keystrokes[0].actual_char == 'a'
        assert loaded.keystrokes[0].status == KeystrokeStatus.CORRECT
        assert loaded.keystrokes[1].expected_char == 'b'
        assert loaded.keystrokes[1].status == KeystrokeStatus.INCORRECT

    def test_get_latest_basic_test(self, memory_db):
        """测试获取最近的基础测试"""
        key_stats = {}
        for i in range(3):
            result = TestResult(
                id=f'test_{i:03d}',
                test_type=TestType.BASIC,
                timestamp=datetime.now(),
                duration=60.0,
                total_characters=100,
                correct_characters=90,
                wpm=30.0,
                cpm=150.0,
                accuracy=0.9,
                key_statistics=key_stats
            )
            memory_db.save_test_result(result)

        latest = memory_db.get_latest_basic_test()
        assert latest is not None
        assert latest.id == 'test_002'

    def test_get_latest_basic_test_none_when_empty(self, memory_db):
        """测试空数据库时最近测试返回 None"""
        latest = memory_db.get_latest_basic_test()
        assert latest is None

    def test_get_test_history_limit(self, memory_db):
        """测试测试历史记录限制"""
        key_stats = {}
        for i in range(10):
            result = TestResult(
                id=f'test_{i:03d}',
                test_type=TestType.BASIC,
                timestamp=datetime.now(),
                duration=60.0,
                total_characters=100,
                correct_characters=90,
                wpm=30.0,
                cpm=150.0,
                accuracy=0.9,
                key_statistics=key_stats
            )
            memory_db.save_test_result(result)

        history = memory_db.get_test_history(limit=5)
        assert len(history) == 5

    def test_get_test_history_order(self, memory_db):
        """测试测试历史按时间降序排列"""
        key_stats = {}
        for i in range(5):
            result = TestResult(
                id=f'test_{i:03d}',
                test_type=TestType.BASIC,
                timestamp=datetime.now(),
                duration=60.0,
                total_characters=100,
                correct_characters=90,
                wpm=30.0,
                cpm=150.0,
                accuracy=0.9,
                key_statistics=key_stats
            )
            memory_db.save_test_result(result)

        history = memory_db.get_test_history(limit=10)
        assert len(history) == 5
        assert history[0].id == 'test_004'
        assert history[-1].id == 'test_000'

    @patch('keyboard_trainer.data_store.logger')
    def test_save_test_result_handles_error(self, mock_logger, sample_test_result):
        """测试保存测试结果时错误处理"""
        db = DataStore(':memory:')
        with patch.object(db, '_get_connection') as mock_get_conn:
            mock_get_conn.side_effect = sqlite3.Error("Test error")
            success = db.save_test_result(sample_test_result)
            assert success is False
            mock_logger.error.assert_called()
        db.close()


class TestWeakKeysPersistence:
    """测试薄弱按键的保存和获取"""

    def test_weak_keys_saved_automatically(self, memory_db, sample_test_result):
        """测试薄弱按键自动保存"""
        memory_db.save_test_result(sample_test_result)
        weak_keys = memory_db.get_weak_keys()

        assert len(weak_keys) > 0
        weak_key_chars = [wk.key for wk in weak_keys]
        assert 'b' in weak_key_chars  # b is weak (low accuracy + high time)

    def test_save_weak_keys_replaces_existing(self, memory_db):
        """测试保存薄弱按键替换现有记录"""
        weak_keys_1 = [
            WeakKey('x', 0.7, 550.0, 35.0),
            WeakKey('y', 0.8, 520.0, 22.0),
        ]
        memory_db.save_weak_keys(weak_keys_1)

        weak_keys_2 = [
            WeakKey('z', 0.6, 600.0, 50.0),
        ]
        memory_db.save_weak_keys(weak_keys_2)

        loaded = memory_db.get_weak_keys()
        assert len(loaded) == 1
        assert loaded[0].key == 'z'

    def test_get_weak_keys_ordered_by_severity(self, memory_db):
        """测试薄弱按键按严重程度降序排列"""
        weak_keys = [
            WeakKey('a', 0.9, 400.0, 10.0),
            WeakKey('b', 0.7, 550.0, 35.0),
            WeakKey('c', 0.5, 600.0, 60.0),
        ]
        memory_db.save_weak_keys(weak_keys)
        loaded = memory_db.get_weak_keys()

        assert loaded[0].key == 'c'
        assert loaded[1].key == 'b'
        assert loaded[2].key == 'a'

    def test_weak_keys_fields_preserved(self, memory_db):
        """测试薄弱按键字段保存正确"""
        weak_key = WeakKey('x', 0.75, 550.0, 30.5)
        memory_db.save_weak_keys([weak_key])
        loaded = memory_db.get_weak_keys()[0]

        assert loaded.key == 'x'
        assert loaded.accuracy == 0.75
        assert loaded.average_response_time == 550.0
        assert loaded.severity_score == 30.5

    def test_get_weak_keys_empty_when_none_saved(self, memory_db):
        """测试无薄弱按键时空列表"""
        weak_keys = memory_db.get_weak_keys()
        assert weak_keys == []


class TestDataIntegrity:
    """测试数据完整性验证"""

    def test_validate_data_integrity_success(self, memory_db, sample_test_result):
        """测试数据完整性验证成功"""
        memory_db.save_test_result(sample_test_result)
        is_valid = memory_db.validate_data_integrity()
        assert is_valid is True

    def test_validate_data_integrity_detects_missing_tables(self):
        """测试检测缺失表"""
        db = DataStore(':memory:')
        cursor = db._connection.cursor()
        cursor.execute("DROP TABLE weak_keys")
        db._connection.commit()

        is_valid = db.validate_data_integrity()
        assert is_valid is False
        db.close()

    def test_validate_data_integrity_detects_orphan_statistics(self, memory_db):
        """测试检测孤立统计记录"""
        cursor = memory_db._connection.cursor()
        cursor.execute("""
            INSERT INTO key_statistics
            (test_result_id, key_char, total_attempts, correct_attempts, accuracy, average_response_time)
            VALUES ('nonexistent', 'x', 10, 8, 0.8, 400.0)
        """)
        memory_db._connection.commit()

        is_valid = memory_db.validate_data_integrity()
        assert is_valid is False

    def test_validate_data_integrity_detects_orphan_keystrokes(self, memory_db):
        """测试检测孤立按键记录"""
        cursor = memory_db._connection.cursor()
        cursor.execute("""
            INSERT INTO keystroke_records
            (test_result_id, expected_char, actual_char, timestamp, response_time, status)
            VALUES ('nonexistent', 'a', 'b', 1000.0, 200.0, 'correct')
        """)
        memory_db._connection.commit()

        is_valid = memory_db.validate_data_integrity()
        assert is_valid is False

    @patch('keyboard_trainer.data_store.logger')
    def test_validate_data_integrity_handles_error(self, mock_logger):
        """测试完整性验证错误处理"""
        db = DataStore(':memory:')
        db.close()
        db._connection = MagicMock()
        db._connection.cursor.side_effect = sqlite3.Error("Test error")

        is_valid = db.validate_data_integrity()
        assert is_valid is False
        mock_logger.error.assert_called()


class TestBackupFunctionality:
    """测试备份功能"""

    def test_backup_corrupted_data_creates_file(self, tmp_path):
        """测试创建备份文件"""
        db_path = str(tmp_path / 'test.db')
        db = DataStore(db_path)
        db.close()

        backup_path = db.backup_corrupted_data()
        assert os.path.exists(backup_path)
        assert 'backup' in backup_path

    def test_backup_corrupted_data_with_bytes(self, tmp_path):
        """测试用字节数据创建备份"""
        db_path = str(tmp_path / 'test.db')
        db = DataStore(db_path)

        test_data = b'corrupted data'
        backup_path = db.backup_corrupted_data(test_data)

        with open(backup_path, 'rb') as f:
            assert f.read() == test_data
        db.close()

    def test_backup_handles_io_error(self):
        """测试备份处理 IO 错误"""
        db = DataStore(':memory:')
        db.db_path = '/nonexistent/path/test.db'
        
        with patch('keyboard_trainer.data_store.os.path.exists') as mock_exists:
            mock_exists.return_value = True
            with patch('keyboard_trainer.data_store.shutil.copy2') as mock_copy:
                mock_copy.side_effect = IOError("Permission denied")
                backup_path = db.backup_corrupted_data()
                assert backup_path == ''
        db.close()
