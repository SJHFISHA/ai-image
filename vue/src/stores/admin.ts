/**
 * 管理员状态管理
 */
import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { adminLogin as adminLoginApi, getAdminInfo } from '@/api/admin'
import type { AdminInfo } from '@/api/admin'
import { message } from 'ant-design-vue'
import router from '@/router'

const ADMIN_TOKEN_KEY = 'admin_access_token'

export const useAdminStore = defineStore('admin', () => {
  const token = ref<string>(localStorage.getItem(ADMIN_TOKEN_KEY) || '')
  const adminInfo = ref<AdminInfo | null>(null)

  const isLoggedIn = computed(() => !!token.value)

  async function login(username: string, password: string) {
    try {
      const res = await adminLoginApi({ username, password })
      token.value = res.access_token
      adminInfo.value = res.admin
      localStorage.setItem(ADMIN_TOKEN_KEY, res.access_token)
      message.success('登录成功')
      router.push('/admin')
      return true
    } catch {
      return false
    }
  }

  async function fetchAdminInfo() {
    try {
      const res = await getAdminInfo()
      adminInfo.value = res
      return true
    } catch {
      return false
    }
  }

  function logout() {
    token.value = ''
    adminInfo.value = null
    localStorage.removeItem(ADMIN_TOKEN_KEY)
    message.success('已退出登录')
    router.push('/admin/login')
  }

  async function init() {
    if (token.value) {
      const success = await fetchAdminInfo()
      if (!success) {
        // 拦截器已处理 401 跳转，这里只清理状态
        token.value = ''
        adminInfo.value = null
        localStorage.removeItem(ADMIN_TOKEN_KEY)
      }
    }
  }

  return {
    token,
    adminInfo,
    isLoggedIn,
    login,
    fetchAdminInfo,
    logout,
    init
  }
})
