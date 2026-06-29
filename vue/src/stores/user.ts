/**
 * 用户状态管理
 */
import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { login as loginApi, register as registerApi, getUserInfo, uploadAvatar as uploadAvatarApi } from '@/api/auth'
import type { UserInfo, TokenResult } from '@/api/auth'
import { message } from 'ant-design-vue'
import router from '@/router'

export const useUserStore = defineStore('user', () => {
  // 状态
  const token = ref<string>(localStorage.getItem('access_token') || '')
  const userInfo = ref<UserInfo | null>(null)

  // 计算属性
  const isLoggedIn = computed(() => !!token.value)

  // 登录
  async function login(username: string, password: string) {
    try {
      const res = await loginApi({ username, password })
      token.value = res.access_token
      localStorage.setItem('access_token', res.access_token)
      // 登录后获取完整用户信息（包含邀请码等）
      const success = await fetchUserInfo()
      if (!success) {
        // 获取用户信息失败，清除 token
        token.value = ''
        userInfo.value = null
        localStorage.removeItem('access_token')
        return false
      }
      message.success('登录成功')
      router.push('/')
      return true
    } catch (error) {
      return false
    }
  }

  // 注册
  async function register(username: string, password: string, confirmPassword: string, inviteCode?: string) {
    try {
      await registerApi({
        username,
        password,
        confirm_password: confirmPassword,
        invite_code: inviteCode
      })
      message.success('注册成功，请登录')
      router.push('/login')
      return true
    } catch (error) {
      return false
    }
  }

  // 获取用户信息
  async function fetchUserInfo() {
    try {
      const res = await getUserInfo()
      userInfo.value = res
      return true
    } catch (error) {
      return false
    }
  }

  // 更新头像（上传到七牛云）
  async function updateAvatar(file: File) {
    try {
      const res = await uploadAvatarApi(file)
      if (userInfo.value) {
        // 需要重新创建对象才能触发 Vue 响应式更新
        userInfo.value = {
          ...userInfo.value,
          avatar_url: res.avatar_url
        }
      }
      message.success('头像更新成功')
      return true
    } catch (error) {
      return false
    }
  }

  // 退出登录
  function logout() {
    token.value = ''
    userInfo.value = null
    localStorage.removeItem('access_token')
    message.success('已退出登录')
    router.push('/login')
  }

  // 初始化（检查token是否有效）
  async function init() {
    if (token.value) {
      const success = await fetchUserInfo()
      if (!success) {
        logout()
      }
    }
  }

  return {
    token,
    userInfo,
    isLoggedIn,
    login,
    register,
    fetchUserInfo,
    updateAvatar,
    logout,
    init
  }
})
