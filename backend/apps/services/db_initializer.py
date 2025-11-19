"""
数据库初始化服务 - 执行 SQL 脚本创建触发器、存储过程、函数等
"""
import logging
from pathlib import Path
from typing import Dict, List

from sqlalchemy import text
from sqlalchemy.engine import Engine

from apps.core.config import get_settings
from apps.core.database import get_all_engines

logger = logging.getLogger(__name__)

SQL_DIR = Path(__file__).parent.parent.parent / "sql"


class DatabaseInitializer:
    """数据库初始化器 - 执行各数据库专用脚本"""

    def __init__(self):
        self.settings = get_settings()
        self.engines = get_all_engines()
        self.sql_files: Dict[str, Path] = {
            "mysql": SQL_DIR / "mysql_complete_schema.sql",
            "mariadb": SQL_DIR / "mariadb_complete_schema.sql",
            "postgres": SQL_DIR / "postgres_complete_schema.sql",
            "sqlite": SQL_DIR / "sqlite_complete_schema.sql",
        }

    def _read_sql_file(self, file_path: Path) -> str:
        """读取 SQL 文件内容"""
        if not file_path.exists():
            raise FileNotFoundError(f"SQL 文件不存在: {file_path}")
        return file_path.read_text(encoding="utf-8")

    def _split_sql_statements(self, sql_content: str, db_type: str) -> List[str]:
        """
        分割 SQL 语句
        - MySQL/MariaDB: 处理 DELIMITER
        - PostgreSQL/SQLite: 按分号分割
        """
        statements = []

        if db_type in ("mysql", "mariadb"):
            # 处理 DELIMITER $$ ... DELIMITER ;
            current_delimiter = ";"
            buffer = []
            lines = sql_content.split("\n")

            for line in lines:
                stripped = line.strip()

                # 跳过注释
                if stripped.startswith("--") or not stripped:
                    continue

                # 检测 DELIMITER 变更
                if stripped.upper().startswith("DELIMITER"):
                    if buffer:
                        statements.append("\n".join(buffer))
                        buffer = []
                    new_delimiter = stripped.split()[-1]
                    current_delimiter = new_delimiter
                    continue

                buffer.append(line)

                # 检查语句结束
                if stripped.endswith(current_delimiter):
                    stmt = "\n".join(buffer).rstrip(current_delimiter).strip()
                    if stmt and not stmt.startswith("--"):
                        statements.append(stmt)
                    buffer = []

            if buffer:
                stmt = "\n".join(buffer).strip()
                if stmt:
                    statements.append(stmt)

        else:
            # PostgreSQL / SQLite: 简单按分号分割
            raw_statements = sql_content.split(";")
            for stmt in raw_statements:
                cleaned = stmt.strip()
                # 过滤空语句和注释
                if cleaned and not cleaned.startswith("--"):
                    statements.append(cleaned)

        return statements

    def execute_sql_for_engine(self, engine: Engine, db_type: str) -> Dict[str, any]:
        """
        为指定引擎执行对应的 SQL 脚本
        """
        result = {
            "db_type": db_type,
            "executed": 0,
            "failed": 0,
            "errors": [],
        }

        sql_file = self.sql_files.get(db_type)
        if not sql_file or not sql_file.exists():
            logger.warning(f"未找到 {db_type} 的 SQL 脚本: {sql_file}")
            return result

        logger.info(f"开始为 {db_type} 执行初始化脚本: {sql_file}")

        try:
            sql_content = self._read_sql_file(sql_file)
            
            # SQLite使用特殊处理
            if db_type == "sqlite":
                with engine.raw_connection() as conn:
                    cursor = conn.cursor()
                    try:
                        cursor.executescript(sql_content)
                        result["executed"] = 1
                        logger.info(f"{db_type} 初始化完成: SQL脚本执行成功")
                    except Exception as e:
                        result["failed"] = 1
                        result["errors"].append(str(e)[:200])
                        logger.error(f"{db_type} 初始化失败: {e}")
                return result

            # PostgreSQL使用psycopg的execute
            if db_type == "postgres":
                try:
                    with engine.raw_connection() as raw_conn:
                        cursor = raw_conn.cursor()
                        try:
                            cursor.execute(sql_content)
                            raw_conn.commit()
                            result["executed"] = 1
                            logger.info(f"{db_type} 初始化完成: SQL脚本执行成功")
                        except Exception as e:
                            result["failed"] = 1
                            result["errors"].append(str(e)[:500])
                            logger.error(f"{db_type} 初始化失败: {e}")
                except Exception as e:
                    result["failed"] = 1
                    result["errors"].append(str(e)[:200])
                    logger.error(f"{db_type} 连接失败: {e}")
                return result

            # MySQL/MariaDB使用逐语句执行
            statements = self._split_sql_statements(sql_content, db_type)
            logger.info(f"{db_type} 共解析出 {len(statements)} 条 SQL 语句")

            with engine.begin() as conn:
                for idx, stmt in enumerate(statements, 1):
                    try:
                        # 跳过空语句
                        if not stmt.strip():
                            continue

                        # 执行 SQL
                        conn.execute(text(stmt))
                        result["executed"] += 1

                    except Exception as e:
                        result["failed"] += 1
                        error_msg = f"语句 {idx} 执行失败: {str(e)[:200]}"
                        result["errors"].append(error_msg)
                        logger.error(f"{db_type} - {error_msg}")
                        # 继续执行其他语句（触发器/存储过程可能部分已存在）

            logger.info(
                f"{db_type} 初始化完成: 成功 {result['executed']}, 失败 {result['failed']}"
            )

        except Exception as e:
            logger.error(f"{db_type} 初始化异常: {e}", exc_info=True)
            result["errors"].append(str(e))

        return result

    def initialize_all_databases(self) -> Dict[str, Dict]:
        """
        初始化所有数据库（创建触发器、存储过程、函数等）
        """
        logger.info("开始初始化所有数据库...")
        results = {}

        for db_name, engine in self.engines.items():
            # 确定数据库类型
            db_type = self._detect_db_type(db_name, engine)
            results[db_name] = self.execute_sql_for_engine(engine, db_type)

        logger.info("所有数据库初始化完成")
        return results

    def _detect_db_type(self, db_name: str, engine: Engine) -> str:
        """根据引擎名称或方言检测数据库类型"""
        dialect_name = engine.dialect.name.lower()

        if "mysql" in db_name.lower() or dialect_name == "mysql":
            # 进一步区分 MySQL 和 MariaDB
            with engine.connect() as conn:
                result = conn.execute(text("SELECT VERSION()")).scalar()
                if "mariadb" in result.lower():
                    return "mariadb"
            return "mysql"
        elif "mariadb" in db_name.lower():
            return "mariadb"
        elif "postgres" in db_name.lower() or dialect_name == "postgresql":
            return "postgres"
        elif "sqlite" in db_name.lower() or dialect_name == "sqlite":
            return "sqlite"

        logger.warning(f"未识别的数据库类型: {db_name} ({dialect_name}), 默认使用 mysql")
        return "mysql"

    def verify_database_objects(self, engine: Engine, db_type: str) -> Dict[str, any]:
        """
        验证数据库对象是否创建成功（触发器、存储过程等）
        """
        verification = {
            "triggers": [],
            "procedures": [],
            "functions": [],
            "views": [],
        }

        try:
            with engine.connect() as conn:
                if db_type == "mysql" or db_type == "mariadb":
                    # 查询触发器
                    triggers = conn.execute(
                        text("SELECT TRIGGER_NAME FROM information_schema.TRIGGERS WHERE TRIGGER_SCHEMA = DATABASE()")
                    ).fetchall()
                    verification["triggers"] = [t[0] for t in triggers]

                    # 查询存储过程
                    procedures = conn.execute(
                        text("SELECT ROUTINE_NAME FROM information_schema.ROUTINES WHERE ROUTINE_SCHEMA = DATABASE() AND ROUTINE_TYPE = 'PROCEDURE'")
                    ).fetchall()
                    verification["procedures"] = [p[0] for p in procedures]

                    # 查询函数
                    functions = conn.execute(
                        text("SELECT ROUTINE_NAME FROM information_schema.ROUTINES WHERE ROUTINE_SCHEMA = DATABASE() AND ROUTINE_TYPE = 'FUNCTION'")
                    ).fetchall()
                    verification["functions"] = [f[0] for f in functions]

                elif db_type == "postgres":
                    # 查询触发器
                    triggers = conn.execute(
                        text("SELECT trigger_name FROM information_schema.triggers WHERE trigger_schema = 'public'")
                    ).fetchall()
                    verification["triggers"] = [t[0] for t in triggers]

                    # 查询函数（PostgreSQL 不区分存储过程）
                    functions = conn.execute(
                        text("SELECT routine_name FROM information_schema.routines WHERE routine_schema = 'public'")
                    ).fetchall()
                    verification["functions"] = [f[0] for f in functions]

                elif db_type == "sqlite":
                    # SQLite 查询触发器
                    triggers = conn.execute(
                        text("SELECT name FROM sqlite_master WHERE type = 'trigger'")
                    ).fetchall()
                    verification["triggers"] = [t[0] for t in triggers]

                # 查询视图
                views = conn.execute(
                    text("SELECT table_name FROM information_schema.views WHERE table_schema = DATABASE()")
                    if db_type in ("mysql", "mariadb")
                    else text("SELECT table_name FROM information_schema.views WHERE table_schema = 'public'")
                    if db_type == "postgres"
                    else text("SELECT name FROM sqlite_master WHERE type = 'view'")
                ).fetchall()
                verification["views"] = [v[0] for v in views]

        except Exception as e:
            logger.error(f"验证数据库对象失败: {e}")

        return verification


# 全局初始化器实例
_initializer = None


def get_initializer() -> DatabaseInitializer:
    """获取数据库初始化器单例"""
    global _initializer
    if _initializer is None:
        _initializer = DatabaseInitializer()
    return _initializer


def initialize_databases() -> Dict[str, Dict]:
    """便捷函数: 初始化所有数据库"""
    initializer = get_initializer()
    return initializer.initialize_all_databases()
