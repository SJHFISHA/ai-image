/**
 * 会话历史相关接口
 */
import { httpGet, httpPost, httpDelete } from '@/utils/request'

// 类型定义
export interface ConversationItem {
  session_id: string
  title?: string
  session_type: string
  last_message_preview?: string
  last_message_at?: string
  created_at: string
}

export interface ConversationListResult {
  total: number
  items: ConversationItem[]
}

export interface MediaAsset {
  asset_id: string
  media_type: string
  url: string
  mime_type?: string
  file_size?: number
  width?: number
  height?: number
}

export interface ConversationMessage {
  message_id: string
  role: string
  content_type: string
  content_text?: string
  task_id?: string
  status: string
  metadata_json?: Record<string, any>
  assets: MediaAsset[]
  created_at: string
}

export interface ConversationDetail {
  session_id: string
  title?: string
  session_type: string
  messages: ConversationMessage[]
}

// 创建会话
export function createConversation(data: {
  session_type?: string
  title?: string
}) {
  return httpPost<ConversationItem>('/conversations', data)
}

// 获取会话列表
export function getConversationList(params?: { page?: number; page_size?: number }) {
  return httpGet<ConversationListResult>('/conversations', { params })
}

// 获取会话详情
export function getConversationDetail(sessionId: string) {
  return httpGet<ConversationDetail>(`/conversations/${sessionId}`)
}

// 删除会话
export function deleteConversation(sessionId: string) {
  return httpDelete(`/conversations/${sessionId}`)
}
