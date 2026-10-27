<script setup>
import { computed } from 'vue'

const props = defineProps({
  result: { type: Object, required: true },
})

const emotionConfig = {
  '开心': { emoji: '😊', color: '#34d399', bg: 'rgba(52,211,153,0.15)' },
  '悲伤': { emoji: '😢', color: '#60a5fa', bg: 'rgba(96,165,250,0.15)' },
  '愤怒': { emoji: '😠', color: '#f87171', bg: 'rgba(248,113,113,0.15)' },
  '中性': { emoji: '😐', color: '#a09cbd', bg: 'rgba(160,156,189,0.15)' },
  '惊讶': { emoji: '😲', color: '#fbbf24', bg: 'rgba(251,191,36,0.15)' },
  '恐惧': { emoji: '😨', color: '#a78bfa', bg: 'rgba(167,139,250,0.15)' },
}

const fused = computed(() => {
  const e = props.result?.fused_emotion
  if (!e) return null
  return {
    label: e.label,
    confidence: Math.round(e.confidence * 100),
    config: emotionConfig[e.label] || emotionConfig['中性'],
  }
})

const confidenceClass = computed(() => {
  if (!fused.value) return ''
  const c = fused.value.confidence
  if (c >= 85) return 'high'
  if (c >= 65) return 'medium'
  return 'low'
})
</script>

<template>
  <div v-if="fused" class="emotion-result glass-card">
    <div class="result-main">
      <div class="emotion-display" :style="{ background: fused.config.bg, borderColor: fused.config.color }">
        <span class="emotion-emoji">{{ fused.config.emoji }}</span>
        <div class="emotion-info">
          <span class="emotion-label" :style="{ color: fused.config.color }">{{ fused.label }}</span>
          <div class="confidence-bar-wrapper">
            <div class="confidence-bar" :class="confidenceClass">
              <div
                class="confidence-fill"
                :style="{ width: fused.confidence + '%', background: fused.config.color }"
              />
            </div>
            <span class="confidence-text" :style="{ color: fused.config.color }">{{ fused.confidence }}%</span>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.emotion-result {
  padding: 24px;
}

.result-main {
  display: flex;
  justify-content: center;
}

.emotion-display {
  display: flex;
  align-items: center;
  gap: 24px;
  padding: 24px 40px;
  border-radius: 20px;
  border: 2px solid;
  min-width: 320px;
}

.emotion-emoji {
  font-size: 56px;
  animation: float 2.5s ease-in-out infinite;
}

.emotion-info {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.emotion-label {
  font-size: 32px;
  font-weight: 800;
}

.confidence-bar-wrapper {
  display: flex;
  align-items: center;
  gap: 12px;
}

.confidence-bar {
  width: 150px;
  height: 10px;
  background: rgba(255,255,255,0.1);
  border-radius: 5px;
  overflow: hidden;
}

.confidence-fill {
  height: 100%;
  border-radius: 5px;
  transition: width 1s ease;
}

.confidence-text {
  font-size: 18px;
  font-weight: 700;
}
</style>
