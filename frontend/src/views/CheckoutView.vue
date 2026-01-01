<template>
  <div class="checkout-view min-h-screen bg-[#f4f4f4]">
    <!-- Header Section -->
    <div class="bg-[#2e3235] text-white py-8 mb-8">
      <div class="max-w-4xl mx-auto px-4">
        <h1 class="text-3xl font-black tracking-tighter uppercase italic">
          Order <span class="text-primary">Confirmation</span>
          <span class="block text-sm font-normal tracking-widest mt-1 opacity-60 italic">PHOENIX AUTO PARTS / FINAL REVIEW</span>
        </h1>
      </div>
    </div>

    <div class="max-w-4xl mx-auto px-4 pb-12">
      <n-spin :show="loading">
        <div v-if="checkoutItems.length > 0" class="space-y-8">
          <!-- Delivery Information -->
          <div class="bg-white border border-gray-200 p-8">
            <h2 class="text-xl font-black uppercase italic tracking-tighter mb-6 flex items-center gap-2">
              <span class="w-2 h-6 bg-primary"></span>
              Logistics Information
            </h2>
            <n-form ref="formRef" :model="deliveryForm" :rules="deliveryRules" label-placement="top">
              <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
                <n-form-item label="RECEIVER NAME" path="receiver_name" class="font-bold tracking-widest text-[10px]">
                  <n-input v-model:value="deliveryForm.receiver_name" placeholder="Enter name" class="uppercase" />
                </n-form-item>
                <n-form-item label="CONTACT PHONE" path="receiver_phone" class="font-bold tracking-widest text-[10px]">
                  <n-input v-model:value="deliveryForm.receiver_phone" placeholder="Enter phone number" />
                </n-form-item>
              </div>
              <n-form-item label="DELIVERY ADDRESS" path="receiver_address" class="font-bold tracking-widest text-[10px]">
                <n-input 
                  v-model:value="deliveryForm.receiver_address" 
                  type="textarea"
                  placeholder="Enter full delivery address"
                  :autosize="{ minRows: 2, maxRows: 4 }"
                />
              </n-form-item>
            </n-form>
          </div>

          <!-- Parts Review -->
          <div class="bg-white border border-gray-200 p-8">
            <h2 class="text-xl font-black uppercase italic tracking-tighter mb-6 flex items-center gap-2">
              <span class="w-2 h-6 bg-primary"></span>
              Parts Review
            </h2>
            <div class="divide-y divide-gray-100">
              <div v-for="item in checkoutItems" :key="item.item_id" class="py-4 flex gap-6 items-center">
                <div class="w-20 h-20 bg-gray-100 flex-shrink-0 border border-gray-100">
                  <img v-if="item.item_image" :src="item.item_image" class="w-full h-full object-cover" />
                  <div v-else class="w-full h-full flex items-center justify-center text-2xl opacity-20">📦</div>
                </div>
                <div class="flex-1 min-w-0">
                  <div class="text-[10px] font-bold text-primary uppercase tracking-widest mb-1">Seller: {{ item.seller_name }}</div>
                  <h3 class="font-black text-base uppercase italic truncate">{{ item.item_title }}</h3>
                  <div class="flex justify-between items-baseline mt-2">
                    <span class="text-lg font-black text-[#2e3235]">¥{{ item.item_price }}</span>
                    <span class="text-sm font-bold text-gray-400 uppercase tracking-tighter">Qty: {{ item.quantity }}</span>
                  </div>
                </div>
              </div>
            </div>
          </div>

          <!-- Final Summary -->
          <div class="bg-[#2e3235] text-white p-8">
            <div class="flex flex-col md:flex-row justify-between items-center gap-6">
              <div class="text-center md:text-left">
                <div class="text-[10px] font-bold uppercase tracking-widest opacity-60 mb-1">Total Procurement Amount</div>
                <div class="text-4xl font-black text-primary italic">¥{{ totalAmount.toFixed(2) }}</div>
              </div>
              <div class="flex gap-4 w-full md:w-auto">
                <n-button size="large" ghost @click="router.back()" class="flex-1 md:flex-none uppercase font-bold italic">
                  Back
                </n-button>
                <n-button type="primary" size="large" class="flex-1 md:flex-none h-14 px-12 text-lg font-black uppercase italic tracking-widest" @click="createOrders">
                  Confirm Order
                </n-button>
              </div>
            </div>
          </div>
        </div>

        <div v-else class="bg-white border border-gray-200 py-24 text-center">
          <h2 class="text-2xl font-black uppercase italic tracking-widest text-gray-400 mb-6">No items to checkout</h2>
          <n-button type="primary" size="large" class="uppercase font-bold italic" @click="router.push('/marketplace')">
            Return to Marketplace
          </n-button>
        </div>
      </n-spin>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useMessage, type FormRules, type FormInst } from 'naive-ui'
import { http } from '@/lib/http'

const router = useRouter()
const route = useRoute()
const message = useMessage()

const loading = ref(true)
const checkoutItems = ref<any[]>([])
const formRef = ref<FormInst | null>(null)

// 收货信息表单
const deliveryForm = ref({
  receiver_name: '',
  receiver_phone: '',
  receiver_address: ''
})

// 表单验证规则
const deliveryRules: FormRules = {
  receiver_name: [
    { required: true, message: '请输入收货人姓名', trigger: 'blur' }
  ],
  receiver_phone: [
    { required: true, message: '请输入联系电话', trigger: 'blur' },
    { pattern: /^1[3-9]\d{9}$/, message: '请输入正确的手机号', trigger: 'blur' }
  ],
  receiver_address: [
    { required: true, message: '请输入收货地址', trigger: 'blur' },
    { min: 5, message: '地址至少5个字符', trigger: 'blur' }
  ]
}

// 计算总数量和总金额
const totalQuantity = computed(() => 
  checkoutItems.value.reduce((sum, item) => sum + item.quantity, 0)
)

const totalAmount = computed(() => 
  checkoutItems.value.reduce((sum, item) => sum + item.item_price * item.quantity, 0)
)

// 获取唯一卖家列表
const uniqueSellers = computed(() => {
  const sellerMap = new Map()
  checkoutItems.value.forEach(item => {
    if (!sellerMap.has(item.seller_id)) {
      sellerMap.set(item.seller_id, {
        id: item.seller_id,
        name: item.seller_name
      })
    }
  })
  return Array.from(sellerMap.values())
})

// 加载结算零件
const loadCheckoutItems = async () => {
  try {
    const itemIds = route.query.items?.toString().split(',').map(Number) || []
    if (itemIds.length === 0) {
      loading.value = false
      return
    }
    
    // 从采购车获取零件详情
    const response = await http.get('/cart')
    const allItems = response.data.items || []
    checkoutItems.value = allItems.filter((item: any) => itemIds.includes(item.id))
  } catch (error: any) {
    message.error('加载失败: ' + (error.response?.data?.detail || error.message))
  } finally {
    loading.value = false
  }
}

// 联系卖家
const contactSeller = (seller: any) => {
  router.push({
    path: '/messages',
    query: { to: seller.id, name: seller.name }
  })
}

// 创建订单
const createOrders = async () => {
  try {
    // 验证表单
    await formRef.value?.validate()
    
    // 为每个零件创建订单
    for (const item of checkoutItems.value) {
      await http.post('/orders', {
        item_id: item.item_id,
        quantity: item.quantity
      })
    }
    
    message.success('订单创建成功！')
    router.push('/orders')
  } catch (error: any) {
    message.error('创建订单失败: ' + (error.response?.data?.detail || error.message))
  }
}

onMounted(() => {
  loadCheckoutItems()
})
</script>

<style scoped>
.checkout-view {
  padding-bottom: 80px;
}
</style>
