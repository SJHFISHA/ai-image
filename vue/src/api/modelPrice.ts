/**
 * 模型价格相关接口
 */
import request from '@/utils/request'

// 查询模型价格配置
export function getModelPrices(capabilityType?: string) {
  const params: Record<string, string> = {}
  if (capabilityType) {
    params.capability_type = capabilityType
  }
  return request.get('/model-prices', { params })
}
