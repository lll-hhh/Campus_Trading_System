"""
数据库初始化管理端点
提供手动触发数据库脚本执行和验证的 API
"""
from fastapi import APIRouter, Depends, HTTPException
from typing import Dict, Any

from apps.api_gateway.dependencies import require_roles
from apps.core.models.users import User
from apps.services.db_initializer import get_initializer

router = APIRouter(prefix="/admin/database", tags=["Database Admin"])


@router.post("/initialize", response_model=Dict[str, Dict])
def initialize_all_databases(
    _: User = Depends(require_roles("market_admin"))
) -> Dict[str, Dict]:
    """
    初始化所有数据库（执行触发器、存储过程、函数脚本）
    
    需要管理员权限
    """
    try:
        initializer = get_initializer()
        results = initializer.initialize_all_databases()
        return results
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"数据库初始化失败: {str(e)}")


@router.post("/initialize/{db_name}", response_model=Dict[str, Any])
def initialize_single_database(
    db_name: str,
    _: User = Depends(require_roles("market_admin"))
) -> Dict[str, Any]:
    """
    初始化单个数据库
    
    参数:
    - db_name: mysql, mariadb, postgres, sqlite
    """
    try:
        initializer = get_initializer()
        
        if db_name not in initializer.engines:
            raise HTTPException(status_code=404, detail=f"数据库 {db_name} 不存在")
        
        engine = initializer.engines[db_name]
        db_type = initializer._detect_db_type(db_name, engine)
        
        result = initializer.execute_sql_for_engine(engine, db_type)
        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"初始化失败: {str(e)}")


@router.get("/verify/{db_name}", response_model=Dict[str, Any])
def verify_database_objects(
    db_name: str,
    _: User = Depends(require_roles("market_admin"))
) -> Dict[str, Any]:
    """
    验证数据库对象（触发器、存储过程、函数、视图）是否创建成功
    
    参数:
    - db_name: mysql, mariadb, postgres, sqlite
    """
    try:
        initializer = get_initializer()
        
        if db_name not in initializer.engines:
            raise HTTPException(status_code=404, detail=f"数据库 {db_name} 不存在")
        
        engine = initializer.engines[db_name]
        db_type = initializer._detect_db_type(db_name, engine)
        
        verification = initializer.verify_database_objects(engine, db_type)
        return verification
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"验证失败: {str(e)}")


@router.get("/status", response_model=Dict[str, Dict])
def get_database_status(
    _: User = Depends(require_roles("market_admin"))
) -> Dict[str, Dict]:
    """
    获取所有数据库的对象创建状态
    """
    try:
        initializer = get_initializer()
        status = {}
        
        for db_name, engine in initializer.engines.items():
            db_type = initializer._detect_db_type(db_name, engine)
            status[db_name] = {
                "db_type": db_type,
                **initializer.verify_database_objects(engine, db_type)
            }
        
        return status
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取状态失败: {str(e)}")
