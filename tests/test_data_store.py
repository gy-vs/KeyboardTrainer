
import pytest
import sqlite3
from datetime import datetime
from unittest.mock import patch, MagicMock
from keyboard_trainer.data_store import DataStore
from keyboard_trainer.models import (
    TestResult,
    TestType,
    KeyStatistics,
    KeystrokeRecord,
    KeystrokeStatus,
    WeakKey
)


class TestDataStore:
    @pytest.fixture
    def in_memory_db(self):
        return ':memory:'

    @pytest.fixture
    def data_store(self, in_memory_db):
        store = DataStore(in_memory_db)
        yield store
        store.close()

    @pytest.fixture
    def sample_test_result(self):
        key_stats = {
            'a': KeyStatistics('a', 5, 5, 1.0, 200.0),
            'b': KeyStatistics('b', 3, 2, 0.666, 300.0),
            'x': KeyStatistics('x', 10, 8, 0.80, 600.0)
        }
        keystrokes = [
            KeystrokeRecord('a', 'a', 1000.0, 150.0, KeystrokeStatus.CORRECT),
            KeystrokeRecord('b', 'c', 1200.0, 180.0, KeystrokeStatus.INCORRECT),
            KeystrokeRecord('x', 'x', 1400.0, 550.0, KeystrokeStatus.CORRECT)
        ]
        return TestResult(
            id='test-001',
            test_type=TestType.BASIC,
            timestamp=datetime.now(),
            duration=60.5,
            total_characters=100,
            correct_characters=90,
            wpm=50.0,
            cpm=250.0,
            accuracy=0.90,
            key_statistics=key_stats,
            keystrokes=keystrokes
        )

    @pytest.fixture
    def sample_weak_keys(self):
        return [
            WeakKey('x', 0.75, 650.0, 40.0),
            WeakKey('y', 0.80, 550.0, 25.0)
        ]

    def test_database_initialization(self, data_store):
        cursor = data_store._get_connection().cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = {row[0] for row in cursor.fetchall()}
        
        required_tables = {'test_results', 'key_statistics', 'keystroke_records', 'weak_keys'}
        assert required_tables.issubset(tables)

    def test_save_test_result(self, data_store, sample_test_result):
        success = data_store.save_test_result(sample_test_result)
        assert success is True

        cursor = data_store._get_connection().cursor()
        cursor.execute("SELECT id FROM test_results WHERE id = ?", (sample_test_result.id,))
        assert cursor.fetchone() is not None

        cursor.execute("SELECT COUNT(*) FROM key_statistics WHERE test_result_id = ?", (sample_test_result.id,))
        assert cursor.fetchone()[0] == len(sample_test_result.key_statistics)

        cursor.execute("SELECT COUNT(*) FROM keystroke_records WHERE test_result_id = ?", (sample_test_result.id,))
        assert cursor.fetchone()[0] == len(sample_test_result.keystrokes)

    def test_get_test_history(self, data_store, sample_test_result):
        data_store.save_test_result(sample_test_result)
        
        history = data_store.get_test_history(limit=10)
        assert len(history) == 1
        assert history[0].id == sample_test_result.id
        assert history[0].test_type == sample_test_result.test_type
        assert history[0].wpm == sample_test_result.wpm

    def test_get_latest_basic_test(self, data_store, sample_test_result):
        data_store.save_test_result(sample_test_result)
        
        latest = data_store.get_latest_basic_test()
        assert latest is not None
        assert latest.id == sample_test_result.id
        assert latest.test_type == TestType.BASIC

    def test_save_and_get_weak_keys(self, data_store, sample_weak_keys):
        success = data_store.save_weak_keys(sample_weak_keys)
        assert success is True

        retrieved = data_store.get_weak_keys()
        assert len(retrieved) == len(sample_weak_keys)
        
        retrieved_keys = {wk.key for wk in retrieved}
        sample_keys = {wk.key for wk in sample_weak_keys}
        assert retrieved_keys == sample_keys

    def test_save_weak_keys_replaces_existing(self, data_store, sample_weak_keys):
        data_store.save_weak_keys(sample_weak_keys)
        assert len(data_store.get_weak_keys()) == 2

        new_weak_keys = [WeakKey('z', 0.70, 700.0, 50.0)]
        data_store.save_weak_keys(new_weak_keys)
        
        retrieved = data_store.get_weak_keys()
        assert len(retrieved) == 1
        assert retrieved[0].key == 'z'

    def test_validate_data_integrity_valid(self, data_store, sample_test_result):
        data_store.save_test_result(sample_test_result)
        assert data_store.validate_data_integrity() is True

    def test_validate_data_integrity_with_missing_tables(self, in_memory_db):
        store = DataStore(in_memory_db)
        cursor = store._get_connection().cursor()
        cursor.execute("DROP TABLE weak_keys")
        store._get_connection().commit()
        
        assert store.validate_data_integrity() is False
        store.close()

    def test_save_test_result_roundtrip(self, data_store, sample_test_result):
        data_store.save_test_result(sample_test_result)
        
        retrieved = data_store.get_test_history(limit=1)[0]
        
        assert retrieved.id == sample_test_result.id
        assert retrieved.test_type == sample_test_result.test_type
        assert retrieved.duration == sample_test_result.duration
        assert retrieved.total_characters == sample_test_result.total_characters
        assert retrieved.correct_characters == sample_test_result.correct_characters
        assert retrieved.wpm == sample_test_result.wpm
        assert retrieved.cpm == sample_test_result.cpm
        assert retrieved.accuracy == sample_test_result.accuracy
        
        assert len(retrieved.key_statistics) == len(sample_test_result.key_statistics)
        for key in sample_test_result.key_statistics:
            assert key in retrieved.key_statistics
            assert retrieved.key_statistics[key].key == sample_test_result.key_statistics[key].key
            assert retrieved.key_statistics[key].total_attempts == sample_test_result.key_statistics[key].total_attempts
            assert retrieved.key_statistics[key].correct_attempts == sample_test_result.key_statistics[key].correct_attempts

        assert len(retrieved.keystrokes) == len(sample_test_result.keystrokes)

    def test_save_test_result_with_error(self, data_store, sample_test_result):
        with patch.object(data_store, '_get_connection') as mock_get_conn:
            mock_conn = MagicMock()
            mock_conn.cursor.side_effect = sqlite3.Error("Database error")
            mock_get_conn.return_value = mock_conn
            
            success = data_store.save_test_result(sample_test_result)
            assert success is False

    def test_get_latest_basic_test_none(self, data_store):
        assert data_store.get_latest_basic_test() is None

    def test_get_test_history_empty(self, data_store):
        assert data_store.get_test_history() == []

    def test_get_weak_keys_empty(self, data_store):
        assert data_store.get_weak_keys() == []

    def test_backup_corrupted_data(self, in_memory_db, tmp_path):
        db_path = str(tmp_path / "test.db")
        store = DataStore(db_path)
        
        backup_path = store.backup_corrupted_data()
        assert backup_path != ""
        store.close()

    def test_close_connection(self, data_store):
        data_store.close()
        assert data_store._connection is None

    def test_weak_keys_saved_automatically(self, data_store, sample_test_result):
        data_store.save_test_result(sample_test_result)
        weak_keys = data_store.get_weak_keys()
        assert len(weak_keys) > 0
        assert any(wk.key == 'x' for wk in weak_keys)

