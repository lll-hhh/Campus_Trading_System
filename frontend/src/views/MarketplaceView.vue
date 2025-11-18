<template>
  <div class="marketplace min-h-screen bg-gray-50">
    <!-- 顶部搜索栏 -->
    <div class="bg-white shadow-sm sticky top-0 z-10">
      <div class="max-w-7xl mx-auto px-4 py-4">
        <div class="flex items-center gap-4">
          <n-input
            v-model:value="searchKeyword"
            placeholder="搜索商品、卖家..."
            size="large"
            clearable
            @keyup.enter="handleSearch"
          >
            <template #prefix>
              <span class="text-xl">🔍</span>
            </template>
          </n-input>
          <n-button type="primary" size="large" @click="handleSearch">
            搜索
          </n-button>
          <n-button size="large" @click="showPublishModal = true" type="success">
            📤 发布商品
          </n-button>
        </div>
        
        <!-- 分类导航 -->
        <div class="flex gap-3 mt-4 overflow-x-auto">
          <n-tag
            v-for="cat in categories"
            :key="cat.id"
            :type="selectedCategory === cat.id ? 'primary' : 'default'"
            :bordered="false"
            size="large"
            class="cursor-pointer"
            @click="selectedCategory = cat.id"
          >
            {{ cat.icon }} {{ cat.name }}
          </n-tag>
        </div>
      </div>
    </div>

    <!-- 商品列表 -->
    <div class="max-w-7xl mx-auto px-4 py-6">
      <div class="grid grid-cols-1 md:grid-cols-3 lg:grid-cols-4 gap-4">
        <n-card
          v-for="item in displayedItems"
          :key="item.id"
          hoverable
          class="cursor-pointer transition-transform hover:scale-105"
          @click="viewItemDetail(item)"
        >
          <!-- 商品图片 -->
          <div class="aspect-square bg-gradient-to-br from-blue-100 to-purple-100 rounded-lg mb-3 flex items-center justify-center overflow-hidden">
            <img v-if="item.image" :src="item.image" :alt="item.name" class="w-full h-full object-cover" />
            <span v-else class="text-6xl">{{ item.emoji }}</span>
          </div>
          
          <!-- 商品信息 -->
          <div>
            <h3 class="font-bold text-lg mb-2 truncate">{{ item.name }}</h3>
            <p class="text-gray-600 text-sm mb-3 line-clamp-2">{{ item.description }}</p>
            
            <div class="flex items-center justify-between">
              <span class="text-red-500 font-bold text-xl">¥{{ item.price }}</span>
              <n-tag :type="item.condition === 'new' ? 'success' : 'warning'" size="small">
                {{ item.condition === 'new' ? '全新' : '二手' }}
              </n-tag>
            </div>
            
            <div class="flex items-center justify-between mt-3 text-sm text-gray-500">
              <span>👤 {{ item.seller }}</span>
              <span>👁️ {{ item.views }}</span>
            </div>
          </div>
        </n-card>
      </div>

      <!-- 加载更多 -->
      <div class="text-center mt-6" v-if="hasMore">
        <n-button @click="loadMore" size="large">加载更多</n-button>
      </div>
    </div>

    <!-- 发布商品对话框 -->
    <n-modal v-model:show="showPublishModal" preset="card" title="📤 发布商品" style="width: 600px">
      <n-form :model="newItem" label-placement="left" label-width="80">
        <n-form-item label="商品名称">
          <n-input v-model:value="newItem.name" placeholder="例如：二手自行车" />
        </n-form-item>
        
        <n-form-item label="分类">
          <n-select v-model:value="newItem.category_id" :options="categoryOptions" />
        </n-form-item>
        
        <n-form-item label="价格">
          <n-input-number v-model:value="newItem.price" :min="0" :precision="2" style="width: 100%">
            <template #prefix>¥</template>
          </n-input-number>
        </n-form-item>
        
        <n-form-item label="成色">
          <n-radio-group v-model:value="newItem.condition">
            <n-radio value="new">全新</n-radio>
            <n-radio value="used">二手</n-radio>
          </n-radio-group>
        </n-form-item>
        
        <n-form-item label="商品描述">
          <n-input
            v-model:value="newItem.description"
            type="textarea"
            placeholder="详细描述商品的状况、购买时间、使用情况等..."
            :rows="4"
          />
        </n-form-item>
        
        <n-form-item label="联系方式">
          <n-input v-model:value="newItem.contact" placeholder="微信、QQ或手机号" />
        </n-form-item>
        
        <n-form-item label="上传图片">
          <n-upload
            :max="5"
            list-type="image-card"
            accept="image/*"
          >
            点击上传
          </n-upload>
        </n-form-item>
      </n-form>
      
      <template #footer>
        <div class="flex justify-end gap-2">
          <n-button @click="showPublishModal = false">取消</n-button>
          <n-button type="primary" @click="handlePublish">发布</n-button>
        </div>
      </template>
    </n-modal>

    <!-- 商品详情对话框 -->
    <n-modal v-model:show="showDetailModal" preset="card" :title="currentItem?.name" style="width: 800px">
      <div v-if="currentItem" class="grid grid-cols-2 gap-6">
        <!-- 左侧图片 -->
        <div>
          <div class="aspect-square bg-gradient-to-br from-blue-100 to-purple-100 rounded-lg flex items-center justify-center mb-4">
            <span class="text-9xl">{{ currentItem.emoji }}</span>
          </div>
          <div class="flex gap-2">
            <div v-for="i in 4" :key="i" class="w-20 h-20 bg-gray-200 rounded cursor-pointer"></div>
          </div>
        </div>
        
        <!-- 右侧信息 -->
        <div>
          <div class="mb-4">
            <span class="text-red-500 font-bold text-3xl">¥{{ currentItem.price }}</span>
            <n-tag :type="currentItem.condition === 'new' ? 'success' : 'warning'" class="ml-2">
              {{ currentItem.condition === 'new' ? '全新' : '二手' }}
            </n-tag>
          </div>
          
          <n-divider />
          
          <div class="space-y-3 text-gray-700">
            <div class="flex items-start">
              <span class="font-bold w-20">描述:</span>
              <span>{{ currentItem.description }}</span>
            </div>
            <div class="flex items-center">
              <span class="font-bold w-20">卖家:</span>
              <span>{{ currentItem.seller }}</span>
            </div>
            <div class="flex items-center">
              <span class="font-bold w-20">浏览量:</span>
              <span>{{ currentItem.views }} 次</span>
            </div>
            <div class="flex items-center">
              <span class="font-bold w-20">发布时间:</span>
              <span>2小时前</span>
            </div>
          </div>
          
          <n-divider />
          
          <div class="flex gap-2">
            <n-button type="primary" size="large" block>
              💬 联系卖家
            </n-button>
            <n-button size="large" block>
              ❤️ 收藏
            </n-button>
          </div>
          
          <n-alert type="info" class="mt-4">
            <template #icon>
              <span class="text-xl">💡</span>
            </template>
            <div class="text-sm">
              <p class="font-bold mb-1">交易提示</p>
              <ul class="list-disc list-inside space-y-1">
                <li>建议当面交易，验货后付款</li>
                <li>警惕过低价格，谨防诈骗</li>
                <li>保留聊天记录作为凭证</li>
              </ul>
            </div>
          </n-alert>
        </div>
      </div>
    </n-modal>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue';
import { NInput, NButton, NCard, NTag, NModal, NForm, NFormItem, NSelect, NInputNumber, NRadioGroup, NRadio, NUpload, NDivider, NAlert, useMessage } from 'naive-ui';

const message = useMessage();

// 搜索关键词
const searchKeyword = ref('');
const selectedCategory = ref<number | null>(null);

// 分类数据
const categories = ref([
  { id: null, name: '全部', icon: '🏪' },
  { id: 1, name: '电子产品', icon: '📱' },
  { id: 2, name: '图书教材', icon: '📚' },
  { id: 3, name: '生活用品', icon: '🛋️' },
  { id: 4, name: '运动器材', icon: '⚽' },
  { id: 5, name: '服装鞋包', icon: '👔' },
  { id: 6, name: '美妆护肤', icon: '💄' },
  { id: 7, name: '其他', icon: '📦' }
]);

const categoryOptions = computed(() => 
  categories.value.filter(c => c.id !== null).map(c => ({
    label: `${c.icon} ${c.name}`,
    value: c.id
  }))
);

// 商品列表
const items = ref([
  { id: 1, name: 'iPhone 13 Pro', description: '99新，用了3个月，无磕碰，带原装充电器', price: 4999, category_id: 1, condition: 'used', seller: '张三', views: 234, emoji: '📱' },
  { id: 2, name: '高等数学教材', description: '同济版第七版，笔记齐全，无破损', price: 25, category_id: 2, condition: 'used', seller: '李四', views: 89, emoji: '📚' },
  { id: 3, name: '山地自行车', description: '捷安特，9成新，刚换轮胎，骑行流畅', price: 800, category_id: 4, condition: 'used', seller: '王五', views: 156, emoji: '🚲' },
  { id: 4, name: '电竞显示器', description: '27寸2K 144Hz，完美屏，包装齐全', price: 1200, category_id: 1, condition: 'new', seller: '赵六', views: 312, emoji: '🖥️' },
  { id: 5, name: '羽毛球拍', description: '尤尼克斯，全新未拆封，送球和包', price: 380, category_id: 4, condition: 'new', seller: '钱七', views: 67, emoji: '🏸' },
  { id: 6, name: '小米台灯', description: '护眼台灯，调光无频闪，功能完好', price: 80, category_id: 3, condition: 'used', seller: '孙八', views: 145, emoji: '💡' },
  { id: 7, name: '机械键盘', description: '樱桃青轴，RGB背光，手感极佳', price: 450, category_id: 1, condition: 'used', seller: '周九', views: 201, emoji: '⌨️' },
  { id: 8, name: '耐克运动鞋', description: 'Air Max 270，42码，穿过2次', price: 320, category_id: 5, condition: 'new', seller: '吴十', views: 178, emoji: '👟' },
]);

// 显示的商品
const displayedItems = computed(() => {
  let filtered = items.value;
  
  if (selectedCategory.value !== null) {
    filtered = filtered.filter(item => item.category_id === selectedCategory.value);
  }
  
  if (searchKeyword.value) {
    const keyword = searchKeyword.value.toLowerCase();
    filtered = filtered.filter(item => 
      item.name.toLowerCase().includes(keyword) || 
      item.description.toLowerCase().includes(keyword)
    );
  }
  
  return filtered;
});

const hasMore = ref(false);

// 发布商品
const showPublishModal = ref(false);
const newItem = ref({
  name: '',
  category_id: null,
  price: 0,
  condition: 'used',
  description: '',
  contact: ''
});

const handlePublish = () => {
  if (!newItem.value.name || !newItem.value.category_id) {
    message.warning('请填写完整信息');
    return;
  }
  
  message.success('发布成功!商品正在审核中');
  showPublishModal.value = false;
  
  // 重置表单
  newItem.value = {
    name: '',
    category_id: null,
    price: 0,
    condition: 'used',
    description: '',
    contact: ''
  };
};

// 商品详情
const showDetailModal = ref(false);
const currentItem = ref<any>(null);

const viewItemDetail = (item: any) => {
  currentItem.value = item;
  showDetailModal.value = true;
};

const handleSearch = () => {
  console.log('搜索:', searchKeyword.value);
};

const loadMore = () => {
  console.log('加载更多');
};

onMounted(() => {
  console.log('商品市场加载完成');
});
</script>

<style scoped>
.line-clamp-2 {
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}
</style>
