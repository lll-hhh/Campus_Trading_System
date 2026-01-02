"""
Unified database operations service with transaction management.

This module provides high-level database operations that automatically:
1. Apply changes to the MySQL database
2. Use transaction management with appropriate isolation levels
3. Handle conflicts and retry on deadlock
"""
from __future__ import annotations

import json
from datetime import datetime
from typing import Any, Dict, Optional

from loguru import logger
from sqlalchemy import text
from sqlalchemy.orm import Session

from apps.core.database import db_manager
from apps.core.transaction import with_transaction


class DatabaseOperationService:
    """
    Unified service for database operations.
    """

    # 目标数据库列表
    TARGET_DATABASES = ["mysql"]
    
    # 主数据库(发起同步的源)
    PRIMARY_DATABASE = "mysql"

    def __init__(self):
        pass

    def execute_on_all_databases(
        self,
        operation_name: str,
        sql: str,
        params: Optional[Dict[str, Any]] = None,
        primary_only: bool = False,
    ) -> Dict[str, Any]:
        """
        Execute SQL on primary database.
        """
        results = {}
        try:
            with db_manager.session_scope(self.PRIMARY_DATABASE) as session:
                result = session.execute(text(sql), params or {})
                results[self.PRIMARY_DATABASE] = {"status": "success", "rows": result.rowcount}
        except Exception as e:
            logger.error(f"Error executing {operation_name} on {self.PRIMARY_DATABASE}: {e}")
            results[self.PRIMARY_DATABASE] = {"status": "error", "message": str(e)}
        
        return results

    @with_transaction(PRIMARY_DATABASE, max_retries=3)
    def insert_with_sync(
        self,
        session: Session,
        table: str,
        data: Dict[str, Any],
        sync_to_all: bool = True,
    ) -> int:
        """
        Insert record.
        """
        # 构建 INSERT 语句
        columns = ', '.join(data.keys())
        placeholders = ', '.join([f':{key}' for key in data.keys()])
        sql = f"INSERT INTO {table} ({columns}) VALUES ({placeholders})"
        
        # 在主库执行
        result = session.execute(text(sql), data)
        session.flush()
        
        # 获取插入的 ID
        inserted_id = result.lastrowid
        
        return inserted_id

    @with_transaction(PRIMARY_DATABASE, max_retries=3)
    def update_with_sync(
        self,
        session: Session,
        table: str,
        data: Dict[str, Any],
        where_clause: str,
        where_params: Dict[str, Any],
        sync_to_all: bool = True,
    ) -> int:
        """
        Update record.
        """
        # 构建 UPDATE 语句
        set_clause = ', '.join([f"{key} = :{key}" for key in data.keys()])
        sql = f"UPDATE {table} SET {set_clause} WHERE {where_clause}"
        
        # 合并参数
        params = {**data, **where_params}
        
        # 在主库执行
        result = session.execute(text(sql), params)
        session.flush()
        
        return result.rowcount

    @with_transaction(PRIMARY_DATABASE, max_retries=3)
    def delete_with_sync(
        self,
        session: Session,
        table: str,
        where_clause: str,
        where_params: Dict[str, Any],
        sync_to_all: bool = True,
    ) -> int:
        """
        Delete record.
        """
        sql = f"DELETE FROM {table} WHERE {where_clause}"
        
        # 在主库执行
        result = session.execute(text(sql), where_params)
        session.flush()
        
        return result.rowcount

    def verify_sync_consistency(
        self,
        table: str,
        record_id: int,
    ) -> Dict[str, Any]:
        """
        Verify that a record is consistent across all databases.
        
        Args:
            table: Table name
            record_id: Record ID to check
            
        Returns:
            Dict with consistency status and any differences
        """
        sql = f"SELECT * FROM {table} WHERE id = :record_id"
        params = {'record_id': record_id}
        
        records = {}
        
        for db_name in self.TARGET_DATABASES:
            try:
                with db_manager.session_scope(db_name) as session:
                    result = session.execute(text(sql), params)
                    row = result.fetchone()
                    
                    if row:
                        # 转换为字典
                        records[db_name] = dict(row._mapping)
                    else:
                        records[db_name] = None
                        
            except Exception as e:
                records[db_name] = {'error': str(e)}
        
        # 检查一致性
        values = [
            json.dumps(r, sort_keys=True, default=str) 
            for r in records.values() 
            if r is not None and 'error' not in r
        ]
        
        is_consistent = len(set(values)) <= 1
        
        return {
            'consistent': is_consistent,
            'records': records,
            'databases_checked': len(self.TARGET_DATABASES),
        }

    def get_sync_status(self) -> Dict[str, Any]:
        """
        Get synchronization status across all databases.
        
        Returns:
            Dict with sync status information
        """
        status = {
            'primary_database': self.PRIMARY_DATABASE,
            'target_databases': self.TARGET_DATABASES,
            'database_status': {},
        }
        
        for db_name in self.TARGET_DATABASES:
            try:
                with db_manager.session_scope(db_name) as session:
                    # 测试连接
                    session.execute(text("SELECT 1"))
                    
                    status['database_status'][db_name] = {
                        'status': 'online',
                        'isolation_level': self._get_isolation_level(db_name),
                    }
                    
            except Exception as e:
                status['database_status'][db_name] = {
                    'status': 'offline',
                    'error': str(e),
                }
        
        return status

    def _get_isolation_level(self, db_name: str) -> str:
        """Get configured isolation level for database."""
        from apps.core.transaction import TransactionConfig
        
        isolation = TransactionConfig.get_isolation_level(db_name)
        return isolation.value


# 全局单例
db_operation_service = DatabaseOperationService()
