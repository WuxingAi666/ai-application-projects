import api from './index'

/**
 * 上传音频文件进行分析
 */
export function analyzeAudio(audioBlob, filename, fusionMethod = 'cross_attention') {
  const formData = new FormData()
  formData.append('audio', audioBlob, filename)
  return api.post(`/analyze?fusion_method=${fusionMethod}`, formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
  })
}

/**
 * 获取历史记录列表
 */
export function getHistory(page = 1, pageSize = 20) {
  return api.get('/history', { params: { page, page_size: pageSize } })
}

/**
 * 获取单条记录详情
 */
export function getHistoryDetail(id) {
  return api.get(`/history/${id}`)
}

/**
 * 删除历史记录
 */
export function deleteHistory(id) {
  return api.delete(`/history/${id}`)
}

/**
 * 健康检查
 */
export function healthCheck() {
  return api.get('/health')
}
