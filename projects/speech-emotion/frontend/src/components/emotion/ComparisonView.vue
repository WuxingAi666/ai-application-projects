<script setup>
import { computed } from 'vue'

const props = defineProps({ result: { type: Object, required: true } })

const emotionConfig = {
  '开心': { emoji: '😊', color: '#34d399' },
  '悲伤': { emoji: '😢', color: '#60a5fa' },
  '愤怒': { emoji: '😠', color: '#f87171' },
  '中性': { emoji: '😐', color: '#a09cbd' },
  '惊讶': { emoji: '😲', color: '#fbbf24' },
  '恐惧': { emoji: '😨', color: '#a78bfa' },
}

const channels = computed(() => {
  const r = props.result
  if (!r) return []

  return [
    {
      name: '声学分析',
      icon: '🎵',
      desc: '基于语音声学特征（语调、语速、音色）',
      data: r.acoustic_emotion,
    },
    {
      name: 'LLM语义分析',
      icon: '🤖',
      desc: '基于大语言模型理解文本语义',
      data: r.semantic_emotion,
    },
    {
      name: '多模态融合结果',
      icon: '🔗',
      desc: `融合方法: ${r.fused_emotion?.fusion_method || '—'}`,
      data: r.fused_emotion,
      highlight: true,
    },
  ]
})
</script>

<template>
  <div class="comparison-view">
    <div
      v-for="ch in channels"
      :key="ch.name"
      :class="['compare-card', 'glass-card', { highlight: ch.highlight }]"
    >
      <div class="card-header">
        <span class="card-icon">{{ ch.icon }}</span>
        <div>
          <h4>{{ ch.name }}</h4>
          <p class="card-desc">{{ ch.desc }}</p>
        </div>
      </div>
      <div class="card-result" v-if="ch.data">
        <span class="emotion-emoji">{{ emotionConfig[ch.data.label]?.emoji || '😐' }}</span>
        <span class="emotion-label" :style="{ color: emotionConfig[ch.data.label]?.color }">
          {{ ch.data.label }}
        </span>
        <span class="confidence">({{ Math.round(ch.data.confidence * 100) }}%)</span>
      </div>
      <div class="card-probs" v-if="ch.data?.probabilities">
        <div
          v-for="(prob, emotion) in ch.data.probabilities"
          :key="emotion"
          class="prob-row"
        >
          <span class="prob-name">{{ emotion }}</span>
          <div class="prob-bar-bg">
            <div
              class="prob-bar-fill"
              :style="{
                width: (prob * 100).toFixed(0) + '%',
                background: emotionConfig[emotion]?.color || '#a09cbd',
              }"
            />
          </div>
          <span class="prob-val">{{ (prob * 100).toFixed(1) }}%</span>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.comparison-view {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 20px;
}

.compare-card {
  padding: 20px;
}

.compare-card.highlight {
  border-color: rgba(251, 191, 36, 0.3);
  box-shadow: 0 0 30px rgba(251, 191, 36, 0.1);
}

.card-header {
  display: flex;
  align-items: flex-start;
  gap: 12px;
  margin-bottom: 16px;
}

.card-icon {
  font-size: 28px;
}

.card-header h4 {
  font-size: 15px;
  margin: 0 0 4px;
  color: var(--text-primary);
}

.card-desc {
  font-size: 11px;
  color: var(--text-muted);
  margin: 0;
}

.card-result {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 14px;
  padding: 10px 14px;
  background: rgba(255,255,255,0.03);
  border-radius: 10px;
}

.emotion-emoji { font-size: 28px; }
.emotion-label { font-size: 20px; font-weight: 700; }
.confidence { color: var(--text-muted); font-size: 13px; margin-left: auto; }

.prob-row {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 5px;
}

.prob-name {
  width: 36px;
  font-size: 11px;
  color: var(--text-muted);
  text-align: right;
}

.prob-bar-bg {
  flex: 1;
  height: 6px;
  background: rgba(255,255,255,0.06);
  border-radius: 3px;
  overflow: hidden;
}

.prob-bar-fill {
  height: 100%;
  border-radius: 3px;
  transition: width 1s ease;
}

.prob-val {
  width: 42px;
  font-size: 11px;
  color: var(--text-secondary);
  text-align: right;
}

@media (max-width: 900px) {
  .comparison-view {
    grid-template-columns: 1fr;
  }
}
</style>
