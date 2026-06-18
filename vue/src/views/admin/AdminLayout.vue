<template>
  <a-layout class="admin-layout" :class="isDark ? 'admin-dark' : 'admin-light'">
    <a-layout-sider
      v-model:collapsed="collapsed"
      :trigger="null"
      collapsible
      :theme="isDark ? 'dark' : 'light'"
      :width="220"
      class="admin-sider"
    >
      <div class="logo">
        <span v-if="!collapsed">后台管理</span>
        <span v-else>Admin</span>
      </div>
      <a-menu
        v-model:selectedKeys="selectedKeys"
        :theme="isDark ? 'dark' : 'light'"
        mode="inline"
        class="sider-menu"
        @click="handleMenuClick"
      >
        <a-menu-item key="/admin/model-configs">
          <template #icon><SettingOutlined /></template>
          <span>模型配置</span>
        </a-menu-item>
        <a-menu-item key="/admin/model-prices">
          <template #icon><SettingOutlined /></template>
          <span>模型价格配置</span>
        </a-menu-item>
        <a-menu-item key="/admin/notifications">
          <template #icon><BellOutlined /></template>
          <span>通知管理</span>
        </a-menu-item>
        <a-menu-item key="/admin/recharge-packages">
          <template #icon><GiftOutlined /></template>
          <span>充值套餐</span>
        </a-menu-item>
        <a-menu-item key="/admin/recharge-orders">
          <template #icon><OrderedListOutlined /></template>
          <span>充值订单</span>
        </a-menu-item>
        <a-menu-item key="/admin/point-accounts">
          <template #icon><WalletOutlined /></template>
          <span>用户积分账户</span>
        </a-menu-item>
        <a-menu-item key="/admin/point-transactions">
          <template #icon><SwapOutlined /></template>
          <span>积分流水</span>
        </a-menu-item>
        <a-menu-item key="/admin/users">
          <template #icon><TeamOutlined /></template>
          <span>用户管理</span>
        </a-menu-item>
        <a-menu-item key="/admin/tasks">
          <template #icon><ThunderboltOutlined /></template>
          <span>任务管理</span>
        </a-menu-item>
      </a-menu>

      <!-- 底部管理员信息 -->
      <div class="sider-footer">
        <a-dropdown>
          <div class="admin-avatar-wrap">
            <a-avatar :size="32" style="background-color: #1677ff">
              <template #icon><UserOutlined /></template>
            </a-avatar>
            <span v-if="!collapsed" class="admin-name">{{ adminStore.adminInfo?.username }}</span>
            <DownOutlined v-if="!collapsed" style="font-size: 10px; color: #999" />
          </div>
          <template #overlay>
            <a-menu>
              <a-menu-item @click="adminStore.logout()">
                <LogoutOutlined />
                退出登录
              </a-menu-item>
            </a-menu>
          </template>
        </a-dropdown>
      </div>
    </a-layout-sider>

    <a-layout class="admin-inner-layout">
      <a-layout-header class="admin-header">
        <div class="header-left">
          <component
            :is="collapsed ? MenuUnfoldOutlined : MenuFoldOutlined"
            class="trigger"
            @click="collapsed = !collapsed"
          />
        </div>
        <div class="header-right">
          <div class="theme-toggle" @click="toggleTheme">
            <BulbOutlined v-if="!isDark" />
            <BulbFilled v-else />
          </div>
        </div>
      </a-layout-header>

      <a-layout-content class="admin-content">
        <router-view />
      </a-layout-content>
    </a-layout>
  </a-layout>
</template>

<script setup lang="ts">
import { ref, watch, onMounted, onUnmounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useAdminStore } from '@/stores/admin'
import {
  MenuFoldOutlined,
  MenuUnfoldOutlined,
  SettingOutlined,
  GiftOutlined,
  OrderedListOutlined,
  WalletOutlined,
  SwapOutlined,
  LogoutOutlined,
  DownOutlined,
  UserOutlined,
  BulbOutlined,
  BulbFilled,
  TeamOutlined,
  ThunderboltOutlined,
  BellOutlined,
} from '@ant-design/icons-vue'

const route = useRoute()
const router = useRouter()
const adminStore = useAdminStore()

const collapsed = ref(false)
const selectedKeys = ref<string[]>([route.path])
const isDark = ref(false)

let themeObserver: MutationObserver | null = null

function syncTheme() {
  const theme = document.documentElement.getAttribute('data-theme')
  isDark.value = theme === 'dark'
}

function toggleTheme() {
  const newTheme = isDark.value ? 'light' : 'dark'
  document.documentElement.setAttribute('data-theme', newTheme)
}

onMounted(() => {
  adminStore.init()
  syncTheme()
  themeObserver = new MutationObserver(syncTheme)
  themeObserver.observe(document.documentElement, {
    attributes: true,
    attributeFilter: ['data-theme']
  })
})

onUnmounted(() => {
  themeObserver?.disconnect()
})

watch(() => route.path, (path) => {
  selectedKeys.value = [path]
})

function handleMenuClick({ key }: { key: string }) {
  router.push(key)
}
</script>

<style scoped>
.admin-layout {
  min-height: 100vh;
}

/* ========== 亮色模式 ========== */
.admin-layout.admin-light .admin-inner-layout {
  background: #f5f5f5;
}

.admin-layout.admin-light .admin-header {
  background: #fff;
  box-shadow: 0 1px 4px rgba(0, 0, 0, 0.08);
}

.admin-layout.admin-light .trigger {
  color: rgba(0, 0, 0, 0.45);
}

.admin-layout.admin-light .trigger:hover {
  color: #1677ff;
}

.admin-layout.admin-light .theme-toggle {
  color: rgba(0, 0, 0, 0.45);
}

.admin-layout.admin-light .theme-toggle:hover {
  color: #1677ff;
}

.admin-layout.admin-light .admin-content {
  margin: 24px;
  padding: 24px;
  background: #fff;
  border-radius: 8px;
  min-height: 280px;
}

.admin-layout.admin-light .logo {
  color: #333;
  border-bottom-color: #f0f0f0;
}

.admin-layout.admin-light .sider-footer {
  border-top: 1px solid #f0f0f0;
}

.admin-layout.admin-light .admin-avatar-wrap:hover {
  background: rgba(0, 0, 0, 0.04);
}

.admin-layout.admin-light .admin-name {
  color: rgba(0, 0, 0, 0.88);
}

/* ========== 暗色模式 ========== */
.admin-layout.admin-dark .admin-inner-layout {
  background: #141414;
}

.admin-layout.admin-dark .admin-header {
  background: #1f1f1f;
  box-shadow: 0 1px 4px rgba(0, 0, 0, 0.3);
}

.admin-layout.admin-dark .trigger {
  color: rgba(255, 255, 255, 0.65);
}

.admin-layout.admin-dark .trigger:hover {
  color: #1677ff;
}

.admin-layout.admin-dark .theme-toggle {
  color: rgba(255, 255, 255, 0.65);
}

.admin-layout.admin-dark .theme-toggle:hover {
  color: #1677ff;
}

.admin-layout.admin-dark .admin-content {
  margin: 24px;
  padding: 24px;
  background: #1f1f1f;
  border-radius: 8px;
  min-height: 280px;
}

.admin-layout.admin-dark .logo {
  color: #fff;
  border-bottom-color: #303030;
}

.admin-layout.admin-dark .sider-footer {
  border-top: 1px solid #303030;
}

.admin-layout.admin-dark .admin-avatar-wrap:hover {
  background: rgba(255, 255, 255, 0.08);
}

.admin-layout.admin-dark .admin-name {
  color: rgba(255, 255, 255, 0.85);
}

/* ========== 通用 ========== */
.admin-sider :deep(.ant-layout-sider-children) {
  display: flex;
  flex-direction: column;
}

.logo {
  height: 64px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 18px;
  font-weight: 600;
  border-bottom: 1px solid rgba(255, 255, 255, 0.1);
}

.sider-menu {
  flex: 1;
}

.sider-footer {
  padding: 12px 16px;
  margin-top: auto;
}

.admin-avatar-wrap {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 12px;
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.3s;
  width: 100%;
}

.admin-name {
  flex: 1;
  font-size: 14px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.admin-header {
  padding: 0 24px;
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.header-left {
  display: flex;
  align-items: center;
}

.trigger {
  font-size: 18px;
  cursor: pointer;
  transition: color 0.3s;
  padding: 0 12px;
}

.header-right {
  display: flex;
  align-items: center;
}

.theme-toggle {
  cursor: pointer;
  font-size: 18px;
  transition: color 0.3s;
}
</style>
