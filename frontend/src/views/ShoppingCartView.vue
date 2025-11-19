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
  useMessage,
} from 'naive-ui'
import api from '../lib/http'

const router = useRouter()
const message = useMessage()

interface CartItem {
  id: number
  item_id: number
  title: string
  price: number
  original_price: number
  seller_name: string
  image_url: string
  condition_type: string
  status: string
  quantity: number
  checked: boolean
}

const cartItems = ref<CartItem[]>([
  {
    id: 1,
    item_id: 101,
    title: 'iPhone 12 Pro 128GB 深空灰',
    price: 3299,
    original_price: 5999,
    seller_name: '张三',
    image_url: '',
    condition_type: 'like_new',
    status: 'available',
    quantity: 1,
    checked: false,
  },
  {
    id: 2,
    item_id: 102,
    title: '苹果 MacBook Air M1',
    price: 5200,
    original_price: 7999,
    seller_name: '李四',
    image_url: '',
    condition_type: 'very_good',
    status: 'available',
    quantity: 1,
    checked: false,
  },
])

const allChecked = computed({
  get: () => cartItems.value.length > 0 && cartItems.value.every(item => item.checked),
  set: (value: boolean) => {
    cartItems.value.forEach(item => {
      item.checked = value
    })
  },
})

const checkedItems = computed(() => cartItems.value.filter(item => item.checked))

const totalPrice = computed(() => {
  return checkedItems.value.reduce((sum, item) => sum + item.price * item.quantity, 0)
})

const totalSavings = computed(() => {
  return checkedItems.value.reduce(
    (sum, item) => sum + (item.original_price - item.price) * item.quantity,
    0
  )
})

const conditionTypeMap: Record<string, string> = {
  brand_new: '全新',
  like_new: '99新',
  very_good: '95新',
  good: '9成新',
  used: '二手',
}

const removeItem = async (id: number) => {
  try {
    // await api.delete(`/api/cart/${id}`)
    const index = cartItems.value.findIndex(item => item.id === id)
    if (index > -1) {
      cartItems.value.splice(index, 1)
      message.success('已从购物车移除')
    }
  } catch (error) {
    message.error('移除失败')
  }
}

const updateQuantity = async (item: CartItem, quantity: number) => {
  if (quantity < 1) {
    message.warning('数量不能小于1')
    return
  }
  item.quantity = quantity
  // TODO: 调用API更新数量
}

const checkout = () => {
  if (checkedItems.value.length === 0) {
    message.warning('请先选择要结算的商品')
    return
  }
  // 注意：这是二手交易平台，应该跳转到联系卖家或约定交易
  router.push({
    name: 'checkout',
    query: { items: checkedItems.value.map(item => item.id).join(',') },
  })
}

const loadCartItems = async () => {
  try {
    // const response = await api.get('/api/cart')
    // cartItems.value = response.data
  } catch (error) {
    message.error('加载购物车失败')
  }
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

      <n-empty v-if="cartItems.length === 0" description="购物车是空的">
        <template #extra>
          <n-button @click="router.push('/marketplace')">去逛逛</n-button>
        </template>
      </n-empty>

      <div v-else>
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
          <div v-for="item in cartItems" :key="item.id" class="cart-item">
            <n-checkbox v-model:checked="item.checked" />

            <div class="item-info">
              <n-image
                :src="item.image_url || 'https://via.placeholder.com/80'"
                width="80"
                height="80"
                object-fit="cover"
                style="border-radius: 4px"
              />
              <div class="item-detail">
                <div class="item-title">{{ item.title }}</div>
                <div class="item-meta">
                  <n-tag size="small" type="info">{{ conditionTypeMap[item.condition_type] }}</n-tag>
                  <span style="margin-left: 8px; color: #666">卖家: {{ item.seller_name }}</span>
                </div>
              </div>
            </div>

            <div class="item-price">
              <div style="color: #f56c6c; font-weight: bold; font-size: 16px">
                ¥{{ item.price.toLocaleString() }}
              </div>
              <div style="color: #999; text-decoration: line-through; font-size: 12px">
                ¥{{ item.original_price.toLocaleString() }}
              </div>
            </div>

            <div class="item-quantity">
              <n-input-number
                v-model:value="item.quantity"
                :min="1"
                :max="1"
                size="small"
                @update:value="(val) => val && updateQuantity(item, val)"
                style="width: 80px"
              />
              <div style="font-size: 12px; color: #999; margin-top: 4px">仅此一件</div>
            </div>

            <div class="item-subtotal">
              <span style="color: #f56c6c; font-weight: bold; font-size: 18px">
                ¥{{ (item.price * item.quantity).toLocaleString() }}
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
            <n-button text type="error" style="margin-left: 16px">删除选中商品</n-button>
          </div>

          <div class="footer-right">
            <div class="price-info">
              <div class="price-row">
                <span>已选商品:</span>
                <span style="font-size: 18px; font-weight: bold">{{ checkedItems.length }} 件</span>
              </div>
              <div class="price-row" v-if="totalSavings > 0">
                <span>已优惠:</span>
                <span style="color: #18a058">-¥{{ totalSavings.toLocaleString() }}</span>
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
</style>
