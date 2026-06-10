/**
 * 积分相关接口（用户端）
 */
import { httpGet } from '@/utils/request'

// 响应数据类型
export interface PointBalance {
  balance_points: number
  frozen_points: number
  total_recharged_points: number
  total_consumed_points: number
}

export interface UserPointTransaction {
  transaction_no: string
  type: string
  direction: string
  points: number
  balance_before: number
  balance_after: number
  frozen_before: number
  frozen_after: number
  related_order_no?: string
  related_task_id?: string
  remark?: string
  created_at: string
}

export interface PointTransactionList {
  total: number
  items: UserPointTransaction[]
}

// 查询积分余额
export function getPointBalance() {
  return httpGet<PointBalance>('/user/points')
}

// 查询积分流水
export function getPointLogs(params?: { page?: number; page_size?: number }) {
  return httpGet<PointTransactionList>('/user/point-logs', { params })
}
