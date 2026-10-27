<script setup>
defineProps({
  url: { type: String, required: true },
})
</script>

<template>
  <div class="spectrogram glass-card">
    <div class="spec-header">
      <span class="label">🔬 梅尔频谱图</span>
    </div>
    <img :src="url" alt="Mel Spectrogram" class="spec-image" />
  </div>
</template>

<style scoped>
.spectrogram {
  padding: 16px;
}

.spec-header {
  margin-bottom: 8px;
}

.label {
  color: var(--text-secondary);
  font-size: 14px;
}

.spec-image {
  width: 100%;
  border-radius: 8px;
  display: block;
}
</style>
