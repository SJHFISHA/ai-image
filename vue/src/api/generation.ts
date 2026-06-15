/**
 * 生图任务相关接口
 */
import { httpGet, httpPost } from '@/utils/request'

// 请求参数类型
export interface CreateImageTaskParams {
  session_id?: string
  price_config_id: number
  prompt: string
}

// 响应数据类型
export interface TaskCreateResult {
  task_id: string
  status: string
  frozen_points: number
  error_message?: string
  session_id?: string
}

export interface TaskDetailResult {
  task_id: string
  status: string
  model_key: string
  model_name: string
  capability_type: string
  image_size?: string
  image_count?: number
  aspect_ratio?: string
  prompt?: string
  frozen_points: number
  consumed_points: number
  refunded_points: number
  error_message?: string
  images?: string[]
  created_at: string
  finished_at?: string
}

export interface TaskListResult {
  total: number
  items: TaskDetailResult[]
}

// 创建生图任务
export function createImageTask(data: CreateImageTaskParams) {
  return httpPost<TaskCreateResult>('/image/generate', data)
}

// 查询任务详情
export function getTaskDetail(taskId: string) {
  return httpGet<TaskDetailResult>(`/tasks/${taskId}`)
}

// 查询我的任务列表
export function getMyTasks(params?: {
  page?: number
  page_size?: number
}) {
  return httpGet<TaskListResult>('/tasks', { params })
}
