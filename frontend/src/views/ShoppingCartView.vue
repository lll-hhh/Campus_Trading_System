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
      // 只勾选可购买的商品
      if (item.item_status === 'available') {
        item.checked = value
      }
    })
  },
})

// ✅ 已选商品
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

// ✅ 加载购物车 - 调用后端 API
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
    console.error('加载购物车失败:', error)
    message.error(error.response?.data?.detail || '加载购物车失败')
  } finally {
    loading.value = false
  }
}

// ✅ 删除商品 - 调用后端 API
const removeItem = async (id: number) => {
  try {
    await http.delete(`/cart/${id}`)
    // 从本地列表移除
    const index = cartItems.value.findIndex(item => item.id === id)
    if (index > -1) {
      cartItems.value.splice(index, 1)
    }
    message.success('已从购物车移除')
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

// ✅ 删除选中商品 - 调用后端 API
const removeCheckedItems = async () => {
  const ids = checkedItems.value.map(item => item.id)
  if (ids.length === 0) {
    message.warning('请先选择要删除的商品')
    return
  }
  
  try {
    await http.post('/cart/batch-delete', { cart_item_ids: ids })
    // 从本地列表移除
    cartItems.value = cartItems.value.filter(item => !item.checked)
    message.success('已删除选中商品')
  } catch (error: any) {
    message.error(error.response?.data?.detail || '删除失败')
  }
}

// ✅ 清空购物车 - 调用后端 API
const clearCart = async () => {
  try {
    await http.delete('/cart')
    cartItems.value = []
    message.success('购物车已清空')
  } catch (error: any) {
    message.error(error.response?.data?.detail || '清空失败')
  }
}

// ✅ 结算/联系卖家
const checkout = async () => {
  if (checkedItems.value.length === 0) {
    message.warning('请先选择要结算的商品')
    return
  }
  
  // 检查是否有不可购买的商品
  const unavailable = checkedItems.value.filter(item => item.item_status !== 'available')
  if (unavailable.length > 0) {
    message.warning('部分商品已下架或已售出，请取消选择后重试')
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

// ✅ 跳转到商品详情
const goToItem = (itemId: number) => {
  router.push(`/item/${itemId}`)
}

// ✅ 获取商品图片，没有则使用随机占位图
const getItemImage = (item: any) => {
  if (item.item_image) {
    return item.item_image
  }
  // 使用 picsum.photos 作为占位图，item_id 保证同一商品图片一致
  return `https://picsum.photos/80/80?random=${item.item_id}`
}

onMounted(() => {
  loadCartItems()
})
</script>

<template>
  <div class="cart-page">
    <n-card title="购物车">
      <template #header-extra>
        <n-space>
          <span style="color: #666">共 {{ cartItems.length }} 件商品</span>
        </n-space>
      </template>

      <!-- 加载状态 -->
      <n-spin :show="loading">
        <n-empty v-if="!loading && cartItems.length === 0" description="购物车是空的">
          <template #extra>
            <n-button @click="router.push('/marketplace')">去逛逛</n-button>
          </template>
        </n-empty>

        <div v-else-if="cartItems.length > 0">
          <!-- 全选 -->
          <div class="cart-header">
            <n-checkbox v-model:checked="allChecked">全选</n-checkbox>
            <span style="margin-left: auto">商品信息</span>
            <span style="width: 120px; text-align: center">单价</span>
            <span style="width: 100px; text-align: center">数量</span>
            <span style="width: 120px; text-align: center">小计</span>
            <span style="width: 80px; text-align: center">操作</span>
          </div>

          <n-divider style="margin: 12px 0" />

          <!-- 商品列表 -->
          <div class="cart-items">
            <div 
              v-for="item in cartItems" 
              :key="item.id" 
              class="cart-item"
              :class="{ 'unavailable': item.item_status !== 'available' }"
            >
              <n-checkbox 
                v-model:checked="item.checked" 
                :disabled="item.item_status !== 'available'"
              />

              <div class="item-info" @click="goToItem(item.item_id)" style="cursor: pointer;">
                <n-image
                  :src="getItemImage(item)"
                  width="80"
                  height="80"
                  object-fit="cover"
                  style="border-radius: 4px"
                  preview-disabled
                />
                <div class="item-detail">
                  <div class="item-title">{{ item.item_title }}</div>
                  <div class="item-meta">
                    <n-tag v-if="item.item_condition" size="small" type="info">
                      {{ conditionTypeMap[item.item_condition] || item.item_condition }}
                    </n-tag>
                    <span style="margin-left: 8px; color: #666">卖家: {{ item.seller_name }}</span>
                    <!-- 商品状态标签 -->
                    <n-tag 
                      v-if="item.item_status !== 'available'" 
                      size="small" 
                      type="error"
                      style="margin-left: 8px"
                    >
                      {{ item.item_status === 'sold' ? '已售出' : '已下架' }}
                    </n-tag>
                  </div>
                </div>
              </div>

              <div class="item-price">
                <div style="color: #f56c6c; font-weight: bold; font-size: 16px">
                  ¥{{ item.item_price.toLocaleString() }}
                </div>
              </div>

              <div class="item-quantity">
                <n-input-number
                  v-model:value="item.quantity"
                  :min="1"
                  :max="99"
                  size="small"
                  :disabled="item.item_status !== 'available'"
                  @update:value="(val) => val && updateQuantity(item, val)"
                  style="width: 80px"
                />
              </div>

              <div class="item-subtotal">
                <span style="color: #f56c6c; font-weight: bold; font-size: 18px">
                  ¥{{ (item.item_price * item.quantity).toLocaleString() }}
                </span>
              </div>

              <div class="item-actions">
                <n-popconfirm @positive-click="removeItem(item.id)">
                  <template #trigger>
                    <n-button text type="error">删除</n-button>
                  </template>
                  确定要从购物车移除此商品吗？
                </n-popconfirm>
              </div>
            </div>
          </div>

          <n-divider style="margin: 24px 0" />

          <!-- 结算区域 -->
          <div class="cart-footer">
            <div class="footer-left">
              <n-checkbox v-model:checked="allChecked">全选</n-checkbox>
              <n-button text type="error" style="margin-left: 16px" @click="removeCheckedItems">
                删除选中商品
              </n-button>
              <n-popconfirm @positive-click="clearCart">
                <template #trigger>
                  <n-button text type="warning" style="margin-left: 16px">清空购物车</n-button>
                </template>
                确定要清空购物车吗？
              </n-popconfirm>
            </div>

            <div class="footer-right">
              <div class="price-info">
                <div class="price-row">
                  <span>已选商品:</span>
                  <span style="font-size: 18px; font-weight: bold">{{ checkedItems.length }} 件</span>
                </div>
                <div class="price-row total">
                  <span>合计:</span>
                  <span class="total-price">¥{{ totalPrice.toLocaleString() }}</span>
                </div>
              </div>

              <n-button
                type="primary"
                size="large"
                :disabled="checkedItems.length === 0"
                @click="checkout"
                style="margin-left: 24px"
              >
                联系卖家 ({{ checkedItems.length }})
              </n-button>
            </div>
          </div>
        </div>
      </n-spin>
    </n-card>

    <!-- 温馨提示 -->
    <n-card title="温馨提示" size="small" style="margin-top: 24px">
      <ul style="color: #666; line-height: 1.8">
        <li>这是校园二手交易平台，所有交易均为线下当面交易</li>
        <li>点击"联系卖家"后，系统将为您提供卖家联系方式</li>
        <li>请务必当面验货后再付款，切勿提前转账</li>
        <li>交易时请注意个人财物安全，建议在公共场所进行交易</li>
        <li>如遇可疑情况，请及时联系平台管理员</li>
      </ul>
    </n-card>
  </div>
</template>

<style scoped>
.cart-page {
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

/* ✅ 不可购买商品的样式 */
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
</style>
