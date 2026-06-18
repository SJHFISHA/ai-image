<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { Modal, message } from 'ant-design-vue'
import {
  createAdminNotification,
  deleteAdminNotification,
  disableAdminNotification,
  getAdminNotificationList,
  publishAdminNotification,
  updateAdminNotification,
} from '@/api/admin'
import type { AdminNotification, AdminNotificationCreateParams } from '@/api/admin'

const columns = [
  { title: 'ID', dataIndex: 'id', key: 'id', width: 80 },
  { title: '标题', dataIndex: 'title', key: 'title', width: 220 },
  { title: '类型', dataIndex: 'type', key: 'type', width: 100 },
  { title: '等级', dataIndex: 'level', key: 'level', width: 100 },
  { title: '状态', dataIndex: 'status', key: 'status', width: 100 },
  { title: '发布时间', dataIndex: 'publish_at', key: 'publish_at', width: 170 },
  { title: '过期时间', dataIndex: 'expire_at', key: 'expire_at', width: 170 },
  { title: '创建时间', dataIndex: 'created_at', key: 'created_at', width: 170 },
  { title: '操作', key: 'action', width: 260, fixed: 'right' as const },
]

const loading = ref(false)
const list = ref<AdminNotification[]>([])
const total = ref(0)
const current = ref(1)
const pageSize = ref(20)

const keyword = ref('')
const statusFilter = ref<string | undefined>(undefined)

const modalVisible = ref(false)
const saving = ref(false)
const editingId = ref<number | null>(null)

const formData = reactive<AdminNotificationCreateParams>({
  title: '',
  content: '',
  type: 'system',
  level: 'info',
  status: 'draft',
  target_type: 'all',
  publish_at: undefined,
  expire_at: undefined,
})

function formatTime(val?: string) {
  if (!val) return '-'
  return val.replace('T', ' ').replace(/\.\d+Z?$/, '')
}

function resetForm() {
  editingId.value = null
  formData.title = ''
  formData.content = ''
  formData.type = 'system'
  formData.level = 'info'
  formData.status = 'draft'
  formData.target_type = 'all'
  formData.publish_at = undefined
  formData.expire_at = undefined
}

async function fetchData() {
  loading.value = true
  try {
    const res = await getAdminNotificationList({
      keyword: keyword.value || undefined,
      status_filter: statusFilter.value,
      page: current.value,
      page_size: pageSize.value,
    })
    list.value = res.items || []
    total.value = res.total || 0
  } catch {
    list.value = []
    total.value = 0
  } finally {
    loading.value = false
  }
}

function handleSearch() {
  current.value = 1
  fetchData()
}

function handleTableChange(pagination: { current?: number; pageSize?: number }) {
  current.value = pagination.current || 1
  pageSize.value = pagination.pageSize || 20
  fetchData()
}

function handleCreate() {
  resetForm()
  modalVisible.value = true
}

function handleEdit(record: AdminNotification) {
  editingId.value = record.id
  formData.title = record.title
  formData.content = record.content
  formData.type = record.type
  formData.level = record.level
  formData.status = record.status
  formData.target_type = record.target_type
  formData.publish_at = record.publish_at
  formData.expire_at = record.expire_at
  modalVisible.value = true
}

async function handleSubmit() {
  if (!formData.title || !formData.content) {
    message.warning('请填写标题和内容')
    return
  }

  saving.value = true
  try {
    if (editingId.value) {
      await updateAdminNotification(editingId.value, formData)
      message.success('更新成功')
    } else {
      await createAdminNotification(formData)
      message.success('创建成功')
    }
    modalVisible.value = false
    fetchData()
  } catch {
    message.error('保存失败')
  } finally {
    saving.value = false
  }
}

function handlePublish(record: AdminNotification) {
  Modal.confirm({
    title: '确认发布',
    content: `确定发布通知「${record.title}」吗？`,
    okText: '发布',
    cancelText: '取消',
    onOk: async () => {
      await publishAdminNotification(record.id)
      message.success('发布成功')
      fetchData()
    },
  })
}

function handleDisable(record: AdminNotification) {
  Modal.confirm({
    title: '确认下架',
    content: `确定下架通知「${record.title}」吗？`,
    okText: '下架',
    cancelText: '取消',
    onOk: async () => {
      await disableAdminNotification(record.id)
      message.success('下架成功')
      fetchData()
    },
  })
}

function handleDelete(record: AdminNotification) {
  Modal.confirm({
    title: '确认删除',
    content: `确定删除通知「${record.title}」吗？`,
    okText: '删除',
    cancelText: '取消',
    okButtonProps: { danger: true },
    onOk: async () => {
      await deleteAdminNotification(record.id)
      message.success('删除成功')
      fetchData()
    },
  })
}

function getStatusColor(status: string) {
  if (status === 'published') return 'green'
  if (status === 'disabled') return 'red'
  return 'default'
}

function getLevelColor(level: string) {
  if (level === 'success') return 'green'
  if (level === 'warning') return 'orange'
  if (level === 'error') return 'red'
  return 'blue'
}

onMounted(() => {
  fetchData()
})
</script>

<template>
  <div>
    <div style="margin-bottom: 16px; display: flex; gap: 12px; align-items: center">
      <a-input
        v-model:value="keyword"
        placeholder="搜索标题/内容"
        style="width: 240px"
        allow-clear
        @pressEnter="handleSearch"
      />
      <a-select
        v-model:value="statusFilter"
        placeholder="状态筛选"
        style="width: 140px"
        allow-clear
        @change="handleSearch"
      >
        <a-select-option value="draft">草稿</a-select-option>
        <a-select-option value="published">已发布</a-select-option>
        <a-select-option value="disabled">已下架</a-select-option>
      </a-select>
      <a-button type="primary" @click="handleSearch">搜索</a-button>
      <a-button type="primary" @click="handleCreate">新增通知</a-button>
    </div>

    <a-table
      :columns="columns"
      :data-source="list"
      :loading="loading"
      :pagination="{
        current,
        pageSize,
        total,
        showSizeChanger: true,
        showTotal: (t: number) => `共 ${t} 条`,
      }"
      row-key="id"
      size="middle"
      :scroll="{ x: 1300 }"
      @change="handleTableChange"
    >
      <template #bodyCell="{ column, record }">
        <template v-if="column.key === 'level'">
          <a-tag :color="getLevelColor(record.level)">
            {{ record.level }}
          </a-tag>
        </template>

        <template v-if="column.key === 'status'">
          <a-tag :color="getStatusColor(record.status)">
            {{ record.status }}
          </a-tag>
        </template>

        <template v-if="column.key === 'publish_at'">
          {{ formatTime(record.publish_at) }}
        </template>

        <template v-if="column.key === 'expire_at'">
          {{ formatTime(record.expire_at) }}
        </template>

        <template v-if="column.key === 'created_at'">
          {{ formatTime(record.created_at) }}
        </template>

        <template v-if="column.key === 'action'">
          <a-space>
            <a-button size="small" @click="handleEdit(record as AdminNotification)">编辑</a-button>
            <a-button
              v-if="record.status !== 'published'"
              size="small"
              type="primary"
              @click="handlePublish(record as AdminNotification)"
            >
              发布
            </a-button>
            <a-button
              v-if="record.status === 'published'"
              size="small"
              danger
              @click="handleDisable(record as AdminNotification)"
            >
              下架
            </a-button>
            <a-button size="small" danger @click="handleDelete(record as AdminNotification)">
              删除
            </a-button>
          </a-space>
        </template>
      </template>
    </a-table>

    <a-modal
      v-model:open="modalVisible"
      :title="editingId ? '编辑通知' : '新增通知'"
      :confirm-loading="saving"
      width="680px"
      @ok="handleSubmit"
      @cancel="modalVisible = false"
    >
      <a-form layout="vertical">
        <a-form-item label="标题" required>
          <a-input v-model:value="formData.title" placeholder="请输入通知标题" />
        </a-form-item>

        <a-form-item label="内容" required>
          <a-textarea
            v-model:value="formData.content"
            placeholder="请输入通知内容"
            :rows="5"
          />
        </a-form-item>

        <div style="display: grid; grid-template-columns: repeat(3, 1fr); gap: 12px">
          <a-form-item label="类型">
            <a-select v-model:value="formData.type">
              <a-select-option value="system">系统</a-select-option>
              <a-select-option value="maintenance">维护</a-select-option>
              <a-select-option value="activity">活动</a-select-option>
              <a-select-option value="update">更新</a-select-option>
            </a-select>
          </a-form-item>

          <a-form-item label="等级">
            <a-select v-model:value="formData.level">
              <a-select-option value="info">info</a-select-option>
              <a-select-option value="success">success</a-select-option>
              <a-select-option value="warning">warning</a-select-option>
              <a-select-option value="error">error</a-select-option>
            </a-select>
          </a-form-item>

          <a-form-item label="状态">
            <a-select v-model:value="formData.status">
              <a-select-option value="draft">草稿</a-select-option>
              <a-select-option value="published">发布</a-select-option>
              <a-select-option value="disabled">下架</a-select-option>
            </a-select>
          </a-form-item>
        </div>

        <a-form-item label="发布时间">
          <a-input
            v-model:value="formData.publish_at"
            placeholder="可不填，发布时自动使用当前时间；格式：2026-06-18T12:00:00"
          />
        </a-form-item>

        <a-form-item label="过期时间">
          <a-input
            v-model:value="formData.expire_at"
            placeholder="可不填，格式：2026-06-30T23:59:59"
          />
        </a-form-item>
      </a-form>
    </a-modal>
  </div>
</template>
