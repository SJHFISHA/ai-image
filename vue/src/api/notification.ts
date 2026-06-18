import { httpGet, httpPost } from '@/utils/request'

export interface NotificationItem {
  id: number
  notification_id: string
  title: string
  content: string
  type: string
  level: string
  status: string
  target_type: string
  publish_at?: string
  expire_at?: string
  is_read?: boolean
  created_by?: number
  created_at: string
  updated_at: string
}

export interface NotificationListResult {
  total: number
  items: NotificationItem[]
}

export interface NotificationUnreadCountResult {
  unread_count: number
}

export function getNotificationList(params?: {
  page?: number
  page_size?: number
}) {
  return httpGet<NotificationListResult>('/notifications', { params })
}

export function getNotificationUnreadCount() {
  return httpGet<NotificationUnreadCountResult>('/notifications/unread-count')
}

export function markNotificationRead(notificationId: string) {
  return httpPost(`/notifications/${notificationId}/read`)
}

export function markAllNotificationsRead() {
  return httpPost('/notifications/read-all')
}
