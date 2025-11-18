# 🎓 校园交易系统 - Campus Trading Platform

基于FastAPI + Vue3的校园二手交易系统,采用四数据库同步架构

## ✨ 核心功能

### 用户端 - 淘宝风格交易市场
- 📱 **商品浏览** - 8大分类、网格/列表双视图、分页浏览
- 🔍 **高级筛选** - 成色筛选、价格区间、5种排序方式
- 🖼️ **商品详情** - 多图轮播、卖家评分、标签系统
- 💬 **评论互动** - 发表评论、楼中楼回复、买卖沟通
- 🤝 **交易流程** - 获取联系方式、线下见面、安全交易
- 📦 **我的商品** - 在售中/已售出/已下架管理
- 💰 **订单记录** - 我买到的/我卖出的

### 管理员端 - 四库同步监控
- 📊 **数据同步监控** - MySQL/PostgreSQL/MariaDB/SQLite实时同步
- 🔄 **冲突处理** - 版本冲突检测、数据一致性校验
- 📈 **数据分析** - 交易统计、用户活跃度

## 🏗️ 技术架构

**后端:** FastAPI + SQLAlchemy + Redis  
**前端:** Vue 3.4 + TypeScript + Naive UI  
**数据库:** MySQL/PostgreSQL/MariaDB/SQLite 四库同步

## 📊 数据库设计

**12张核心表:**
users, items, categories, item_images, comments, transactions, messages, favorites, reports, audit_logs, conflict_records, system_configs

详见: [SQL脚本文档](backend/sql/SQL_GUIDE.md)

## 🚀 快速开始

```bash
# Docker启动
docker-compose up -d

# 访问系统
# 前端: http://localhost:5174
# API: http://localhost:8001/docs
```

## 📚 文档

- [交易流程说明](TRANSACTION_FLOW.md)
- [数据库同步](backend/docs/4-DATABASE-SYNC.md)
- [SQL脚本](backend/sql/SQL_GUIDE.md)

---
**版本:** 2.0 | **更新:** 2025-11-18
