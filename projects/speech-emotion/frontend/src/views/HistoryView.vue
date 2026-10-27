<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useAnalysisStore } from '@/stores/analysis'
import { ElMessageBox } from 'element-plus'

const store = useAnalysisStore()
const router = useRouter()
const loading = ref(false)

const emotionConfig = {
  '开心': { emoji: '😊', color: '#34d399' },
  '悲伤': { emoji: '😢', color: '#60a5fa' },
  '愤怒': { emoji: '😠', color: '#f87171' },
  '中性': { emoji: '😐', color: '#a09cbd' },
  '惊讶': { emoji: '😲', color: '#fbbf24' },
  '恐惧': { emoji: '😨', color: '#a78bfa' },
}

onMounted(async () => {
  loading.value = true
  await store.loadHistory()
  loading.value = false
})

async function viewDetail(id) {
  try {
    await store.loadHistoryDetail(id)
    router.push('/')
  } catch (e) {}
}

async function handleDelete(id) {
  try {
    await ElMessageBox.confirm('确定要删除这条记录吗？', '确认删除', { type: 'warning' })
    await store.removeHistory(id)
  } catch (e) {}
}

function formatDate(dateStr) {
  if (!dateStr) return '—'
  const d = new Date(dateStr)
  return d.toLocaleString('zh-CN', {
    month: '2-digit', day: '2-digit',
    hour: '2-digit', minute: '2-digit',
  })
}
</script>

<template>
  <div class="history-page">
    <div class="history-header">
      <h2>📋 历史分析记录</h2>
      <span class="count">共 {{ store.historyTotal }} 条</span>
    </div>

    <!-- 加载中 -->
    <div v-if="loading" class="history-loading">
      <p>加载中...</p>
    </div>

    <!-- 空状态 -->
    <div v-else-if="store.history.length === 0" class="history-empty glass-card">
      <span class="empty-icon">📭</span>
      <p>暂无分析记录</p>
      <el-button type="primary" @click="router.push('/')">去分析</el-button>
    </div>

    <!-- 记录列表 -->
    <div v-else class="history-list">
      <div
        v-for="item in store.history"
        :key="item.id"
        class="history-item glass-card"
        @click="viewDetail(item.id)"
      >
        <div class="item-main">
          <span class="item-emoji" :style="{ color: emotionConfig[item.emotion_label]?.color }">
            {{ emotionConfig[item.emotion_label]?.emoji || '😐' }}
          </span>
          <div class="item-info">
            <span class="item-emotion" :style="{ color: emotionConfig[item.emotion_label]?.color }">
              {{ item.emotion_label }}
            </span>
            <span class="item-confidence">
              置信度 {{ Math.round(item.confidence * 100) }}%
            </span>
            <span class="item-transcript" v-if="item.transcript_preview">
              "{{ item.transcript_preview }}"
            </span>
          </div>
        </div>
        <div class="item-meta">
          <span class="item-time">{{ formatDate(item.created_at) }}</span>
          <span class="item-duration">{{ item.duration?.toFixed(1) }}s</span>
          <el-button
            type="danger"
            size="small"
            text
            @click.stop="handleDelete(item.id)"
          >
            <el-icon><Delete /></el-icon>
          </el-button>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.history-page {
  max-width: 800px;
  margin: 0 auto;
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.history-header {
  display: flex;
  align-items: baseline;
  gap: 12px;
}

.history-header h2 {
  font-size: 22px;
  color: var(--text-primary);
}

.count {
  color: var(--text-muted);
  font-size: 14px;
}

.history-loading,
.history-empty {
  text-align: center;
  padding: 60px 20px;
}

.empty-icon {
  font-size: 48px;
  display: block;
  margin-bottom: 12px;
}

.history-empty p {
  color: var(--text-secondary);
  margin-bottom: 16px;
}

.history-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.history-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px 20px;
  cursor: pointer;
  transition: all 0.3s ease;
}

.history-item:hover {
  transform: translateX(4px);
  border-color: rgba(124,92,252,0.3);
}

.item-main {
  display: flex;
  align-items: center;
  gap: 14px;
}

.item-emoji {
  font-size: 32px;
}

.item-info {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.item-emotion {
  font-size: 17px;
  font-weight: 700;
}

.item-confidence {
  font-size: 12px;
  color: var(--text-muted);
}

.item-transcript {
  font-size: 12px;
  color: var(--text-secondary);
  font-style: italic;
  margin-top: 2px;
}

.item-meta {
  display: flex;
  align-items: center;
  gap: 12px;
  flex-shrink: 0;
}

.item-time,
.item-duration {
  color: var(--text-muted);
  font-size: 12px;
}
</style>
