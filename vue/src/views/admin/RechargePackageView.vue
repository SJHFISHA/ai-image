<template>
  <div>
    <div class="page-header">
      <h2>充值套餐</h2>
      <a-button type="primary" @click="openCreateModal">
        <PlusOutlined /> 新增套餐
      </a-button>
    </div>

    <!-- 筛选栏 -->
    <div class="filter-bar">
      <a-input-search
        v-model:value="filters.keyword"
        placeholder="搜索套餐名称"
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
        <template v-if="column.key === 'amount'">
          ¥{{ record.amount }}
        </template>
        <template v-if="column.key === 'points'">
          {{ record.base_points }} + {{ record.bonus_points }}(赠) = {{ record.total_points }}
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
      :title="isEdit ? '编辑套餐' : '新增套餐'"
      @ok="handleSubmit"
      :confirm-loading="submitting"
    >
      <a-form :model="formData" :label-col="{ span: 6 }" :wrapper-col="{ span: 16 }">
        <a-form-item label="套餐名称" required>
          <a-input v-model:value="formData.package_name" placeholder="如 基础套餐" />
        </a-form-item>
        <a-form-item label="金额(¥)" required>
          <a-input-number v-model:value="formData.amount" :min="0" :precision="2" style="width: 100%" />
        </a-form-item>
        <a-form-item label="基础积分" required>
          <a-input-number v-model:value="formData.base_points" :min="0" style="width: 100%" />
        </a-form-item>
        <a-form-item label="赠送积分">
          <a-input-number v-model:value="formData.bonus_points" :min="0" style="width: 100%" />
        </a-form-item>
        <a-form-item label="总积分" required>
          <a-input-number v-model:value="formData.total_points" :min="0" style="width: 100%" />
        </a-form-item>
        <a-form-item label="排序">
          <a-input-number v-model:value="formData.sort_order" :min="0" style="width: 100%" />
        </a-form-item>
        <a-form-item label="启用">
          <a-switch :checked="formData.enabled === 1" @change="(checked: boolean) => formData.enabled = checked ? 1 : 0" />
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
  getRechargePackageList,
  createRechargePackage,
  updateRechargePackage,
  deleteRechargePackage,
} from '@/api/admin'
import type { RechargePackage } from '@/api/admin'

const list = ref<RechargePackage[]>([])
const loading = ref(false)
const modalVisible = ref(false)
const isEdit = ref(false)
const editingId = ref(0)
const submitting = ref(false)

const filters = reactive({
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
  package_name: '',
  amount: 0,
  base_points: 0,
  bonus_points: 0,
  total_points: 0,
  sort_order: 0,
  enabled: 1,
})

const columns = [
  { title: 'ID', dataIndex: 'id', key: 'id', width: 60 },
  { title: '套餐名称', dataIndex: 'package_name', key: 'package_name' },
  { title: '金额', key: 'amount', width: 100 },
  { title: '积分明细', key: 'points' },
  { title: '启用', key: 'enabled', width: 90 },
  { title: '排序', dataIndex: 'sort_order', key: 'sort_order', width: 70 },
  { title: '操作', key: 'action', width: 130, fixed: 'right' as const },
]

async function fetchList() {
  loading.value = true
  try {
    const res = await getRechargePackageList({
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
    package_name: '', amount: 0, base_points: 0,
    bonus_points: 0, total_points: 0, sort_order: 0, enabled: 1,
  })
  modalVisible.value = true
}

function openEditModal(record: RechargePackage) {
  isEdit.value = true
  editingId.value = record.id
  Object.assign(formData, {
    package_name: record.package_name,
    amount: record.amount,
    base_points: record.base_points,
    bonus_points: record.bonus_points,
    total_points: record.total_points,
    sort_order: record.sort_order,
    enabled: record.enabled,
  })
  modalVisible.value = true
}

async function handleSubmit() {
  if (!formData.package_name || !formData.amount || !formData.total_points) {
    message.warning('请填写必要字段')
    return
  }
  submitting.value = true
  try {
    if (isEdit.value) {
      await updateRechargePackage(editingId.value, { ...formData })
      message.success('更新成功')
    } else {
      await createRechargePackage({ ...formData } as any)
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
    await deleteRechargePackage(id)
    message.success('删除成功')
    fetchList()
  } catch { /* interceptor handles error */ }
}

async function handleToggleEnabled(record: RechargePackage, checked: boolean) {
  try {
    await updateRechargePackage(record.id, { enabled: checked ? 1 : 0 })
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
  font-size: 18px;
}

.filter-bar {
  display: flex;
  gap: 12px;
  margin-bottom: 16px;
}
</style>
