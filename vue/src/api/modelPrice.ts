/**
 * 模型价格相关接口
 */
import { httpGet } from '@/utils/request'

// 响应数据类型
export interface ModelPriceItem {
  id: number
  model_key: string
  model_name: string
  capability_type: string
  image_size?: string
  image_count?: number
  video_duration?: number
  video_resolution?: string
  points: number
}

export interface ModelPriceListResult {
  total: number
  items: ModelPriceItem[]
}

// 查询模型价格配置
export function getModelPrices(capabilityType?: string) {
  const params: Record<string, string> = {}
  if (capabilityType) {
    params.capability_type = capabilityType
  }
  return httpGet<ModelPriceListResult>('/model-prices', { params })
}
