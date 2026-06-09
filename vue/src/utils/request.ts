/**
 * Axios 请求封装
 */
import axios, { type AxiosRequestConfig } from 'axios'
import { message } from 'ant-design-vue'
import router from '@/router'

// 创建 axios 实例
const request = axios.create({
  baseURL: '/api',
  timeout: 300000,
  headers: {
    'Content-Type': 'application/json'
  }
})

// 请求拦截器
request.interceptors.request.use(
  (config) => {
    // 根据请求路径自动选择 token：管理员接口用 admin_access_token，普通接口用 access_token
    const url = config.url || ''
    const isAdminApi = url.startsWith('/admin/')
    const tokenKey = isAdminApi ? 'admin_access_token' : 'access_token'
    const token = localStorage.getItem(tokenKey)
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }
    return config
  },
  (error) => {
    return Promise.reject(error)
  }
)

// 响应拦截器
request.interceptors.response.use(
  (response) => {
    const res = response.data

    // 处理统一的 ApiResponse 结构
    if (res && typeof res === 'object' && 'success' in res) {
      // 统一响应结构处理
      if (res.success === false) {
        message.error(res.message || '请求失败')
        return Promise.reject(res)
      }
      // 成功时只返回 data 字段
      return res.data
    }

    // 兼容非统一结构的响应（历史接口）
    return res
  },
  (error) => {
    const { response } = error

    if (response) {
      // 尝试从统一响应结构中获取错误信息
      const res = response.data
      const errorMessage = res?.message || res?.detail || '请求失败'

      switch (response.status) {
        case 401:
          // token 过期或无效，根据路径判断跳转到用户还是管理员登录页
          const reqUrl = error?.config?.url || ''
          if (reqUrl.startsWith('/admin/')) {
            localStorage.removeItem('admin_access_token')
            message.error('管理员登录已过期，请重新登录')
            router.push('/admin/login')
          } else {
            localStorage.removeItem('access_token')
            message.error('登录已过期，请重新登录')
            router.push('/login')
          }
          break
        case 403:
          message.error(errorMessage || '没有权限访问')
          break
        case 404:
          message.error(errorMessage || '请求的资源不存在')
          break
        case 422:
          message.error(errorMessage || '参数校验失败')
          break
        case 500:
          message.error(errorMessage || '服务器内部错误')
          break
        default:
          message.error(errorMessage)
      }
    } else {
      message.error('网络连接失败')
    }

    return Promise.reject(error)
  }
)

/**
 * 类型安全的请求封装
 * 拦截器已经解包了 ApiResponse，所以返回值直接是 T
 */
export function httpGet<T = any>(url: string, config?: AxiosRequestConfig): Promise<T> {
  return request.get(url, config) as unknown as Promise<T>
}

export function httpPost<T = any>(url: string, data?: any, config?: AxiosRequestConfig): Promise<T> {
  return request.post(url, data, config) as unknown as Promise<T>
}

export function httpPut<T = any>(url: string, data?: any, config?: AxiosRequestConfig): Promise<T> {
  return request.put(url, data, config) as unknown as Promise<T>
}

export function httpDelete<T = any>(url: string, config?: AxiosRequestConfig): Promise<T> {
  return request.delete(url, config) as unknown as Promise<T>
}

export default request
