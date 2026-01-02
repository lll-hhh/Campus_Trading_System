<script setup lang="ts">
import { ref, reactive, computed } from 'vue'
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
  NModal,
  NImage,
  NTag,
  NDivider,
  NGrid,
  NGridItem,
  useMessage,
  type UploadFileInfo,
  type FormRules
} from 'naive-ui'
import { useAuthStore } from '@/stores/auth'
import { http } from '@/lib/http'

const router = useRouter()
const message = useMessage()
const authStore = useAuthStore()

const loading = ref(false)
const aiLoading = ref(false)
const showPreview = ref(false)
const fileList = ref<UploadFileInfo[]>([])

// 表单数据
const formData = reactive({
  title: '',
  category: null as string | null,
  condition: 'used',
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
  { label: '⚙️ 发动机系统', value: 'engine' },
  { label: '🛑 制动系统', value: 'brakes' },
  { label: '🌪️ 滤清器', value: 'filters' },
  { label: '🔋 蓄电池', value: 'batteries' },
  { label: '⭕ 轮胎轮毂', value: 'tires' },
  { label: '💡 灯光照明', value: 'lighting' },
  { label: '🚜 悬挂系统', value: 'suspension' },
  { label: '⛓️ 传动系统', value: 'transmission' },
  { label: '🚗 车身外观', value: 'body' },
  { label: '🛋️ 内饰配件', value: 'interior' },
  { label: '📦 其他配件', value: 'other' }
]

// 成色选项
const conditionOptions = [
  { label: '原厂全新', value: 'new' },
  { label: '原厂拆车', value: 'like-new' },
  { label: '品牌件', value: 'excellent' },
  { label: '副厂件', value: 'good' },
  { label: '翻新件', value: 'used' }
]

// 联系方式选项
const contactMethodOptions = [
  { label: '站内聊天', value: 'chat' },
  { label: '电话', value: 'phone' },
  { label: '微信', value: 'wechat' },
  { label: '多种方式', value: 'multiple' }
]

// 表单验证规则
const rules: FormRules = {
  title: [
    { required: true, message: '请输入零件名称/型号', trigger: 'blur' },
    { min: 5, max: 100, message: '名称长度为5-100个字符', trigger: 'blur' }
  ],
  category: [
    { required: true, message: '请选择零件分类', trigger: 'change' }
  ],
  price: [
    { required: true, message: '请输入零件价格', trigger: 'blur' },
    { type: 'number', min: 0, message: '价格不能为负数', trigger: 'blur' }
  ],
  description: [
    { required: true, message: '请输入零件描述', trigger: 'blur' },
    { min: 10, message: '描述至少10个字符', trigger: 'blur' }
  ],
  location: [
    { required: true, message: '请输入交易地点', trigger: 'blur' }
  ]
}

// 图片上传处理
const syncImagesFromFiles = (files: UploadFileInfo[]) => {
  const urls = files
    .map((file) => file.url || file.thumbnailUrl)
    .filter((url): url is string => !!url)
  formData.images = urls
}

const handleUploadChange = (data: { fileList: UploadFileInfo[] }) => {
  fileList.value = data.fileList
  syncImagesFromFiles(data.fileList)
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
const customUpload = async ({ file, onFinish, onError }: any) => {
  try {
    // 创建 FormData 上传到服务器
    const uploadData = new FormData()
    uploadData.append('file', file.file as File)
    
    // 尝试上传到服务器
    try {
      const response = await http.post('/upload/image', uploadData, {
        headers: { 'Content-Type': 'multipart/form-data' }
      })
      file.url = response.data.url
      formData.images = Array.from(new Set([...formData.images, response.data.url]))
      onFinish()
      message.success('图片上传成功')
    } catch (uploadError) {
      // 如果服务器上传失败，使用本地预览
      console.warn('服务器上传失败，使用本地预览:', uploadError)
      if (file.file) {
        const url = URL.createObjectURL(file.file as File)
        file.url = url
        formData.images = Array.from(new Set([...formData.images, url]))
      }
      onFinish()
      message.info('已使用本地预览')
    }
  } catch (error) {
    console.error('图片上传失败', error)
    onError()
    message.error('图片上传失败')
  }
}

// 获取 AI 定价建议
const getAIPriceSuggestion = async () => {
  if (!formData.title || !formData.description) {
    message.warning('请先填写零件标题和描述，以便 AI 进行分析')
    return
  }
  
  aiLoading.value = true
  try {
    const response = await http.post('/ai/chat', {
      messages: [
        { role: 'user', content: `请为以下零件提供定价建议：\n标题：${formData.title}\n描述：${formData.description}\n分类：${formData.category}\n成色：${formData.condition}` }
      ],
      context_type: 'item_analysis',
      context_data: {
        title: formData.title,
        description: formData.description,
        category: formData.category,
        condition: formData.condition,
        price: formData.price || 0
      }
    })
    
    const aiSuggestion = response.data.message
    message.info('AI 建议：' + aiSuggestion, { duration: 10000, closable: true })
  } catch (error) {
    console.error('AI 定价失败:', error)
    message.error('获取 AI 定价建议失败')
  } finally {
    aiLoading.value = false
  }
}

// 提交发布
const handlePublish = async () => {
  if (!authStore.isAuthenticated) {
    message.warning('请先登录')
    router.push('/login')
    return
  }
  
  // 验证图片
  if (!formData.images || formData.images.length === 0) {
    message.warning('请至少上传一张零件图片')
    return
  }
  
  loading.value = true
  
  try {
    await http.post('/items', {
      title: formData.title,
      description: formData.description,
      price: formData.price,
      category: formData.category,
      condition: formData.condition,
      status: 'available',
      images: formData.images,
      original_price: formData.originalPrice,
      location: formData.location,
      contact_method: formData.contactMethod,
      phone: formData.phone,
      wechat: formData.wechat,
      allow_bargain: formData.allowBargain,
      accept_return: formData.acceptReturn
    })
    
    message.success('零件发布成功！')
    router.push('/my-items')
  } catch (error: any) {
    message.error(error.response?.data?.detail || error.message || '发布失败，请重试')
  } finally {
    loading.value = false
  }
}

// 保存草稿
const handleSaveDraft = () => {
  // 保存到 localStorage
  const draft = {
    ...formData,
    savedAt: new Date().toISOString()
  }
  localStorage.setItem('publishItemDraft', JSON.stringify(draft))
  message.success('草稿已保存到本地')
}

// 获取分类标签
const getCategoryLabel = computed(() => {
  const option = categoryOptions.find(o => o.value === formData.category)
  return option?.label || '未选择'
})

// 获取成色标签
const getConditionLabel = computed(() => {
  const option = conditionOptions.find(o => o.value === formData.condition)
  return option?.label || '未选择'
})

// 获取预览图片列表
const previewImages = computed(() => {
  return fileList.value
    .filter(f => f.status === 'finished' && f.url)
    .map(f => f.url as string)
})

// 预览
const handlePreview = () => {
  // 基本验证
  if (!formData.title) {
    message.warning('请先输入零件标题')
    return
  }
  if (!formData.category) {
    message.warning('请先选择零件分类')
    return
  }
  if (!formData.price) {
    message.warning('请先输入零件价格')
    return
  }
  showPreview.value = true
}
</script>

<template>
  <div class="publish-item min-h-screen bg-[#f4f4f4]">
    <!-- Header Section -->
    <div class="bg-[#2e3235] text-white py-8 mb-8">
      <div class="max-w-5xl mx-auto px-4">
        <h1 class="text-3xl font-black tracking-tighter uppercase italic">
          List New <span class="text-primary">Part</span>
          <span class="block text-sm font-normal tracking-widest mt-1 opacity-60 italic">PHOENIX AUTO PARTS / INVENTORY ADDITION</span>
        </h1>
      </div>
    </div>

    <div class="max-w-5xl mx-auto px-4 pb-12">
      <div class="grid grid-cols-1 lg:grid-cols-3 gap-8">
        <!-- Main Form -->
        <div class="lg:col-span-2 space-y-8">
          <div class="bg-white border border-gray-200 p-8">
            <h2 class="text-xl font-black uppercase italic tracking-tighter mb-6 flex items-center gap-2">
              <span class="w-2 h-6 bg-primary"></span>
              Part Specifications
            </h2>
            
            <n-form ref="formRef" :model="formData" :rules="rules" label-placement="top">
              <n-form-item label="PART TITLE / MODEL" path="title" class="font-bold tracking-widest text-[10px]">
                <n-input v-model:value="formData.title" placeholder="e.g. BREMBO GT6 BRAKE CALIPER SET" class="uppercase" />
              </n-form-item>

              <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
                <n-form-item label="CATEGORY" path="category" class="font-bold tracking-widest text-[10px]">
                  <n-select v-model:value="formData.category" :options="categoryOptions" placeholder="Select Category" />
                </n-form-item>
                <n-form-item label="CONDITION" path="condition" class="font-bold tracking-widest text-[10px]">
                  <n-select v-model:value="formData.condition" :options="conditionOptions" placeholder="Select Condition" />
                </n-form-item>
              </div>

              <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
                <n-form-item label="PRICE (CNY)" path="price" class="font-bold tracking-widest text-[10px]">
                  <n-input-number v-model:value="formData.price" :min="0" placeholder="0.00" class="w-full" />
                </n-form-item>
                <n-form-item label="ORIGINAL PRICE" path="originalPrice" class="font-bold tracking-widest text-[10px]">
                  <n-input-number v-model:value="formData.originalPrice" :min="0" placeholder="0.00" class="w-full" />
                </n-form-item>
              </div>

              <n-form-item label="TECHNICAL DESCRIPTION" path="description" class="font-bold tracking-widest text-[10px]">
                <n-input 
                  v-model:value="formData.description" 
                  type="textarea" 
                  placeholder="Provide detailed technical specifications, compatibility, and usage history..."
                  :autosize="{ minRows: 4, maxRows: 8 }"
                />
              </n-form-item>

              <n-form-item label="PART IMAGES" class="font-bold tracking-widest text-[10px]">
                <n-upload
                  multiple
                  directory-dnd
                  :max="9"
                  list-type="image-card"
                  :file-list="fileList"
                  @change="handleUploadChange"
                  :custom-request="customUpload"
                  @before-upload="handleBeforeUpload"
                >
                  <div class="text-center">
                    <div class="text-2xl mb-1">📸</div>
                    <div class="text-[8px] font-black uppercase tracking-tighter">Upload</div>
                  </div>
                </n-upload>
              </n-form-item>
            </n-form>
          </div>

          <div class="bg-white border border-gray-200 p-8">
            <h2 class="text-xl font-black uppercase italic tracking-tighter mb-6 flex items-center gap-2">
              <span class="w-2 h-6 bg-primary"></span>
              Logistics & Contact
            </h2>
            <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
              <n-form-item label="WAREHOUSE LOCATION" path="location" class="font-bold tracking-widest text-[10px]">
                <n-input v-model:value="formData.location" placeholder="e.g. Shanghai Warehouse A" />
              </n-form-item>
              <n-form-item label="CONTACT METHOD" path="contactMethod" class="font-bold tracking-widest text-[10px]">
                <n-select v-model:value="formData.contactMethod" :options="contactMethodOptions" />
              </n-form-item>
            </div>
          </div>
        </div>

        <!-- Sidebar Actions -->
        <div class="lg:col-span-1">
          <div class="bg-[#2e3235] text-white p-6 sticky top-24">
            <h2 class="text-xl font-black uppercase italic tracking-tighter mb-6 border-b border-white/10 pb-4">
              Listing <span class="text-primary">Actions</span>
            </h2>
            
            <div class="space-y-4">
              <n-button 
                block 
                secondary 
                strong 
                type="primary" 
                class="h-12 uppercase font-bold italic tracking-widest"
                :loading="aiLoading"
                @click="getAIPriceSuggestion"
              >
                🤖 AI Price Analysis
              </n-button>
              
              <n-button 
                block 
                ghost 
                class="h-12 uppercase font-bold italic tracking-widest text-white border-white/20"
                @click="showPreview = true"
              >
                Preview Listing
              </n-button>

              <div class="pt-4 border-t border-white/10">
                <n-button 
                  type="primary" 
                  block 
                  size="large" 
                  class="h-16 text-lg font-black uppercase italic tracking-widest"
                  :loading="loading"
                  @click="handlePublish"
                >
                  Publish Part
                </n-button>
              </div>
            </div>

            <p class="text-[10px] text-center mt-6 opacity-40 font-bold uppercase tracking-widest leading-relaxed">
              By publishing, you agree to Phoenix Auto Parts Seller Terms and Quality Standards.
            </p>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>
