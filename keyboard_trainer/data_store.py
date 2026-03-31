"""
数据存储模块

管理测试结果的持久化，使用 SQLite 数据库存储。

Requirements: 8.1, 8.2, 8.3, 8.4, 8.5
"""

import json
import logging
import os
import shutil
import sqlite3
from datetime import datetime
from typing import Dict, List, Optional

from keyboard_trainer.models import (
    KeyStatistics,
    KeystrokeRecord,
    KeystrokeStatus,
    TestResult,
    TestType,
    WeakKey,
)

logger = logging.getLogger(__name__)


class DataStore:
    """数据存储，管理测试结果的持久化"""

    def __init__(self, db_path: str):
        """
        初始化数据存储
        
        Args:
            db_path: SQLite 数据库文件路径
        """
        self.db_path = db_path
        self._connection: Optional[sqlite3.Connection] = None
        self._ensure_directory()
        self._init_database()

    def _ensure_directory(self) -> None:
        """确保数据库目录存在"""
        db_dir = os.path.dirname(self.db_path)
        if db_dir and not os.path.exists(db_dir):
            os.makedirs(db_dir, exist_ok=True)

    def _init_database(self) -> None:
        """初始化数据库表结构"""
        self._connection = sqlite3.connect(self.db_path)
        self._connection.row_factory = sqlite3.Row
        cursor = self._connection.cursor()
        
        # 测试结果表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS test_results (
                id TEXT PRIMARY KEY,
                test_type TEXT NOT NULL,
                timestamp TEXT NOT NULL,
                duration REAL NOT NULL,
                total_characters INTEGER NOT NULL,
                correct_characters INTEGER NOT NULL,
                wpm REAL NOT NULL,
                cpm REAL NOT NULL,
                accuracy REAL NOT NULL
            )
        """)
        
        # 按键统计表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS key_statistics (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                test_result_id TEXT NOT NULL,
                key_char TEXT NOT NULL,
                total_attempts INTEGER NOT NULL,
                correct_attempts INTEGER NOT NULL,
                accuracy REAL NOT NULL,
                average_response_time REAL NOT NULL,
                FOREIGN KEY (test_result_id) REFERENCES test_results(id)
            )
        """)
        
        # 按键记录表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS keystroke_records (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                test_result_id TEXT NOT NULL,
                expected_char TEXT NOT NULL,
                actual_char TEXT NOT NULL,
                timestamp REAL NOT NULL,
                response_time REAL NOT NULL,
                status TEXT NOT NULL,
                FOREIGN KEY (test_result_id) REFERENCES test_results(id)
            )
        """)
        
        # 薄弱按键表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS weak_keys (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                key_char TEXT NOT NULL,
                accuracy REAL NOT NULL,
                average_response_time REAL NOT NULL,
                severity_score REAL NOT NULL,
                identified_at TEXT NOT NULL
            )
        """)
        
        self._connection.commit()

    def close(self) -> None:
        """关闭数据库连接"""
        if self._connection:
            self._connection.close()
            self._connection = None

    def _get_connection(self) -> sqlite3.Connection:
        """获取数据库连接"""
        if self._connection is None:
            self._connection = sqlite3.connect(self.db_path)
            self._connection.row_factory = sqlite3.Row
        return self._connection

    def save_test_result(self, result: TestResult) -> bool:
        """
        保存测试结果
        
        Args:
            result: 测试结果对象
            
        Returns:
            保存是否成功
        """
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            # 保存测试结果
            cursor.execute("""
                INSERT INTO test_results 
                (id, test_type, timestamp, duration, total_characters, 
                 correct_characters, wpm, cpm, accuracy)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                result.id,
                result.test_type.value,
                result.timestamp.isoformat(),
                result.duration,
                result.total_characters,
                result.correct_characters,
                result.wpm,
                result.cpm,
                result.accuracy
            ))
            
            # 保存按键统计
            for key, stats in result.key_statistics.items():
                cursor.execute("""
                    INSERT INTO key_statistics
                    (test_result_id, key_char, total_attempts, correct_attempts,
                     accuracy, average_response_time)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (
                    result.id,
                    stats.key,
                    stats.total_attempts,
                    stats.correct_attempts,
                    stats.accuracy,
                    stats.average_response_time
                ))
            
            # 保存按键记录
            for keystroke in result.keystrokes:
                cursor.execute("""
                    INSERT INTO keystroke_records
                    (test_result_id, expected_char, actual_char, timestamp,
                     response_time, status)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (
                    result.id,
                    keystroke.expected_char,
                    keystroke.actual_char,
                    keystroke.timestamp,
                    keystroke.response_time,
                    keystroke.status.value
                ))
            
            # 识别并保存薄弱按键
            weak_keys = []
            for key, stats in result.key_statistics.items():
                if stats.is_weak:
                    # 计算严重程度评分：准确率越低、响应时间越高，评分越高
                    accuracy_penalty = (1.0 - stats.accuracy) * 100
                    time_penalty = max(0, (stats.average_response_time - 500) / 10) if stats.average_response_time > 500 else 0
                    severity = accuracy_penalty + time_penalty
                    weak_keys.append(WeakKey(
                        key=key,
                        accuracy=stats.accuracy,
                        average_response_time=stats.average_response_time,
                        severity_score=severity
                    ))
            
            if weak_keys:
                self.save_weak_keys(weak_keys)
            
            conn.commit()
            logger.info(f"Saved test result: {result.id}")
            return True
            
        except sqlite3.Error as e:
            logger.error(f"Failed to save test result: {e}")
            return False

    def get_latest_basic_test(self) -> Optional[TestResult]:
        """
        获取最近的基础测试结果
        
        Returns:
            最近的基础测试结果，如果没有则返回 None
        """
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            cursor.execute("""
                SELECT id, test_type, timestamp, duration, total_characters,
                       correct_characters, wpm, cpm, accuracy
                FROM test_results
                WHERE test_type = ?
                ORDER BY timestamp DESC
                LIMIT 1
            """, (TestType.BASIC.value,))
            
            row = cursor.fetchone()
            if row:
                return self._load_test_result(conn, row)
            return None
            
        except sqlite3.Error as e:
            logger.error(f"Failed to get latest basic test: {e}")
            return None

    def get_test_history(self, limit: int = 10) -> List[TestResult]:
        """
        获取测试历史记录
        
        Args:
            limit: 返回记录数量限制
            
        Returns:
            测试结果列表
        """
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            cursor.execute("""
                SELECT id, test_type, timestamp, duration, total_characters,
                       correct_characters, wpm, cpm, accuracy
                FROM test_results
                ORDER BY timestamp DESC
                LIMIT ?
            """, (limit,))
            
            results = []
            for row in cursor.fetchall():
                result = self._load_test_result(conn, row)
                if result:
                    results.append(result)
            return results
            
        except sqlite3.Error as e:
            logger.error(f"Failed to get test history: {e}")
            return []

    def get_weak_keys(self) -> List[WeakKey]:
        """
        获取当前薄弱按键列表
        
        Returns:
            薄弱按键列表
        """
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            cursor.execute("""
                SELECT key_char, accuracy, average_response_time, severity_score
                FROM weak_keys
                ORDER BY severity_score DESC
            """)
            
            return [
                WeakKey(
                    key=row[0],
                    accuracy=row[1],
                    average_response_time=row[2],
                    severity_score=row[3]
                )
                for row in cursor.fetchall()
            ]
            
        except sqlite3.Error as e:
            logger.error(f"Failed to get weak keys: {e}")
            return []

    def save_weak_keys(self, weak_keys: List[WeakKey]) -> bool:
        """
        保存薄弱按键列表（替换现有记录）
        
        Args:
            weak_keys: 薄弱按键列表
            
        Returns:
            保存是否成功
        """
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            # 清除现有记录
            cursor.execute("DELETE FROM weak_keys")
            
            # 插入新记录
            now = datetime.now().isoformat()
            for wk in weak_keys:
                cursor.execute("""
                    INSERT INTO weak_keys
                    (key_char, accuracy, average_response_time, severity_score, identified_at)
                    VALUES (?, ?, ?, ?, ?)
                """, (wk.key, wk.accuracy, wk.average_response_time, wk.severity_score, now))
            
            conn.commit()
            return True
            
        except sqlite3.Error as e:
            logger.error(f"Failed to save weak keys: {e}")
            return False

    def validate_data_integrity(self) -> bool:
        """
        验证数据完整性
        
        Returns:
            数据是否完整有效
        """
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            # 检查表是否存在
            cursor.execute("""
                SELECT name FROM sqlite_master 
                WHERE type='table' AND name IN 
                ('test_results', 'key_statistics', 'keystroke_records', 'weak_keys')
            """)
            tables = {row[0] for row in cursor.fetchall()}
            required_tables = {'test_results', 'key_statistics', 'keystroke_records', 'weak_keys'}
            
            if not required_tables.issubset(tables):
                logger.warning("Missing required tables")
                return False
            
            # 检查外键完整性
            cursor.execute("""
                SELECT COUNT(*) FROM key_statistics ks
                LEFT JOIN test_results tr ON ks.test_result_id = tr.id
                WHERE tr.id IS NULL
            """)
            orphan_stats = cursor.fetchone()[0]
            
            cursor.execute("""
                SELECT COUNT(*) FROM keystroke_records kr
                LEFT JOIN test_results tr ON kr.test_result_id = tr.id
                WHERE tr.id IS NULL
            """)
            orphan_keystrokes = cursor.fetchone()[0]
            
            if orphan_stats > 0 or orphan_keystrokes > 0:
                logger.warning(f"Found orphan records: stats={orphan_stats}, keystrokes={orphan_keystrokes}")
                return False
            
            return True
            
        except sqlite3.Error as e:
            logger.error(f"Data integrity check failed: {e}")
            return False

    def backup_corrupted_data(self, data: bytes = None) -> str:
        """
        备份损坏的数据
        
        Args:
            data: 可选的损坏数据字节。如果提供，将保存这些字节；否则备份数据库文件
            
        Returns:
            备份文件路径
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_path = f"{self.db_path}.backup_{timestamp}"
        
        try:
            if data:
                # 保存原始数据字节
                with open(backup_path, 'wb') as f:
                    f.write(data)
                logger.info(f"Saved corrupted data to: {backup_path}")
            elif os.path.exists(self.db_path):
                # 备份数据库文件
                shutil.copy2(self.db_path, backup_path)
                logger.info(f"Created backup at: {backup_path}")
                
            return backup_path
            
        except (IOError, OSError) as e:
            logger.error(f"Failed to create backup: {e}")
            return ""

    def _load_test_result(self, conn: sqlite3.Connection, row: tuple) -> Optional[TestResult]:
        """从数据库行加载完整的测试结果"""
        try:
            cursor = conn.cursor()
            test_id = row[0]
            
            # 加载按键统计
            cursor.execute("""
                SELECT key_char, total_attempts, correct_attempts, accuracy, average_response_time
                FROM key_statistics
                WHERE test_result_id = ?
            """, (test_id,))
            
            key_statistics: Dict[str, KeyStatistics] = {}
            for stat_row in cursor.fetchall():
                key_statistics[stat_row[0]] = KeyStatistics(
                    key=stat_row[0],
                    total_attempts=stat_row[1],
                    correct_attempts=stat_row[2],
                    accuracy=stat_row[3],
                    average_response_time=stat_row[4]
                )
            
            # 加载按键记录
            cursor.execute("""
                SELECT expected_char, actual_char, timestamp, response_time, status
                FROM keystroke_records
                WHERE test_result_id = ?
                ORDER BY timestamp
            """, (test_id,))
            
            keystrokes: List[KeystrokeRecord] = []
            for ks_row in cursor.fetchall():
                keystrokes.append(KeystrokeRecord(
                    expected_char=ks_row[0],
                    actual_char=ks_row[1],
                    timestamp=ks_row[2],
                    response_time=ks_row[3],
                    status=KeystrokeStatus(ks_row[4])
                ))
            
            return TestResult(
                id=row[0],
                test_type=TestType(row[1]),
                timestamp=datetime.fromisoformat(row[2]),
                duration=row[3],
                total_characters=row[4],
                correct_characters=row[5],
                wpm=row[6],
                cpm=row[7],
                accuracy=row[8],
                key_statistics=key_statistics,
                keystrokes=keystrokes
            )
            
        except (ValueError, KeyError) as e:
            logger.error(f"Failed to load test result: {e}")
            return None
