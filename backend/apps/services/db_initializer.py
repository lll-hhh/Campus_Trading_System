"""
Database initializer for multiple database engines.
"""
import logging
import os
from pathlib import Path
from typing import Dict, Any, Optional

from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine

logger = logging.getLogger(__name__)

# 全局初始化器实例（懒加载）
_initializer_instance: Optional["DatabaseInitializer"] = None


class DatabaseInitializer:
    """多数据库初始化器"""
    
    SQL_DIR = Path(__file__).parent.parent.parent / "sql"
    
    # 数据库类型到脚本的映射 - 添加 inserts 文件
    DB_SCRIPTS = {
        "mysql": ["mysql_complete_schema.sql", "mysql_complete_inserts.sql"],
        "mariadb": ["mariadb_complete_schema.sql"],  # MariaDB 可共用 MySQL inserts
        "postgres": ["postgres_complete_schema.sql"],
        "sqlite": ["sqlite_complete_schema.sql"],
    }
    
    def __init__(self, engines: Dict[str, Engine]):
        self.engines = engines
    
    def initialize_all_databases(self) -> Dict[str, Any]:
        """初始化所有数据库"""
        results = {}
        
        for db_name, engine in self.engines.items():
            try:
                result = self.initialize_database(db_name, engine)
                results[db_name] = result
                
                # 打印简要结果
                if result.get("success"):
                    logger.info(f"✅ {db_name} 初始化成功: {result.get('executed', 0)} 条语句")
                else:
                    logger.warning(f"⚠️ {db_name} 初始化有错误: {result.get('failed', 0)} 条失败")
                    for err in result.get("errors", [])[:3]:
                        logger.warning(f"   {db_name} 错误: {err}")
                        
            except Exception as e:
                logger.error(f"❌ {db_name} 初始化失败: {e}")
                results[db_name] = {"success": False, "error": str(e)}
        
        return results
    
    def initialize_database(self, db_name: str, engine: Engine) -> Dict[str, Any]:
        """初始化单个数据库"""
        db_type = self._detect_db_type(db_name, engine)
        script_names = self.DB_SCRIPTS.get(db_type, [])
        
        if not script_names:
            return {"success": False, "error": f"不支持的数据库类型: {db_type}"}
        
        # 确保是列表
        if isinstance(script_names, str):
            script_names = [script_names]
        
        total_result = {"success": True, "executed": 0, "failed": 0, "errors": []}
        
        for script_name in script_names:
            script_path = self.SQL_DIR / script_name
            
            if not script_path.exists():
                logger.warning(f"{db_name}: 脚本不存在 {script_path}")
                continue
            
            logger.info(f"{db_name}: 执行脚本 {script_name}")
            result = self.execute_sql_for_engine(db_name, engine, script_path, db_type)
            
            total_result["executed"] += result.get("executed", 0)
            total_result["failed"] += result.get("failed", 0)
            total_result["errors"].extend(result.get("errors", []))
            
            if not result.get("success"):
                total_result["success"] = False
        
        return total_result
    
    def _detect_db_type(self, db_name: str, engine: Engine) -> str:
        """检测数据库类型"""
        dsn = str(engine.url)
        
        if 'postgresql' in dsn or 'postgres' in dsn:
            return 'postgres'
        elif 'sqlite' in dsn:
            return 'sqlite'
        elif 'mysql' in dsn or 'pymysql' in dsn:
            if 'mariadb' in db_name.lower():
                return 'mariadb'
            return 'mysql'
        
        return 'unknown'
    
    def execute_sql_for_engine(
        self, 
        db_name: str, 
        engine: Engine, 
        script_path: Path,
        db_type: str
    ) -> Dict[str, Any]:
        """执行SQL脚本 - 每条语句独立事务"""
        try:
            sql_content = script_path.read_text(encoding='utf-8')
            statements = self._parse_sql_statements(sql_content, db_type)
            
            executed = 0
            failed = 0
            errors = []
            
            logger.info(f"{db_name}: 解析到 {len(statements)} 条SQL语句")
            
            for i, stmt in enumerate(statements):
                stmt = stmt.strip()
                if not stmt or stmt.startswith('--'):
                    continue
                
                # ✅ 关键修复：每条语句使用独立连接/事务
                try:
                    with engine.connect() as conn:
                        # 开始事务
                        trans = conn.begin()
                        try:
                            conn.execute(text(stmt))
                            trans.commit()
                            executed += 1
                        except Exception as e:
                            trans.rollback()
                            raise e
                            
                except Exception as e:
                    failed += 1
                    error_msg = str(e)[:150]
                    
                    # 忽略 "already exists" 类型的错误
                    if any(x in error_msg.lower() for x in ['already exists', 'duplicate', 'unique constraint']):
                        # 这不是真正的错误，对象已存在
                        executed += 1
                        failed -= 1
                    else:
                        errors.append(f"语句 {i+1}: {error_msg}")
                        if len(errors) <= 5:
                            logger.warning(f"{db_name} - 语句 {i+1} 执行失败: {error_msg[:80]}")
            
            # 记录 INSERT 语句执行情况
            insert_count = sum(1 for s in statements if 'INSERT' in s.upper())
            logger.info(f"{db_name}: 共 {insert_count} 条 INSERT 语句")
            
            return {
                "success": failed == 0 or failed < len(statements) * 0.1,  # 允许 10% 失败率
                "executed": executed,
                "failed": failed,
                "total": len(statements),
                "errors": errors[:10]  # 只返回前10个错误
            }
            
        except Exception as e:
            logger.error(f"{db_name} 初始化异常: {e}")
            return {"success": False, "error": str(e)}
    
    def _parse_sql_statements(self, sql_content: str, db_type: str) -> list:
        """解析SQL语句"""
        # 移除单行注释（但保留 SQL 内容）
        lines = []
        for line in sql_content.split('\n'):
            stripped = line.strip()
            if stripped.startswith('--'):
                continue
            lines.append(line)
        
        sql_content = '\n'.join(lines)
        
        # MySQL/MariaDB：处理 DELIMITER
        if db_type in ('mysql', 'mariadb') and 'DELIMITER' in sql_content:
            return self._parse_with_delimiter(sql_content)
        
        # PostgreSQL：处理 $$ 函数体
        if db_type == 'postgres':
            return self._parse_postgres_style(sql_content)
        
        # SQLite：简单按分号分割
        if db_type == 'sqlite':
            return self._parse_simple(sql_content)
        
        # 默认：简单分割
        return self._parse_simple(sql_content)
    
    def _parse_simple(self, sql_content: str) -> list:
        """简单按分号分割（适用于SQLite和简单SQL）"""
        statements = []
        current = []
        
        for line in sql_content.split('\n'):
            stripped = line.strip()
            if not stripped:
                continue
            
            current.append(line)
            
            if stripped.endswith(';'):
                stmt = '\n'.join(current).strip()
                # 移除末尾分号后检查是否有内容
                if stmt and stmt != ';':
                    statements.append(stmt)
                current = []
        
        if current:
            stmt = '\n'.join(current).strip()
            if stmt:
                statements.append(stmt)
        
        return statements
    
    def _parse_postgres_style(self, sql_content: str) -> list:
        """解析 PostgreSQL 风格的 SQL（处理 $$ 函数体）"""
        statements = []
        current = []
        in_dollar_quote = False
        
        for line in sql_content.split('\n'):
            stripped = line.strip()
            if not stripped:
                current.append(line)
                continue
                
            current.append(line)
            
            # 检测 $$ 引用（计算这一行有多少个 $$）
            dollar_count = line.count('$$')
            if dollar_count % 2 == 1:
                in_dollar_quote = not in_dollar_quote
            
            # 如果不在 $$ 块内且行以分号结尾
            if not in_dollar_quote and stripped.endswith(';'):
                stmt = '\n'.join(current).strip()
                if stmt and stmt != ';':
                    statements.append(stmt)
                current = []
        
        if current:
            stmt = '\n'.join(current).strip()
            if stmt:
                statements.append(stmt)
        
        return statements
    
    def _parse_with_delimiter(self, sql_content: str) -> list:
        """处理包含 DELIMITER 的 SQL（MySQL/MariaDB）"""
        statements = []
        current_delimiter = ';'
        current_stmt = []
        
        for line in sql_content.split('\n'):
            stripped = line.strip()
            
            # 检查 DELIMITER 命令
            if stripped.upper().startswith('DELIMITER'):
                parts = stripped.split()
                if len(parts) >= 2:
                    if current_stmt:
                        stmt = '\n'.join(current_stmt).strip()
                        if stmt:
                            statements.append(stmt)
                        current_stmt = []
                    current_delimiter = parts[1]
                continue
            
            current_stmt.append(line)
            
            # 检查是否到达语句结尾
            if stripped.endswith(current_delimiter):
                stmt = '\n'.join(current_stmt)
                if current_delimiter != ';':
                    stmt = stmt.rsplit(current_delimiter, 1)[0]
                stmt = stmt.strip()
                if stmt:
                    statements.append(stmt)
                current_stmt = []
        
        if current_stmt:
            stmt = '\n'.join(current_stmt).strip()
            if stmt:
                statements.append(stmt)
        
        return statements
    
    def verify_database_objects(self, engine: Engine, db_type: str) -> Dict[str, Any]:
        """验证数据库对象"""
        result = {"tables": [], "success": True}
        
        try:
            with engine.connect() as conn:
                if db_type in ('mysql', 'mariadb'):
                    tables = conn.execute(text("SHOW TABLES")).fetchall()
                    result["tables"] = [t[0] for t in tables]
                    
                    # 检查是否有数据
                    for table in ['users', 'categories', 'items']:
                        if table in result["tables"]:
                            count = conn.execute(text(f"SELECT COUNT(*) FROM {table}")).scalar()
                            result[f"{table}_count"] = count
                    
                elif db_type == 'postgres':
                    tables = conn.execute(text(
                        "SELECT tablename FROM pg_tables WHERE schemaname = 'public'"
                    )).fetchall()
                    result["tables"] = [t[0] for t in tables]
                    
                elif db_type == 'sqlite':
                    tables = conn.execute(text(
                        "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'"
                    )).fetchall()
                    result["tables"] = [t[0] for t in tables]
                    
        except Exception as e:
            result["success"] = False
            result["error"] = str(e)
        
        return result


def get_initializer() -> DatabaseInitializer:
    """获取全局初始化器实例"""
    global _initializer_instance
    
    if _initializer_instance is None:
        engines = _create_engines()
        _initializer_instance = DatabaseInitializer(engines)
    
    return _initializer_instance


def _create_engines() -> Dict[str, Engine]:
    """创建数据库引擎"""
    engines = {}
    
    dsn_map = {
        'mysql': 'MYSQL_DSN',
    }
    
    for db_name, env_var in dsn_map.items():
        dsn = os.getenv(env_var)
        if dsn:
            try:
                engine = create_engine(
                    dsn,
                    pool_size=5,
                    max_overflow=10,
                    pool_timeout=30,
                    pool_recycle=3600,
                )
                engines[db_name] = engine
                logger.info(f"Created engine for {db_name}")
            except Exception as e:
                logger.error(f"Failed to create engine for {db_name}: {e}")
    
    return engines


def initialize_databases() -> Dict[str, Any]:
    """初始化所有数据库（入口函数）"""
    initializer = get_initializer()
    return initializer.initialize_all_databases()