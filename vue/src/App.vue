<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { ConfigProvider, Layout, Menu, Dropdown, Tooltip } from 'ant-design-vue'
import { useRouter, useRoute } from 'vue-router'
import { useUserStore } from '@/stores/user'
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
  BellOutlined,
  MobileOutlined,
} from '@ant-design/icons-vue'
import type { MenuTheme } from 'ant-design-vue'

const router = useRouter()
const route = useRoute()
const userStore = useUserStore()

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
  { key: 'inspiration', label: '灵感', icon: HomeOutlined },
  { key: 'generate', label: '生成', icon: AppstoreOutlined },
  { key: 'assets', label: '资产', icon: FolderOutlined },
  { key: 'canvas', label: '画布', icon: AppstoreOutlined },
]

const selectedPrimaryKey = ref('generate')

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
    // 检查文件大小（最大2MB）
    if (file.size > 2 * 1024 * 1024) {
      alert('图片大小不能超过2MB')
      return
    }
    // 读取文件并预览
    const reader = new FileReader()
    reader.onload = (e) => {
      const base64 = e.target?.result as string
      userStore.updateAvatar(base64)
    }
    reader.readAsDataURL(file)
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
                <div class="brand-mark">✦</div>

                <nav class="primary-nav">
                  <button
                    v-for="item in primaryNavItems"
                    :key="item.key"
                    class="primary-nav-item"
                    :class="{ active: selectedPrimaryKey === item.key }"
                    type="button"
                    @click="selectedPrimaryKey = item.key"
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
                          :size="32"
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
                          <Menu.Item @click="router.push('/')">
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

                  <button class="primary-tool-btn" type="button">
                    <BellOutlined />
                  </button>
                  <button class="primary-tool-btn" type="button">
                    <MobileOutlined />
                    <span>CLI</span>
                  </button>
                </div>
              </aside>

              <aside class="secondary-sidebar" :class="{ collapsed }">
                <div class="secondary-header">
                  <button class="quick-new-chat-btn" type="button" @click="selectedKeys = ['new-chat']">
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
                    @select="({ key }) => (selectedKeys = [String(key)])"
                  >
                    <Menu.Item key="new-chat">
                      <template #icon>
                        <EditOutlined />
                      </template>
                      新对话
                    </Menu.Item>
                    <Menu.Item key="default-create">
                      <template #icon>
                        <MessageOutlined />
                      </template>
                      默认创作
                    </Menu.Item>
                  </Menu>

                  <div class="recent-section">
                    <div class="recent-title">最近</div>
                    <button class="recent-item" type="button">
                      <span class="recent-thumb"></span>
                      <span class="recent-text">未来机甲战士都市废墟</span>
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
  color: #12b5ff;
  font-size: 24px;
  font-weight: 700;
  margin-bottom: 140px;
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
  width: 40px;
  height: 40px;
  border: none;
  border-radius: 50%;
  background: transparent;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  padding: 0;
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

.primary-tool-btn {
  width: 40px;
  min-height: 36px;
  border: none;
  border-radius: 8px;
  background: transparent;
  color: rgba(0, 0, 0, 0.68);
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 2px;
  font-size: 11px;
  cursor: pointer;
}

.primary-tool-btn:hover {
  background: #f2f3f5;
  color: rgba(0, 0, 0, 0.88);
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
[data-theme='dark'] .primary-tool-btn,
[data-theme='dark'] .secondary-header,
[data-theme='dark'] .secondary-collapse-btn,
[data-theme='dark'] .recent-item {
  color: rgba(255, 255, 255, 0.86);
}

[data-theme='dark'] .primary-nav-item:hover,
[data-theme='dark'] .primary-nav-item.active,
[data-theme='dark'] .primary-tool-btn:hover,
[data-theme='dark'] .secondary-collapse-btn:hover,
[data-theme='dark'] .recent-item:hover,
[data-theme='dark'] .secondary-menu .ant-menu-item-selected {
  background: #262626;
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
