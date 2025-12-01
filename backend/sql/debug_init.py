#!/usr/bin/env python3
"""
数据库初始化调试脚本
用于排查为什么 INSERT 语句没有执行成功
"""
import os
import sys
from pathlib import Path

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import create_engine, text

def debug_database():
    """调试数据库初始化"""
    
    print("=" * 60)
    print("🔍 数据库初始化调试")
    print("=" * 60)
    
    # 1. 检查环境变量
    print("\n📋 1. 检查环境变量:")
    dsn_vars = ['MYSQL_DSN', 'MARIADB_DSN', 'POSTGRES_DSN', 'SQLITE_DSN']
    for var in dsn_vars:
        value = os.getenv(var)
        if value:
            # 隐藏密码
            display = value.replace(value.split('@')[0].split(':')[-1], '***') if '@' in value else value
            print(f"  ✅ {var} = {display}")
        else:
            print(f"  ❌ {var} = 未设置")
    
    # 2. 检查 SQL 文件
    print("\n📋 2. 检查 SQL 文件:")
    sql_dir = Path(__file__).parent
    sql_files = {
        'mysql': 'mysql_complete_schema.sql',
        'mariadb': 'mariadb_complete_schema.sql', 
        'postgres': 'postgres_complete_schema.sql',
        'sqlite': 'sqlite_complete_schema.sql',
    }
    
    for db, filename in sql_files.items():
        filepath = sql_dir / filename
        if filepath.exists():
            size = filepath.stat().st_size
            # 检查是否包含 INSERT
            content = filepath.read_text(encoding='utf-8')
            insert_count = content.upper().count('INSERT ')
            print(f"  ✅ {filename}: {size} 字节, {insert_count} 条 INSERT")
        else:
            print(f"  ❌ {filename}: 不存在")
    
    # 3. 测试数据库连接和数据
    print("\n📋 3. 测试数据库连接和数据:")
    
    mysql_dsn = os.getenv('MYSQL_DSN')
    if mysql_dsn:
        try:
            engine = create_engine(mysql_dsn)
            with engine.connect() as conn:
                # 检查表
                tables = conn.execute(text("SHOW TABLES")).fetchall()
                print(f"  MySQL 表数量: {len(tables)}")
                
                if tables:
                    print(f"  表列表: {[t[0] for t in tables[:10]]}")
                
                # 检查 categories 数据
                try:
                    count = conn.execute(text("SELECT COUNT(*) FROM categories")).scalar()
                    print(f"  ✅ categories 表: {count} 条记录")
                    
                    if count > 0:
                        rows = conn.execute(text("SELECT id, name, slug FROM categories LIMIT 5")).fetchall()
                        for row in rows:
                            print(f"     - {row}")
                    else:
                        print("  ⚠️ categories 表为空!")
                        
                except Exception as e:
                    print(f"  ❌ categories 表查询失败: {e}")
                
                # 检查 system_configs 数据
                try:
                    count = conn.execute(text("SELECT COUNT(*) FROM system_configs")).scalar()
                    print(f"  ✅ system_configs 表: {count} 条记录")
                except Exception as e:
                    print(f"  ❌ system_configs 表查询失败: {e}")
                    
        except Exception as e:
            print(f"  ❌ MySQL 连接失败: {e}")
    
    # 4. 手动执行 INSERT 测试
    print("\n📋 4. 手动执行 INSERT 测试:")
    if mysql_dsn:
        try:
            engine = create_engine(mysql_dsn)
            with engine.connect() as conn:
                # 尝试插入测试数据
                try:
                    conn.execute(text("""
                        INSERT INTO categories (name, slug, description, sort_order) 
                        VALUES ('测试分类', 'test-category', '这是测试', 999)
                        ON DUPLICATE KEY UPDATE name=VALUES(name)
                    """))
                    conn.commit()
                    print("  ✅ INSERT 测试成功")
                    
                    # 验证
                    count = conn.execute(text("SELECT COUNT(*) FROM categories WHERE slug='test-category'")).scalar()
                    print(f"  ✅ 验证: 找到 {count} 条测试记录")
                    
                    # 清理
                    conn.execute(text("DELETE FROM categories WHERE slug='test-category'"))
                    conn.commit()
                    print("  ✅ 清理测试数据成功")
                    
                except Exception as e:
                    print(f"  ❌ INSERT 测试失败: {e}")
                    
        except Exception as e:
            print(f"  ❌ 连接失败: {e}")
    
    # 5. 解析并执行实际 SQL
    print("\n📋 5. 模拟执行 SQL 脚本:")
    sql_file = sql_dir / 'mysql_complete_schema.sql'
    if sql_file.exists():
        content = sql_file.read_text(encoding='utf-8')
        
        # 查找 INSERT 语句
        lines = content.split('\n')
        insert_lines = []
        in_insert = False
        current_insert = []
        
        for i, line in enumerate(lines):
            stripped = line.strip()
            
            if stripped.upper().startswith('INSERT '):
                in_insert = True
                current_insert = [line]
            elif in_insert:
                current_insert.append(line)
                if stripped.endswith(';'):
                    insert_lines.append('\n'.join(current_insert))
                    in_insert = False
                    current_insert = []
        
        print(f"  找到 {len(insert_lines)} 条 INSERT 语句")
        
        # 显示前几条
        for i, stmt in enumerate(insert_lines[:3]):
            preview = stmt[:100].replace('\n', ' ')
            print(f"  [{i+1}] {preview}...")
        
        # 尝试执行
        if mysql_dsn and insert_lines:
            print("\n  尝试执行 INSERT 语句:")
            engine = create_engine(mysql_dsn)
            
            for i, stmt in enumerate(insert_lines):
                try:
                    with engine.connect() as conn:
                        conn.execute(text(stmt))
                        conn.commit()
                        print(f"  ✅ INSERT #{i+1} 执行成功")
                except Exception as e:
                    error_msg = str(e)[:80]
                    if 'Duplicate' in error_msg or 'already exists' in error_msg.lower():
                        print(f"  ⏭️ INSERT #{i+1} 跳过(已存在)")
                    else:
                        print(f"  ❌ INSERT #{i+1} 失败: {error_msg}")

    print("\n" + "=" * 60)
    print("调试完成")
    print("=" * 60)


if __name__ == '__main__':
    debug_database()