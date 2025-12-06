<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import { NButton, NInput, NSelect, NDatePicker, NInputNumber, NCard, NSpace, NTag, NCollapse, NCollapseItem } from 'naive-ui'

export interface FilterCondition {
  id: string
  field: string
  operator: string
  value: any
  logic?: 'AND' | 'OR'
}

export interface TableColumn {
  key: string
  title: string
  type: 'string' | 'number' | 'date' | 'enum' | 'boolean'
  enumOptions?: { label: string; value: any }[]
}

const props = defineProps<{
  columns: TableColumn[]
  modelValue: FilterCondition[]
}>()

const emit = defineEmits<{
  'update:modelValue': [value: FilterCondition[]]
  'apply': [conditions: FilterCondition[]]
  'reset': []
}>()

const conditions = ref<FilterCondition[]>(props.modelValue || [])

// 操作符选项
const operatorOptions = {
  string: [
    { label: '等于', value: 'eq' },
    { label: '不等于', value: 'ne' },
    { label: '包含', value: 'contains' },
    { label: '不包含', value: 'notContains' },
    { label: '开头是', value: 'startsWith' },
    { label: '结尾是', value: 'endsWith' },
    { label: '为空', value: 'isEmpty' },
    { label: '不为空', value: 'isNotEmpty' },
  ],
  number: [
    { label: '等于', value: 'eq' },
    { label: '不等于', value: 'ne' },
    { label: '大于', value: 'gt' },
    { label: '大于等于', value: 'gte' },
    { label: '小于', value: 'lt' },
    { label: '小于等于', value: 'lte' },
    { label: '在范围内', value: 'between' },
    { label: '不在范围内', value: 'notBetween' },
    { label: '在列表中', value: 'in' },
    { label: '不在列表中', value: 'notIn' },
  ],
  date: [
    { label: '等于', value: 'eq' },
    { label: '在...之后', value: 'after' },
    { label: '在...之前', value: 'before' },
    { label: '在范围内', value: 'between' },
    { label: '最近7天', value: 'last7days' },
    { label: '最近30天', value: 'last30days' },
    { label: '最近90天', value: 'last90days' },
    { label: '今天', value: 'today' },
    { label: '本周', value: 'thisWeek' },
    { label: '本月', value: 'thisMonth' },
  ],
  enum: [
    { label: '等于', value: 'eq' },
    { label: '不等于', value: 'ne' },
    { label: '在列表中', value: 'in' },
    { label: '不在列表中', value: 'notIn' },
  ],
  boolean: [
    { label: '是', value: 'true' },
    { label: '否', value: 'false' },
  ],
}

const columnOptions = computed(() => {
  return props.columns.map(col => ({
    label: col.title,
    value: col.key,
  }))
})

const getColumnType = (fieldKey: string) => {
  return props.columns.find(col => col.key === fieldKey)?.type || 'string'
}

const getOperatorOptions = (fieldKey: string) => {
  const type = getColumnType(fieldKey)
  return operatorOptions[type] || operatorOptions.string
}

const getEnumOptions = (fieldKey: string) => {
  return props.columns.find(col => col.key === fieldKey)?.enumOptions || []
}

// 添加条件
const addCondition = () => {
  conditions.value.push({
    id: `condition_${Date.now()}`,
    field: props.columns[0]?.key || '',
    operator: 'eq',
    value: null,
    logic: conditions.value.length > 0 ? 'AND' : undefined,
  })
}

// 删除条件
const removeCondition = (id: string) => {
  const index = conditions.value.findIndex(c => c.id === id)
  if (index > -1) {
    conditions.value.splice(index, 1)
    // 如果删除第一个条件，移除第二个条件的logic
    if (index === 0 && conditions.value.length > 0) {
      conditions.value[0].logic = undefined
    }
  }
}

// 应用筛选
const applyFilters = () => {
  emit('update:modelValue', conditions.value)
  emit('apply', conditions.value)
}

// 重置筛选
const resetFilters = () => {
  conditions.value = []
  emit('update:modelValue', [])
  emit('reset')
}

// 导出/保存筛选条件
const saveFilters = () => {
  const filtersJson = JSON.stringify(conditions.value, null, 2)
  const blob = new Blob([filtersJson], { type: 'application/json' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = `filters_${Date.now()}.json`
  a.click()
  URL.revokeObjectURL(url)
}

// 判断是否需要范围输入
const needsRangeInput = (operator: string) => {
  return ['between', 'notBetween'].includes(operator)
}

// 判断是否不需要值输入
const needsNoInput = (operator: string) => {
  return ['isEmpty', 'isNotEmpty', 'last7days', 'last30days', 'last90days', 'today', 'thisWeek', 'thisMonth'].includes(operator)
}

// 监听条件变化
watch(conditions, () => {
  emit('update:modelValue', conditions.value)
}, { deep: true })

// 初始化时添加一个条件
if (conditions.value.length === 0) {
  addCondition()
}
</script>

<template>
  <n-card title="高级筛选" :segmented="{ content: 'soft' }">
    <template #header-extra>
      <n-space>
        <n-button secondary size="small" @click="saveFilters">
          保存筛选
        </n-button>
        <n-button secondary type="warning" size="small" @click="resetFilters">
          重置
        </n-button>
        <n-button type="primary" size="small" @click="applyFilters">
          应用筛选
        </n-button>
      </n-space>
    </template>

    <n-space vertical size="large">
      <!-- 筛选条件列表 -->
      <div v-for="(condition, index) in conditions" :key="condition.id" class="filter-condition">
        <n-space align="center" :wrap="false">
          <!-- 逻辑运算符 -->
          <n-select
            v-if="index > 0"
            v-model:value="condition.logic"
            :options="[
              { label: '并且 (AND)', value: 'AND' },
              { label: '或者 (OR)', value: 'OR' },
            ]"
            style="width: 120px"
          />

          <!-- 字段选择 -->
          <n-select
            v-model:value="condition.field"
            :options="columnOptions"
            placeholder="选择字段"
            style="width: 180px"
            filterable
          />

          <!-- 操作符选择 -->
          <n-select
            v-model:value="condition.operator"
            :options="getOperatorOptions(condition.field)"
            placeholder="操作符"
            style="width: 150px"
          />

          <!-- 值输入 -->
          <template v-if="!needsNoInput(condition.operator)">
            <!-- 字符串输入 -->
            <n-input
              v-if="getColumnType(condition.field) === 'string'"
              v-model:value="condition.value"
              placeholder="输入值"
              style="width: 200px"
              clearable
            />

            <!-- 数字输入 -->
            <template v-else-if="getColumnType(condition.field) === 'number'">
              <n-input-number
                v-if="!needsRangeInput(condition.operator)"
                v-model:value="condition.value"
                placeholder="输入数字"
                style="width: 200px"
                clearable
              />
              <n-space v-else :wrap="false">
                <n-input-number
                  v-model:value="condition.value[0]"
                  placeholder="最小值"
                  style="width: 120px"
                  clearable
                />
                <span>至</span>
                <n-input-number
                  v-model:value="condition.value[1]"
                  placeholder="最大值"
                  style="width: 120px"
                  clearable
                />
              </n-space>
            </template>

            <!-- 日期选择 -->
            <template v-else-if="getColumnType(condition.field) === 'date'">
              <n-date-picker
                v-if="!needsRangeInput(condition.operator)"
                v-model:value="condition.value"
                type="datetime"
                placeholder="选择日期"
                style="width: 240px"
                clearable
              />
              <n-date-picker
                v-else
                v-model:value="condition.value"
                type="datetimerange"
                placeholder="选择日期范围"
                style="width: 360px"
                clearable
              />
            </template>

            <!-- 枚举选择 -->
            <n-select
              v-else-if="getColumnType(condition.field) === 'enum'"
              v-model:value="condition.value"
              :options="getEnumOptions(condition.field)"
              :multiple="['in', 'notIn'].includes(condition.operator)"
              placeholder="选择值"
              style="width: 200px"
              filterable
            />

            <!-- 布尔选择 -->
            <n-select
              v-else-if="getColumnType(condition.field) === 'boolean'"
              v-model:value="condition.value"
              :options="[
                { label: '是', value: 'true' },
                { label: '否', value: 'false' },
              ]"
              placeholder="选择"
              style="width: 120px"
            />
          </template>

          <!-- 删除按钮 -->
          <n-button
            circle
            quaternary
            type="error"
            @click="removeCondition(condition.id)"
          >
            ✕
          </n-button>
        </n-space>
      </div>

      <!-- 添加条件按钮 -->
      <n-button dashed block @click="addCondition">
        + 添加筛选条件
      </n-button>

      <!-- 筛选预览 -->
      <n-collapse v-if="conditions.length > 0">
        <n-collapse-item title="筛选条件预览" name="preview">
          <n-space>
            <n-tag
              v-for="(condition, index) in conditions"
              :key="condition.id"
              type="info"
              closable
              @close="removeCondition(condition.id)"
            >
              {{ index > 0 ? condition.logic + ' ' : '' }}
              {{ columns.find(c => c.key === condition.field)?.title }}
              {{ getOperatorOptions(condition.field).find(op => op.value === condition.operator)?.label }}
              {{ needsNoInput(condition.operator) ? '' : condition.value }}
            </n-tag>
          </n-space>
        </n-collapse-item>
      </n-collapse>
    </n-space>
  </n-card>
</template>

<style scoped>
.filter-condition {
  padding: 12px;
  border: 1px solid #e0e0e6;
  border-radius: 4px;
  background-color: #fafafa;
}

.filter-condition:hover {
  border-color: #18a058;
  background-color: #f0f9ff;
}
</style>
