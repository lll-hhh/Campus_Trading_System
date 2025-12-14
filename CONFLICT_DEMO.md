# 🔄 四库冲突演示 & 手动同步指南

本指南记录“用脚本快速制造一条跨库冲突 → 在现有后台界面/接口里手动选择保留哪份 → 触发一次同步修复”的完整流程，便于演示或自测，无需编写额外前端代码。

---

## 1. 环境前提

- 已按 `RUNNING.md` 启动 **后端**（FastAPI + Redis + 四个数据库）和可选的 **前端**。
- `backend/.venv` 虚拟环境可用，并能连接 MySQL/MariaDB/PostgreSQL（SQLite 仅做对照即可）。
- 拥有管理员账号（默认 `admin/admin123`）或其 Bearer Token，用于访问 `/api/v1/sync/*` 接口。

---

## 2. 一键造冲突脚本

1. 进入后端目录并激活虚拟环境：

```bash
cd backend
python -m venv .venv && source .venv/bin/activate  # 如已创建可跳过
```

2. 运行下面的脚本。它会：
   - 在 **MySQL** 插入一行 `items` 记录（`sync_version = 1`）。
   - 在 **MariaDB / PostgreSQL** 中写入同一条记录，但字段内容和 `sync_version = 5`，制造冲突。
   - 日志会输出生成的 `item_id`，后续修复时会用到。

```bash
python - <<'PY'
from apps.core.database import db_manager
from sqlalchemy import text
import random, string, datetime

def random_title():
    return "Demo冲突商品-" + ''.join(random.choices(string.ascii_uppercase + string.digits, k=5))

with db_manager.session_scope("mysql") as session:
    title = random_title()
    session.execute(text("""
        INSERT INTO items (title, description, price, status, seller_id, sync_version, created_at, updated_at)
        VALUES (:title, 'mysql baseline', 99.99, 'available', 1, 1, NOW(), NOW())
    """), {"title": title})
    item_id = session.execute(text("SELECT LAST_INSERT_ID()")).scalar_one()
    session.commit()
    print("基准记录 ID:", item_id, title)

payload = {
    "id": item_id,
    "title": title + "-Maria",
    "description": "mariadb changed",
    "price": 199.99,
    "status": "reserved",
    "seller_id": 1,
    "sync_version": 5,
    "created_at": datetime.datetime.utcnow(),
    "updated_at": datetime.datetime.utcnow(),
}

for db in ("mariadb", "postgres"):
    with db_manager.session_scope(db) as session:
        session.execute(text("DELETE FROM items WHERE id = :id"), {"id": item_id})
        columns = ", ".join(payload.keys())
        values = ", ".join(f":{k}" for k in payload.keys())
        session.execute(text(f"INSERT INTO items ({columns}) VALUES ({values})"), payload)
        session.commit()
        print(f"{db} 已改造冲突")

print("冲突制造完成，/api/v1/sync/conflicts 将看到新记录。")
PY
```

运行完成后即可在 `conflict_records` 表、`/api/v1/sync/conflicts`、或后台“同步监控”页面看到新冲突。

---

## 3. 手动选择保留哪份数据

### 3.1 直接使用后台 UI（推荐）

1. 前端目录执行 `npm run dev -- --host 0.0.0.0 --port 5173`，浏览器访问 `http://localhost:5173` 并使用管理员账号登录。
2. 进入任意包含同步模块的页面：
   - `🔄 四库同步`（`/admin/console`）或
   - `同步监控`（`/admin/sync-monitor`）。
3. 在“冲突记录”表格中找到刚刚脚本生成的那条记录，点击“详情”查看 local/remote payload。
4. 点击“标记为已解决”，会出现策略选项：
   - **source**：保留来源数据库（默认 MySQL）。
   - **target**：保留目标数据库（例如 MariaDB/PostgreSQL）。
   - **manual**：仅标记解决，数据自行处理。
5. 选择策略后提交即可，系统会把 `conflict_records.resolution_strategy` 等字段写入数据库。

### 3.2 用 API / curl 的方式

无需打开前端也能完成同样的操作：

```bash
# 1) 查看冲突列表
authorization="Authorization: Bearer <admin_token>"
curl -H "$authorization" http://localhost:8010/api/v1/sync/conflicts

# 2) 标记保留目标库
d conflito_id=<上一步返回的ID>
curl -X PUT -H "$authorization" -H "Content-Type: application/json" \
     -d '{"strategy": "target"}' \
     http://localhost:8010/api/v1/sync/conflicts/$conflict_id/resolve
```

> 将 `strategy` 改成 `source`/`manual` 即可对应不同的保留策略。

---

## 4. 触发一次同步/修复

策略确定后，可以让系统再同步一遍，把“保留”动作真正落到其它数据库：

### 4.1 后台页面

在“同步监控”页弹出的“同步修复”表单里输入：
- **表名**：`items`
- **记录 ID**：脚本输出的 `item_id`
- **强制修复**：按需勾选（`force = true` 会先删除再重插）

点击“开始修复”即可触发 `/api/v1/sync/repair`。

### 4.2 API 方式

```bash
curl -X POST -H "$authorization" -H "Content-Type: application/json" \
     -d '{"table":"items","record_id":ITEM_ID,"force":true}' \
     http://localhost:8010/api/v1/sync/repair
```

若想直接推送自定义 payload，也可以调用 `/api/v1/sync/write`，传入 `table/action/data` 参数完成 insert/update/delete 并观察四库写入结果。

---

## 5. 验证同步结果

- `curl http://localhost:8010/api/v1/sync/databases/status` 可以查看各库的状态、延迟和最近一次同步时间。
- `curl http://localhost:8010/api/v1/sync/logs` 可确认同步日志里出现了刚刚触发的修复任务。
- 进入后台“性能监控”页，`🔄 四数据库同步状态` 卡片会展示同步版本号与记录数的变化；“同步日志”表也会显示最新记录。

---

完成以上步骤，即可完整演示“脚本造冲突 → 人工决定保留版本 → 手动触发修复/同步”的流程，满足手动控制场景，且整个过程都借助现有 API 与管理 UI，无需额外开发。