#!/bin/bash
# 数据流水模拟器启动脚本
# 用法: ./start_simulator.sh [start|stop|status|logs]

CONTAINER_NAME="campuswap-gateway"
SCRIPT_PATH="/app/scripts/data_simulator.py"

case "$1" in
  start)
    echo "🚀 启动数据模拟器..."
    # 先停止可能存在的旧进程
    sudo docker compose exec $CONTAINER_NAME pkill -f data_simulator.py 2>/dev/null
    sleep 1
    # 后台启动
    sudo docker compose exec -d $CONTAINER_NAME python $SCRIPT_PATH --interval ${2:-4} --intensity ${3:-high}
    echo "✅ 模拟器已在后台启动 (间隔: ${2:-4}秒, 强度: ${3:-high})"
    echo "📊 打开管理后台查看实时数据变化: http://localhost:5173/admin"
    echo "📈 同步监控页面: http://localhost:5173/sync-monitor"
    ;;
  stop)
    echo "🛑 停止数据模拟器..."
    sudo docker compose exec $CONTAINER_NAME pkill -f data_simulator.py 2>/dev/null
    echo "✅ 模拟器已停止"
    ;;
  status)
    echo "📋 模拟器状态:"
    sudo docker compose exec $CONTAINER_NAME ps aux | grep -E "data_simulator|PID" | grep -v grep
    ;;
  logs)
    echo "📜 查看模拟器输出 (最近 50 行)..."
    sudo docker compose logs $CONTAINER_NAME --tail 100 | grep -E "(📦|💰|👁️|🏷️|🔄|🛒|💬|🔍|⏱️|周期)" | tail -50
    ;;
  foreground)
    echo "🖥️ 前台运行模拟器 (Ctrl+C 停止)..."
    sudo docker compose exec $CONTAINER_NAME python $SCRIPT_PATH --interval ${2:-4} --intensity ${3:-high}
    ;;
  *)
    echo "用法: $0 {start|stop|status|logs|foreground} [间隔秒数] [强度:low/medium/high]"
    echo ""
    echo "示例:"
    echo "  $0 start          # 默认启动 (4秒间隔, high强度)"
    echo "  $0 start 2 high   # 2秒间隔, high强度"
    echo "  $0 stop           # 停止模拟器"
    echo "  $0 status         # 查看运行状态"
    echo "  $0 logs           # 查看输出日志"
    echo "  $0 foreground     # 前台运行 (可看实时输出)"
    exit 1
    ;;
esac
