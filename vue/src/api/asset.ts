import { httpGet } from '@/utils/request'

export type AssetType = 'image' | 'video' | 'audio'

export interface AssetItem {
  id: number
  asset_id: string
  task_id: string
  type: AssetType
  url: string
  cover_url?: string
  title?: string
  prompt?: string
  model_name?: string
  created_at: string
}

export interface AssetListResult {
  total: number
  items: AssetItem[]
}

export function getAssets(params?: {
  type?: AssetType
  page?: number
  page_size?: number
}) {
  return httpGet<AssetListResult>('/assets', { params })
}
