<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import {
  NCard,
  NSpace,
  NButton,
  NCheckbox,
  NInputNumber,
  NEmpty,
  NImage,
  NTag,
  NDivider,
  NPopconfirm,
  NSpin,
  useMessage,
} from 'naive-ui'
import { http } from '@/lib/http'

const router = useRouter()
const message = useMessage()

// ✅ 与后端 CartItemResponse 匹配的接口
interface CartItem {
  id: number
  item_id: number
  item_title: string
  item_price: number
  item_image: string | null
  item_condition: string | null
  seller_id: number
  seller_name: string
  quantity: number
  subtotal: number
  item_status: string
  added_at: string
  // 前端专用字段
  checked: boolean
}

interface CartSummary {
  items: Omit<CartItem, 'checked'>[]
  total_items: number
  total_quantity: number
  total_price: number
  available_count: number
  unavailable_count: number
}

const cartItems = ref<CartItem[]>([])
const loading = ref(false)

// ✅ 全选逻辑
const allChecked = computed({
  get: () => cartItems.value.length > 0 && cartItems.value.every(item => item.checked),
  set: (value: boolean) => {
    cartItems.value.forEach(item => {
      // 只勾选可购买的零件
      if (item.item_status === 'available') {
        item.checked = value
      }
    })
  },
})

// ✅ 已选零件
const checkedItems = computed(() => cartItems.value.filter(item => item.checked))

// ✅ 总价
const totalPrice = computed(() => {
  return checkedItems.value.reduce((sum, item) => sum + item.item_price * item.quantity, 0)
})

// ✅ 成色映射
const conditionTypeMap: Record<string, string> = {
  new: '全新',
  like_new: '99新',
  good: '良好',
  fair: '一般',
}

// ✅ 加载采购车 - 调用后端 API
const loadCartItems = async () => {
  loading.value = true
  try {
    const response = await http.get<CartSummary>('/cart')
    // 将后端数据转换为前端格式，添加 checked 字段
    cartItems.value = response.data.items.map(item => ({
      ...item,
      checked: false  // 默认不选中
    }))
  } catch (error: any) {
    console.error('加载采购车失败:', error)
    message.error(error.response?.data?.detail || '加载采购车失败')
  } finally {
    loading.value = false
  }
}

// ✅ 删除零件 - 调用后端 API
const removeItem = async (id: number) => {
  try {
    await http.delete(`/cart/${id}`)
    // 从本地列表移除
    const index = cartItems.value.findIndex(item => item.id === id)
    if (index > -1) {
      cartItems.value.splice(index, 1)
    }
    message.success('已从采购车移除')
  } catch (error: any) {
    message.error(error.response?.data?.detail || '移除失败')
  }
}

// ✅ 更新数量 - 调用后端 API
const updateQuantity = async (item: CartItem, quantity: number) => {
  if (quantity < 1) {
    message.warning('数量不能小于1')
    return
  }
  
  try {
    await http.put(`/cart/${item.id}`, { quantity })
    item.quantity = quantity
  } catch (error: any) {
    message.error(error.response?.data?.detail || '更新失败')
  }
}

// ✅ 删除选中零件 - 调用后端 API
const removeCheckedItems = async () => {
  const ids = checkedItems.value.map(item => item.id)
  if (ids.length === 0) {
    message.warning('请先选择要删除的零件')
    return
  }
  
  try {
    await http.post('/cart/batch-delete', { cart_item_ids: ids })
    // 从本地列表移除
    cartItems.value = cartItems.value.filter(item => !item.checked)
    message.success('已删除选中零件')
  } catch (error: any) {
    message.error(error.response?.data?.detail || '删除失败')
  }
}

// ✅ 清空采购车 - 调用后端 API
const clearCart = async () => {
  try {
    await http.delete('/cart')
    cartItems.value = []
    message.success('采购车已清空')
  } catch (error: any) {
    message.error(error.response?.data?.detail || '清空失败')
  }
}

// ✅ 结算/联系卖家
const checkout = async () => {
  if (checkedItems.value.length === 0) {
    message.warning('请先选择要结算的零件')
    return
  }
  
  // 检查是否有不可购买的零件
  const unavailable = checkedItems.value.filter(item => item.item_status !== 'available')
  if (unavailable.length > 0) {
    message.warning('部分零件已下架或已售出，请取消选择后重试')
    return
  }
  
  try {
    // 调用结算预览 API
    const ids = checkedItems.value.map(item => item.id)
    const response = await http.post('/cart/checkout-preview', null, {
      params: { cart_item_ids: ids }
    })
    
    console.log('结算预览:', response.data)
    
    // 跳转到结算页面（或显示结算弹窗）
    router.push({
      path: '/checkout',
      query: { items: ids.join(',') }
    })
  } catch (error: any) {
    message.error(error.response?.data?.detail || '结算失败')
  }
}

// ✅ 跳转到零件详情
const goToItem = (itemId: number) => {
  router.push(`/item/${itemId}`)
}

// ✅ 获取零件图片，没有则使用随机占位图
const getItemImage = (item: any) => {
  if (item.item_image) {
    return item.item_image
  }
  // 使用 picsum.photos 作为占位图，item_id 保证同一零件图片一致
  return `https://picsum.photos/80/80?random=${item.item_id}`
}

onMounted(() => {
  loadCartItems()
})
</script>

<template>
  <div class="shopping-cart min-h-screen bg-[#f4f4f4]">
    <!-- Header Section -->
    <div class="bg-[#2e3235] text-white py-8 mb-8">
      <div class="max-w-7xl mx-auto px-4">
        <h1 class="text-3xl font-black tracking-tighter uppercase italic">
          Procurement <span class="text-primary">Cart</span>
          <span class="block text-sm font-normal tracking-widest mt-1 opacity-60 italic">PHOENIX AUTO PARTS / ORDER PREPARATION</span>
        </h1>
      </div>
    </div>

    <div class="max-w-7xl mx-auto px-4 pb-12">
      <n-spin :show="loading">
        <div v-if="cartItems.length > 0" class="grid grid-cols-1 lg:grid-cols-3 gap-8">
          <!-- Cart Items List -->
          <div class="lg:col-span-2 space-y-4">
            <div class="bg-white border border-gray-200 p-4 flex items-center justify-between mb-4">
              <n-checkbox v-model:checked="allChecked" class="font-bold uppercase tracking-tighter">
                Select All Parts
              </n-checkbox>
              <n-button quaternary type="error" size="small" @click="removeCheckedItems" class="uppercase font-bold italic">
                Remove Selected
              </n-button>
            </div>

            <div v-for="item in cartItems" :key="item.id" 
                 class="bg-white border border-gray-200 p-4 flex gap-6 items-center group hover:border-primary transition-colors">
              <n-checkbox v-model:checked="item.checked" :disabled="item.item_status !== 'available'" />
              
              <div class="w-32 h-32 bg-gray-100 overflow-hidden flex-shrink-0 border border-gray-100">
                <img :src="getItemImage(item)" class="w-full h-full object-cover group-hover:scale-105 transition-transform duration-500" />
              </div>

              <div class="flex-1 min-w-0">
                <div class="flex justify-between items-start mb-2">
                  <div>
                    <div class="text-[10px] font-bold text-primary uppercase tracking-widest mb-1">Seller: {{ item.seller_name }}</div>
                    <h3 class="font-black text-lg uppercase italic truncate cursor-pointer hover:text-primary transition-colors" @click="goToItem(item.item_id)">
                      {{ item.item_title }}
                    </h3>
                  </div>
                  <n-button quaternary circle type="error" @click="removeItem(item.id)">
                    <template #icon>🗑️</template>
                  </n-button>
                </div>

                <div class="flex items-center justify-between mt-4">
                  <div class="flex items-baseline gap-2">
                    <span class="text-2xl font-black text-[#2e3235]">¥{{ item.item_price }}</span>
                    <span v-if="item.item_status !== 'available'" class="text-xs font-bold text-red-500 uppercase tracking-tighter bg-red-50 px-2 py-0.5 border border-red-100">
                      Unavailable
                    </span>
                  </div>
                  
                  <div class="flex items-center gap-4">
                    <n-input-number 
                      v-model:value="item.quantity" 
                      :min="1" 
                      size="small"
                      @update:value="(val) => updateQuantity(item, val || 1)"
                      class="w-24"
                    />
                  </div>
                </div>
              </div>
            </div>
          </div>

          <!-- Order Summary -->
          <div class="lg:col-span-1">
            <div class="bg-[#2e3235] text-white p-6 sticky top-24">
              <h2 class="text-xl font-black uppercase italic tracking-tighter mb-6 border-b border-white/10 pb-4">
                Order <span class="text-primary">Summary</span>
              </h2>
              
              <div class="space-y-4 mb-8">
                <div class="flex justify-between text-sm font-bold uppercase tracking-widest opacity-60">
                  <span>Selected Parts</span>
                  <span>{{ checkedItems.length }}</span>
                </div>
                <div class="flex justify-between text-sm font-bold uppercase tracking-widest opacity-60">
                  <span>Total Quantity</span>
                  <span>{{ checkedItems.reduce((s, i) => s + i.quantity, 0) }}</span>
                </div>
                <div class="pt-4 border-t border-white/10 flex justify-between items-baseline">
                  <span class="text-lg font-black uppercase italic">Total</span>
                  <span class="text-3xl font-black text-primary">¥{{ totalPrice.toFixed(2) }}</span>
                </div>
              </div>

              <n-button 
                type="primary" 
                block 
                size="large" 
                class="h-14 text-lg font-black uppercase italic tracking-widest"
                :disabled="checkedItems.length === 0"
                @click="checkout"
              >
                Proceed to Checkout
              </n-button>
              
              <p class="text-[10px] text-center mt-4 opacity-40 font-bold uppercase tracking-widest">
                Secure Procurement / Phoenix Logistics
              </p>
            </div>
          </div>
        </div>

        <div v-else class="bg-white border border-gray-200 py-24 text-center">
          <div class="text-6xl mb-6 opacity-20">🛒</div>
          <h2 class="text-2xl font-black uppercase italic tracking-widest text-gray-400 mb-6">Your cart is empty</h2>
          <n-button type="primary" size="large" class="uppercase font-bold italic" @click="router.push('/marketplace')">
            Browse Parts Catalog
          </n-button>
        </div>
      </n-spin>
    </div>
  </div>
</template>

<style scoped>
.shopping-cart {
  max-width: 1200px;
  margin: 0 auto;
  padding: 24px;
}

.cart-header {
  display: flex;
  align-items: center;
  gap: 24px;
  padding: 12px 16px;
  background: #fafafa;
  border-radius: 4px;
  font-weight: 500;
}

.cart-items {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.cart-item {
  display: flex;
  align-items: center;
  gap: 24px;
  padding: 16px;
  border: 1px solid #e0e0e6;
  border-radius: 4px;
  transition: all 0.3s;
}

.cart-item:hover {
  border-color: #18a058;
  box-shadow: 0 2px 8px rgba(24, 160, 88, 0.1);
}

/* ✅ 不可购买零件的样式 */
.cart-item.unavailable {
  opacity: 0.6;
  background: #f5f5f5;
}

.cart-item.unavailable:hover {
  border-color: #e0e0e6;
  box-shadow: none;
}

.item-info {
  flex: 1;
  display: flex;
  gap: 16px;
  align-items: center;
}

.item-detail {
  flex: 1;
}

.item-title {
  font-size: 16px;
  font-weight: 500;
  margin-bottom: 8px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.item-meta {
  display: flex;
  align-items: center;
  font-size: 14px;
  flex-wrap: wrap;
  gap: 4px;
}

.item-price {
  width: 120px;
  text-align: center;
}

.item-quantity {
  width: 100px;
  display: flex;
  flex-direction: column;
  align-items: center;
}

.item-subtotal {
  width: 120px;
  text-align: center;
}

.item-actions {
  width: 80px;
  text-align: center;
}

.cart-footer {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px;
  background: #fafafa;
  border-radius: 4px;
}

.footer-left {
  display: flex;
  align-items: center;
}

.footer-right {
  display: flex;
  align-items: center;
}

.price-info {
  display: flex;
  flex-direction: column;
  gap: 8px;
  text-align: right;
}

.price-row {
  display: flex;
  justify-content: space-between;
  gap: 16px;
  font-size: 14px;
}

.price-row.total {
  font-size: 16px;
  font-weight: bold;
  margin-top: 8px;
  padding-top: 8px;
  border-top: 1px solid #e0e0e6;
}

.total-price {
  color: #f56c6c;
  font-size: 24px;
}

.item-image-wrapper {
  width: 80px;
  height: 80px;
  flex-shrink: 0;
}

.item-placeholder {
  width: 80px;
  height: 80px;
  flex-shrink: 0;
  background: linear-gradient(135deg, #f0f9ff 0%, #e0f2fe 100%);
  border-radius: 4px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.placeholder-icon {
  font-size: 32px;
}

/* 新增样式 */
.bg-primary {
  background-color: #18a058;
}

.text-primary {
  color: #18a058;
}

.uppercase {
  text-transform: uppercase;
}

.italic {
  font-style: italic;
}

.tracking-tighter {
  letter-spacing: -0.02em;
}

.tracking-widest {
  letter-spacing: 0.1em;
}

.font-black {
  font-weight: 900;
}

.font-bold {
  font-weight: 700;
}

.font-normal {
  font-weight: 400;
}

.text-sm {
  font-size: 0.875rem;
}

.text-xs {
  font-size: 0.75rem;
}

.text-lg {
  font-size: 1.125rem;
}

.text-2xl {
  font-size: 1.5rem;
}

.text-3xl {
  font-size: 1.875rem;
}

.leading-tight {
  line-height: 1.2;
}

.leading-snug {
  line-height: 1.375;
}

.py-8 {
  padding-top: 2rem;
  padding-bottom: 2rem;
}

.mb-8 {
  margin-bottom: 2rem;
}

.px-4 {
  padding-left: 1rem;
  padding-right: 1rem;
}

.pt-4 {
  padding-top: 1rem;
}

.pb-4 {
  padding-bottom: 1rem;
}

.border-b {
  border-bottom-width: 1px;
}

.border-t {
  border-top-width: 1px;
}

.border-primary {
  border-color: #18a058;
}

.hover\:border-primary:hover {
  border-color: #18a058;
}

.transition-colors {
  transition-property: color, background-color, border-color;
}

.transition-transform {
  transition-property: transform;
}

.duration-500 {
  transition-duration: 500ms;
}

.sticky {
  position: -webkit-sticky;
  position: sticky;
  top: 0;
}

.group {
  position: relative;
}

.group-hover\:scale-105:hover {
  transform: scale(1.05);
}

.group-hover\:rotate-3:hover {
  transform: rotate(3deg);
}

.rotate-3 {
  transform: rotate(3deg);
}

.scale-105 {
  transform: scale(1.05);
}

.scale-110 {
  transform: scale(1.1);
}

.cursor-pointer {
  cursor: pointer;
}

.overflow-hidden {
  overflow: hidden;
}

.overflow-auto {
  overflow: auto;
}

.overflow-scroll {
  overflow: scroll;
}

.overscroll-auto {
  overscroll-behavior: auto;
}

.overscroll-contain {
  overscroll-behavior: contain;
}

.overscroll-none {
  overscroll-behavior: none;
}

.min-h-screen {
  min-height: 100vh;
}

.h-14 {
  height: 3.5rem;
}

.w-24 {
  width: 6rem;
}

.max-w-7xl {
  max-width: 80rem;
}

.mx-auto {
  margin-left: auto;
  margin-right: auto;
}

.text-center {
  text-align: center;
}

.text-right {
  text-align: right;
}

.flex {
  display: flex;
}

.inline-flex {
  display: inline-flex;
}

.block {
  display: block;
}

.hidden {
  display: none;
}

.items-center {
  align-items: center;
}

.items-start {
  align-items: flex-start;
}

.items-end {
  align-items: flex-end;
}

.justify-center {
  justify-content: center;
}

.justify-start {
  justify-content: flex-start;
}

.justify-end {
  justify-content: flex-end;
}

.gap-4 {
  gap: 1rem;
}

.gap-6 {
  gap: 1.5rem;
}

.space-y-4 > :not(template) ~ :not(template) {
  margin-top: 1rem;
}

.space-y-8 > :not(template) ~ :not(template) {
  margin-top: 2rem;
}

.border {
  border-width: 1px;
}

.rounded {
  border-radius: 0.375rem;
}

.rounded-md {
  border-radius: 0.375rem;
}

.rounded-lg {
  border-radius: 0.5rem;
}

.rounded-full {
  border-radius: 9999px;
}

.shadow {
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
}

.shadow-md {
  box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
}

.shadow-lg {
  box-shadow: 0 10px 15px rgba(0, 0, 0, 0.1);
}

.opacity-40 {
  opacity: 0.4;
}

.opacity-60 {
  opacity: 0.6;
}

.cursor-not-allowed {
  cursor: not-allowed;
}

.pointer-events-none {
  pointer-events: none;
}

.list-none {
  list-style-type: none;
}

.preline {
  white-space: pre-line;
}

.break-words {
  overflow-wrap: break-word;
}

.truncate {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.text-ellipsis {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.leading-relaxed {
  line-height: 1.625;
}

.leading-loose {
  line-height: 2;
}

.text-red-500 {
  color: #f56565;
}

.bg-red-50 {
  background-color: #fef2f2;
}

.border-red-100 {
  border-color: #fed7d7;
}

.text-green-500 {
  color: #48bb78;
}

.bg-green-50 {
  background-color: #f0fff4;
}

.border-green-100 {
  border-color: #c6f6d5;
}

.text-blue-500 {
  color: #4299e1;
}

.bg-blue-50 {
  background-color: #ebf8ff;
}

.border-blue-100 {
  border-color: #bee3f8;
}

.text-yellow-500 {
  color: #ecc94b;
}

.bg-yellow-50 {
  background-color: #fefcbf;
}

.border-yellow-100 {
  border-color: #fefcbf;
}
</style>
