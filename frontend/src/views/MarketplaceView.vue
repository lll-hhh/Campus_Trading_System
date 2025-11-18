<template>
  <div class="marketplace min-h-screen bg-gray-100">
    <!-- 顶部搜索栏 - 淘宝风格 -->
    <div class="bg-gradient-to-r from-orange-500 to-pink-500 shadow-lg sticky top-0 z-50">
      <div class="max-w-7xl mx-auto px-4 py-3">
        <div class="flex items-center gap-4">
          <!-- Logo -->
          <div class="text-white font-bold text-xl flex-shrink-0">
            🎓 校园淘
          </div>
          
          <!-- 搜索框 -->
          <div class="flex-1 max-w-3xl">
            <div class="flex">
              <n-input
                v-model:value="searchKeyword"
                placeholder="搜索宝贝、店铺..."
                size="large"
                class="rounded-r-none"
                @keyup.enter="handleSearch"
              >
                <template #prefix>
                  <span class="text-gray-400">🔍</span>
                </template>
              </n-input>
              <n-button 
                type="error" 
                size="large" 
                class="rounded-l-none px-8"
                @click="handleSearch"
                strong
              >
                搜索
              </n-button>
            </div>
            
            <!-- 热门搜索 -->
            <div class="flex gap-2 mt-2 text-xs">
              <span class="text-white/80">热门:</span>
              <span 
                v-for="hot in hotSearches" 
                :key="hot"
                class="text-white hover:underline cursor-pointer"
                @click="searchKeyword = hot; handleSearch()"
              >
                {{ hot }}
              </span>
            </div>
          </div>
          
          <!-- 右侧按钮 -->
          <n-button 
            size="large" 
            @click="showPublishModal = true" 
            type="warning"
            class="flex-shrink-0"
            strong
          >
            <template #icon>
              <span class="text-lg">📤</span>
            </template>
            我要卖
          </n-button>
        </div>
      </div>
    </div>
    
    <!-- 分类导航栏 -->
    <div class="bg-white shadow-sm border-b">
      <div class="max-w-7xl mx-auto px-4">
        <div class="flex items-center gap-6 py-3 overflow-x-auto">
          <div
            v-for="cat in categories"
            :key="cat.id"
            @click="selectedCategory = cat.id"
            :class="[
              'flex items-center gap-2 px-4 py-2 rounded-lg cursor-pointer transition-all whitespace-nowrap',
              selectedCategory === cat.id 
                ? 'bg-orange-500 text-white shadow-lg transform scale-105' 
                : 'hover:bg-orange-50 text-gray-700'
            ]"
          >
            <span class="text-xl">{{ cat.icon }}</span>
            <span class="font-medium">{{ cat.name }}</span>
            <span v-if="selectedCategory === cat.id" class="text-xs bg-white/20 px-2 py-0.5 rounded-full">
              {{ cat.count }}
            </span>
          </div>
        </div>
      </div>
    </div>
    
    <!-- 筛选栏 -->
    <div class="bg-white shadow-sm border-b">
      <div class="max-w-7xl mx-auto px-4 py-3">
        <div class="flex items-center gap-6 text-sm">
          <div class="flex items-center gap-3">
            <span class="text-gray-600">成色:</span>
            <n-radio-group v-model:value="filterCondition" size="small">
              <n-radio-button value="all">全部</n-radio-button>
              <n-radio-button value="new">全新</n-radio-button>
              <n-radio-button value="like-new">99新</n-radio-button>
              <n-radio-button value="used">二手</n-radio-button>
            </n-radio-group>
          </div>
          
          <n-divider vertical />
          
          <div class="flex items-center gap-3">
            <span class="text-gray-600">价格:</span>
            <n-input-group>
              <n-input-number v-model:value="priceRange[0]" placeholder="最低价" size="small" style="width: 100px" :show-button="false" />
              <n-input-number v-model:value="priceRange[1]" placeholder="最高价" size="small" style="width: 100px" :show-button="false" />
            </n-input-group>
          </div>
          
          <n-divider vertical />
          
          <div class="flex items-center gap-3">
            <span class="text-gray-600">排序:</span>
            <n-select v-model:value="sortBy" :options="sortOptions" size="small" style="width: 150px" />
          </div>
          
          <div class="ml-auto flex items-center gap-2">
            <span class="text-gray-500">共 {{ totalCount }} 件宝贝</span>
            <n-divider vertical />
            <div class="flex gap-1">
              <n-button size="small" :type="viewMode === 'grid' ? 'primary' : 'default'" @click="viewMode = 'grid'">
                <template #icon>⊞</template>
              </n-button>
              <n-button size="small" :type="viewMode === 'list' ? 'primary' : 'default'" @click="viewMode = 'list'">
                <template #icon>☰</template>
              </n-button>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- 商品列表 - 淘宝风格 -->
    <div class="max-w-7xl mx-auto px-4 py-6">
      <!-- 网格视图 -->
      <div v-if="viewMode === 'grid'" class="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-5 gap-3">
        <div
          v-for="item in paginatedItems"
          :key="item.id"
          class="bg-white rounded-lg overflow-hidden cursor-pointer transition-all hover:shadow-xl border border-transparent hover:border-orange-400"
          @click="viewItemDetail(item)"
        >
          <!-- 商品图片 -->
          <div class="relative aspect-square bg-gray-100">
            <img 
              v-if="item.images && item.images[0]" 
              :src="item.images[0]" 
              :alt="item.name" 
              class="w-full h-full object-cover"
            />
            <div v-else class="w-full h-full flex items-center justify-center bg-gradient-to-br from-orange-100 to-pink-100">
              <span class="text-6xl">{{ item.emoji }}</span>
            </div>
            
            <!-- 成色标签 -->
            <div class="absolute top-2 left-2">
              <n-tag 
                :type="getConditionColor(item.condition)" 
                size="small"
                :bordered="false"
                class="shadow-lg"
              >
                {{ getConditionText(item.condition) }}
              </n-tag>
            </div>
            
            <!-- 校园认证标签 -->
            <div class="absolute top-2 right-2">
              <n-tag type="info" size="small" :bordered="false" class="shadow-lg">
                🎓 校内
              </n-tag>
            </div>
            
            <!-- 多图标识 -->
            <div v-if="item.images && item.images.length > 1" class="absolute bottom-2 right-2 bg-black/60 text-white text-xs px-2 py-1 rounded">
              📷 {{ item.images.length }}
            </div>
          </div>
          
          <!-- 商品信息 -->
          <div class="p-3">
            <!-- 价格 -->
            <div class="mb-2">
              <span class="text-orange-600 font-bold text-xl">¥{{ item.price }}</span>
              <span v-if="item.originalPrice" class="text-gray-400 text-sm line-through ml-2">
                ¥{{ item.originalPrice }}
              </span>
            </div>
            
            <!-- 标题 -->
            <h3 class="text-sm mb-2 line-clamp-2 h-10 leading-5">{{ item.name }}</h3>
            
            <!-- 标签 -->
            <div class="flex flex-wrap gap-1 mb-2">
              <n-tag 
                v-for="tag in item.tags" 
                :key="tag"
                size="small"
                :bordered="false"
                class="text-xs"
              >
                {{ tag }}
              </n-tag>
            </div>
            
            <!-- 底部信息 -->
            <div class="flex items-center justify-between text-xs text-gray-500 pt-2 border-t">
              <div class="flex items-center gap-1">
                <n-avatar :size="20" round>
                  {{ item.seller[0] }}
                </n-avatar>
                <span>{{ item.seller }}</span>
              </div>
              <div class="flex items-center gap-2">
                <span>💬 {{ item.inquiries || 0 }}</span>
                <span>👁 {{ item.views }}</span>
              </div>
            </div>
            
            <!-- 位置 -->
            <div class="text-xs text-gray-400 mt-1">
              📍 {{ item.location || '东区宿舍' }}
            </div>
          </div>
        </div>
      </div>
      
      <!-- 列表视图 -->
      <div v-else class="space-y-3">
        <div
          v-for="item in paginatedItems"
          :key="item.id"
          class="bg-white rounded-lg p-4 cursor-pointer hover:shadow-lg transition-shadow border"
          @click="viewItemDetail(item)"
        >
          <div class="flex gap-4">
            <!-- 缩略图 -->
            <div class="w-40 h-40 bg-gray-100 rounded-lg flex-shrink-0 overflow-hidden">
              <img 
                v-if="item.images && item.images[0]" 
                :src="item.images[0]" 
                class="w-full h-full object-cover"
              />
              <div v-else class="w-full h-full flex items-center justify-center bg-gradient-to-br from-orange-100 to-pink-100">
                <span class="text-5xl">{{ item.emoji }}</span>
              </div>
            </div>
            
            <!-- 详细信息 -->
            <div class="flex-1">
              <div class="flex items-start justify-between mb-2">
                <div>
                  <h3 class="text-lg font-bold mb-1">{{ item.name }}</h3>
                  <p class="text-gray-600 text-sm line-clamp-2">{{ item.description }}</p>
                </div>
                <div class="text-right">
                  <div class="text-orange-600 font-bold text-2xl">¥{{ item.price }}</div>
                  <div v-if="item.originalPrice" class="text-gray-400 text-sm line-through">
                    ¥{{ item.originalPrice }}
                  </div>
                </div>
              </div>
              
              <div class="flex items-center gap-2 mb-3">
                <n-tag :type="getConditionColor(item.condition)" size="small">
                  {{ getConditionText(item.condition) }}
                </n-tag>
                <n-tag v-for="tag in item.tags" :key="tag" size="small" :bordered="false">
                  {{ tag }}
                </n-tag>
                <n-tag type="info" size="small">🎓 校内认证</n-tag>
              </div>
              
              <div class="flex items-center justify-between text-sm text-gray-500">
                <div class="flex items-center gap-4">
                  <div class="flex items-center gap-1">
                    <n-avatar :size="24" round>{{ item.seller[0] }}</n-avatar>
                    <span>{{ item.seller }}</span>
                  </div>
                  <span>� {{ item.location || '东区宿舍' }}</span>
                </div>
                <div class="flex items-center gap-4">
                  <span>💬 {{ item.inquiries || 0 }} 咨询</span>
                  <span>👁 {{ item.views }} 浏览</span>
                  <span>⏰ {{ item.publishTime || '2小时前' }}</span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- 分页 -->
      <div class="flex justify-center mt-8">
        <n-pagination
          v-model:page="currentPage"
          :page-count="totalPages"
          :page-size="pageSize"
          show-size-picker
          :page-sizes="[20, 40, 60, 100]"
          @update:page-size="handlePageSizeChange"
        />
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
import { NInput, NButton, NTag, NModal, NForm, NFormItem, NSelect, NInputNumber, NRadioGroup, NRadio, NRadioButton, NUpload, NDivider, NAlert, NAvatar, NPagination, NInputGroup, useMessage } from 'naive-ui';

const message = useMessage();

// 搜索和筛选
const searchKeyword = ref('');
const selectedCategory = ref<number | null>(null);
const filterCondition = ref('all');
const priceRange = ref([null, null] as [number | null, number | null]);
const sortBy = ref('default');
const viewMode = ref<'grid' | 'list'>('grid');

// 热门搜索
const hotSearches = ref(['iPhone', '自行车', '教材', '显示器', '二手书']);

// 分类数据 (扩展版)
const categories = ref([
  { id: null, name: '全部分类', icon: '🏪', count: 156 },
  { id: 1, name: '数码产品', icon: '📱', count: 45 },
  { id: 2, name: '图书教材', icon: '📚', count: 38 },
  { id: 3, name: '生活用品', icon: '🛋️', count: 28 },
  { id: 4, name: '运动器材', icon: '⚽', count: 15 },
  { id: 5, name: '服装鞋包', icon: '👔', count: 12 },
  { id: 6, name: '美妆护肤', icon: '💄', count: 8 },
  { id: 7, name: '其他闲置', icon: '📦', count: 10 }
]);

// 排序选项
const sortOptions = [
  { label: '综合排序', value: 'default' },
  { label: '最新发布', value: 'newest' },
  { label: '价格从低到高', value: 'price-asc' },
  { label: '价格从高到低', value: 'price-desc' },
  { label: '浏览最多', value: 'views' }
];

// 完整商品数据 (淘宝风格,包含多图、标签、位置等)
const items = ref([
  { 
    id: 1, 
    name: 'iPhone 13 Pro 128G 远峰蓝 99新', 
    description: '去年双11购入,使用3个月,无磕碰无划痕,原装充电器+数据线+耳机全套,还有11个月官方保修,支持验机,诚心要可小刀', 
    price: 4999, 
    originalPrice: 7999,
    category_id: 1, 
    condition: 'like-new', 
    seller: '张同学', 
    sellerLevel: 5,
    views: 1234, 
    inquiries: 89,
    emoji: '📱',
    images: [
      'https://picsum.photos/400/400?random=1',
      'https://picsum.photos/400/400?random=2',
      'https://picsum.photos/400/400?random=3'
    ],
    tags: ['可小刀', '包邮', '支持验机'],
    location: '东区7号楼',
    publishTime: '2小时前'
  },
  { 
    id: 2, 
    name: '高等数学同济第七版上下册+习题详解 笔记齐全', 
    description: '高数上下册+配套习题详解,保存完好,笔记齐全,重点都标注了,期末必备!当面交易', 
    price: 25, 
    originalPrice: 89,
    category_id: 2, 
    condition: 'used', 
    seller: '李学霸', 
    sellerLevel: 4,
    views: 456, 
    inquiries: 23,
    emoji: '📚',
    images: [
      'https://picsum.photos/400/400?random=4',
      'https://picsum.photos/400/400?random=5'
    ],
    tags: ['当面交易', '笔记齐全'],
    location: '图书馆门口',
    publishTime: '5小时前'
  },
  { 
    id: 3, 
    name: '捷安特山地自行车 ATX770 9成新', 
    description: '大二买的,骑了一年,车况良好,刚换了新轮胎,变速流畅,刹车灵敏,毕业甩卖急出,可试骑', 
    price: 800, 
    originalPrice: 1899,
    category_id: 4, 
    condition: 'like-new', 
    seller: '王骑士', 
    sellerLevel: 3,
    views: 789, 
    inquiries: 45,
    emoji: '🚲',
    images: [
      'https://picsum.photos/400/400?random=6',
      'https://picsum.photos/400/400?random=7',
      'https://picsum.photos/400/400?random=8',
      'https://picsum.photos/400/400?random=9'
    ],
    tags: ['急出', '可试骑', '包邮'],
    location: '西区操场',
    publishTime: '1天前'
  },
  { 
    id: 4, 
    name: 'LG 27寸2K 144Hz电竞显示器 完美屏', 
    description: '今年618入手,IPS面板,完美屏无亮点坏点,HDR400,响应时间1ms,打游戏超爽,原包装齐全,支持上门自提', 
    price: 1200, 
    originalPrice: 1899,
    category_id: 1, 
    condition: 'new', 
    seller: '赵电竞', 
    sellerLevel: 5,
    views: 1567, 
    inquiries: 112,
    emoji: '🖥️',
    images: [
      'https://picsum.photos/400/400?random=10',
      'https://picsum.photos/400/400?random=11'
    ],
    tags: ['全新', '完美屏', '支持自提'],
    location: '南区宿舍',
    publishTime: '3小时前'
  },
  { 
    id: 5, 
    name: 'YONEX尤尼克斯羽毛球拍 天斧77 全新未拆封', 
    description: '朋友送的,自己已经有一支了,全新未拆封,送球和拍包,线已穿好,到手就能打,比官方便宜500', 
    price: 680, 
    originalPrice: 1180,
    category_id: 4, 
    condition: 'new', 
    seller: '钱羽毛', 
    sellerLevel: 4,
    views: 345, 
    inquiries: 28,
    emoji: '🏸',
    images: [
      'https://picsum.photos/400/400?random=12'
    ],
    tags: ['全新未拆', '包邮'],
    location: '体育馆',
    publishTime: '6小时前'
  },
  { 
    id: 6, 
    name: '小米米家LED智能台灯 Pro 护眼台灯', 
    description: '用了一学期,功能完好,无频闪护眼,支持App控制,冷暖光可调,学习必备,搬家甩卖', 
    price: 129, 
    originalPrice: 299,
    category_id: 3, 
    condition: 'used', 
    seller: '孙明灯', 
    sellerLevel: 3,
    views: 234, 
    inquiries: 15,
    emoji: '💡',
    images: [
      'https://picsum.photos/400/400?random=13',
      'https://picsum.photos/400/400?random=14'
    ],
    tags: ['护眼', '智能'],
    location: '东区2号楼',
    publishTime: '8小时前'
  },
  { 
    id: 7, 
    name: '樱桃Cherry MX青轴机械键盘 RGB背光', 
    description: '德国原厂青轴,段落感强,打字贼爽,RGB灯效可调,PBT键帽,用了半年,9成新', 
    price: 450, 
    originalPrice: 799,
    category_id: 1, 
    condition: 'like-new', 
    seller: '周码农', 
    sellerLevel: 5,
    views: 567, 
    inquiries: 34,
    emoji: '⌨️',
    images: [
      'https://picsum.photos/400/400?random=15',
      'https://picsum.photos/400/400?random=16',
      'https://picsum.photos/400/400?random=17'
    ],
    tags: ['原厂轴', 'RGB'],
    location: '西区5号楼',
    publishTime: '12小时前'
  },
  { 
    id: 8, 
    name: 'Nike Air Max 270 耐克气垫运动鞋 42码', 
    description: '正品保证,专柜购入,42码,穿过2次,鞋盒齐全,洗干净了,支持闲鱼验货', 
    price: 399, 
    originalPrice: 899,
    category_id: 5, 
    condition: 'like-new', 
    seller: '吴跑步', 
    sellerLevel: 4,
    views: 445, 
    inquiries: 38,
    emoji: '👟',
    images: [
      'https://picsum.photos/400/400?random=18',
      'https://picsum.photos/400/400?random=19'
    ],
    tags: ['正品', '支持验货'],
    location: '南区6号楼',
    publishTime: '1天前'
  },
  { 
    id: 9, 
    name: '罗技MX Master 3无线鼠标 办公神器', 
    description: '人体工学设计,电磁滚轮,多设备连接,续航2个月,办公设计必备,8成新', 
    price: 380, 
    originalPrice: 699,
    category_id: 1, 
    condition: 'used', 
    seller: '郑设计', 
    sellerLevel: 4,
    views: 389, 
    inquiries: 22,
    emoji: '🖱️',
    images: [
      'https://picsum.photos/400/400?random=20'
    ],
    tags: ['无线', '多设备'],
    location: '北区3号楼',
    publishTime: '2天前'
  },
  { 
    id: 10, 
    name: '小爱同学音箱 Pro 智能音箱 白色', 
    description: '闲置音箱,声音清晰,智能语音控制,可以控制宿舍小米设备,95新', 
    price: 199, 
    originalPrice: 299,
    category_id: 3, 
    condition: 'like-new', 
    seller: '冯智能', 
    sellerLevel: 3,
    views: 267, 
    inquiries: 18,
    emoji: '🔊',
    images: [
      'https://picsum.photos/400/400?random=21',
      'https://picsum.photos/400/400?random=22'
    ],
    tags: ['智能音箱', '95新'],
    location: '东区9号楼',
    publishTime: '3天前'
  },
  // 再添加更多商品...
  { id: 11, name: 'iPad 2021款 64G WiFi版', description: '学习娱乐两不误', price: 1899, originalPrice: 2499, category_id: 1, condition: 'like-new', seller: '陈平板', sellerLevel: 5, views: 890, inquiries: 67, emoji: '📱', images: ['https://picsum.photos/400/400?random=23'], tags: ['Apple Pencil', '键盘套'], location: '西区', publishTime: '4小时前' },
  { id: 12, name: '线性代数教材+配套练习册', description: '同济版,笔记详细', price: 30, originalPrice: 78, category_id: 2, condition: 'used', seller: '林数学', sellerLevel: 4, views: 156, inquiries: 12, emoji: '📚', images: ['https://picsum.photos/400/400?random=24'], tags: ['包邮'], location: '图书馆', publishTime: '1天前' },
  { id: 13, name: '宜家书桌 白色 可升降', description: '搬家处理,9成新', price: 350, originalPrice: 599, category_id: 3, condition: 'like-new', seller: '黄搬家', sellerLevel: 3, views: 234, inquiries: 19, emoji: '🪑', images: ['https://picsum.photos/400/400?random=25', 'https://picsum.photos/400/400?random=26'], tags: ['急出', '自提'], location: '南区', publishTime: '6小时前' },
  { id: 14, name: '网球拍Wilson威尔逊 送球包', description: '大一买的,用了一学期', price: 280, originalPrice: 580, category_id: 4, condition: 'used', seller: '蒋网球', sellerLevel: 3, views: 123, inquiries: 8, emoji: '🎾', images: ['https://picsum.photos/400/400?random=27'], tags: ['送球包'], location: '网球场', publishTime: '2天前' },
  { id: 15, name: 'Adidas运动裤 L码 黑色', description: '正品,洗过一次', price: 150, originalPrice: 399, category_id: 5, condition: 'new', seller: '韩运动', sellerLevel: 4, views: 189, inquiries: 14, emoji: '👖', images: ['https://picsum.photos/400/400?random=28'], tags: ['正品', '全新'], location: '东区', publishTime: '1天前' },
  { id: 16, name: '雅诗兰黛小棕瓶眼霜 15ml', description: '专柜小样,全新未开封', price: 188, originalPrice: 390, category_id: 6, condition: 'new', seller: '杨美妆', sellerLevel: 5, views: 456, inquiries: 35, emoji: '💄', images: ['https://picsum.photos/400/400?random=29'], tags: ['专柜正品', '全新'], location: '西区', publishTime: '5小时前' },
  { id: 17, name: '宿舍收纳箱 3个装 透明', description: '搬家不要了,很新', price: 50, originalPrice: 99, category_id: 3, condition: 'like-new', seller: '沈收纳', sellerLevel: 2, views: 78, inquiries: 5, emoji: '📦', images: ['https://picsum.photos/400/400?random=30'], tags: ['打包价'], location: '北区', publishTime: '3天前' },
  { id: 18, name: 'Switch游戏卡 健身环大冒险', description: '已通关,9成新卡带', price: 280, originalPrice: 399, category_id: 1, condition: 'like-new', seller: '吴游戏', sellerLevel: 4, views: 567, inquiries: 43, emoji: '🎮', images: ['https://picsum.photos/400/400?random=31'], tags: ['可刀'], location: '东区', publishTime: '8小时前' },
  { id: 19, name: '戴尔显示器支架 双屏', description: '质量很好,承重15kg', price: 180, originalPrice: 299, category_id: 1, condition: 'used', seller: '冯支架', sellerLevel: 3, views: 234, inquiries: 16, emoji: '�️', images: ['https://picsum.photos/400/400?random=32'], tags: ['双屏'], location: '南区', publishTime: '2天前' },
  { id: 20, name: '吉他Yamaha雅马哈F310', description: '练习琴,音色不错', price: 550, originalPrice: 899, category_id: 4, condition: 'used', seller: '谢音乐', sellerLevel: 4, views: 345, inquiries: 27, emoji: '🎸', images: ['https://picsum.photos/400/400?random=33', 'https://picsum.photos/400/400?random=34'], tags: ['送琴包', '包邮'], location: '西区', publishTime: '1天前' },
]);

// 计算总数
const totalCount = computed(() => filteredItems.value.length);

// 筛选后的商品
const filteredItems = computed(() => {
  let filtered = items.value;
  
  // 分类筛选
  if (selectedCategory.value !== null) {
    filtered = filtered.filter(item => item.category_id === selectedCategory.value);
  }
  
  // 成色筛选
  if (filterCondition.value !== 'all') {
    filtered = filtered.filter(item => item.condition === filterCondition.value);
  }
  
  // 价格筛选
  if (priceRange.value[0] !== null) {
    filtered = filtered.filter(item => item.price >= (priceRange.value[0] || 0));
  }
  if (priceRange.value[1] !== null) {
    filtered = filtered.filter(item => item.price <= (priceRange.value[1] || 999999));
  }
  
  // 搜索
  if (searchKeyword.value) {
    const keyword = searchKeyword.value.toLowerCase();
    filtered = filtered.filter(item => 
      item.name.toLowerCase().includes(keyword) || 
      item.description.toLowerCase().includes(keyword) ||
      item.tags.some(tag => tag.toLowerCase().includes(keyword))
    );
  }
  
  // 排序
  switch (sortBy.value) {
    case 'newest':
      // 按发布时间排序 (这里简化为按id倒序)
      filtered = [...filtered].sort((a, b) => b.id - a.id);
      break;
    case 'price-asc':
      filtered = [...filtered].sort((a, b) => a.price - b.price);
      break;
    case 'price-desc':
      filtered = [...filtered].sort((a, b) => b.price - a.price);
      break;
    case 'views':
      filtered = [...filtered].sort((a, b) => b.views - a.views);
      break;
  }
  
  return filtered;
});

// 分页
const currentPage = ref(1);
const pageSize = ref(20);

const totalPages = computed(() => Math.ceil(filteredItems.value.length / pageSize.value));

const paginatedItems = computed(() => {
  const start = (currentPage.value - 1) * pageSize.value;
  const end = start + pageSize.value;
  return filteredItems.value.slice(start, end);
});

const handlePageSizeChange = (size: number) => {
  pageSize.value = size;
  currentPage.value = 1;
};

// 成色相关
const getConditionText = (condition: string) => {
  const map: Record<string, string> = {
    'new': '全新',
    'like-new': '99新',
    'used': '二手'
  };
  return map[condition] || condition;
};

const getConditionColor = (condition: string) => {
  const map: Record<string, any> = {
    'new': 'success',
    'like-new': 'warning',
    'used': 'default'
  };
  return map[condition] || 'default';
};

// 发布商品
const showPublishModal = ref(false);
const newItem = ref({
  name: '',
  category_id: null as number | null,
  price: 0,
  condition: 'used',
  description: '',
  contact: ''
});

const categoryOptions = computed(() => 
  categories.value.filter(c => c.id !== null).map(c => ({
    label: `${c.icon} ${c.name}`,
    value: c.id
  }))
);

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
  currentPage.value = 1; // 重置到第一页
  console.log('搜索:', searchKeyword.value);
};

onMounted(() => {
  console.log('淘宝风格商品市场加载完成');
});
</script>

<style scoped>
.line-clamp-2 {
  display: -webkit-box;
  -webkit-line-clamp: 2;
  line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}
</style>
