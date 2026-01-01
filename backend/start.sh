#!/bin/bash
# filepath: backend/start.sh
# Gateway 启动脚本 - 包含 SQLite 初始化

set -e

echo "🚀 校园交易系统 Gateway 启动中..."

# 创建数据目录
mkdir -p /app/data
chmod 755 /app/data

# ========================================
# 等待依赖服务就绪
# ========================================
echo "⏳ 等待数据库服务就绪..."

wait_for_service() {
    local host=$1
    local port=$2
    local name=$3
    local max_retries=30
    local count=0
    
    while [ $count -lt $max_retries ]; do
        if nc -z "$host" "$port" 2>/dev/null; then
            echo "✅ $name 就绪"
            return 0
        fi
        count=$((count + 1))
        sleep 2
    done
    echo "⚠️ $name 连接超时，继续启动..."
    return 1
}

wait_for_service mysql 3306 "MySQL"
wait_for_service redis 6379 "Redis"

# 额外等待确保数据库初始化完成
sleep 5

# ========================================
# 验证数据库状态
# ========================================
echo ""
echo "📋 数据库状态检查:"

# MySQL
python3 -c "
from sqlalchemy import create_engine, text
import os
try:
    dsn = os.getenv('MYSQL_DSN', 'mysql+pymysql://root:campuswap_root@mysql:3306/campuswap')
    engine = create_engine(dsn)
    with engine.connect() as conn:
        count = conn.execute(text('SELECT COUNT(*) FROM users')).scalar()
        print(f'  MySQL: {count} 用户')
except Exception as e:
    print(f'  MySQL: 连接失败 - {e}')
" 2>/dev/null || echo "  MySQL: 检查失败"

# ========================================
# 启动应用
# ========================================
echo "🚀 启动 API Gateway..."
exec uvicorn apps.api_gateway.main:app --host 0.0.0.0 --port 8000 --reload

echo ""
echo "🚀 启动 API Gateway..."
exec uvicorn apps.api_gateway.main:app --host 0.0.0.0 --port 8000 --reload