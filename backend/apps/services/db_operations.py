"""
Unified database operations service with transaction management and 4-database sync.

This module provides high-level database operations that automatically:
1. Apply changes to all 4 databases (MySQL/MariaDB/PostgreSQL/SQLite)
2. Use transaction management with appropriate isolation levels
3. Publish sync events to Redis Streams
4. Handle conflicts and retry on deadlock
"""
from __future__ import annotations

import json
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

from loguru import logger
from sqlalchemy import text
from sqlalchemy.orm import Session

from apps.core.database import db_manager
from apps.core.sync_engine import SyncEvent, sync_engine
from apps.core.transaction import with_transaction, IsolationLevel


class DatabaseOperationService:
    """
    Unified service for database operations across all 4 databases.
    
    All operations automatically:
    - Execute in transactions with retry on deadlock
    - Replicate to all target databases
    - Publish events to Redis Streams for async sync
    - Log conflicts for manual resolution
    """

    # 目标数据库列表
    TARGET_DATABASES = ["mysql", "mariadb", "postgres", "sqlite"]
    
    # 主数据库(发起同步的源)
    PRIMARY_DATABASE = "mysql"

    def __init__(self):
        self.sync_engine = sync_engine

    def execute_on_all_databases(
        self,
        operation_name: str,
        sql: str,
        params: Optional[Dict[str, Any]] = None,
        primary_only: bool = False,
    ) -> Dict[str, Any]:
        """
        Execute SQL on all databases with transaction management.
        
        Args:
            operation_name: Operation description for logging
            sql: SQL statement to execute
            params: Parameters for the SQL statement
            primary_only: If True, only execute on primary database
            
        Returns:
            Dict with execution results per database
        """
        params = params or {}
        results = {}
        
        # 确定目标数据库
        targets = [self.PRIMARY_DATABASE] if primary_only else self.TARGET_DATABASES
        
        for db_name in targets:
            try:
                with db_manager.session_scope(db_name) as session:
                    result = session.execute(text(sql), params)
                    session.flush()
                    
                    results[db_name] = {
                        'status': 'success',
                        'rowcount': result.rowcount,
                    }
                    
                    logger.info(
                        f"{operation_name} executed on {db_name}",
                        rowcount=result.rowcount,
                    )
                    
            except Exception as e:
                results[db_name] = {
                    'status': 'failed',
                    'error': str(e),
                }
                logger.error(
                    f"{operation_name} failed on {db_name}",
                    error=str(e),
                )
        
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
        Insert record with automatic sync to all databases.
        
        Args:
            session: Database session (for primary database)
            table: Table name
            data: Record data as dict
            sync_to_all: If True, sync to all databases
            
        Returns:
            Inserted record ID
        """
        # 构建 INSERT 语句
        columns = ', '.join(data.keys())
        placeholders = ', '.join([f':{key}' for key in data.keys()])
        sql = f"INSERT INTO {table} ({columns}) VALUES ({placeholders})"
        
        # 在主库执行
        result = session.execute(text(sql), data)
        session.flush()
        
        # 获取插入的 ID (假设使用自增主键)
        inserted_id = result.lastrowid
        
        if sync_to_all:
            # 发布同步事件
            event = SyncEvent(
                table=table,
                action='insert',
                payload={
                    'statement': sql,
                    'params': data,
                    'record_id': inserted_id,
                },
                origin=self.PRIMARY_DATABASE,
                occurred_at=datetime.utcnow(),
                sync_version=1,
                record_id=str(inserted_id),
            )
            
            # 立即同步到其他数据库
            other_targets = [
                db for db in self.TARGET_DATABASES 
                if db != self.PRIMARY_DATABASE
            ]
            self.sync_engine.replicate(event, other_targets)
            
            # 发布到 Redis Stream (供 worker 异步处理)
            self.sync_engine.publish_event(event)
        
        return inserted_id

    @with_transaction(PRIMARY_DATABASE, max_retries=3)
    def update_with_sync(
        self,
        session: Session,
        table: str,
        record_id: int,
        data: Dict[str, Any],
        sync_to_all: bool = True,
    ) -> int:
        """
        Update record with automatic sync to all databases.
        
        Args:
            session: Database session (for primary database)
            table: Table name
            record_id: Record ID to update
            data: New data as dict
            sync_to_all: If True, sync to all databases
            
        Returns:
            Number of affected rows
        """
        # 构建 UPDATE 语句
        set_clause = ', '.join([f"{key} = :{key}" for key in data.keys()])
        sql = f"UPDATE {table} SET {set_clause} WHERE id = :record_id"
        
        params = {**data, 'record_id': record_id}
        
        # 在主库执行
        result = session.execute(text(sql), params)
        session.flush()
        
        if sync_to_all and result.rowcount > 0:
            # 发布同步事件
            event = SyncEvent(
                table=table,
                action='update',
                payload={
                    'statement': sql,
                    'params': params,
                    'record_id': record_id,
                },
                origin=self.PRIMARY_DATABASE,
                occurred_at=datetime.utcnow(),
                sync_version=1,
                record_id=str(record_id),
            )
            
            # 立即同步到其他数据库
            other_targets = [
                db for db in self.TARGET_DATABASES 
                if db != self.PRIMARY_DATABASE
            ]
            self.sync_engine.replicate(event, other_targets)
            
            # 发布到 Redis Stream
            self.sync_engine.publish_event(event)
        
        return result.rowcount

    @with_transaction(PRIMARY_DATABASE, max_retries=3)
    def delete_with_sync(
        self,
        session: Session,
        table: str,
        record_id: int,
        sync_to_all: bool = True,
    ) -> int:
        """
        Delete record with automatic sync to all databases.
        
        Args:
            session: Database session (for primary database)
            table: Table name
            record_id: Record ID to delete
            sync_to_all: If True, sync to all databases
            
        Returns:
            Number of affected rows
        """
        sql = f"DELETE FROM {table} WHERE id = :record_id"
        params = {'record_id': record_id}
        
        # 在主库执行
        result = session.execute(text(sql), params)
        session.flush()
        
        if sync_to_all and result.rowcount > 0:
            # 发布同步事件
            event = SyncEvent(
                table=table,
                action='delete',
                payload={
                    'statement': sql,
                    'params': params,
                    'record_id': record_id,
                },
                origin=self.PRIMARY_DATABASE,
                occurred_at=datetime.utcnow(),
                sync_version=1,
                record_id=str(record_id),
            )
            
            # 立即同步到其他数据库
            other_targets = [
                db for db in self.TARGET_DATABASES 
                if db != self.PRIMARY_DATABASE
            ]
            self.sync_engine.replicate(event, other_targets)
            
            # 发布到 Redis Stream
            self.sync_engine.publish_event(event)
        
        return result.rowcount

    def bulk_insert_with_sync(
        self,
        table: str,
        records: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """
        Bulk insert records to all databases with transaction management.
        
        Args:
            table: Table name
            records: List of records to insert
            
        Returns:
            Results dict with success/failure per database
        """
        results = {}
        
        for db_name in self.TARGET_DATABASES:
            try:
                with db_manager.session_scope(db_name) as session:
                    # 批量插入
                    if records:
                        columns = ', '.join(records[0].keys())
                        placeholders = ', '.join([f':{key}' for key in records[0].keys()])
                        sql = f"INSERT INTO {table} ({columns}) VALUES ({placeholders})"
                        
                        for record in records:
                            session.execute(text(sql), record)
                        
                        session.flush()
                        
                        results[db_name] = {
                            'status': 'success',
                            'count': len(records),
                        }
                        
                        logger.info(
                            f"Bulk insert to {db_name}",
                            table=table,
                            count=len(records),
                        )
                        
            except Exception as e:
                results[db_name] = {
                    'status': 'failed',
                    'error': str(e),
                }
                logger.error(
                    f"Bulk insert failed on {db_name}",
                    table=table,
                    error=str(e),
                )
        
        return results

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
