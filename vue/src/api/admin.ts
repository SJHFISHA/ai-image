/**
 * 管理员相关接口
 */
import { httpGet, httpPost, httpPut, httpDelete } from '@/utils/request'

// ======================== 类型定义 ========================

export interface AdminLoginParams {
  username: string
  password: string
}

export interface AdminInfo {
  id: number
  username: string
  nickname?: string
  role: string
}

export interface AdminLoginResult {
  access_token: string
  token_type: string
  admin: AdminInfo
}

export interface AdminNotification {
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
  created_by?: number
  created_at: string
  updated_at: string
}

export interface AdminNotificationCreateParams {
  title: string
  content: string
  type?: string
  level?: string
  status?: string
  target_type?: string
  publish_at?: string
  expire_at?: string
}

export interface AdminNotificationListResult {
  total: number
  items: AdminNotification[]
}

// 模型配置
export interface ModelConfig {
  id: number
  model_key: string
  model_name: string
  provider_key: string
  route_mode?: string
  capability_type: string
  enabled: number
  sort_order: number
  remark?: string
  created_at: string
  updated_at: string
}

export interface ModelConfigCreateParams {
  model_key: string
  model_name: string
  provider_key: string
  route_mode?: string
  capability_type: string
  enabled?: number
  sort_order?: number
  remark?: string
}

export interface ModelConfigListResult {
  total: number
  items: ModelConfig[]
}

// 模型价格配置
export interface ModelPriceConfig {
  id: number
  model_id: number
  model_key: string
  model_name: string
  capability_type: string
  provider_key: string
  billing_mode: string
  image_size?: string
  image_count: number
  aspect_ratio?: string
  video_duration?: number
  video_resolution?: string
  points: number
  cost_amount?: number
  cost_currency: string
  enabled: number
  sort_order: number
  remark?: string
  created_at: string
  updated_at: string
}

export interface ModelPriceConfigCreateParams {
  model_id: number
  billing_mode?: string
  image_size?: string
  image_count?: number
  aspect_ratio?: string
  video_duration?: number
  video_resolution?: string
  points: number
  cost_amount?: number
  cost_currency?: string
  enabled?: number
  sort_order?: number
  remark?: string
}

export interface ModelPriceConfigListResult {
  total: number
  items: ModelPriceConfig[]
}

// 充值套餐
export interface RechargePackage {
  id: number
  package_name: string
  amount: number
  base_points: number
  bonus_points: number
  total_points: number
  enabled: number
  sort_order: number
  created_at: string
  updated_at: string
}

export interface RechargePackageCreateParams {
  package_name: string
  amount: number
  base_points: number
  bonus_points?: number
  total_points: number
  enabled?: number
  sort_order?: number
}

export interface RechargePackageListResult {
  total: number
  items: RechargePackage[]
}

// 充值订单
export interface RechargeOrder {
  id: number
  order_no: string
  user_id: number
  package_id: number
  package_name: string
  amount: number
  currency: string
  base_points: number
  bonus_points: number
  total_points: number
  pay_channel?: string
  pay_status: string
  pay_trade_no?: string
  paid_at?: string
  created_at: string
  updated_at: string
}

export interface RechargeOrderListResult {
  total: number
  items: RechargeOrder[]
}

// 用户积分账户
export interface PointAccount {
  id: number
  user_id: number
  username?: string
  balance_points: number
  frozen_points: number
  total_recharged_points: number
  total_consumed_points: number
  created_at: string
  updated_at: string
}

export interface PointAccountListResult {
  total: number
  items: PointAccount[]
}

// 积分流水
export interface PointTransaction {
  id: number
  transaction_no: string
  user_id: number
  username?: string
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

export interface PointTransactionListResult {
  total: number
  items: PointTransaction[]
}

// ======================== API 调用 ========================

// 管理员认证
export function adminLogin(data: AdminLoginParams) {
  return httpPost<AdminLoginResult>('/admin/auth/login', data)
}

export function getAdminInfo() {
  return httpGet<AdminInfo>('/admin/auth/me')
}

export function getAdminNotificationList(params?: {
  keyword?: string
  status_filter?: string
  page?: number
  page_size?: number
}) {
  return httpGet<AdminNotificationListResult>('/admin/notifications', { params })
}

export function createAdminNotification(data: AdminNotificationCreateParams) {
  return httpPost<AdminNotification>('/admin/notifications', data)
}

export function updateAdminNotification(id: number, data: Partial<AdminNotificationCreateParams>) {
  return httpPut<AdminNotification>(`/admin/notifications/${id}`, data)
}

export function deleteAdminNotification(id: number) {
  return httpDelete(`/admin/notifications/${id}`)
}

export function publishAdminNotification(id: number) {
  return httpPost<AdminNotification>(`/admin/notifications/${id}/publish`)
}

export function disableAdminNotification(id: number) {
  return httpPost<AdminNotification>(`/admin/notifications/${id}/disable`)
}

// 模型配置
export function getModelConfigList(params?: {
  capability_type?: string
  keyword?: string
  enabled?: number
  page?: number
  page_size?: number
}) {
  return httpGet<ModelConfigListResult>('/admin/model-configs', { params })
}

export function createModelConfig(data: ModelConfigCreateParams) {
  return httpPost<ModelConfig>('/admin/model-configs', data)
}

export function updateModelConfig(id: number, data: Partial<ModelConfigCreateParams>) {
  return httpPut<ModelConfig>(`/admin/model-configs/${id}`, data)
}

export function deleteModelConfig(id: number) {
  return httpDelete(`/admin/model-configs/${id}`)
}

// 模型价格配置
export function getModelPriceList(params?: {
  capability_type?: string
  keyword?: string
  enabled?: number
  page?: number
  page_size?: number
}) {
  return httpGet<ModelPriceConfigListResult>('/admin/model-prices', { params })
}

export function createModelPriceConfig(data: ModelPriceConfigCreateParams) {
  return httpPost<ModelPriceConfig>('/admin/model-prices', data)
}

export function updateModelPriceConfig(id: number, data: Partial<ModelPriceConfigCreateParams>) {
  return httpPut<ModelPriceConfig>(`/admin/model-prices/${id}`, data)
}

export function deleteModelPriceConfig(id: number) {
  return httpDelete(`/admin/model-prices/${id}`)
}

// 充值套餐
export function getRechargePackageList(params?: {
  keyword?: string
  enabled?: number
  page?: number
  page_size?: number
}) {
  return httpGet<RechargePackageListResult>('/admin/recharge-packages', { params })
}

export function createRechargePackage(data: RechargePackageCreateParams) {
  return httpPost<RechargePackage>('/admin/recharge-packages', data)
}

export function updateRechargePackage(id: number, data: Partial<RechargePackageCreateParams>) {
  return httpPut<RechargePackage>(`/admin/recharge-packages/${id}`, data)
}

export function deleteRechargePackage(id: number) {
  return httpDelete(`/admin/recharge-packages/${id}`)
}

// 充值订单
export function getRechargeOrderList(params?: {
  user_id?: number
  pay_status?: string
  order_no?: string
  page?: number
  page_size?: number
}) {
  return httpGet<RechargeOrderListResult>('/admin/recharge-orders', { params })
}

export function updateRechargeOrderStatus(id: number, pay_status: string) {
  return httpPut<RechargeOrder>(`/admin/recharge-orders/${id}/status`, { pay_status })
}

// 用户积分账户
export function getPointAccountList(params?: {
  user_id?: number
  keyword?: string
  page?: number
  page_size?: number
}) {
  return httpGet<PointAccountListResult>('/admin/point-accounts', { params })
}

export function adjustUserPoints(data: { user_id: number; points: number; remark: string }) {
  return httpPost<PointAccount>('/admin/point-accounts/adjust', data)
}

// 积分流水
export function getPointTransactionList(params?: {
  user_id?: number
  transaction_type?: string
  page?: number
  page_size?: number
}) {
  return httpGet<PointTransactionListResult>('/admin/point-transactions', { params })
}

// ======================== 用户管理 ========================

export interface AdminUser {
  id: number
  username?: string
  email?: string
  phone?: string
  nickname?: string
  avatar_url?: string
  status: string
  last_login_at?: string
  created_at: string
  updated_at: string
}

export interface AdminUserListResult {
  total: number
  items: AdminUser[]
}

export function getAdminUserList(params?: {
  keyword?: string
  status?: string
  page?: number
  page_size?: number
}) {
  return httpGet<AdminUserListResult>('/admin/users', { params })
}

export function updateAdminUserStatus(id: number, status: string) {
  return httpPut<AdminUser>(`/admin/users/${id}/status`, { status })
}

// ======================== 生成任务管理 ========================

export interface AdminTask {
  id: number
  task_id: string
  user_id: number
  username?: string
  price_config_id: number
  model_key: string
  model_name: string
  capability_type: string
  image_size?: string
  image_count?: number
  status: string
  frozen_points: number
  consumed_points: number
  refunded_points: number
  prompt?: string
  error_message?: string
  request_json?: Record<string, any>
  provider_response_json?: Record<string, any>
  created_at: string
  started_at?: string
  finished_at?: string
}

export interface AdminTaskListResult {
  total: number
  items: AdminTask[]
}

export function getAdminTaskList(params?: {
  user_id?: number
  status?: string
  task_id?: string
  keyword?: string
  page?: number
  page_size?: number
}) {
  return httpGet<AdminTaskListResult>('/admin/tasks', { params })
}
