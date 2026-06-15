<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted, watch } from 'vue'
import { ConfigProvider, Layout, Menu, Dropdown, Tooltip, Popconfirm, message } from 'ant-design-vue'
import { useRouter, useRoute } from 'vue-router'
import { useUserStore } from '@/stores/user'
import { getConversationList, deleteConversation } from '@/api/conversation'
import type { ConversationItem } from '@/api/conversation'
import {
  EditOutlined,
  MessageOutlined,
  MenuFoldOutlined,
  MenuUnfoldOutlined,
  BulbOutlined,
  BulbFilled,
  UserOutlined,
  LogoutOutlined,
  PictureOutlined,
  HomeOutlined,
  FolderOutlined,
  AppstoreOutlined,
  FileImageOutlined,
  BellOutlined,
  ClockCircleOutlined,
  DeleteOutlined,
} from '@ant-design/icons-vue'
import type { MenuTheme } from 'ant-design-vue'

const router = useRouter()
const route = useRoute()
const userStore = useUserStore()

// 历史会话列表
const historySessions = ref<ConversationItem[]>([])
const historyLoading = ref(false)

async function loadHistory() {
  if (!userStore.isLoggedIn) {
    historySessions.value = []
    return
  }
  historyLoading.value = true
  try {
    const res = await getConversationList({ page: 1, page_size: 20 })
    historySessions.value = res.items || []
  } catch {
    historySessions.value = []
  } finally {
    historyLoading.value = false
  }
}

function openSession(session: ConversationItem) {
  router.push({ path: '/image-generate', query: { session_id: session.session_id } })
}

async function handleDeleteSession(sessionId: string, event: Event) {
  event.stopPropagation()
  try {
    await deleteConversation(sessionId)
    message.success('删除成功')
    await loadHistory()
    // 如果删除的是当前正在查看的会话，跳转到新对话页面
    if (route.query.session_id === sessionId) {
      router.replace({ path: '/image-generate', query: {} })
    }
  } catch {
    message.error('删除失败')
  }
}

function handleNewChat() {
  selectedKeys.value = ['new-chat']
  // 检查当前是否已经在 /image-generate 页面
  if (route.path === '/image-generate' && !route.query.session_id) {
    // 如果已经在新对话页面，使用 window.location.reload() 刷新页面
    window.location.reload()
  } else {
    // 否则使用 replace 清除 session_id 参数
    router.replace({ path: '/image-generate', query: {} })
  }
}

function handleMenuSelect({ key }: { key: string | number }) {
  if (key === 'new-chat') {
    handleNewChat()
  }
}

// 判断是否为登录/注册页或管理员页面，这些页面不显示用户侧边栏
const isAuthPage = computed(() => {
  const name = route.name as string
  if (['login', 'register'].includes(name)) return true
  if (route.path.startsWith('/admin')) return true
  return false
})

const { Sider, Content } = Layout

const isDark = ref(false)
const collapsed = ref(false)
const selectedKeys = ref<string[]>(['new-chat'])
const primaryNavItems = [
  { key: 'assets', label: '资产', icon: FileImageOutlined, path: '/assets' },
  { key: 'generate', label: '生成', icon: AppstoreOutlined, path: '/image-generate' },
  { key: 'tasks', label: '任务', icon: FolderOutlined, path: '/tasks' },
  { key: 'points', label: '积分', icon: EditOutlined, path: '/points/logs' },
]

const selectedPrimaryKey = ref('generate')

function handlePrimaryNavClick(key: string) {
  selectedPrimaryKey.value = key
  const item = primaryNavItems.find(i => i.key === key)
  if (item?.path) {
    router.push(item.path)
  }
}

// 根据当前路由同步侧边栏高亮
watch(() => route.path, (path) => {
  const matched = primaryNavItems.find(item => item.path && path.startsWith(item.path))
  if (matched) {
    selectedPrimaryKey.value = matched.key
  }
}, { immediate: true })

const siderTheme = computed<MenuTheme>(() => (isDark.value ? 'dark' : 'light'))

// 头像上传
const avatarInput = ref<HTMLInputElement | null>(null)

function triggerAvatarUpload() {
  avatarInput.value?.click()
}

function handleAvatarChange(event: Event) {
  const input = event.target as HTMLInputElement
  if (input.files && input.files[0]) {
    const file = input.files[0]
    // 检查文件类型
    if (!file.type.startsWith('image/')) {
      alert('请选择图片文件')
      return
    }
    // 检查文件大小（最大50MB）
    if (file.size > 50 * 1024 * 1024) {
      alert('图片大小不能超过50MB')
      return
    }
    // 上传到后端
    userStore.updateAvatar(file)
  }
}

function toggleTheme() {
  isDark.value = !isDark.value
}

// 退出登录
function handleLogout() {
  userStore.logout()
}

// 初始化
onMounted(async () => {
  if (userStore.isLoggedIn) {
    await userStore.init()
    await loadHistory()
  }
  // 监听生图完成事件，刷新历史列表
  window.addEventListener('history-refresh', loadHistory)
})

onUnmounted(() => {
  window.removeEventListener('history-refresh', loadHistory)
})

// 登录状态变化时重新加载历史
watch(() => userStore.isLoggedIn, (loggedIn) => {
  if (loggedIn) {
    loadHistory()
  } else {
    historySessions.value = []
  }
})
</script>

<template>
  <ConfigProvider
    :theme="{
      token: {
        colorPrimary: '#1677ff',
        borderRadius: 8,
      },
    }"
  >
    <div :data-theme="isDark ? 'dark' : 'light'" style="height: 100%">
      <!-- 登录/注册页：不显示侧边栏 -->
      <template v-if="isAuthPage">
        <router-view />
      </template>

      <!-- 其他页面：显示侧边栏布局 -->
      <template v-else>
        <Layout class="app-layout" style="height: 100vh">
          <Sider
            :width="collapsed ? 248 : 320"
            class="app-shell-sider"
            :class="{ 'app-shell-sider-collapsed': collapsed }"
            :theme="siderTheme"
            :trigger="null"
          >
            <div class="two-level-sidebar">
              <aside class="primary-sidebar">
                <div class="brand-mark">
                  <img src="/favicon.png" alt="logo" class="brand-logo" />
                </div>

                <nav class="primary-nav">
                  <button
                    v-for="item in primaryNavItems"
                    :key="item.key"
                    class="primary-nav-item"
                    :class="{ active: selectedPrimaryKey === item.key }"
                    type="button"
                    @click="handlePrimaryNavClick(item.key)"
                  >
                    <component :is="item.icon" class="primary-nav-icon" />
                    <span>{{ item.label }}</span>
                  </button>
                </nav>

                <div class="primary-sidebar-bottom">
                  <div class="points-pill">
                    <span class="points-value">✦ {{ userStore.userInfo?.available_points ?? 0 }}</span>
                    <span class="points-label">积分</span>
                  </div>

                  <template v-if="userStore.isLoggedIn">
                    <input
                      ref="avatarInput"
                      type="file"
                      accept="image/*"
                      style="display: none"
                      @change="handleAvatarChange"
                    />
                    <Dropdown :trigger="['click']">
                      <button class="primary-avatar-btn" type="button">
                        <a-avatar
                          :size="24"
                          :src="userStore.userInfo?.avatar_url"
                          class="primary-avatar"
                        >
                          <template #icon><UserOutlined /></template>
                        </a-avatar>
                      </button>
                      <template #overlay>
                        <Menu>
                          <Menu.Item @click="triggerAvatarUpload">
                            <PictureOutlined />
                            更换头像
                          </Menu.Item>
                          <Menu.Item @click="router.push('/dashboard')">
                            <UserOutlined />
                            用户中心
                          </Menu.Item>
                          <a-menu-divider />
                          <Menu.Item @click="handleLogout">
                            <LogoutOutlined />
                            退出登录
                          </Menu.Item>
                        </Menu>
                      </template>
                    </Dropdown>
                  </template>

                  <template v-else>
                    <button class="primary-login-btn" type="button" @click="router.push('/login')">
                      登录
                    </button>
                  </template>

                  <button class="primary-bell-btn" type="button" title="通知">
                    <BellOutlined class="primary-bell-icon" />
                  </button>
                </div>
              </aside>

              <aside class="secondary-sidebar" :class="{ collapsed }">
                <div class="secondary-header">
                  <button class="quick-new-chat-btn" type="button" @click="handleNewChat">
                    新对话
                  </button>

                  <Tooltip :title="collapsed ? '展开聊天区域' : '收起聊天区域'">
                    <button class="secondary-collapse-btn" type="button" @click="collapsed = !collapsed">
                      <MenuUnfoldOutlined v-if="collapsed" />
                      <MenuFoldOutlined v-else />
                    </button>
                  </Tooltip>
                </div>

                <template v-if="!collapsed">
                  <Menu
                    :selected-keys="selectedKeys"
                    mode="inline"
                    :theme="siderTheme"
                    class="secondary-menu"
                    @select="handleMenuSelect"
                  >
                    <Menu.Item key="new-chat" @click="handleNewChat">
                      <template #icon>
                        <EditOutlined />
                      </template>
                      新对话
                    </Menu.Item>
                  </Menu>

                  <div class="recent-section">
                    <div class="recent-title">历史记录</div>
                    <div v-if="historyLoading" class="history-loading">加载中...</div>
                    <div v-else-if="historySessions.length === 0" class="history-empty">暂无历史记录</div>
                    <button
                      v-for="session in historySessions"
                      :key="session.session_id"
                      class="recent-item"
                      type="button"
                      @click="openSession(session)"
                    >
                      <ClockCircleOutlined class="recent-icon" />
                      <span class="recent-text" :title="session.title || session.last_message_preview">
                        {{ session.title || session.last_message_preview || '未命名会话' }}
                      </span>
                      <Popconfirm
                        title="确定删除此会话？"
                        ok-text="确定"
                        cancel-text="取消"
                        @confirm="(e: Event) => handleDeleteSession(session.session_id, e)"
                      >
                        <DeleteOutlined class="recent-delete-icon" @click.stop />
                      </Popconfirm>
                    </button>
                  </div>
                </template>
              </aside>
            </div>
          </Sider>

          <Layout>
            <Content class="main-content">
              <router-view />
            </Content>
          </Layout>
        </Layout>
      </template>

      <!-- 管理员页面不显示此灯泡，由 AdminLayout 自己管理 -->
      <div v-if="!isAuthPage" class="theme-toggle-btn" @click="toggleTheme">
        <BulbOutlined v-if="!isDark" />
        <BulbFilled v-else />
      </div>
    </div>
  </ConfigProvider>
</template>

<style>
.app-layout.ant-layout {
  min-height: 100vh;
}

.ant-layout-sider {
  transition: all 0.2s;
}

.ant-menu-item-selected {
  font-weight: 500;
}

.ant-dropdown-menu {
  border-radius: 8px;
}

.app-shell-sider.ant-layout-sider {
  background: #fff;
  border-right: 1px solid #eeeeee;
  box-shadow: none;
}

.app-shell-sider.ant-layout-sider.app-shell-sider-collapsed {
  border-right: none;
}

.two-level-sidebar {
  height: 100vh;
  display: flex;
  background: #fff;
}

.primary-sidebar {
  width: 72px;
  height: 100%;
  border-right: 1px solid #eeeeee;
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 20px 10px 18px;
  box-sizing: border-box;
}

.brand-mark {
  width: 36px;
  height: 36px;
  border-radius: 10px;
  display: flex;
  align-items: center;
  justify-content: center;
  margin-bottom: 140px;
  overflow: hidden;
}

.brand-logo {
  width: 100%;
  height: 100%;
  object-fit: contain;
  display: block;
}

.primary-nav {
  width: 100%;
  display: flex;
  flex-direction: column;
  gap: 18px;
}

.primary-nav-item {
  width: 52px;
  min-height: 44px;
  border: none;
  background: transparent;
  color: rgba(0, 0, 0, 0.88);
  cursor: pointer;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 6px;
  font-size: 12px;
  border-radius: 8px;
  padding: 4px 0;
}

.primary-nav-item:hover,
.primary-nav-item.active {
  background: #f2f3f5;
}

.primary-nav-icon {
  font-size: 18px;
}

.primary-sidebar-bottom {
  width: 100%;
  margin-top: auto;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 14px;
}

.points-pill {
  width: 48px;
  min-height: 42px;
  border-radius: 10px;
  background: #f2fbff;
  color: #00a6ed;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 2px;
  font-size: 12px;
}

.points-value {
  font-weight: 600;
  line-height: 1;
}

.points-label {
  font-size: 12px;
  line-height: 1;
}

.primary-avatar-btn {
  width: 36px;
  height: 36px;
  border: none;
  border-radius: 8px;
  background: transparent;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  padding: 0;
}

.primary-bell-btn {
  width: 36px;
  height: 36px;
  border: none;
  border-radius: 8px;
  background: transparent;
  color: #5f6b7a;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  padding: 0;
  font-size: 18px;
}

.primary-bell-btn:hover {
  background: #f2f3f5;
  color: rgba(0, 0, 0, 0.88);
}

.primary-bell-icon {
  color: currentColor;
  font-size: 18px;
  line-height: 1;
}

[data-theme='dark'] .primary-bell-btn {
  background: transparent;
  color: rgba(255, 255, 255, 0.72);
}

[data-theme='dark'] .primary-bell-btn:hover {
  background: #262626;
  color: #fff;
}

.primary-avatar {
  cursor: pointer;
  flex-shrink: 0;
}

.primary-login-btn {
  border: none;
  background: #1677ff;
  color: #fff;
  height: 28px;
  padding: 0 10px;
  border-radius: 14px;
  font-size: 12px;
  cursor: pointer;
}


.secondary-sidebar {
  width: 248px;
  height: 100%;
  padding: 28px 20px 20px;
  box-sizing: border-box;
  background: #fff;
  transition: width 0.2s ease, padding 0.2s ease;
  overflow: hidden;
}

.secondary-sidebar.collapsed {
  width: 176px;
  padding: 28px 26px 20px;
}

.secondary-header {
  height: 36px;
  display: inline-flex;
  align-items: center;
  gap: 8px;
  padding: 0 10px;
  border: 1px solid #eeeeee;
  border-radius: 8px;
  background: #fff;
  box-shadow: 0 1px 2px rgba(0, 0, 0, 0.04);
  color: rgba(0, 0, 0, 0.88);
  font-size: 14px;
  margin-bottom: 20px;
  white-space: nowrap;
}

.quick-new-chat-btn {
  height: 28px;
  border: none;
  background: transparent;
  color: rgba(0, 0, 0, 0.88);
  font-size: 14px;
  cursor: pointer;
  padding: 0 2px;
  white-space: nowrap;
}

.quick-new-chat-btn:hover {
  color: #1677ff;
}

.secondary-collapse-btn {
  width: 28px;
  height: 28px;
  border: none;
  border-left: 1px solid #eeeeee;
  border-radius: 0;
  background: transparent;
  color: rgba(0, 0, 0, 0.72);
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  padding-left: 8px;
}

.secondary-collapse-btn:hover {
  background: #f2f3f5;
}

.secondary-menu.ant-menu {
  border-inline-end: none;
  background: transparent;
}

.secondary-menu .ant-menu-item {
  height: 36px;
  line-height: 36px;
  border-radius: 8px;
  margin-inline: 0;
  margin-block: 4px;
  width: 100%;
}

.secondary-menu .ant-menu-item-selected {
  background: #f2f3f5;
  color: rgba(0, 0, 0, 0.88);
}

.recent-section {
  margin-top: 24px;
}

.recent-title {
  color: rgba(0, 0, 0, 0.42);
  font-size: 12px;
  margin-bottom: 10px;
}

.recent-item {
  width: 100%;
  border: none;
  background: transparent;
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 6px 2px;
  border-radius: 8px;
  cursor: pointer;
  color: rgba(0, 0, 0, 0.88);
  text-align: left;
}

.recent-item:hover {
  background: #f5f5f5;
}

.recent-thumb {
  width: 32px;
  height: 32px;
  border-radius: 8px;
  flex-shrink: 0;
  background: linear-gradient(135deg, #1d3557, #52b6ff);
}

.recent-icon {
  font-size: 16px;
  flex-shrink: 0;
  color: rgba(0, 0, 0, 0.35);
}

.recent-delete-icon {
  margin-left: auto;
  color: rgba(0, 0, 0, 0.25);
  opacity: 0;
  transition: opacity 0.2s;
}

.recent-item:hover .recent-delete-icon {
  opacity: 1;
}

.recent-delete-icon:hover {
  color: #ff4d4f;
}

.history-loading,
.history-empty {
  font-size: 12px;
  color: rgba(0, 0, 0, 0.35);
  padding: 8px 0;
}

.recent-text {
  font-size: 13px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

[data-theme='dark'] .app-shell-sider.ant-layout-sider,
[data-theme='dark'] .two-level-sidebar,
[data-theme='dark'] .primary-sidebar,
[data-theme='dark'] .secondary-sidebar {
  background: #141414;
  border-color: #303030;
}


[data-theme='dark'] .secondary-header {
  background: #141414;
  border-color: #303030;
}

[data-theme='dark'] .quick-new-chat-btn {
  color: rgba(255, 255, 255, 0.86);
}

[data-theme='dark'] .quick-new-chat-btn:hover {
  color: #4096ff;
}

[data-theme='dark'] .secondary-collapse-btn {
  border-left-color: #303030;
}

[data-theme='dark'] .primary-nav-item,
[data-theme='dark'] .primary-bell-btn,
[data-theme='dark'] .secondary-header,
[data-theme='dark'] .secondary-collapse-btn,
[data-theme='dark'] .recent-item {
  color: rgba(255, 255, 255, 0.86);
}

[data-theme='dark'] .primary-nav-item:hover,
[data-theme='dark'] .primary-nav-item.active,
[data-theme='dark'] .primary-bell-btn:hover,
[data-theme='dark'] .secondary-collapse-btn:hover,
[data-theme='dark'] .recent-item:hover,
[data-theme='dark'] .secondary-menu .ant-menu-item-selected {
  background: #262626;
}

[data-theme='dark'] .recent-delete-icon {
  color: rgba(255, 255, 255, 0.25);
}

[data-theme='dark'] .recent-delete-icon:hover {
  color: #ff4d4f;
}

[data-theme='dark'] .points-pill {
  background: rgba(0, 166, 237, 0.12);
}

.theme-toggle-btn {
  position: fixed;
  top: 24px;
  right: 28px;
  z-index: 20;
  width: 32px;
  height: 32px;
  border-radius: 8px;
  background: transparent;
  color: rgba(0, 0, 0, 0.58);
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
}

.theme-toggle-btn:hover {
  background: #f2f3f5;
  color: rgba(0, 0, 0, 0.88);
}


</style>
