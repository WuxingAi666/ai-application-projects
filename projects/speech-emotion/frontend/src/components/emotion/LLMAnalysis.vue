<script setup>
import { computed } from 'vue'

const props = defineProps({
  semantic: { type: Object, required: true },
})

const reasoning = computed(() => props.semantic?.reasoning || '')
const keyPhrases = computed(() => props.semantic?.key_phrases || [])
const model = computed(() => props.semantic?.model || 'unknown')
</script>

<template>
  <div class="llm-analysis glass-card">
    <div class="llm-header">
      <span class="llm-icon">🤖</span>
      <div>
        <h3>LLM 语义推理过程</h3>
        <p class="llm-model">模型: {{ model }}</p>
      </div>
    </div>

    <div class="llm-reasoning">
      <div class="reasoning-icon">💭</div>
      <p>{{ reasoning }}</p>
    </div>

    <div v-if="keyPhrases.length" class="llm-phrases">
      <span class="phrases-label">🔑 关键情感词:</span>
      <span v-for="p in keyPhrases" :key="p" class="phrase-tag">{{ p }}</span>
    </div>
  </div>
</template>

<style scoped>
.llm-analysis {
  padding: 20px;
}

.llm-header {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 16px;
}

.llm-icon { font-size: 28px; }

.llm-header h3 {
  margin: 0;
  color: var(--text-primary);
  font-size: 16px;
}

.llm-model {
  margin: 2px 0 0;
  color: var(--text-muted);
  font-size: 12px;
}

.llm-reasoning {
  display: flex;
  gap: 12px;
  padding: 16px;
  background: rgba(52,211,153,0.06);
  border-left: 3px solid #34d399;
  border-radius: 0 10px 10px 0;
  margin-bottom: 14px;
}

.reasoning-icon { font-size: 18px; flex-shrink: 0; }

.llm-reasoning p {
  margin: 0;
  color: var(--text-primary);
  font-size: 14px;
  line-height: 1.7;
}

.llm-phrases {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-wrap: wrap;
}

.phrases-label {
  color: var(--text-secondary);
  font-size: 13px;
}

.phrase-tag {
  padding: 4px 12px;
  background: rgba(124,92,252,0.15);
  border: 1px solid rgba(124,92,252,0.3);
  border-radius: 20px;
  color: var(--accent-light);
  font-size: 12px;
  font-weight: 600;
}
</style>
