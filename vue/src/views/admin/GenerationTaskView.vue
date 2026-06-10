<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { Table, Tag, Input, Select, Button, Modal, Image } from 'ant-design-vue'
import { getAdminTaskList } from '@/api/admin'
import type { AdminTask } from '@/api/admin'

const columns = [
  { title: '任务ID', dataIndex: 'task_id', key: 'task_id', width: 180 },
  { title: '用户', dataIndex: 'username', key: 'username', width: 100 },
  { title: '模型', dataIndex: 'model_name', key: 'model_name', width: 120 },
  { title: '尺寸', dataIndex: 'image_size', key: 'image_size', width: 110 },
  { title: '状态', dataIndex: 'status', key: 'status', width: 90 },
  { title: '冻结', dataIndex: 'frozen_points', key: 'frozen_points', width: 70, align: 'right' as const },
  { title: '消费', dataIndex: 'consumed_points', key: 'consumed_points', width: 70, align: 'right' as const },
  { title: '退回', dataIndex: 'refunded_points', key: 'refunded_points', width: 70, align: 'right' as const },
  { title: '提示词', dataIndex: 'prompt', key: 'prompt', ellipsis: true },
  { title: '创建时间', dataIndex: 'created_at', key: 'created_at', width: 160 },
  { title: '操作', key: 'action', width: 80, align: 'center' as const },
]

const tasks = ref<AdminTask[]>([])
const loading = ref(false)
const total = ref(0)
const current = ref(1)
const pageSize = ref(20)

const keyword = ref('')
const statusFilter = ref<string | undefined>(undefined)

const statusMap: Record<string, { text: string; color: string }> = {
  pending: { text: '待执行', color: 'default' },
  running: { text: '生成中', color: 'processing' },
  success: { text: '成功', color: 'success' },
  failed: { text: '失败', color: 'error' },
}

// 详情弹窗
const detailVisible = ref(false)
const detailTask = ref<AdminTask | null>(null)

function formatTime(val: string) {
  if (!val) return '-'
  return val.replace('T', ' ').replace(/\.\d+Z?$/, '')
}

async function fetchData() {
  loading.value = true
  try {
    const res = await getAdminTaskList({
      keyword: keyword.value || undefined,
      status: statusFilter.value,
      page: current.value,
      page_size: pageSize.value,
    })
    tasks.value = res.items || []
    total.value = res.total || 0
  } catch {
    tasks.value = []
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

function showDetail(record: AdminTask) {
  detailTask.value = record
  detailVisible.value = true
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
        placeholder="搜索任务ID/模型/提示词"
        style="width: 260px"
        allow-clear
        @pressEnter="handleSearch"
      />
      <Select
        v-model:value="statusFilter"
        placeholder="状态筛选"
        style="width: 130px"
        allow-clear
        @change="handleSearch"
      >
        <Select.Option value="pending">待执行</Select.Option>
        <Select.Option value="running">生成中</Select.Option>
        <Select.Option value="success">成功</Select.Option>
        <Select.Option value="failed">失败</Select.Option>
      </Select>
      <Button type="primary" @click="handleSearch">搜索</Button>
    </div>

    <Table
      :columns="columns"
      :data-source="tasks"
      :loading="loading"
      :pagination="{
        current,
        pageSize,
        total,
        showSizeChanger: true,
        showTotal: (t: number) => `共 ${t} 条`,
      }"
      row-key="task_id"
      size="middle"
      @change="handleTableChange"
    >
      <template #bodyCell="{ column, record }">
        <template v-if="column.key === 'status'">
          <Tag :color="statusMap[record.status]?.color || 'default'">
            {{ statusMap[record.status]?.text || record.status }}
          </Tag>
        </template>

        <template v-if="column.key === 'prompt'">
          <span :title="record.prompt">{{ record.prompt || '-' }}</span>
        </template>

        <template v-if="column.key === 'created_at'">
          {{ formatTime(record.created_at) }}
        </template>

        <template v-if="column.key === 'action'">
          <Button type="link" size="small" @click="showDetail(record as AdminTask)">详情</Button>
        </template>
      </template>
    </Table>

    <!-- 任务详情弹窗 -->
    <Modal
      v-model:open="detailVisible"
      title="任务详情"
      :footer="null"
      width="700px"
    >
      <div v-if="detailTask" style="display: flex; flex-direction: column; gap: 10px; font-size: 14px;">
        <div><span style="color: rgba(0,0,0,0.45); min-width: 100px; display: inline-block;">任务ID：</span>{{ detailTask.task_id }}</div>
        <div><span style="color: rgba(0,0,0,0.45); min-width: 100px; display: inline-block;">用户：</span>{{ detailTask.username }} (ID: {{ detailTask.user_id }})</div>
        <div><span style="color: rgba(0,0,0,0.45); min-width: 100px; display: inline-block;">模型：</span>{{ detailTask.model_name }} ({{ detailTask.model_key }})</div>
        <div><span style="color: rgba(0,0,0,0.45); min-width: 100px; display: inline-block;">尺寸：</span>{{ detailTask.image_size || '-' }}</div>
        <div><span style="color: rgba(0,0,0,0.45); min-width: 100px; display: inline-block;">数量：</span>{{ detailTask.image_count || '-' }}</div>
        <div>
          <span style="color: rgba(0,0,0,0.45); min-width: 100px; display: inline-block;">状态：</span>
          <Tag :color="statusMap[detailTask.status]?.color || 'default'">
            {{ statusMap[detailTask.status]?.text || detailTask.status }}
          </Tag>
        </div>
        <div><span style="color: rgba(0,0,0,0.45); min-width: 100px; display: inline-block;">冻结积分：</span>{{ detailTask.frozen_points }}</div>
        <div><span style="color: rgba(0,0,0,0.45); min-width: 100px; display: inline-block;">消费积分：</span>{{ detailTask.consumed_points }}</div>
        <div><span style="color: rgba(0,0,0,0.45); min-width: 100px; display: inline-block;">退回积分：</span>{{ detailTask.refunded_points }}</div>
        <div style="word-break: break-all;"><span style="color: rgba(0,0,0,0.45); min-width: 100px; display: inline-block;">提示词：</span>{{ detailTask.prompt || '-' }}</div>
        <div v-if="detailTask.error_message" style="color: #ff4d4f;"><span style="color: rgba(0,0,0,0.45); min-width: 100px; display: inline-block;">错误信息：</span>{{ detailTask.error_message }}</div>
        <div><span style="color: rgba(0,0,0,0.45); min-width: 100px; display: inline-block;">创建时间：</span>{{ formatTime(detailTask.created_at) }}</div>
        <div><span style="color: rgba(0,0,0,0.45); min-width: 100px; display: inline-block;">开始时间：</span>{{ formatTime(detailTask.started_at || '') }}</div>
        <div><span style="color: rgba(0,0,0,0.45); min-width: 100px; display: inline-block;">完成时间：</span>{{ formatTime(detailTask.finished_at || '') }}</div>

        <div v-if="detailTask.request_json" style="margin-top: 8px;">
          <div style="font-weight: 500; margin-bottom: 4px;">请求参数</div>
          <pre style="background: #f5f5f5; padding: 12px; border-radius: 6px; font-size: 12px; overflow-x: auto; margin: 0;">{{ JSON.stringify(detailTask.request_json, null, 2) }}</pre>
        </div>
      </div>
    </Modal>
  </div>
</template>
