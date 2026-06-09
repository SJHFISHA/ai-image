<template>
  <div>
    <div class="page-header">
      <h2>用户积分账户</h2>
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
        v-model:value="filters.keyword"
        placeholder="搜索用户名"
        style="width: 250px"
        @search="fetchList"
        allow-clear
      />
      <a-button @click="fetchList">查询</a-button>
      <a-button type="primary" @click="openAdjustModal">
        <PlusOutlined /> 调整积分
      </a-button>
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
        <template v-if="column.key === 'action'">
          <a-button type="link" size="small" @click="openAdjustModalForUser(record)">调整积分</a-button>
        </template>
      </template>
    </a-table>

    <!-- 调整积分弹窗 -->
    <a-modal
      v-model:open="adjustModalVisible"
      title="调整用户积分"
      @ok="handleAdjust"
      :confirm-loading="adjusting"
    >
      <a-form :model="adjustForm" :label-col="{ span: 6 }" :wrapper-col="{ span: 16 }">
        <a-form-item label="用户ID" required>
          <a-input-number
            v-model:value="adjustForm.user_id"
            :min="1"
            style="width: 100%"
            :disabled="adjustFormDisabled"
          />
        </a-form-item>
        <a-form-item label="调整积分" required>
          <a-input-number v-model:value="adjustForm.points" style="width: 100%" />
          <div class="field-hint">正数增加，负数扣减</div>
        </a-form-item>
        <a-form-item label="调整原因" required>
          <a-textarea v-model:value="adjustForm.remark" :rows="3" placeholder="请输入调整原因" />
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
  getPointAccountList,
  adjustUserPoints,
} from '@/api/admin'
import type { PointAccount } from '@/api/admin'

const list = ref<PointAccount[]>([])
const loading = ref(false)
const adjustModalVisible = ref(false)
const adjusting = ref(false)
const adjustFormDisabled = ref(false)

const filters = reactive({
  user_id: undefined as number | undefined,
  keyword: '',
})

const pagination = reactive({
  current: 1,
  pageSize: 20,
  total: 0,
  showSizeChanger: true,
  showTotal: (total: number) => `共 ${total} 条`,
})

const adjustForm = reactive({
  user_id: undefined as number | undefined,
  points: 0,
  remark: '',
})

const columns = [
  { title: 'ID', dataIndex: 'id', key: 'id', width: 60 },
  { title: '用户ID', dataIndex: 'user_id', key: 'user_id', width: 80 },
  { title: '用户名', dataIndex: 'username', key: 'username' },
  { title: '可用积分', dataIndex: 'balance_points', key: 'balance_points', width: 100 },
  { title: '冻结积分', dataIndex: 'frozen_points', key: 'frozen_points', width: 100 },
  { title: '累计充值', dataIndex: 'total_recharged_points', key: 'total_recharged_points', width: 100 },
  { title: '累计消费', dataIndex: 'total_consumed_points', key: 'total_consumed_points', width: 100 },
  { title: '更新时间', dataIndex: 'updated_at', key: 'updated_at', width: 170 },
  { title: '操作', key: 'action', width: 100, fixed: 'right' as const },
]

async function fetchList() {
  loading.value = true
  try {
    const res = await getPointAccountList({
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

function openAdjustModal() {
  adjustFormDisabled.value = false
  Object.assign(adjustForm, { user_id: undefined, points: 0, remark: '' })
  adjustModalVisible.value = true
}

function openAdjustModalForUser(record: PointAccount) {
  adjustFormDisabled.value = true
  Object.assign(adjustForm, { user_id: record.user_id, points: 0, remark: '' })
  adjustModalVisible.value = true
}

async function handleAdjust() {
  if (!adjustForm.user_id || adjustForm.points === 0 || !adjustForm.remark) {
    message.warning('请填写完整信息')
    return
  }
  adjusting.value = true
  try {
    await adjustUserPoints({
      user_id: adjustForm.user_id,
      points: adjustForm.points,
      remark: adjustForm.remark,
    })
    message.success('积分调整成功')
    adjustModalVisible.value = false
    fetchList()
  } finally {
    adjusting.value = false
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

.field-hint {
  color: #999;
  font-size: 12px;
  margin-top: 4px;
}
</style>
