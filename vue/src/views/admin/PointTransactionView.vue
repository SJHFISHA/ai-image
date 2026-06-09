<template>
  <div>
    <div class="page-header">
      <h2>积分流水</h2>
    </div>

    <!-- 筛选栏 -->
    <div class="filter-bar">
      <a-input-number
        v-model:value="filters.user_id"
        placeholder="用户ID"
        style="width: 150px"
        :min="1"
        @press-enter="fetchList"
      />
      <a-select
        v-model:value="filters.type"
        placeholder="流水类型"
        allow-clear
        style="width: 160px"
        @change="fetchList"
      >
        <a-select-option value="recharge">充值</a-select-option>
        <a-select-option value="freeze">冻结</a-select-option>
        <a-select-option value="consume">消费</a-select-option>
        <a-select-option value="refund">退款</a-select-option>
        <a-select-option value="unfreeze">解冻</a-select-option>
        <a-select-option value="admin_adjust">管理员调整</a-select-option>
      </a-select>
      <a-button @click="fetchList">查询</a-button>
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
        <template v-if="column.key === 'type'">
          <a-tag :color="typeColor(record.type)">
            {{ typeLabel(record.type) }}
          </a-tag>
        </template>
        <template v-if="column.key === 'direction'">
          <span :style="{ color: directionColor(record.direction) }">
            {{ directionLabel(record.direction) }}
          </span>
        </template>
        <template v-if="column.key === 'points'">
          <span :style="{ color: record.direction === 'income' ? '#52c41a' : record.direction === 'expense' ? '#ff4d4f' : '#faad14' }">
            {{ record.direction === 'income' ? '+' : record.direction === 'expense' ? '-' : '' }}{{ record.points }}
          </span>
        </template>
      </template>
    </a-table>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import {
  getPointTransactionList,
} from '@/api/admin'
import type { PointTransaction } from '@/api/admin'

const list = ref<PointTransaction[]>([])
const loading = ref(false)

const filters = reactive({
  user_id: undefined as number | undefined,
  type: undefined as string | undefined,
})

const pagination = reactive({
  current: 1,
  pageSize: 20,
  total: 0,
  showSizeChanger: true,
  showTotal: (total: number) => `共 ${total} 条`,
})

const columns = [
  { title: 'ID', dataIndex: 'id', key: 'id', width: 60 },
  { title: '流水号', dataIndex: 'transaction_no', key: 'transaction_no' },
  { title: '用户ID', dataIndex: 'user_id', key: 'user_id', width: 80 },
  { title: '用户名', dataIndex: 'username', key: 'username' },
  { title: '类型', key: 'type', width: 110 },
  { title: '方向', key: 'direction', width: 80 },
  { title: '变动积分', key: 'points', width: 100 },
  { title: '变动前余额', dataIndex: 'balance_before', key: 'balance_before', width: 100 },
  { title: '变动后余额', dataIndex: 'balance_after', key: 'balance_after', width: 100 },
  { title: '备注', dataIndex: 'remark', key: 'remark', ellipsis: true },
  { title: '创建时间', dataIndex: 'created_at', key: 'created_at', width: 170 },
]

function typeColor(type: string) {
  const map: Record<string, string> = {
    recharge: 'green', freeze: 'orange', consume: 'red',
    refund: 'purple', unfreeze: 'blue', admin_adjust: 'gold',
  }
  return map[type] || 'default'
}

function typeLabel(type: string) {
  const map: Record<string, string> = {
    recharge: '充值', freeze: '冻结', consume: '消费',
    refund: '退款', unfreeze: '解冻', admin_adjust: '管理员调整',
  }
  return map[type] || type
}

function directionColor(direction: string) {
  const map: Record<string, string> = {
    income: '#52c41a', expense: '#ff4d4f', freeze: '#faad14', unfreeze: '#1677ff',
  }
  return map[direction] || '#333'
}

function directionLabel(direction: string) {
  const map: Record<string, string> = {
    income: '收入', expense: '支出', freeze: '冻结', unfreeze: '解冻',
  }
  return map[direction] || direction
}

async function fetchList() {
  loading.value = true
  try {
    const res = await getPointTransactionList({
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
  font-size: 18px;
}

.filter-bar {
  display: flex;
  gap: 12px;
  margin-bottom: 16px;
  align-items: center;
}
</style>
