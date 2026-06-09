/**
 * 认证相关接口
 */
import request from '@/utils/request'

// 注册
export function register(data: {
  username: string
  password: string
  confirm_password: string
}) {
  return request.post('/auth/register', data)
}

// 登录
export function login(data: {
  username: string
  password: string
}) {
  return request.post('/auth/login', data)
}

// 获取当前用户信息
export function getUserInfo() {
  return request.get('/auth/me')
}
