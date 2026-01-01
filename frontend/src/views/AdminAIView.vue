<template>
  <div class="admin-ai-view">
    <div class="ai-header">
      <div class="header-content">
        <h1 class="text-3xl font-bold text-white">🤖 AI 智能助手</h1>
        <p class="mt-2 text-sm text-white/80">
          管理员专用AI助手 - 数据分析、决策支持、问题诊断
        </p>
        <div v-if="aiStatus" class="mt-2 flex items-center gap-2">
          <span 
            class="inline-flex items-center gap-1 rounded-full px-3 py-1 text-xs font-semibold"
            :class="aiStatus.status === 'healthy' ? 'bg-green-500/20 text-green-100' : 
                    aiStatus.status === 'unavailable' ? 'bg-yellow-500/20 text-yellow-100' :
                    'bg-red-500/20 text-red-100'"
          >
            <span>{{ aiStatus.status === 'healthy' ? '●' : aiStatus.status === 'unavailable' ? '◐' : '○' }}</span>
            <span>{{ aiStatus.message }}</span>
          </span>
          <span v-if="aiStatus.model" class="text-xs text-white/60">
            模型: {{ aiStatus.model }}
          </span>
        </div>
      </div>
      <button @click="clearHistory" class="clear-btn">
        🗑️ 清空对话
      </button>
    </div>

    <div class="chat-container">
      <!-- 侧边栏：快捷功能 -->
      <div class="sidebar">
        <h3 class="sidebar-title">⚡ 快捷功能</h3>
        
        <div class="quick-section">
          <h4 class="section-title">📊 数据查询</h4>
          <button
            v-for="action in dataActions"
            :key="action.id"
            @click="executeQuickAction(action)"
            class="quick-action-btn"
            :disabled="isLoading"
          >
            {{ action.icon }} {{ action.label }}
          </button>
        </div>

        <div class="quick-section">
          <h4 class="section-title">🔧 系统管理</h4>
          <button
            v-for="action in systemActions"
            :key="action.id"
            @click="executeQuickAction(action)"
            class="quick-action-btn"
            :disabled="isLoading"
          >
            {{ action.icon }} {{ action.label }}
          </button>
        </div>

        <div class="quick-section">
          <h4 class="section-title">💡 帮助指南</h4>
          <button
            v-for="action in helpActions"
            :key="action.id"
            @click="executeQuickAction(action)"
            class="quick-action-btn"
            :disabled="isLoading"
          >
            {{ action.icon }} {{ action.label }}
          </button>
        </div>
      </div>

      <!-- 主聊天区域 -->
      <div class="chat-main">
        <div class="messages-area" ref="messagesContainer">
          <!-- 欢迎消息 -->
          <div v-if="messages.length === 0" class="welcome-card">
            <div class="welcome-icon">🤖</div>
            <h2 class="welcome-title">您好，管理员！</h2>
            <p class="welcome-desc">我是您的AI助手，可以帮您：</p>
            <div class="welcome-features">
              <div class="feature-item">
                <span class="feature-icon">📊</span>
                <span>实时数据分析与统计</span>
              </div>
              <div class="feature-item">
                <span class="feature-icon">🔍</span>
                <span>系统状态监控诊断</span>
              </div>
              <div class="feature-item">
                <span class="feature-icon">⚙️</span>
                <span>配置优化建议</span>
              </div>
              <div class="feature-item">
                <span class="feature-icon">💡</span>
                <span>决策支持与建议</span>
              </div>
            </div>
            <p class="welcome-tip">💡 使用左侧快捷功能或直接输入问题开始对话</p>
          </div>

          <!-- 消息列表 -->
          <div
            v-for="(msg, index) in messages"
            :key="index"
            :class="['message-item', msg.role]"
          >
            <div class="message-avatar">
              {{ msg.role === 'user' ? '👤' : '🤖' }}
            </div>
            <div class="message-bubble">
              <div class="message-header">
                <span class="message-sender">
                  {{ msg.role === 'user' ? '您' : 'AI助手' }}
                </span>
                <span class="message-time">{{ formatTime(msg.timestamp) }}</span>
              </div>
              <div class="message-text" v-html="formatMessage(msg.content)"></div>
            </div>
          </div>

          <!-- 加载指示器 -->
          <div v-if="isLoading" class="message-item assistant">
            <div class="message-avatar">🤖</div>
            <div class="message-bubble">
              <div class="typing-indicator">
                <span></span>
                <span></span>
                <span></span>
              </div>
            </div>
          </div>
        </div>

        <!-- 输入区域 -->
        <div class="input-area">
          <n-input
            v-model:value="userInput"
            type="textarea"
            placeholder="输入您的问题... (Shift + Enter 换行，Enter 发送)"
            :autosize="{ minRows: 2, maxRows: 6 }"
            @keydown.enter.exact.prevent="sendMessage"
            :disabled="isLoading"
          />
          <button
            @click="sendMessage"
            :disabled="!userInput.trim() || isLoading"
            class="send-button"
          >
            {{ isLoading ? '⏳ 思考中' : '➤ 发送' }}
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, nextTick, onMounted } from 'vue'
import { NInput, useMessage } from 'naive-ui'
import { http } from '@/lib/http'

interface Message {
  role: 'user' | 'assistant'
  content: string
  timestamp: Date
}

interface QuickAction {
  id: string
  label: string
  icon: string
  prompt: string
}

const message = useMessage()
const messages = ref<Message[]>([])
const userInput = ref('')
const isLoading = ref(false)
const messagesContainer = ref<HTMLElement | null>(null)
const aiStatus = ref<any>(null)

// 数据查询快捷功能
const dataActions: QuickAction[] = [
  { id: 'user-stats', label: '用户统计', icon: '👥', prompt: '请提供最新的用户统计数据，包括总用户数、活跃用户、新增趋势等' },
  { id: 'item-stats', label: '零件统计', icon: '📦', prompt: '请分析零件数据，包括在售零件数、热门分类、交易趋势等' },
  { id: 'transaction-stats', label: '交易统计', icon: '💰', prompt: '请统计交易数据，包括总交易额、交易量、成功率等' },
  { id: 'anomaly-stats', label: '异常统计', icon: '⚠️', prompt: '请分析系统异常记录，包括错误数量、类型分布、解决状态等' },
]

// 系统管理快捷功能
const systemActions: QuickAction[] = [
  { id: 'db-status', label: '数据库状态', icon: '💾', prompt: '请检查数据库的连接状态、响应延迟和性能指标' },
  { id: 'performance', label: '性能分析', icon: '⚡', prompt: '请分析系统性能，包括响应时间、查询效率、资源使用情况' },
  { id: 'system-health', label: '系统健康度', icon: '�️', prompt: '请评估系统的整体健康状况，提供优化建议' },
  { id: 'error-log', label: '错误日志', icon: '🐛', prompt: '请检查最近的系统错误日志，分析常见问题' },
]

// 帮助指南快捷功能
const helpActions: QuickAction[] = [
  { id: 'optimize-tips', label: '优化建议', icon: '💡', prompt: '基于当前系统状态，请提供性能优化和配置改进建议' },
  { id: 'best-practice', label: '最佳实践', icon: '⭐', prompt: '请介绍凤凰交易系统管理的最佳实践和注意事项' },
  { id: 'troubleshooting', label: '故障排查', icon: '🔧', prompt: '请提供常见故障的排查流程和解决方案' },
]

const scrollToBottom = async () => {
  await nextTick()
  if (messagesContainer.value) {
    messagesContainer.value.scrollTop = messagesContainer.value.scrollHeight
  }
}

const formatMessage = (content: string) => {
  return content
    .replace(/\n/g, '<br>')
    .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
    .replace(/\*(.*?)\*/g, '<em>$1</em>')
    .replace(/`(.*?)`/g, '<code>$1</code>')
    .replace(/###\s+(.*?)(<br>|$)/g, '<h3>$1</h3>')
    .replace(/##\s+(.*?)(<br>|$)/g, '<h2>$1</h2>')
    .replace(/^-\s+/gm, '• ')
}

const formatTime = (date: Date) => {
  const now = new Date()
  const diff = now.getTime() - date.getTime()
  
  if (diff < 60000) return '刚刚'
  if (diff < 3600000) return `${Math.floor(diff / 60000)}分钟前`
  if (diff < 86400000) return `${Math.floor(diff / 3600000)}小时前`
  
  return date.toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' })
}

const sendMessage = async () => {
  if (!userInput.value.trim() || isLoading.value) return

  const userMessage = userInput.value.trim()
  messages.value.push({
    role: 'user',
    content: userMessage,
    timestamp: new Date()
  })
  userInput.value = ''
  isLoading.value = true

  await scrollToBottom()

  try {
    // 调用真实的 AI API
    const response = await http.post('/ai/chat', {
      messages: messages.value.map(m => ({
        role: m.role,
        content: m.content
      })),
      context_type: 'general',
      context_data: null
    })
    
    if (response.data.message) {
      messages.value.push({
        role: 'assistant',
        content: response.data.message,
        timestamp: new Date()
      })
      message.success('AI响应完成')
    } else {
      throw new Error('AI响应格式错误')
    }
  } catch (error: any) {
    console.error('AI对话错误:', error)
    
    let errorMessage = '抱歉，AI服务暂时不可用。'
    
    if (error.response?.status === 500 && error.response?.data?.detail?.includes('GLM API密钥未配置')) {
      errorMessage = '⚠️ AI服务未配置密钥，当前使用模拟响应。\n\n' + generateMockResponse(userMessage)
    } else if (error.response?.status === 504) {
      errorMessage = 'AI服务响应超时，请稍后重试。'
    } else if (error.response?.data?.detail) {
      errorMessage = `AI服务错误：${error.response.data.detail}`
    }
    
    messages.value.push({
      role: 'assistant',
      content: errorMessage,
      timestamp: new Date()
    })
    
    if (error.response?.data?.detail?.includes('GLM API密钥未配置')) {
      message.warning('AI服务未配置，使用模拟数据')
    } else {
      message.error('AI服务错误')
    }
  } finally {
    isLoading.value = false
    await scrollToBottom()
  }
}

const executeQuickAction = async (action: QuickAction) => {
  userInput.value = action.prompt
  await sendMessage()
}

const clearHistory = () => {
  if (messages.value.length === 0) return
  
  if (confirm('确定要清空所有对话记录吗？')) {
    messages.value = []
    message.success('对话记录已清空')
  }
}

// 检查 AI 服务健康状态
const checkAIHealth = async () => {
  try {
    const response = await http.get('/ai/health')
    aiStatus.value = response.data
  } catch (error) {
    console.error('检查AI服务健康状态失败:', error)
    aiStatus.value = {
      status: 'error',
      message: 'AI服务连接失败'
    }
  }
}

// 组件挂载时检查AI服务状态
onMounted(() => {
  checkAIHealth()
})

// 模拟AI响应（当真实API不可用时使用）
const generateMockResponse = (question: string): string => {
  const lowerQ = question.toLowerCase()
  
  if (lowerQ.includes('用户') && lowerQ.includes('统计')) {
    return `**用户统计数据分析**

📊 **总体概况:**
- 总用户数: **204** 人
- 活跃用户: **156** 人 (最近7天有活动)
- 本月新增: **23** 人 (+12.7% 较上月)

👥 **用户分布:**
- 普通用户: 198人 (97%)
- 管理员: 6人 (3%)
- 认证用户: 187人 (91.7%)

📈 **活跃度趋势:**
- 日均活跃: 45人
- 周活跃增长: +8.3%
- 用户留存率: 78.5%

💡 **优化建议:**
1. 活跃度良好，可考虑增加用户互动功能
2. 认证率较高，说明信任体系运作良好
3. 建议针对新用户推出引导活动`
  }
  
  if (lowerQ.includes('零件') && lowerQ.includes('统计')) {
    return `**零件数据分析报告**

📦 **零件概况:**
- 总零件数: **11,586** 件
- 在售零件: **11,569** 件
- 已售零件: **8,234** 件
- 售罄率: **71.2%**

🏆 **热门分类TOP5:**
1. 电子产品 - 3,245件 (28%)
2. 图书教材 - 2,890件 (25%)
3. 生活用品 - 2,156件 (18.6%)
4. 运动器材 - 1,543件 (13.3%)
5. 服饰配饰 - 1,752件 (15.1%)

💰 **价格分布:**
- 平均价格: ¥156.8
- 价格区间: ¥5 - ¥8,500
- 主流价格带: ¥50-¥300 (占67%)

📈 **趋势分析:**
- 本周新增: +127件
- 交易增长: +15.3%
- 用户满意度: 4.6/5.0

✅ **运营建议:**
1. 电子产品和图书类最受欢迎，可加强推荐
2. 高售罄率说明供需平衡良好
3. 建议对滞销零件进行促销活动`
  }
  
  if (lowerQ.includes('交易') && lowerQ.includes('统计')) {
    return `**交易数据统计分析**

💰 **交易概况:**
- 总交易额: **¥1,234,567.89**
- 交易笔数: **8,456** 笔
- 平均客单价: **¥146.0**
- 交易成功率: **94.3%**

📊 **交易状态分布:**
- 已完成: 7,975笔 (94.3%)
- 进行中: 342笔 (4.0%)
- 已取消: 98笔 (1.2%)
- 退款中: 41笔 (0.5%)

📈 **交易趋势:**
- 日均交易: 156笔
- 周增长率: +12.5%
- 月增长率: +23.7%

⏰ **交易高峰时段:**
- 10:00-12:00 (28%)
- 14:00-16:00 (24%)
- 19:00-21:00 (31%)

💡 **优化建议:**
1. 交易成功率高，系统运行稳定
2. 晚间交易活跃，可增加客服支持
3. 退款率低，说明零件质量把控良好
4. 建议在高峰时段推送促销活动`
  }
  
  if (lowerQ.includes('异常') || lowerQ.includes('错误')) {
    return `**系统异常记录分析**

⚠️ **异常统计:**
- 总异常数: **23** 个
- 未解决: **5** 个
- 已解决: **16** 个
- 已忽略: **2** 个

🔍 **异常类型分布:**
- 数据库连接超时: 12个 (52%)
- API 响应异常: 8个 (35%)
- 权限验证失败: 3个 (13%)

💾 **数据库状态:**
- MySQL: ✅ 正常 (延迟 12ms)
- Redis: ✅ 正常 (延迟 2ms)

📊 **系统效率:**
- 请求成功率: 99.7%
- 平均响应时间: 85ms
- 上次备份时间: 2小时前

🔧 **处理建议:**
1. 5个未解决异常需要人工排查
2. 连接超时较多，建议检查网络稳定性
3. 响应时间在正常范围内
4. 建议增加自动重试机制`
  }
  
  if (lowerQ.includes('数据库') && lowerQ.includes('状态')) {
    return `**数据库系统状态报告**

💾 **连接状态:**
- 主业务数据库: ✅ 连接正常 - 142 活跃连接
- 库存分析数据库: ✅ 连接正常 - 45 活跃连接
- 交易日志数据库: ✅ 连接正常 - 28 活跃连接
- Redis (缓存): ✅ 连接正常 - 98 活跃连接

⚡ **性能指标:**
- 主业务数据库: 查询延迟 12ms, 错误率 0.01%
- Redis: 读写延迟 2ms, 命中率 85%

📊 **资源使用:**
- CPU: 23.5% (正常)
- 内存: 42.8% (正常)
- 磁盘I/O: 156 MB/s (正常)
- 网络带宽: 23.4 MB/s (正常)

✅ **健康评分: 98/100**

💡 **优化建议:**
1. 所有数据库运行正常，无需立即处理
2. 缓存命中率良好，可继续保持
3. 连接池配置合理，负载均衡良好
4. 建议定期进行数据备份和清理`
  }
  
  if (lowerQ.includes('性能') || lowerQ.includes('优化')) {
    return `**系统性能分析与优化建议**

⚡ **当前性能指标:**
- API响应时间: **87ms** (优秀)
- 页面加载时间: **1.2s** (良好)
- 数据库查询: **13.5ms** (优秀)
- 并发处理: **500+ req/s** (良好)

📊 **资源使用情况:**
- CPU使用率: 23.5%
- 内存使用率: 42.8%
- 磁盘使用率: 58.3%
- 网络带宽: 23.4 MB/s

🎯 **性能瓶颈分析:**
1. ✅ API响应快速，无明显瓶颈
2. ⚠️ 部分复杂查询可优化
3. ✅ 缓存命中率较高 (78%)
4. ⚠️ 图片加载可使用CDN加速

💡 **优化建议:**

**短期优化 (1-2周):**
1. 为常用查询添加复合索引
2. 启用查询结果缓存
3. 压缩静态资源文件
4. 优化数据库连接池配置

**中期优化 (1-2月):**
1. 引入Redis缓存热点数据
2. 实施API接口限流
3. 数据库读写分离
4. 图片资源迁移至CDN

**长期规划:**
1. 考虑微服务架构拆分
2. 实施自动伸缩机制
3. 建立完善的监控告警体系
4. 定期进行性能压测

✨ **预期效果:**
- API响应时间可降至 50ms以下
- 并发处理能力提升至 1000+ req/s
- 系统稳定性达到 99.9%
- 用户体验显著提升`
  }
  
  if (lowerQ.includes('帮助') || lowerQ.includes('指南')) {
    return `**凤凰交易系统管理指南**

📚 **核心功能模块:**

**1. 数据监控 📊**
- 实时查看用户、零件、交易统计
- 监控系统性能和资源使用
- 分析业务趋势和异常情况

**2. 业务管理 📦**
- 零件审核与上架管理
- 交易订单跟踪与处理
- 分类与库存维护

**3. 用户管理 👥**
- 用户信息查看和编辑
- 角色权限分配
- 信用分管理和违规处理

**4. 系统配置 ⚙️**
- 数据库连接配置
- 系统参数调整
- 通知和邮件配置

**5. 安全审计 🔒**
- 查看操作审计日志
- 监控异常登录
- 数据备份和恢复

🎯 **最佳实践:**

1. **定期检查** - 每日查看系统概况和关键指标
2. **主动维护** - 及时处理异常和举报
3. **数据备份** - 每周进行完整数据备份
4. **性能优化** - 根据监控数据调整配置
5. **用户服务** - 快速响应用户反馈和投诉

⚠️ **注意事项:**
- 修改数据库配置前务必备份
- 批量操作前先小范围测试
- 重要操作建议双人复核
- 定期查看审计日志

💡 **常见问题:**
- 发现异常如何处理？→ 查看异常详情，根据类型排查
- 如何优化性能？→ 分析慢查询，添加索引
- 用户投诉怎么办？→ 查看交易记录，公正处理

如需具体操作指导，请描述您的问题！`
  }
  
  // 默认响应
  return `我已收到您的问题："${question}"

作为管理员AI助手，我可以帮您：

🔍 **数据分析** - 提供用户、零件、交易等统计数据
💾 **系统监控** - 检查数据库状态和性能指标  
⚙️ **配置优化** - 给出系统优化和改进建议
🔧 **问题诊断** - 分析系统错误和故障原因
💡 **决策支持** - 提供运营建议和最佳实践

您可以：
- 使用左侧快捷功能快速获取信息
- 直接提问，我会尽力为您解答
- 描述具体问题，获得针对性建议

请告诉我您需要什么帮助？`
}
</script>

<style scoped>
.admin-ai-view {
  height: 100vh;
  display: flex;
  flex-direction: column;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
}

.ai-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 2rem;
  background: rgba(255, 255, 255, 0.1);
  backdrop-filter: blur(10px);
}

.header-content h1 {
  margin: 0;
}

.clear-btn {
  padding: 0.75rem 1.5rem;
  background: rgba(255, 255, 255, 0.2);
  border: none;
  border-radius: 12px;
  color: white;
  font-size: 14px;
  cursor: pointer;
  transition: all 0.3s;
}

.clear-btn:hover {
  background: rgba(255, 255, 255, 0.3);
  transform: translateY(-2px);
}

.chat-container {
  flex: 1;
  display: grid;
  grid-template-columns: 280px 1fr;
  gap: 1.5rem;
  padding: 1.5rem;
  overflow: hidden;
}

.sidebar {
  background: white;
  border-radius: 16px;
  padding: 1.5rem;
  overflow-y: auto;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
}

.sidebar-title {
  font-size: 18px;
  font-weight: 600;
  margin: 0 0 1rem 0;
  color: #667eea;
}

.quick-section {
  margin-bottom: 1.5rem;
}

.section-title {
  font-size: 13px;
  font-weight: 600;
  color: #666;
  margin: 0 0 0.75rem 0;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.quick-action-btn {
  width: 100%;
  padding: 0.75rem 1rem;
  margin-bottom: 0.5rem;
  background: #f8f9fa;
  border: 2px solid transparent;
  border-radius: 10px;
  text-align: left;
  font-size: 14px;
  cursor: pointer;
  transition: all 0.2s;
  color: #333;
}

.quick-action-btn:hover:not(:disabled) {
  background: #e3f2fd;
  border-color: #667eea;
  transform: translateX(4px);
}

.quick-action-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.chat-main {
  display: flex;
  flex-direction: column;
  background: white;
  border-radius: 16px;
  overflow: hidden;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
}

.messages-area {
  flex: 1;
  padding: 2rem;
  overflow-y: auto;
}

.welcome-card {
  text-align: center;
  padding: 3rem 2rem;
  max-width: 600px;
  margin: 0 auto;
}

.welcome-icon {
  font-size: 64px;
  margin-bottom: 1rem;
}

.welcome-title {
  font-size: 28px;
  font-weight: 600;
  color: #333;
  margin: 0 0 0.5rem 0;
}

.welcome-desc {
  color: #666;
  margin: 0 0 2rem 0;
  font-size: 16px;
}

.welcome-features {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 1rem;
  margin-bottom: 2rem;
}

.feature-item {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding: 1rem;
  background: #f8f9fa;
  border-radius: 12px;
  font-size: 14px;
}

.feature-icon {
  font-size: 24px;
}

.welcome-tip {
  color: #999;
  font-size: 14px;
  font-style: italic;
}

.message-item {
  display: flex;
  gap: 1rem;
  margin-bottom: 1.5rem;
  animation: fadeIn 0.3s;
}

.message-item.user {
  flex-direction: row-reverse;
}

.message-avatar {
  width: 40px;
  height: 40px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 20px;
  flex-shrink: 0;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
}

.message-item.user .message-avatar {
  background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
}

.message-bubble {
  max-width: 70%;
  background: #f8f9fa;
  border-radius: 16px;
  padding: 1rem;
}

.message-item.user .message-bubble {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
}

.message-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 0.5rem;
  font-size: 12px;
}

.message-sender {
  font-weight: 600;
}

.message-time {
  opacity: 0.6;
}

.message-text {
  line-height: 1.6;
  font-size: 14px;
}

.message-text :deep(strong) {
  font-weight: 600;
  color: #667eea;
}

.message-text :deep(code) {
  background: rgba(0, 0, 0, 0.05);
  padding: 2px 6px;
  border-radius: 4px;
  font-family: monospace;
  font-size: 13px;
}

.message-text :deep(h2),
.message-text :deep(h3) {
  margin: 1rem 0 0.5rem 0;
  font-weight: 600;
}

.typing-indicator {
  display: flex;
  gap: 4px;
  padding: 0.5rem 0;
}

.typing-indicator span {
  width: 8px;
  height: 8px;
  background: #667eea;
  border-radius: 50%;
  animation: typing 1.4s infinite;
}

.typing-indicator span:nth-child(2) {
  animation-delay: 0.2s;
}

.typing-indicator span:nth-child(3) {
  animation-delay: 0.4s;
}

.input-area {
  display: flex;
  gap: 1rem;
  padding: 1.5rem;
  border-top: 2px solid #f0f0f0;
  background: #fafafa;
}

.send-button {
  padding: 0.75rem 2rem;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  border: none;
  border-radius: 12px;
  color: white;
  font-size: 14px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.3s;
  white-space: nowrap;
}

.send-button:hover:not(:disabled) {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(102, 126, 234, 0.4);
}

.send-button:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

@keyframes fadeIn {
  from {
    opacity: 0;
    transform: translateY(10px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

@keyframes typing {
  0%, 60%, 100% {
    transform: translateY(0);
  }
  30% {
    transform: translateY(-10px);
  }
}

::-webkit-scrollbar {
  width: 6px;
}

::-webkit-scrollbar-track {
  background: #f1f1f1;
  border-radius: 10px;
}

::-webkit-scrollbar-thumb {
  background: #667eea;
  border-radius: 10px;
}

::-webkit-scrollbar-thumb:hover {
  background: #764ba2;
}
</style>
