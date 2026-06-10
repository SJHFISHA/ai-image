<script setup lang="ts">
import { ref, onMounted, onUnmounted } from 'vue'
import { Table, Tag, Modal, Image } from 'ant-design-vue'
import { getMyTasks, getTaskDetail } from '@/api/generation'
import type { TaskDetailResult } from '@/api/generation'

const columns = [
  { title: '创建时间', dataIndex: 'created_at', key: 'created_at', width: 170 },
  { title: '模型', dataIndex: 'model_name', key: 'model_name', width: 130 },
  { title: '尺寸', dataIndex: 'image_size', key: 'image_size', width: 110 },
  { title: '数量', dataIndex: 'image_count', key: 'image_count', width: 70, align: 'center' as const },
  { title: '提示词', dataIndex: 'prompt', key: 'prompt', ellipsis: true },
  { title: '状态', dataIndex: 'status', key: 'status', width: 100 },
  { title: '冻结', dataIndex: 'frozen_points', key: 'frozen_points', width: 80, align: 'right' as const },
  { title: '消费', dataIndex: 'consumed_points', key: 'consumed_points', width: 80, align: 'right' as const },
  { title: '退回', dataIndex: 'refunded_points', key: 'refunded_points', width: 80, align: 'right' as const },
  { title: '操作', key: 'action', width: 80, align: 'center' as const },
]

const tasks = ref<TaskDetailResult[]>([])
const loading = ref(false)
const total = ref(0)
const current = ref(1)
const pageSize = ref(20)

const statusMap: Record<string, { text: string; color: string }> = {
  pending: { text: '待执行', color: 'default' },
  running: { text: '生成中', color: 'processing' },
  success: { text: '成功', color: 'success' },
  failed: { text: '失败', color: 'error' },
}

// 详情弹窗
const detailVisible = ref(false)
const detailLoading = ref(false)
const detailTask = ref<TaskDetailResult | null>(null)

function formatTime(val: string) {
  if (!val) return '-'
  return val.replace('T', ' ').replace(/\.\d+Z?$/, '')
}

async function fetchData() {
  loading.value = true
  try {
    const res = await getMyTasks({ page: current.value, page_size: pageSize.value })
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

async function showDetail(taskId: string) {
  detailVisible.value = true
  detailLoading.value = true
  try {
    const res = await getTaskDetail(taskId)
    detailTask.value = res
  } catch {
    detailTask.value = null
  } finally {
    detailLoading.value = false
  }
}

function closeDetail() {
  detailVisible.value = false
  detailTask.value = null
}

onMounted(() => {
  fetchData()
})
</script>

<template>
  <div class="task-list-page">
    <h2 class="page-title">我的任务</h2>

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
        pageSizeOptions: ['10', '20', '50'],
      }"
      row-key="task_id"
      size="middle"
      @change="handleTableChange"
    >
      <template #bodyCell="{ column, record }">
        <template v-if="column.key === 'created_at'">
          {{ formatTime(record.created_at) }}
        </template>

        <template v-if="column.key === 'prompt'">
          <span class="prompt-text" :title="record.prompt">{{ record.prompt || '-' }}</span>
        </template>

        <template v-if="column.key === 'status'">
          <Tag :color="statusMap[record.status]?.color || 'default'">
            {{ statusMap[record.status]?.text || record.status }}
          </Tag>
        </template>

        <template v-if="column.key === 'action'">
          <a @click="showDetail(record.task_id)">详情</a>
        </template>
      </template>
    </Table>

    <!-- 任务详情弹窗 -->
    <Modal
      v-model:open="detailVisible"
      title="任务详情"
      :footer="null"
      width="640px"
      @cancel="closeDetail"
    >
      <div v-if="detailLoading" class="detail-loading">加载中...</div>
      <div v-else-if="detailTask" class="detail-content">
        <div class="detail-row">
          <span class="detail-label">任务ID：</span>
          <span>{{ detailTask.task_id }}</span>
        </div>
        <div class="detail-row">
          <span class="detail-label">状态：</span>
          <Tag :color="statusMap[detailTask.status]?.color || 'default'">
            {{ statusMap[detailTask.status]?.text || detailTask.status }}
          </Tag>
        </div>
        <div class="detail-row">
          <span class="detail-label">模型：</span>
          <span>{{ detailTask.model_name }} ({{ detailTask.model_key }})</span>
        </div>
        <div class="detail-row">
          <span class="detail-label">尺寸：</span>
          <span>{{ detailTask.image_size || '-' }}</span>
        </div>
        <div class="detail-row">
          <span class="detail-label">数量：</span>
          <span>{{ detailTask.image_count || '-' }}</span>
        </div>
        <div class="detail-row">
          <span class="detail-label">提示词：</span>
          <span>{{ detailTask.prompt || '-' }}</span>
        </div>
        <div class="detail-row">
          <span class="detail-label">冻结积分：</span>
          <span>{{ detailTask.frozen_points }}</span>
        </div>
        <div class="detail-row">
          <span class="detail-label">消费积分：</span>
          <span>{{ detailTask.consumed_points }}</span>
        </div>
        <div class="detail-row">
          <span class="detail-label">退回积分：</span>
          <span>{{ detailTask.refunded_points }}</span>
        </div>
        <div v-if="detailTask.error_message" class="detail-row">
          <span class="detail-label">错误信息：</span>
          <span class="error-text">{{ detailTask.error_message }}</span>
        </div>
        <div class="detail-row">
          <span class="detail-label">创建时间：</span>
          <span>{{ formatTime(detailTask.created_at) }}</span>
        </div>
        <div v-if="detailTask.finished_at" class="detail-row">
          <span class="detail-label">完成时间：</span>
          <span>{{ formatTime(detailTask.finished_at) }}</span>
        </div>

        <div v-if="detailTask.images && detailTask.images.length" class="detail-images">
          <div class="detail-images-title">生成结果</div>
          <Image.PreviewGroup>
            <div class="detail-images-grid">
              <Image
                v-for="(img, idx) in detailTask.images"
                :key="idx"
                :src="img"
                class="detail-image"
                :preview="{ getContainer: false }"
              />
            </div>
          </Image.PreviewGroup>
        </div>
      </div>
    </Modal>
  </div>
</template>

<style scoped>
.task-list-page {
  max-width: 1100px;
  margin: 0 auto;
  padding: 32px 24px;
}

.page-title {
  font-size: 20px;
  font-weight: 600;
  margin: 0 0 24px 0;
  color: rgba(0, 0, 0, 0.88);
}

.prompt-text {
  max-width: 200px;
  display: inline-block;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.detail-loading {
  text-align: center;
  padding: 24px;
  color: rgba(0, 0, 0, 0.45);
}

.detail-content {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.detail-row {
  display: flex;
  align-items: flex-start;
  gap: 8px;
  font-size: 14px;
  line-height: 1.6;
}

.detail-label {
  color: rgba(0, 0, 0, 0.45);
  white-space: nowrap;
  min-width: 80px;
}

.error-text {
  color: #ff4d4f;
}

.detail-images {
  margin-top: 16px;
  padding-top: 16px;
  border-top: 1px solid #f0f0f0;
}

.detail-images-title {
  font-size: 14px;
  font-weight: 500;
  margin-bottom: 12px;
  color: rgba(0, 0, 0, 0.88);
}

.detail-images-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(160px, 1fr));
  gap: 12px;
}

.detail-image {
  width: 100%;
  aspect-ratio: 1;
  object-fit: cover;
  border-radius: 8px;
  cursor: zoom-in;
}
</style>
