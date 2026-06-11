/**
 * 认证相关接口
 */
import { httpGet, httpPost } from '@/utils/request'

// 请求参数类型
export interface RegisterParams {
  username: string
  password: string
  confirm_password: string
}

export interface LoginParams {
  username: string
  password: string
}

// 响应数据类型
export interface UserInfo {
  id: number
  username: string
  nickname?: string
  avatar_url?: string
  available_points?: number
}

export interface TokenResult {
  access_token: string
  token_type: string
  user: UserInfo
}

export interface RegisterResult {
  message: string
  user: UserInfo
}

export interface AvatarUploadResult {
  avatar_url: string
}

// 注册
export function register(data: RegisterParams) {
  return httpPost<RegisterResult>('/auth/register', data)
}

// 登录
export function login(data: LoginParams) {
  return httpPost<TokenResult>('/auth/login', data)
}

// 获取当前用户信息
export function getUserInfo() {
  return httpGet<UserInfo>('/auth/me')
}

// 上传头像
export function uploadAvatar(file: File) {
  const formData = new FormData()
  formData.append('file', file)
  return httpPost<AvatarUploadResult>('/auth/avatar', formData, {
    headers: { 'Content-Type': undefined }
  })
}
