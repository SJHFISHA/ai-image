<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { Card, Row, Col, Statistic, Button, Space, Avatar } from 'ant-design-vue'
import {
  UserOutlined,
  PictureOutlined,
  WalletOutlined,
  FileTextOutlined,
  ThunderboltOutlined,
} from '@ant-design/icons-vue'
import { useUserStore } from '@/stores/user'
import { getPointBalance } from '@/api/points'
import type { PointBalance } from '@/api/points'

const router = useRouter()
const userStore = useUserStore()
const pointBalance = ref<PointBalance | null>(null)
const loading = ref(true)

onMounted(async () => {
  try {
    const res = await getPointBalance()
    pointBalance.value = res
  } catch {
    // 接口异常时静默处理
  } finally {
    loading.value = false
  }
})

function goTo(path: string) {
  router.push(path)
}
</script>

<template>
  <div class="dashboard-page">
    <div class="dashboard-header">
      <div class="user-profile">
        <Avatar :size="64" :src="userStore.userInfo?.avatar_url" class="user-avatar">
          <template #icon><UserOutlined /></template>
        </Avatar>
        <div class="user-info">
          <h2 class="user-nickname">{{ userStore.userInfo?.nickname || userStore.userInfo?.username || '用户' }}</h2>
          <p class="user-username">@{{ userStore.userInfo?.username }}</p>
        </div>
      </div>
    </div>

    <Row :gutter="[16, 16]" class="stats-row">
      <Col :xs="12" :sm="6">
        <Card class="stat-card">
          <Statistic
            title="可用积分"
            :value="pointBalance?.balance_points ?? 0"
            :loading="loading"
            class="stat-available"
          >
            <template #prefix><WalletOutlined /></template>
          </Statistic>
        </Card>
      </Col>
      <Col :xs="12" :sm="6">
        <Card class="stat-card">
          <Statistic
            title="冻结积分"
            :value="pointBalance?.frozen_points ?? 0"
            :loading="loading"
          />
        </Card>
      </Col>
      <Col :xs="12" :sm="6">
        <Card class="stat-card">
          <Statistic
            title="累计充值"
            :value="pointBalance?.total_recharged_points ?? 0"
            :loading="loading"
          />
        </Card>
      </Col>
      <Col :xs="12" :sm="6">
        <Card class="stat-card">
          <Statistic
            title="累计消费"
            :value="pointBalance?.total_consumed_points ?? 0"
            :loading="loading"
          />
        </Card>
      </Col>
    </Row>

    <div class="quick-actions">
      <h3 class="section-title">快捷入口</h3>
      <Row :gutter="[16, 16]">
        <Col :xs="12" :sm="6">
          <Button class="action-card" block @click="goTo('/image-generate')">
            <PictureOutlined class="action-icon" />
            <span>生成图片</span>
          </Button>
        </Col>
        <Col :xs="12" :sm="6">
          <Button class="action-card" block @click="goTo('/points/logs')">
            <FileTextOutlined class="action-icon" />
            <span>积分流水</span>
          </Button>
        </Col>
        <Col :xs="12" :sm="6">
          <Button class="action-card" block @click="goTo('/tasks')">
            <ThunderboltOutlined class="action-icon" />
            <span>我的任务</span>
          </Button>
        </Col>
        <Col :xs="12" :sm="6">
          <Button class="action-card" block @click="goTo('/')">
            <WalletOutlined class="action-icon" />
            <span>充值</span>
          </Button>
        </Col>
      </Row>
    </div>
  </div>
</template>

<style scoped>
.dashboard-page {
  max-width: 800px;
  margin: 0 auto;
  padding: 32px 24px;
}

.dashboard-header {
  margin-bottom: 32px;
}

.user-profile {
  display: flex;
  align-items: center;
  gap: 20px;
}

.user-avatar {
  flex-shrink: 0;
}

.user-info {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.user-nickname {
  font-size: 22px;
  font-weight: 600;
  margin: 0;
  color: rgba(0, 0, 0, 0.88);
}

.user-username {
  font-size: 14px;
  color: rgba(0, 0, 0, 0.45);
  margin: 0;
}

.stats-row {
  margin-bottom: 32px;
}

.stat-card {
  border-radius: 12px;
  text-align: center;
}

.stat-card :deep(.ant-statistic-title) {
  font-size: 13px;
  color: rgba(0, 0, 0, 0.45);
}

.stat-card :deep(.ant-statistic-content) {
  font-size: 24px;
}

.stat-available :deep(.ant-statistic-content-value) {
  color: #1677ff;
}

.section-title {
  font-size: 16px;
  font-weight: 600;
  margin: 0 0 16px 0;
  color: rgba(0, 0, 0, 0.88);
}

.action-card {
  height: 80px;
  border-radius: 12px;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 8px;
  font-size: 14px;
  border: 1px solid #f0f0f0;
}

.action-card:hover {
  border-color: #1677ff;
  color: #1677ff;
}

.action-icon {
  font-size: 22px;
}
</style>
