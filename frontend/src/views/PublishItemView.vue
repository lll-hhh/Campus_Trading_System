<script setup lang="ts">
import { ref, reactive } from 'vue'
import { useRouter } from 'vue-router'
import {
  NCard,
  NForm,
  NFormItem,
  NInput,
  NInputNumber,
  NSelect,
  NUpload,
  NButton,
  NSpace,
  NRadioGroup,
  NRadio,
  NCheckbox,
  useMessage,
  type UploadFileInfo
} from 'naive-ui'
import { useAuthStore } from '@/stores/auth'

const router = useRouter()
const message = useMessage()
const authStore = useAuthStore()

const loading = ref(false)
const fileList = ref<UploadFileInfo[]>([])

// 表单数据
const formData = reactive({
  title: '',
  category: null as string | null,
  condition: '全新',
  price: null as number | null,
  originalPrice: null as number | null,
  description: '',
  location: '',
  contactMethod: 'chat',
  phone: '',
  wechat: '',
  allowBargain: true,
  acceptReturn: false,
  images: [] as string[]
})

// 分类选项
const categoryOptions = [
  { label: '📱 数码产品', value: 'digital' },
  { label: '📚 教材书籍', value: 'books' },
  { label: '👕 服装鞋帽', value: 'clothing' },
  { label: '🏀 运动器材', value: 'sports' },
  { label: '🎮 娱乐休闲', value: 'entertainment' },
  { label: '🛏️ 生活用品', value: 'daily' },
  { label: '🎨 文具办公', value: 'stationery' },
  { label: '🎸 乐器设备', value: 'music' },
  { label: '🚲 自行车', value: 'bicycle' },
  { label: '📦 其他', value: 'other' }
]

// 成色选项
const conditionOptions = [
  { label: '全新', value: '全新' },
  { label: '99新', value: '99新' },
  { label: '95新', value: '95新' },
  { label: '9成新', value: '9成新' },
  { label: '8成新', value: '8成新' },
  { label: '7成新以下', value: '7成新以下' }
]

// 联系方式选项
const contactMethodOptions = [
  { label: '站内聊天', value: 'chat' },
  { label: '电话', value: 'phone' },
  { label: '微信', value: 'wechat' },
  { label: '多种方式', value: 'multiple' }
]

// 表单验证规则
const rules = {
  title: [
    { required: true, message: '请输入商品标题', trigger: 'blur' },
    { min: 5, max: 100, message: '标题长度为5-100个字符', trigger: 'blur' }
  ],
  category: [
    { required: true, message: '请选择商品分类', trigger: 'change' }
  ],
  price: [
    { required: true, message: '请输入商品价格', trigger: 'blur' },
    { type: 'number', min: 0, message: '价格不能为负数', trigger: 'blur' }
  ],
  description: [
    { required: true, message: '请输入商品描述', trigger: 'blur' },
    { min: 10, message: '描述至少10个字符', trigger: 'blur' }
  ],
  location: [
    { required: true, message: '请输入交易地点', trigger: 'blur' }
  ]
}

// 图片上传处理
const handleUploadChange = ({ fileList: newFileList }: { fileList: UploadFileInfo[] }) => {
  fileList.value = newFileList
}

const handleBeforeUpload = (data: { file: UploadFileInfo }) => {
  // 检查文件类型
  if (!data.file.file?.type?.startsWith('image/')) {
    message.error('只能上传图片文件')
    return false
  }
  
  // 检查文件大小（最大5MB）
  if (data.file.file && data.file.file.size > 5 * 1024 * 1024) {
    message.error('图片大小不能超过5MB')
    return false
  }
  
  return true
}

// 自定义上传
const customUpload = ({ file, onFinish, onError }: any) => {
  // TODO: 实际上传到服务器
  // 这里模拟上传过程
  setTimeout(() => {
    // 创建本地预览URL
    const url = URL.createObjectURL(file.file)
    formData.images.push(url)
    onFinish()
    message.success('图片上传成功')
  }, 1000)
}

// 提交表单
const handleSubmit = async () => {
  if (!authStore.isAuthenticated) {
    message.warning('请先登录')
    router.push('/login')
    return
  }
  
  // 验证图片
  if (fileList.value.length === 0) {
    message.warning('请至少上传一张商品图片')
    return
  }
  
  loading.value = true
  
  try {
    // TODO: 调用API发布商品
    await new Promise(resolve => setTimeout(resolve, 1500))
    
    message.success('商品发布成功！')
    router.push('/my-items')
  } catch (error: any) {
    message.error(error.message || '发布失败，请重试')
  } finally {
    loading.value = false
  }
}

// 保存草稿
const handleSaveDraft = () => {
  message.success('草稿已保存')
}

// 预览
const handlePreview = () => {
  message.info('预览功能开发中...')
}
</script>

<template>
  <div class="publish-item-view">
    <n-card title="📝 发布商品">
      <n-form
        :model="formData"
        :rules="rules"
        label-placement="left"
        label-width="120"
        require-mark-placement="left"
      >
        <!-- 商品图片 -->
        <n-form-item label="商品图片" path="images">
          <n-upload
            v-model:file-list="fileList"
            list-type="image-card"
            :max="9"
            :custom-request="customUpload"
            @before-upload="handleBeforeUpload"
            @update:file-list="handleUploadChange"
          >
            <div style="text-align: center">
              <div style="font-size: 32px">📷</div>
              <div style="font-size: 14px; margin-top: 8px">
                点击上传<br/>
                <span style="font-size: 12px; color: #999">
                  最多9张，每张不超过5MB
                </span>
              </div>
            </div>
          </n-upload>
        </n-form-item>

        <!-- 商品标题 -->
        <n-form-item label="商品标题" path="title">
          <n-input
            v-model:value="formData.title"
            placeholder="请输入商品标题，简洁明了更易吸引买家"
            maxlength="100"
            show-count
          />
        </n-form-item>

        <!-- 商品分类 -->
        <n-form-item label="商品分类" path="category">
          <n-select
            v-model:value="formData.category"
            :options="categoryOptions"
            placeholder="请选择商品分类"
          />
        </n-form-item>

        <!-- 成色 -->
        <n-form-item label="成色" path="condition">
          <n-select
            v-model:value="formData.condition"
            :options="conditionOptions"
            placeholder="请选择商品成色"
          />
        </n-form-item>

        <!-- 价格 -->
        <n-form-item label="出售价格" path="price">
          <n-input-number
            v-model:value="formData.price"
            placeholder="请输入价格"
            :min="0"
            :precision="2"
            style="width: 100%"
          >
            <template #prefix>¥</template>
          </n-input-number>
        </n-form-item>

        <!-- 原价（可选） -->
        <n-form-item label="原价">
          <n-input-number
            v-model:value="formData.originalPrice"
            placeholder="选填，用于显示优惠力度"
            :min="0"
            :precision="2"
            style="width: 100%"
          >
            <template #prefix>¥</template>
          </n-input-number>
        </n-form-item>

        <!-- 商品描述 -->
        <n-form-item label="商品描述" path="description">
          <n-input
            v-model:value="formData.description"
            type="textarea"
            placeholder="详细描述商品的特点、购买时间、使用情况、出售原因等信息"
            :rows="6"
            maxlength="2000"
            show-count
          />
        </n-form-item>

        <!-- 交易地点 -->
        <n-form-item label="交易地点" path="location">
          <n-input
            v-model:value="formData.location"
            placeholder="例如：北京大学 学生公寓1号楼"
          />
        </n-form-item>

        <!-- 联系方式 -->
        <n-form-item label="联系方式">
          <n-space vertical style="width: 100%">
            <n-radio-group v-model:value="formData.contactMethod">
              <n-space>
                <n-radio
                  v-for="option in contactMethodOptions"
                  :key="option.value"
                  :value="option.value"
                >
                  {{ option.label }}
                </n-radio>
              </n-space>
            </n-radio-group>
            
            <n-input
              v-if="formData.contactMethod === 'phone' || formData.contactMethod === 'multiple'"
              v-model:value="formData.phone"
              placeholder="手机号码"
            />
            
            <n-input
              v-if="formData.contactMethod === 'wechat' || formData.contactMethod === 'multiple'"
              v-model:value="formData.wechat"
              placeholder="微信号"
            />
          </n-space>
        </n-form-item>

        <!-- 交易选项 -->
        <n-form-item label="交易选项">
          <n-space vertical>
            <n-checkbox v-model:checked="formData.allowBargain">
              支持议价
            </n-checkbox>
            <n-checkbox v-model:checked="formData.acceptReturn">
              支持退换（需说明条件）
            </n-checkbox>
          </n-space>
        </n-form-item>

        <!-- 操作按钮 -->
        <n-form-item>
          <n-space>
            <n-button
              type="primary"
              size="large"
              :loading="loading"
              @click="handleSubmit"
            >
              🚀 立即发布
            </n-button>
            <n-button size="large" @click="handleSaveDraft">
              💾 保存草稿
            </n-button>
            <n-button size="large" @click="handlePreview">
              👁️ 预览
            </n-button>
            <n-button size="large" @click="router.back()">
              ❌ 取消
            </n-button>
          </n-space>
        </n-form-item>
      </n-form>
    </n-card>

    <!-- 发布须知 -->
    <n-card title="📋 发布须知" style="margin-top: 24px">
      <ul style="line-height: 2; color: #666">
        <li>请确保商品信息真实准确，上传的图片与实物相符</li>
        <li>禁止发布违禁物品、假冒伪劣商品</li>
        <li>建议使用高质量图片，提高商品吸引力</li>
        <li>详细的商品描述能帮助买家更好地了解商品</li>
        <li>请诚信交易，维护良好的交易环境</li>
        <li>商品发布后可在"我的商品"中管理</li>
      </ul>
    </n-card>
  </div>
</template>

<style scoped>
.publish-item-view {
  max-width: 900px;
  margin: 0 auto;
}
</style>
