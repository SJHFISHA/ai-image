<template>
  <div>
    <div class="page-header">
      <h2>充值订单</h2>
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
      <a-input-search
        v-model:value="filters.order_no"
        placeholder="搜索订单号"
        style="width: 250px"
        @search="fetchList"
        allow-clear
      />
      <a-select
        v-model:value="filters.pay_status"
        placeholder="支付状态"
        allow-clear
        style="width: 140px"
        @change="fetchList"
      >
        <a-select-option value="pending">待支付</a-select-option>
        <a-select-option value="paid">已支付</a-select-option>
        <a-select-option value="failed">失败</a-select-option>
        <a-select-option value="closed">已关闭</a-select-option>
        <a-select-option value="refunded">已退款</a-select-option>
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
        <template v-if="column.key === 'amount'">
          ¥{{ record.amount }}
        </template>
        <template v-if="column.key === 'pay_status'">
          <a-tag :color="statusColor(record.pay_status)">
            {{ statusLabel(record.pay_status) }}
          </a-tag>
        </template>
        <template v-if="column.key === 'action'">
          <a-button type="link" size="small" @click="openStatusModal(record)">改状态</a-button>
        </template>
      </template>
    </a-table>

    <!-- 修改状态弹窗 -->
    <a-modal
      v-model:open="statusModalVisible"
      title="修改订单状态"
      @ok="handleStatusUpdate"
      :confirm-loading="statusUpdating"
    >
      <a-form :label-col="{ span: 6 }" :wrapper-col="{ span: 16 }">
        <a-form-item label="订单号">
          <span>{{ currentOrder?.order_no }}</span>
        </a-form-item>
        <a-form-item label="当前状态">
          <a-tag :color="statusColor(currentOrder?.pay_status || '')">
            {{ statusLabel(currentOrder?.pay_status || '') }}
          </a-tag>
        </a-form-item>
        <a-form-item label="新状态" required>
          <a-select v-model:value="newStatus">
            <a-select-option value="pending">待支付</a-select-option>
            <a-select-option value="paid">已支付</a-select-option>
            <a-select-option value="failed">失败</a-select-option>
            <a-select-option value="closed">已关闭</a-select-option>
            <a-select-option value="refunded">已退款</a-select-option>
          </a-select>
        </a-form-item>
      </a-form>
    </a-modal>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { message } from 'ant-design-vue'
import {
  getRechargeOrderList,
  updateRechargeOrderStatus,
} from '@/api/admin'
import type { RechargeOrder } from '@/api/admin'

const list = ref<RechargeOrder[]>([])
const loading = ref(false)
const statusModalVisible = ref(false)
const statusUpdating = ref(false)
const currentOrder = ref<RechargeOrder | null>(null)
const newStatus = ref('')

const filters = reactive({
  user_id: undefined as number | undefined,
  order_no: '',
  pay_status: undefined as string | undefined,
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
  { title: '订单号', dataIndex: 'order_no', key: 'order_no' },
  { title: '用户ID', dataIndex: 'user_id', key: 'user_id', width: 80 },
  { title: '套餐', dataIndex: 'package_name', key: 'package_name' },
  { title: '金额', key: 'amount', width: 90 },
  { title: '积分', dataIndex: 'total_points', key: 'total_points', width: 80 },
  { title: '支付渠道', dataIndex: 'pay_channel', key: 'pay_channel', width: 90 },
  { title: '状态', key: 'pay_status', width: 90 },
  { title: '创建时间', dataIndex: 'created_at', key: 'created_at', width: 170 },
  { title: '操作', key: 'action', width: 90, fixed: 'right' as const },
]

function statusColor(status: string) {
  const map: Record<string, string> = {
    pending: 'orange', paid: 'green', failed: 'red',
    closed: 'default', refunded: 'purple',
  }
  return map[status] || 'default'
}

function statusLabel(status: string) {
  const map: Record<string, string> = {
    pending: '待支付', paid: '已支付', failed: '失败',
    closed: '已关闭', refunded: '已退款',
  }
  return map[status] || status
}

async function fetchList() {
  loading.value = true
  try {
    const res = await getRechargeOrderList({
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

function openStatusModal(record: RechargeOrder) {
  currentOrder.value = record
  newStatus.value = record.pay_status
  statusModalVisible.value = true
}

async function handleStatusUpdate() {
  if (!currentOrder.value) return
  statusUpdating.value = true
  try {
    await updateRechargeOrderStatus(currentOrder.value.id, newStatus.value)
    message.success('状态更新成功')
    statusModalVisible.value = false
    fetchList()
  } finally {
    statusUpdating.value = false
  }
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
