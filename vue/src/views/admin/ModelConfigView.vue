<template>
  <div>
    <div class="page-header">
      <h2>模型配置</h2>
      <a-button type="primary" @click="openCreateModal">
        <PlusOutlined /> 新增模型
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
        <template v-if="column.key === 'route_mode'">
          <a-tag v-if="record.route_mode" :color="routeModeColor(record.route_mode)">
            {{ routeModeLabel(record.route_mode) }}
          </a-tag>
          <span v-else>-</span>
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
      :title="isEdit ? '编辑模型' : '新增模型'"
      @ok="handleSubmit"
      :confirm-loading="submitting"
      width="600px"
    >
      <a-form :model="formData" :label-col="{ span: 6 }" :wrapper-col="{ span: 16 }">
        <a-form-item label="模型标识" required>
          <a-input v-model:value="formData.model_key" placeholder="如 gpt-image-2" />
        </a-form-item>
        <a-form-item label="展示名称" required>
          <a-input v-model:value="formData.model_name" placeholder="如 GPT Image 2" />
        </a-form-item>
        <a-form-item label="供应商标识" required>
          <a-select v-model:value="formData.provider_key">
            <a-select-option value="api_gateway">API Gateway</a-select-option>
            <a-select-option value="google_genai">Google GenAI</a-select-option>
          </a-select>
        </a-form-item>
        <a-form-item label="路由模式">
          <a-select v-model:value="formData.route_mode" allow-clear placeholder="请选择路由模式">
            <a-select-option value="price">价格最低</a-select-option>
            <a-select-option value="speed">速度最快</a-select-option>
            <a-select-option value="success_rate">成功率最高</a-select-option>
          </a-select>
        </a-form-item>
        <a-form-item label="能力类型" required>
          <a-select v-model:value="formData.capability_type">
            <a-select-option value="image">图片生成</a-select-option>
            <a-select-option value="video">视频生成</a-select-option>
            <a-select-option value="text">文本生成</a-select-option>
            <a-select-option value="audio">音频生成</a-select-option>
          </a-select>
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
import { ref, reactive, onMounted } from 'vue'
import { message } from 'ant-design-vue'
import { PlusOutlined } from '@ant-design/icons-vue'
import {
  getModelConfigList,
  createModelConfig,
  updateModelConfig,
  deleteModelConfig,
} from '@/api/admin'
import type { ModelConfig } from '@/api/admin'

const list = ref<ModelConfig[]>([])
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
  model_key: '',
  model_name: '',
  provider_key: 'api_gateway',
  route_mode: undefined as string | undefined,
  capability_type: 'image',
  sort_order: 0,
  enabled: 1,
  remark: '',
})

const columns = [
  { title: 'ID', dataIndex: 'id', key: 'id', width: 60 },
  { title: '模型标识', dataIndex: 'model_key', key: 'model_key' },
  { title: '展示名称', dataIndex: 'model_name', key: 'model_name' },
  { title: '供应商', dataIndex: 'provider_key', key: 'provider_key', width: 120 },
  { title: '路由模式', dataIndex: 'route_mode', key: 'route_mode', width: 120 },
  { title: '类型', key: 'capability_type', width: 100 },
  { title: '启用', key: 'enabled', width: 90 },
  { title: '排序', dataIndex: 'sort_order', key: 'sort_order', width: 70 },
  { title: '操作', key: 'action', width: 130, fixed: 'right' as const },
]

function capabilityColor(type: string) {
  const map: Record<string, string> = { image: 'blue', video: 'purple', text: 'green', audio: 'orange' }
  return map[type] || 'default'
}

function capabilityLabel(type: string) {
  const map: Record<string, string> = { image: '图片', video: '视频', text: '文本', audio: '音频' }
  return map[type] || type
}

function routeModeColor(mode: string) {
  const map: Record<string, string> = { price: 'green', speed: 'orange', success_rate: 'blue' }
  return map[mode] || 'default'
}

function routeModeLabel(mode: string) {
  const map: Record<string, string> = { price: '价格最低', speed: '速度最快', success_rate: '成功率最高' }
  return map[mode] || mode
}

async function fetchList() {
  loading.value = true
  try {
    const res = await getModelConfigList({
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

function handleTableChange(pag: any) {
  pagination.current = pag.current
  pagination.pageSize = pag.pageSize
  fetchList()
}

function openCreateModal() {
  isEdit.value = false
  editingId.value = 0
  Object.assign(formData, {
    model_key: '', model_name: '', provider_key: 'api_gateway',
    route_mode: undefined, capability_type: 'image', sort_order: 0, enabled: 1, remark: '',
  })
  modalVisible.value = true
}

function openEditModal(record: ModelConfig) {
  isEdit.value = true
  editingId.value = record.id
  Object.assign(formData, {
    model_key: record.model_key,
    model_name: record.model_name,
    provider_key: record.provider_key,
    route_mode: record.route_mode,
    capability_type: record.capability_type,
    sort_order: record.sort_order,
    enabled: record.enabled,
    remark: record.remark || '',
  })
  modalVisible.value = true
}

async function handleSubmit() {
  if (!formData.model_key || !formData.model_name || !formData.provider_key) {
    message.warning('请填写必要字段')
    return
  }
  submitting.value = true
  try {
    if (isEdit.value) {
      await updateModelConfig(editingId.value, { ...formData })
      message.success('更新成功')
    } else {
      await createModelConfig({ ...formData })
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
    await deleteModelConfig(id)
    message.success('删除成功')
    fetchList()
  } catch { /* interceptor handles error */ }
}

async function handleToggleEnabled(record: ModelConfig, checked: boolean) {
  try {
    await updateModelConfig(record.id, { enabled: checked ? 1 : 0 })
    message.success(checked ? '已启用' : '已禁用')
    fetchList()
  } catch { /* interceptor handles error */ }
}

onMounted(fetchList)
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
}

.filter-bar {
  display: flex;
  gap: 12px;
  margin-bottom: 16px;
}
</style>
