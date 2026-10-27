import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { analyzeAudio, getHistory, getHistoryDetail, deleteHistory } from '@/api/analyze'

export const useAnalysisStore = defineStore('analysis', () => {
  // ========== 状态 ==========
  const currentResult = ref(null)
  const isAnalyzing = ref(false)
  const error = ref(null)
  const history = ref([])
  const historyTotal = ref(0)
  const fusionMethod = ref('late_fusion')

  // ========== 计算属性 ==========
  const hasResult = computed(() => currentResult.value !== null)
  const emotionLabel = computed(() => currentResult.value?.fused_emotion?.label || '—')
  const emotionConfidence = computed(() => {
    const conf = currentResult.value?.fused_emotion?.confidence || 0
    return Math.round(conf * 100)
  })

  // ========== 动作 ==========

  /**
   * 分析音频
   */
  async function analyze(audioBlob, filename) {
    isAnalyzing.value = true
    error.value = null
    currentResult.value = null

    try {
      const response = await analyzeAudio(audioBlob, filename, fusionMethod.value)
      currentResult.value = response.data
      return response.data
    } catch (e) {
      error.value = e.message || '分析失败'
      throw e
    } finally {
      isAnalyzing.value = false
    }
  }

  /**
   * 加载历史记录
   */
  async function loadHistory(page = 1) {
    try {
      const response = await getHistory(page)
      history.value = response.data.items
      historyTotal.value = response.data.total
      return response.data
    } catch (e) {
      history.value = []
      return { items: [], total: 0 }
    }
  }

  /**
   * 加载单条历史详情
   */
  async function loadHistoryDetail(id) {
    try {
      const response = await getHistoryDetail(id)
      currentResult.value = response.data
      return response.data
    } catch (e) {
      throw e
    }
  }

  /**
   * 删除历史记录
   */
  async function removeHistory(id) {
    await deleteHistory(id)
    history.value = history.value.filter((item) => item.id !== id)
    historyTotal.value = Math.max(0, historyTotal.value - 1)
  }

  /**
   * 清除当前结果
   */
  function clearResult() {
    currentResult.value = null
    error.value = null
  }

  return {
    currentResult,
    isAnalyzing,
    error,
    history,
    historyTotal,
    fusionMethod,
    hasResult,
    emotionLabel,
    emotionConfidence,
    analyze,
    loadHistory,
    loadHistoryDetail,
    removeHistory,
    clearResult,
  }
})
