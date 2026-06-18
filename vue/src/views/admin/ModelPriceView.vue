<template>
  <div>
    <div class="page-header">
      <h2>模型价格配置</h2>
      <a-button type="primary" @click="openCreateModal">
        <PlusOutlined /> 新增配置
      </a-button>
    </div>

    <!-- 筛选栏 -->
    <div class="filter-bar">
      <a-select
        v-model:value="filters.capability_type"
        placeholder="能力类型"
        allow-clear
        style="width: 150px"
        @change="fetchList"
      >
        <a-select-option value="image">图片生成</a-select-option>
        <a-select-option value="image_edit">图片编辑</a-select-option>
        <a-select-option value="video">视频生成</a-select-option>
        <a-select-option value="text">文本生成</a-select-option>
        <a-select-option value="audio">音频生成</a-select-option>
      </a-select>
      <a-input-search
        v-model:value="filters.keyword"
        placeholder="搜索模型标识/名称"
        style="width: 250px"
        @search="fetchList"
        allow-clear
      />
      <a-select
        v-model:value="filters.enabled"
        placeholder="启用状态"
        allow-clear
        style="width: 130px"
        @change="fetchList"
      >
        <a-select-option :value="1">已启用</a-select-option>
        <a-select-option :value="0">已禁用</a-select-option>
      </a-select>
    </div>

    <!-- 表格 -->
    <a-table
      :columns="columns"
      :data-source="list"
      :loading="loading"
      :pagination="pagination"
      row-key="id"
      @change="handleTableChange"
      size="middle"
    >
      <template #bodyCell="{ column, record }">
        <template v-if="column.key === 'aspect_ratio'">
          <span>{{ record.aspect_ratio || '-' }}</span>
        </template>
        <template v-if="column.key === 'capability_type'">
          <a-tag :color="capabilityColor(record.capability_type)">
            {{ capabilityLabel(record.capability_type) }}
          </a-tag>
        </template>
        <template v-if="column.key === 'enabled'">
          <a-switch
            :checked="record.enabled === 1"
            checked-children="启用"
            un-checked-children="禁用"
            @change="(checked: boolean) => handleToggleEnabled(record, checked)"
          />
        </template>
        <template v-if="column.key === 'action'">
          <a-space>
            <a-button type="link" size="small" @click="openEditModal(record)">编辑</a-button>
            <a-popconfirm title="确定删除？" @confirm="handleDelete(record.id)">
              <a-button type="link" size="small" danger>删除</a-button>
            </a-popconfirm>
          </a-space>
        </template>
      </template>
    </a-table>

    <!-- 新增/编辑弹窗 -->
    <a-modal
      v-model:open="modalVisible"
      :title="isEdit ? '编辑配置' : '新增配置'"
      @ok="handleSubmit"
      :confirm-loading="submitting"
      width="680px"
    >
      <a-form :model="formData" :label-col="{ span: 6 }" :wrapper-col="{ span: 16 }">
        <a-form-item label="选择模型" required>
          <a-select
            v-model:value="formData.model_id"
            placeholder="请选择模型"
            :options="modelOptions"
            show-search
            :filter-option="(input: string, option: any) => option.label.toLowerCase().indexOf(input.toLowerCase()) >= 0"
          />
        </a-form-item>
        <a-form-item label="图片尺寸">
          <a-auto-complete
            v-model:value="formData.image_size"
            :options="imageSizeOptions"
            allow-clear
            placeholder="请选择或输入图片尺寸，如 1024x1024"
          />
        </a-form-item>
        <a-form-item label="宽高比">
          <a-auto-complete
            v-model:value="formData.aspect_ratio"
            :options="aspectRatioOptions"
            allow-clear
            placeholder="请选择或输入宽高比，如 1:1"
          />
        </a-form-item>
        <a-form-item label="图片数量">
          <a-input-number v-model:value="formData.image_count" :min="1" style="width: 100%" />
        </a-form-item>
        <a-form-item label="消耗积分" required>
          <a-input-number v-model:value="formData.points" :min="0" style="width: 100%" />
        </a-form-item>
        <a-form-item label="成本金额">
          <a-input-number v-model:value="formData.cost_amount" :min="0" :precision="6" style="width: 100%" />
        </a-form-item>
        <a-form-item label="排序">
          <a-input-number v-model:value="formData.sort_order" :min="0" style="width: 100%" />
        </a-form-item>
        <a-form-item label="启用">
          <a-switch :checked="formData.enabled === 1" @change="(checked: boolean) => formData.enabled = checked ? 1 : 0" />
        </a-form-item>
        <a-form-item label="备注">
          <a-textarea v-model:value="formData.remark" :rows="2" />
        </a-form-item>
      </a-form>
    </a-modal>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted, computed } from 'vue'
import { message } from 'ant-design-vue'
import { PlusOutlined } from '@ant-design/icons-vue'
import {
  getModelPriceList,
  createModelPriceConfig,
  updateModelPriceConfig,
  deleteModelPriceConfig,
  getModelConfigList,
} from '@/api/admin'
import type { ModelPriceConfig, ModelConfig } from '@/api/admin'

const list = ref<ModelPriceConfig[]>([])
const modelList = ref<ModelConfig[]>([])
const loading = ref(false)
const modalVisible = ref(false)
const isEdit = ref(false)
const editingId = ref(0)
const submitting = ref(false)

const filters = reactive({
  capability_type: undefined as string | undefined,
  keyword: '',
  enabled: undefined as number | undefined,
})

const pagination = reactive({
  current: 1,
  pageSize: 20,
  total: 0,
  showSizeChanger: true,
  showTotal: (total: number) => `共 ${total} 条`,
})

const formData = reactive({
  model_id: undefined as number | undefined,
  image_size: undefined as string | undefined,
  image_count: 1,
  aspect_ratio: undefined as string | undefined,
  points: 0,
  cost_amount: undefined as number | undefined,
  sort_order: 0,
  enabled: 1,
  remark: '',
})

const imageSizeOptions = [
  { value: '1024x1024' },
  { value: '1536x1024' },
  { value: '1024x1536' },
  { value: '1K' },
  { value: '2K' },
  { value: '4K' },
]

const aspectRatioOptions = [
  { value: '1:1' },
  { value: '16:9' },
  { value: '9:16' },
  { value: '4:3' },
  { value: '3:4' },
]

const modelOptions = computed(() =>
  modelList.value.map(m => ({
    value: m.id,
    label: `${m.model_name} (${m.model_key})`,
  }))
)

const columns = [
  { title: 'ID', dataIndex: 'id', key: 'id', width: 60 },
  { title: '模型标识', dataIndex: 'model_key', key: 'model_key' },
  { title: '展示名称', dataIndex: 'model_name', key: 'model_name' },
  { title: '类型', key: 'capability_type', width: 100 },
  { title: '图片尺寸', dataIndex: 'image_size', key: 'image_size' },
  { title: '宽高比', dataIndex: 'aspect_ratio', key: 'aspect_ratio', width: 80 },
  { title: '数量', dataIndex: 'image_count', key: 'image_count', width: 70 },
  { title: '积分', dataIndex: 'points', key: 'points', width: 80 },
  { title: '启用', key: 'enabled', width: 90 },
  { title: '排序', dataIndex: 'sort_order', key: 'sort_order', width: 70 },
  { title: '操作', key: 'action', width: 130, fixed: 'right' as const },
]

function capabilityColor(type: string) {
  const map: Record<string, string> = { image: 'blue', image_edit: 'cyan', video: 'purple', text: 'green', audio: 'orange' }
  return map[type] || 'default'
}

function capabilityLabel(type: string) {
  const map: Record<string, string> = { image: '图片生成', image_edit: '图片编辑', video: '视频', text: '文本', audio: '音频' }
  return map[type] || type
}

async function fetchList() {
  loading.value = true
  try {
    const res = await getModelPriceList({
      ...filters,
      page: pagination.current,
      page_size: pagination.pageSize,
    })
    list.value = res.items
    pagination.total = res.total
  } finally {
    loading.value = false
  }
}

async function fetchModels() {
  try {
    const res = await getModelConfigList({ page_size: 100 })
    modelList.value = res.items
  } catch { /* ignore */ }
}

function handleTableChange(pag: any) {
  pagination.current = pag.current
  pagination.pageSize = pag.pageSize
  fetchList()
}

function openCreateModal() {
  isEdit.value = false
  editingId.value = 0
  Object.assign(formData, {
    model_id: undefined,
    image_size: undefined, image_count: 1,
    aspect_ratio: undefined,
    points: 0,
    cost_amount: undefined, sort_order: 0, enabled: 1, remark: '',
  })
  modalVisible.value = true
}

function openEditModal(record: ModelPriceConfig) {
  isEdit.value = true
  editingId.value = record.id
  Object.assign(formData, {
    model_id: record.model_id,
    image_size: record.image_size,
    image_count: record.image_count,
    aspect_ratio: record.aspect_ratio,
    points: record.points,
    cost_amount: record.cost_amount,
    sort_order: record.sort_order,
    enabled: record.enabled,
    remark: record.remark || '',
  })
  modalVisible.value = true
}

async function handleSubmit() {
  if (!formData.model_id || !formData.points) {
    message.warning('请填写必要字段')
    return
  }
  submitting.value = true
  try {
    if (isEdit.value) {
      await updateModelPriceConfig(editingId.value, { ...formData })
      message.success('更新成功')
    } else {
      await createModelPriceConfig({ ...formData } as any)
      message.success('创建成功')
    }
    modalVisible.value = false
    fetchList()
  } finally {
    submitting.value = false
  }
}

async function handleDelete(id: number) {
  try {
    await deleteModelPriceConfig(id)
    message.success('删除成功')
    fetchList()
  } catch { /* interceptor handles error */ }
}

async function handleToggleEnabled(record: ModelPriceConfig, checked: boolean) {
  try {
    await updateModelPriceConfig(record.id, { enabled: checked ? 1 : 0 })
    message.success(checked ? '已启用' : '已禁用')
    fetchList()
  } catch { /* interceptor handles error */ }
}

onMounted(() => {
  fetchList()
  fetchModels()
})
</script>

<style scoped>
.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
}

.page-header h2 {
  margin: 0;
  font-size: 18px;
}

.filter-bar {
  display: flex;
  gap: 12px;
  margin-bottom: 16px;
}
</style>
