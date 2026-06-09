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
  DownOutlined,
  UserOutlined,
  LogoutOutlined,
  PictureOutlined,
} from '@ant-design/icons-vue'
import type { MenuTheme } from 'ant-design-vue'

const router = useRouter()
const route = useRoute()
const userStore = useUserStore()

// 判断是否为登录/注册页，这些页面不显示侧边栏
const isAuthPage = computed(() => ['login', 'register'].includes(route.name as string))

const { Sider, Content } = Layout

const isDark = ref(false)
const collapsed = ref(false)
const selectedKeys = ref<string[]>(['new-chat'])

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
            v-model:collapsed="collapsed"
            :collapsed-width="0"
            :width="240"
            class="app-sider"
            :theme="siderTheme"
            :trigger="null"
            collapsible
          >
            <div class="sider-header">
              <span v-if="!collapsed">开启创作</span>
              <span v-else style="font-size: 14px">菜单</span>
              <div class="sider-header-actions">
                <Tooltip :title="collapsed ? '展开菜单' : '收起菜单'">
                  <MenuUnfoldOutlined
                    v-if="collapsed"
                    class="sider-collapse-btn"
                    @click="collapsed = false"
                  />
                  <MenuFoldOutlined
                    v-else
                    class="sider-collapse-btn"
                    @click="collapsed = true"
                  />
                </Tooltip>
              </div>
            </div>
            <Menu
              v-if="!collapsed"
              v-model:selectedKeys="selectedKeys"
              mode="inline"
              :theme="siderTheme"
              class="sider-menu"
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

            <!-- 底部用户信息 -->
            <div class="sider-footer">
              <template v-if="userStore.isLoggedIn">
                <input
                  ref="avatarInput"
                  type="file"
                  accept="image/*"
                  style="display: none"
                  @change="handleAvatarChange"
                />
                <Dropdown :trigger="['click']">
                  <div class="user-avatar-wrap">
                    <a-avatar
                      :size="36"
                      :src="userStore.userInfo?.avatar_url"
                      class="user-avatar"
                    >
                      <template #icon><UserOutlined /></template>
                    </a-avatar>
                    <span class="user-name">{{ userStore.userInfo?.username }}</span>
                    <DownOutlined style="font-size: 10px; color: #999" />
                  </div>
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
                <a-button type="primary" size="small" block @click="router.push('/login')">
                  登录
                </a-button>
              </template>
            </div>
          </Sider>

          <!-- 收起后显示的展开按钮 -->
          <div v-if="collapsed" class="sider-expand-btn-wrap">
            <Tooltip title="展开菜单">
              <MenuUnfoldOutlined class="sider-expand-btn" @click="collapsed = false" />
            </Tooltip>
          </div>

          <Layout>
            <Content class="main-content">
              <router-view />
            </Content>
          </Layout>
        </Layout>
      </template>

      <div class="theme-toggle-btn" @click="toggleTheme">
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

.sider-header-actions {
  display: flex;
  align-items: center;
  gap: 4px;
}

.sider-expand-btn-wrap {
  position: absolute;
  top: 12px;
  left: 12px;
  z-index: 10;
}

.top-bar {
  height: 48px;
  background: #fff;
  border-bottom: 1px solid #f0f0f0;
  display: flex;
  align-items: center;
  justify-content: flex-end;
  padding: 0 16px;
}

.top-bar-right {
  display: flex;
  align-items: center;
  gap: 8px;
}

.user-avatar-wrap {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 12px;
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.3s;
  width: 100%;
}

.user-avatar-wrap:hover {
  background: rgba(0, 0, 0, 0.04);
}

.user-avatar {
  cursor: pointer;
  flex-shrink: 0;
}

.user-name {
  flex: 1;
  font-size: 14px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
</style>
