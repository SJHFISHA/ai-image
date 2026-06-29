<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { Table, Tag } from 'ant-design-vue'
import { getPointLogs } from '@/api/points'
import type { UserPointTransaction } from '@/api/points'

const columns = [
  { title: '时间', dataIndex: 'created_at', key: 'created_at', width: 170 },
  { title: '类型', dataIndex: 'type', key: 'type', width: 100 },
  { title: '方向', dataIndex: 'direction', key: 'direction', width: 80 },
  { title: '积分', dataIndex: 'points', key: 'points', width: 100, align: 'right' as const },
  { title: '变动前', dataIndex: 'balance_before', key: 'balance_before', width: 100, align: 'right' as const },
  { title: '变动后', dataIndex: 'balance_after', key: 'balance_after', width: 100, align: 'right' as const },
  { title: '关联任务', dataIndex: 'related_task_id', key: 'related_task_id', width: 140 },
  { title: '关联订单', dataIndex: 'related_order_no', key: 'related_order_no', width: 140 },
  { title: '备注', dataIndex: 'remark', key: 'remark', ellipsis: true },
]

const transactions = ref<UserPointTransaction[]>([])
const loading = ref(false)
const total = ref(0)
const current = ref(1)
const pageSize = ref(20)

const typeMap: Record<string, { text: string; color: string }> = {
  recharge: { text: '充值', color: 'green' },
  freeze: { text: '冻结', color: 'orange' },
  consume: { text: '消费', color: 'red' },
  unfreeze: { text: '解冻', color: 'blue' },
  refund: { text: '退款', color: 'purple' },
  admin_adjust: { text: '后台调整', color: 'cyan' },
  invite_reward: { text: '邀请奖励', color: 'magenta' },
}

const directionMap: Record<string, string> = {
  income: '收入',
  expense: '支出',
  freeze: '冻结',
  unfreeze: '解冻',
}

function formatTime(val: string) {
  if (!val) return '-'
  return val.replace('T', ' ').replace(/\.\d+Z?$/, '')
}

async function fetchData() {
  loading.value = true
  try {
    const res = await getPointLogs({ page: current.value, page_size: pageSize.value })
    transactions.value = res.items || []
    total.value = res.total || 0
  } catch {
    transactions.value = []
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

onMounted(() => {
  fetchData()
})
</script>

<template>
  <div class="point-logs-page">
    <h2 class="page-title">积分流水</h2>

    <Table
      :columns="columns"
      :data-source="transactions"
      :loading="loading"
      :pagination="{
        current,
        pageSize,
        total,
        showSizeChanger: true,
        showTotal: (t: number) => `共 ${t} 条`,
        pageSizeOptions: ['10', '20', '50'],
      }"
      row-key="transaction_no"
      size="middle"
      @change="handleTableChange"
    >
      <template #bodyCell="{ column, record }">
        <template v-if="column.key === 'created_at'">
          {{ formatTime(record.created_at) }}
        </template>

        <template v-if="column.key === 'type'">
          <Tag :color="typeMap[record.type]?.color || 'default'">
            {{ typeMap[record.type]?.text || record.type }}
          </Tag>
        </template>

        <template v-if="column.key === 'direction'">
          {{ directionMap[record.direction] || record.direction }}
        </template>

        <template v-if="column.key === 'points'">
          <span :style="{ color: record.direction === 'income' ? '#52c41a' : record.direction === 'expense' ? '#ff4d4f' : '#faad14' }">
            {{ record.direction === 'income' ? '+' : record.direction === 'expense' ? '-' : '' }}{{ record.points }}
          </span>
        </template>

        <template v-if="column.key === 'related_task_id'">
          {{ record.related_task_id || '-' }}
        </template>

        <template v-if="column.key === 'related_order_no'">
          {{ record.related_order_no || '-' }}
        </template>

        <template v-if="column.key === 'remark'">
          {{ record.remark || '-' }}
        </template>
      </template>
    </Table>
  </div>
</template>

<style scoped>
.point-logs-page {
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
</style>
