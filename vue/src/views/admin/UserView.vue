<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { Table, Tag, Button, Input, Select, Space, Modal, message } from 'ant-design-vue'
import { getAdminUserList, updateAdminUserStatus } from '@/api/admin'
import type { AdminUser } from '@/api/admin'

const columns = [
  { title: 'ID', dataIndex: 'id', key: 'id', width: 80 },
  { title: '用户名', dataIndex: 'username', key: 'username', width: 120 },
  { title: '昵称', dataIndex: 'nickname', key: 'nickname', width: 120 },
  { title: '邮箱', dataIndex: 'email', key: 'email', width: 180 },
  { title: '手机号', dataIndex: 'phone', key: 'phone', width: 130 },
  { title: '状态', dataIndex: 'status', key: 'status', width: 100 },
  { title: '最后登录', dataIndex: 'last_login_at', key: 'last_login_at', width: 170 },
  { title: '注册时间', dataIndex: 'created_at', key: 'created_at', width: 170 },
  { title: '操作', key: 'action', width: 120, align: 'center' as const },
]

const users = ref<AdminUser[]>([])
const loading = ref(false)
const total = ref(0)
const current = ref(1)
const pageSize = ref(20)

const keyword = ref('')
const statusFilter = ref<string | undefined>(undefined)

function formatTime(val: string) {
  if (!val) return '-'
  return val.replace('T', ' ').replace(/\.\d+Z?$/, '')
}

async function fetchData() {
  loading.value = true
  try {
    const res = await getAdminUserList({
      keyword: keyword.value || undefined,
      status: statusFilter.value,
      page: current.value,
      page_size: pageSize.value,
    })
    users.value = res.items || []
    total.value = res.total || 0
  } catch {
    users.value = []
    total.value = 0
  } finally {
    loading.value = false
  }
}

function handleTableChange(pagination: any) {
  current.value = pagination.current
  pageSize.value = pagination.pageSize
  fetchData()
}

function handleSearch() {
  current.value = 1
  fetchData()
}

async function handleToggleStatus(record: AdminUser) {
  const newStatus = record.status === 'normal' ? 'disabled' : 'normal'
  const actionText = newStatus === 'disabled' ? '禁用' : '启用'

  Modal.confirm({
    title: `确认${actionText}`,
    content: `确定要${actionText}用户「${record.username}」吗？`,
    okText: '确认',
    cancelText: '取消',
    onOk: async () => {
      try {
        await updateAdminUserStatus(record.id, newStatus)
        message.success(`${actionText}成功`)
        fetchData()
      } catch {
        message.error(`${actionText}失败`)
      }
    },
  })
}

onMounted(() => {
  fetchData()
})
</script>

<template>
  <div>
    <div style="margin-bottom: 16px; display: flex; gap: 12px; align-items: center">
      <Input
        v-model:value="keyword"
        placeholder="搜索用户名/昵称"
        style="width: 240px"
        allow-clear
        @pressEnter="handleSearch"
      />
      <Select
        v-model:value="statusFilter"
        placeholder="状态筛选"
        style="width: 140px"
        allow-clear
        @change="handleSearch"
      >
        <Select.Option value="normal">正常</Select.Option>
        <Select.Option value="disabled">已禁用</Select.Option>
      </Select>
      <Button type="primary" @click="handleSearch">搜索</Button>
    </div>

    <Table
      :columns="columns"
      :data-source="users"
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
      @change="handleTableChange"
    >
      <template #bodyCell="{ column, record }">
        <template v-if="column.key === 'status'">
          <Tag :color="record.status === 'normal' ? 'green' : 'red'">
            {{ record.status === 'normal' ? '正常' : '已禁用' }}
          </Tag>
        </template>

        <template v-if="column.key === 'last_login_at'">
          {{ formatTime(record.last_login_at) }}
        </template>

        <template v-if="column.key === 'created_at'">
          {{ formatTime(record.created_at) }}
        </template>

        <template v-if="column.key === 'action'">
          <Button
            type="primary"
            :danger="record.status === 'normal'"
            size="small"
            @click="handleToggleStatus(record as AdminUser)"
          >
            {{ record.status === 'normal' ? '禁用' : '启用' }}
          </Button>
        </template>
      </template>
    </Table>
  </div>
</template>
