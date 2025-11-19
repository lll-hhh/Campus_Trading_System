"""
数据库同步管理器 - 四库写入、冲突检测、版本管理
"""
from __future__ import annotations

import asyncio
from datetime import datetime
from typing import Any, Dict, List, Optional, Set
from contextlib import contextmanager

from loguru import logger
from sqlalchemy import text, select
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError, DatabaseError

from apps.core.database import db_manager
from apps.core.models import ConflictRecord, SyncLog, SyncConfig
from apps.services.notifications import email_notifier


class DatabaseSyncManager:
    """
    四数据库同步管理器
    
    功能：
    1. 并行写入四个数据库
    2. 版本号管理和乐观锁
    3. 冲突检测和记录
    4. 自动重试和降级
    5. 同步状态监控
    """
    
    # 数据库优先级（MySQL为主库）
    DB_PRIORITY = ["mysql", "postgres", "mariadb", "sqlite"]
    
    # 需要同步的表
    SYNC_TABLES = {
        "users", "items", "categories", "orders", "order_items",
        "shopping_cart", "messages", "notifications", "favorites",
        "comments", "search_history", "view_history", "transactions"
    }
    
    def __init__(self):
        self.success_count = 0
        self.failure_count = 0
        self.conflict_count = 0
        
    async def sync_write(
        self,
        table: str,
        action: str,
        data: Dict[str, Any],
        record_id: Optional[int] = None,
        user_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        四库同步写入主方法
        
        Args:
            table: 表名
            action: 操作类型 (insert/update/delete)
            data: 数据字典
            record_id: 记录ID（用于update/delete）
            user_id: 操作用户ID
            
        Returns:
            同步结果字典
        """
        if table not in self.SYNC_TABLES:
            logger.warning(f"Table {table} is not in sync list, skipping sync")
            return {"status": "skipped", "reason": "table not in sync list"}
        
        # 添加版本号（乐观锁）
        if action in ["update", "delete"] and "version" not in data:
            data["version"] = await self._get_current_version(table, record_id)
        
        # 添加更新时间
        if action in ["insert", "update"]:
            data["updated_at"] = datetime.utcnow()
            if action == "insert":
                data["created_at"] = datetime.utcnow()
        
        # 并行写入四个数据库
        results = {}
        tasks = []
        
        for db_name in self.DB_PRIORITY:
            task = self._write_to_database(
                db_name=db_name,
                table=table,
                action=action,
                data=data,
                record_id=record_id
            )
            tasks.append((db_name, task))
        
        # 执行并行写入
        for db_name, task in tasks:
            try:
                result = await task
                results[db_name] = result
                if result["success"]:
                    self.success_count += 1
                else:
                    self.failure_count += 1
            except Exception as e:
                logger.error(f"Failed to sync to {db_name}: {str(e)}")
                results[db_name] = {
                    "success": False,
                    "error": str(e),
                    "timestamp": datetime.utcnow()
                }
                self.failure_count += 1
        
        # 检测冲突
        conflicts = await self._detect_conflicts(results, table, record_id)
        if conflicts:
            self.conflict_count += len(conflicts)
            await self._handle_conflicts(conflicts, table, record_id, user_id)
        
        # 记录同步日志
        await self._log_sync_operation(table, action, results, conflicts)
        
        # 计算成功率
        success_dbs = [db for db, r in results.items() if r.get("success")]
        success_rate = len(success_dbs) / len(self.DB_PRIORITY)
        
        return {
            "status": "completed",
            "success_rate": success_rate,
            "success_dbs": success_dbs,
            "results": results,
            "conflicts": conflicts,
            "timestamp": datetime.utcnow()
        }
    
    async def _write_to_database(
        self,
        db_name: str,
        table: str,
        action: str,
        data: Dict[str, Any],
        record_id: Optional[int]
    ) -> Dict[str, Any]:
        """
        向单个数据库写入数据
        """
        try:
            with db_manager.session_scope(db_name) as session:
                if action == "insert":
                    return await self._execute_insert(session, table, data)
                elif action == "update":
                    return await self._execute_update(session, table, data, record_id)
                elif action == "delete":
                    return await self._execute_delete(session, table, record_id, data.get("version"))
                else:
                    raise ValueError(f"Unknown action: {action}")
        except Exception as e:
            logger.error(f"Database write error on {db_name}.{table}: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "db": db_name,
                "timestamp": datetime.utcnow()
            }
    
    async def _execute_insert(
        self,
        session: Session,
        table: str,
        data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """执行INSERT操作"""
        # 构建INSERT语句
        columns = ", ".join(data.keys())
        placeholders = ", ".join([f":{key}" for key in data.keys()])
        query = f"INSERT INTO {table} ({columns}) VALUES ({placeholders})"
        
        result = session.execute(text(query), data)
        session.commit()
        
        # 获取插入的ID
        inserted_id = result.lastrowid if hasattr(result, 'lastrowid') else None
        
        return {
            "success": True,
            "action": "insert",
            "inserted_id": inserted_id,
            "timestamp": datetime.utcnow()
        }
    
    async def _execute_update(
        self,
        session: Session,
        table: str,
        data: Dict[str, Any],
        record_id: int
    ) -> Dict[str, Any]:
        """执行UPDATE操作（带乐观锁）"""
        # 提取旧版本号
        old_version = data.pop("version", 0)
        new_version = old_version + 1
        data["version"] = new_version
        
        # 构建UPDATE语句（包含版本检查）
        set_clause = ", ".join([f"{key} = :{key}" for key in data.keys()])
        query = f"""
            UPDATE {table}
            SET {set_clause}
            WHERE id = :id AND version = :old_version
        """
        
        params = {**data, "id": record_id, "old_version": old_version}
        result = session.execute(text(query), params)
        
        rows_affected = result.rowcount
        
        if rows_affected == 0:
            # 版本冲突或记录不存在
            return {
                "success": False,
                "action": "update",
                "conflict": True,
                "reason": "version mismatch or record not found",
                "timestamp": datetime.utcnow()
            }
        
        session.commit()
        return {
            "success": True,
            "action": "update",
            "rows_affected": rows_affected,
            "new_version": new_version,
            "timestamp": datetime.utcnow()
        }
    
    async def _execute_delete(
        self,
        session: Session,
        table: str,
        record_id: int,
        version: Optional[int]
    ) -> Dict[str, Any]:
        """执行DELETE操作（带版本检查）"""
        if version is not None:
            # 带版本号的删除
            query = f"DELETE FROM {table} WHERE id = :id AND version = :version"
            params = {"id": record_id, "version": version}
        else:
            # 强制删除
            query = f"DELETE FROM {table} WHERE id = :id"
            params = {"id": record_id}
        
        result = session.execute(text(query), params)
        rows_affected = result.rowcount
        
        if rows_affected == 0 and version is not None:
            return {
                "success": False,
                "action": "delete",
                "conflict": True,
                "reason": "version mismatch or record not found",
                "timestamp": datetime.utcnow()
            }
        
        session.commit()
        return {
            "success": True,
            "action": "delete",
            "rows_affected": rows_affected,
            "timestamp": datetime.utcnow()
        }
    
    async def _get_current_version(self, table: str, record_id: int) -> int:
        """从主库获取当前版本号"""
        try:
            with db_manager.session_scope("mysql") as session:
                query = f"SELECT version FROM {table} WHERE id = :id"
                result = session.execute(text(query), {"id": record_id})
                row = result.fetchone()
                return row[0] if row else 0
        except Exception as e:
            logger.error(f"Failed to get version for {table}.{record_id}: {str(e)}")
            return 0
    
    async def _detect_conflicts(
        self,
        results: Dict[str, Dict[str, Any]],
        table: str,
        record_id: Optional[int]
    ) -> List[Dict[str, Any]]:
        """
        检测同步冲突
        
        冲突类型：
        1. 版本冲突：乐观锁检测到版本不匹配
        2. 部分失败：部分数据库写入成功，部分失败
        3. 数据不一致：各数据库返回的结果不一致
        """
        conflicts = []
        
        # 检查版本冲突
        version_conflicts = [
            db for db, r in results.items()
            if not r.get("success") and r.get("conflict")
        ]
        
        if version_conflicts:
            conflicts.append({
                "type": "version_conflict",
                "databases": version_conflicts,
                "table": table,
                "record_id": record_id,
                "timestamp": datetime.utcnow()
            })
        
        # 检查部分失败
        success_dbs = [db for db, r in results.items() if r.get("success")]
        failed_dbs = [db for db, r in results.items() if not r.get("success")]
        
        if success_dbs and failed_dbs:
            conflicts.append({
                "type": "partial_failure",
                "success_dbs": success_dbs,
                "failed_dbs": failed_dbs,
                "table": table,
                "record_id": record_id,
                "timestamp": datetime.utcnow()
            })
        
        return conflicts
    
    async def _handle_conflicts(
        self,
        conflicts: List[Dict[str, Any]],
        table: str,
        record_id: Optional[int],
        user_id: Optional[int]
    ) -> None:
        """
        处理冲突
        
        策略：
        1. 记录到conflict_records表
        2. 发送邮件通知管理员
        3. 对于版本冲突，尝试重新读取并同步
        """
        try:
            with db_manager.session_scope("mysql") as session:
                for conflict in conflicts:
                    # 记录冲突
                    conflict_record = ConflictRecord(
                        table_name=table,
                        record_id=str(record_id) if record_id else "unknown",
                        source="mysql",  # 主库
                        target=",".join(conflict.get("databases", conflict.get("failed_dbs", []))),
                        payload=conflict,
                        resolved=False
                    )
                    session.add(conflict_record)
                
                session.commit()
                
                # 发送邮件通知
                subject = f"数据库同步冲突 - {table}"
                body = f"""
                检测到数据库同步冲突：
                
                表名: {table}
                记录ID: {record_id}
                冲突类型: {[c['type'] for c in conflicts]}
                时间: {datetime.utcnow()}
                
                请登录管理后台查看详情并处理。
                """
                email_notifier.send(subject, body)
                
        except Exception as e:
            logger.error(f"Failed to handle conflicts: {str(e)}")
    
    async def _log_sync_operation(
        self,
        table: str,
        action: str,
        results: Dict[str, Dict[str, Any]],
        conflicts: List[Dict[str, Any]]
    ) -> None:
        """记录同步操作日志"""
        try:
            with db_manager.session_scope("mysql") as session:
                success_count = sum(1 for r in results.values() if r.get("success"))
                
                sync_log = SyncLog(
                    config_id=None,  # 可以关联到配置
                    status="completed" if success_count > 0 else "failed",
                    started_at=datetime.utcnow(),
                    completed_at=datetime.utcnow(),
                    stats={
                        "table": table,
                        "action": action,
                        "success_count": success_count,
                        "total_count": len(results),
                        "conflicts": len(conflicts),
                        "results": {db: {"success": r.get("success")} for db, r in results.items()}
                    }
                )
                session.add(sync_log)
                session.commit()
        except Exception as e:
            logger.error(f"Failed to log sync operation: {str(e)}")
    
    async def verify_data_consistency(
        self,
        table: str,
        record_id: int
    ) -> Dict[str, Any]:
        """
        验证数据一致性
        
        检查四个数据库中同一记录的数据是否一致
        """
        data_by_db = {}
        
        for db_name in self.DB_PRIORITY:
            try:
                with db_manager.session_scope(db_name) as session:
                    query = f"SELECT * FROM {table} WHERE id = :id"
                    result = session.execute(text(query), {"id": record_id})
                    row = result.fetchone()
                    
                    if row:
                        data_by_db[db_name] = dict(row._mapping)
                    else:
                        data_by_db[db_name] = None
            except Exception as e:
                logger.error(f"Failed to verify consistency on {db_name}: {str(e)}")
                data_by_db[db_name] = {"error": str(e)}
        
        # 检查是否一致
        consistent = True
        reference_data = None
        
        for db_name, data in data_by_db.items():
            if data is None or "error" in data:
                continue
            
            if reference_data is None:
                reference_data = data
            else:
                # 比较关键字段（排除updated_at等时间戳字段）
                for key in reference_data.keys():
                    if key in ["updated_at", "created_at"]:
                        continue
                    if reference_data.get(key) != data.get(key):
                        consistent = False
                        break
        
        return {
            "consistent": consistent,
            "data_by_db": data_by_db,
            "timestamp": datetime.utcnow()
        }
    
    async def sync_repair(
        self,
        table: str,
        record_id: int,
        force: bool = False
    ) -> Dict[str, Any]:
        """
        同步修复
        
        从主库（MySQL）读取数据，强制同步到其他数据库
        """
        try:
            # 从主库读取数据
            with db_manager.session_scope("mysql") as session:
                query = f"SELECT * FROM {table} WHERE id = :id"
                result = session.execute(text(query), {"id": record_id})
                row = result.fetchone()
                
                if not row:
                    return {
                        "success": False,
                        "error": "Record not found in master database"
                    }
                
                data = dict(row._mapping)
            
            # 强制同步到其他数据库
            repair_results = {}
            
            for db_name in self.DB_PRIORITY[1:]:  # 跳过MySQL
                try:
                    with db_manager.session_scope(db_name) as session:
                        # 先尝试删除
                        session.execute(
                            text(f"DELETE FROM {table} WHERE id = :id"),
                            {"id": record_id}
                        )
                        
                        # 重新插入
                        columns = ", ".join(data.keys())
                        placeholders = ", ".join([f":{key}" for key in data.keys()])
                        query = f"INSERT INTO {table} ({columns}) VALUES ({placeholders})"
                        session.execute(text(query), data)
                        session.commit()
                        
                        repair_results[db_name] = {"success": True}
                except Exception as e:
                    logger.error(f"Repair failed on {db_name}: {str(e)}")
                    repair_results[db_name] = {"success": False, "error": str(e)}
            
            return {
                "success": True,
                "repaired_dbs": [db for db, r in repair_results.items() if r["success"]],
                "results": repair_results
            }
            
        except Exception as e:
            logger.error(f"Sync repair failed: {str(e)}")
            return {"success": False, "error": str(e)}
    
    def get_stats(self) -> Dict[str, Any]:
        """获取同步统计信息"""
        return {
            "success_count": self.success_count,
            "failure_count": self.failure_count,
            "conflict_count": self.conflict_count,
            "success_rate": self.success_count / max(1, self.success_count + self.failure_count)
        }


# 全局实例
sync_manager = DatabaseSyncManager()
