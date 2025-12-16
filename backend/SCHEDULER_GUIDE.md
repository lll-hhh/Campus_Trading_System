# 定时任务与周期同步说明

本项目的周期同步/数据模拟任务目前通过**命令行脚本持续运行**实现，适用于开发演示和轻量级生产场景。

## 现有脚本
1. **长流数据模拟**: `backend/scripts/long_stream_simulator.py`
   - 生成商品发布、交易更新、消息发送等随机业务数据
   - 持续运行示例: `python scripts/long_stream_simulator.py --interval 3 --intensity high --duration 0`

2. **冲突记录模拟**: `backend/scripts/conflict_simulator.py`
   - 模拟多库同步冲突并写入通知
   - 持续运行示例: `python scripts/conflict_simulator.py --batch 10 --interval 60 --loops 0`

3. **同步日志模拟**: `backend/scripts/sync_simulator.py`
   - 生成同步日志和性能指标
   - 周期运行示例: `python scripts/sync_simulator.py --batch 5 --interval 300 --loops 0`

## 部署方案

### 方案一：systemd 服务（推荐Linux生产环境）
创建 `/etc/systemd/system/campuswap-sync.service`:
```ini
[Unit]
Description=CampuSwap Data Sync Simulator
After=network.target mysql.service

[Service]
Type=simple
User=www-data
WorkingDirectory=/path/to/newkeshe2/backend
ExecStart=/path/to/venv/bin/python scripts/sync_simulator.py --interval 300 --loops 0
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```
启用: `sudo systemctl enable --now campuswap-sync`

### 方案二：crontab 定时任务
编辑 crontab (`crontab -e`):
```bash
# 每5分钟运行一次同步模拟
*/5 * * * * cd /path/to/backend && /path/to/venv/bin/python scripts/sync_simulator.py --batch 10 --interval 0 --loops 1

# 每小时生成冲突记录
0 * * * * cd /path/to/backend && /path/to/venv/bin/python scripts/conflict_simulator.py --batch 20 --interval 0 --loops 1
```

### 方案三：Celery Beat（可选扩展）
如需更复杂的任务调度（重试、监控、分布式），可集成 Celery：
1. 安装依赖: `pip install celery redis`
2. 创建 `backend/celeryapp.py`:
```python
from celery import Celery
from celery.schedules import crontab

app = Celery('campuswap', broker='redis://localhost:6379/0')

@app.task
def run_sync_simulator():
    import subprocess
    subprocess.run(['python', 'scripts/sync_simulator.py', '--batch', '10', '--interval', '0', '--loops', '1'])

app.conf.beat_schedule = {
    'sync-every-5-minutes': {
        'task': 'celeryapp.run_sync_simulator',
        'schedule': crontab(minute='*/5'),
    },
}
```
3. 启动: `celery -A celeryapp beat` 和 `celery -A celeryapp worker`

## 答辩演示建议
- 开发阶段：使用脚本 `--interval` 参数持续跑，后台实时刷新
- 生产说明：文档中注明"支持 systemd/cron/Celery 多种部署方式"并提供示例配置

## 注意事项
- 脚本需在 backend 目录下运行，并激活 venv
- 确保 MySQL 等数据库服务已启动
- 生产环境建议限制 `--loops` 或使用 systemd 自动重启
