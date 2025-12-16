# AI聊天助手配置指南

## 功能介绍

AI聊天助手是一个智能对话功能,集成在CampusSwap平台中,提供以下能力:

1. **商品分析**: 分析商品价格合理性、评估商品状况、提供交易建议
2. **冲突解决**: 协助解决交易纠纷、提供公正的仲裁建议
3. **平台咨询**: 回答用户关于平台使用的问题

## 配置步骤

### 1. 获取智谱AI API密钥

1. 访问 [智谱AI开放平台](https://open.bigmodel.cn/)
2. 注册/登录账号
3. 进入控制台 -> API Keys
4. 创建新的API Key并复制保存

### 2. 配置环境变量

在项目根目录创建或编辑 `.env` 文件:

```bash
# GLM AI 配置
GLM_API_KEY=your_api_key_here
GLM_MODEL=glm-4-flash  # 可选: glm-4, glm-4-flash, glm-3-turbo
```

### 3. 重启服务

如果使用Docker:
```bash
docker-compose down
docker-compose up -d gateway
```

如果直接运行:
```bash
cd backend
source venv/bin/activate
uvicorn apps.api_gateway.main:app --reload
```

## 使用方法

### 前端使用

AI聊天助手会以悬浮按钮的形式出现在页面右下角(登录用户可见):

1. **通用对话**: 点击悬浮按钮打开聊天框,直接输入问题
2. **商品分析**: 在商品详情页,可以传递商品上下文进行针对性分析
3. **冲突解决**: 在交易纠纷处理中,可以请求AI给出解决建议

### API使用

#### 1. 基础对话

```bash
POST /api/v1/ai/chat
Content-Type: application/json
Authorization: Bearer {token}

{
  "messages": [
    {"role": "user", "content": "我想卖一个二手笔记本,应该如何定价?"}
  ],
  "context_type": "general"
}
```

#### 2. 商品分析

```bash
POST /api/v1/ai/chat
Content-Type: application/json
Authorization: Bearer {token}

{
  "messages": [
    {"role": "user", "content": "请分析这个商品的价格"}
  ],
  "context_type": "item_analysis",
  "context_data": {
    "title": "MacBook Pro 2020",
    "price": 8000,
    "description": "8+256GB配置,使用一年",
    "category": "数码产品",
    "condition": "良好"
  }
}
```

#### 3. 冲突解决

```bash
POST /api/v1/ai/chat
Content-Type: application/json
Authorization: Bearer {token}

{
  "messages": [
    {"role": "user", "content": "请给出解决建议"}
  ],
  "context_type": "conflict_resolution",
  "context_data": {
    "conflict_type": "商品质量纠纷",
    "buyer_view": "商品与描述不符",
    "seller_view": "商品如实描述",
    "amount": 500
  }
}
```

#### 4. 快速商品分析

```bash
POST /api/v1/ai/quick-actions/analyze-item?item_id=123
Authorization: Bearer {token}
```

#### 5. 快速冲突解决

```bash
POST /api/v1/ai/quick-actions/resolve-conflict?transaction_id=456
Authorization: Bearer {token}
```

#### 6. 健康检查

```bash
GET /api/v1/ai/health
```

## 模型选择

智谱AI提供多个模型,可根据需求选择:

| 模型 | 特点 | 适用场景 |
|------|------|---------|
| glm-4-flash | 快速响应,成本低 | 推荐用于日常对话 |
| glm-4 | 性能强,理解力好 | 复杂分析场景 |
| glm-3-turbo | 平衡性能和成本 | 一般场景 |

## 成本说明

智谱AI采用按使用量计费:

- GLM-4-Flash: 约 ¥0.001/千tokens
- GLM-4: 约 ¥0.1/千tokens
- GLM-3-Turbo: 约 ¥0.005/千tokens

建议:
- 开发测试使用 glm-4-flash
- 生产环境可根据预算和需求选择合适模型
- 设置每月配额限制以控制成本

## 安全注意事项

1. **API密钥保护**: 
   - 不要将API密钥提交到Git仓库
   - 使用环境变量或密钥管理服务
   - 定期轮换密钥

2. **内容审核**:
   - AI回复仅供参考,重要决策需人工审核
   - 冲突解决建议不具法律效力

3. **隐私保护**:
   - 不要在对话中包含用户敏感信息
   - 对话历史不会被持久化存储

## 故障排查

### 1. AI服务不可用

**症状**: 前端显示"AI服务暂时不可用"

**解决**:
```bash
# 检查API密钥是否配置
docker exec campuswap-gateway env | grep GLM_API_KEY

# 检查健康状态
curl http://localhost:8000/api/v1/ai/health

# 查看后端日志
docker logs campuswap-gateway --tail 100
```

### 2. 响应超时

**症状**: 请求超时,没有返回

**解决**:
- 检查网络连接
- 尝试使用更快的模型 (glm-4-flash)
- 增加超时时间配置

### 3. API配额不足

**症状**: 返回配额不足错误

**解决**:
- 访问智谱AI控制台充值
- 检查是否超过月度配额限制

## 开发扩展

### 添加新的上下文类型

1. 在 `backend/apps/api_gateway/routers/ai_chat.py` 中添加新的 `context_type`
2. 在 `build_system_prompt()` 函数中添加对应的提示词
3. 在前端 `AIChatBox.vue` 中添加对应的UI

### 自定义快捷操作

编辑 `frontend/src/components/AIChatBox.vue`:

```typescript
const quickActions = computed(() => {
  // 添加自定义快捷操作
  return [
    { 
      label: '自定义操作', 
      icon: YourIcon, 
      prompt: '您的提示词' 
    }
  ]
})
```

## 更新日志

- 2025-12-16: 初始版本发布
  - 支持通用对话、商品分析、冲突解决
  - 集成智谱AI GLM-4模型
  - 提供悬浮聊天框UI
