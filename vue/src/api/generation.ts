/**
 * 生图任务相关接口
 */
import request from '@/utils/request'

// 创建生图任务
export function createImageTask(data: {
  price_config_id: number
  prompt: string
}) {
  return request.post('/image/generate', data)
}

// 查询任务详情
export function getTaskDetail(taskId: string) {
  return request.get(`/tasks/${taskId}`)
}

// 查询我的任务列表
export function getMyTasks(params?: {
  page?: number
  page_size?: number
}) {
  return request.get('/tasks', { params })
}
