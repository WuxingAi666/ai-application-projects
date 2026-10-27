<template>
  <div class="loading-spinner">
    <div class="spinner">
      <div class="ring" />
      <div class="ring" />
      <div class="ring" />
    </div>
    <p class="loading-label"><slot>正在分析中...</slot></p>
  </div>
</template>

<style scoped>
.loading-spinner {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 20px;
}

.spinner {
  position: relative;
  width: 80px;
  height: 80px;
}

.ring {
  position: absolute;
  inset: 0;
  border: 3px solid transparent;
  border-radius: 50%;
  animation: ring-spin 1.2s cubic-bezier(0.5, 0, 0.5, 1) infinite;
}

.ring:nth-child(1) {
  border-top-color: #7c5cfc;
  animation-delay: -0.45s;
}
.ring:nth-child(2) {
  border-right-color: #34d399;
  animation-delay: -0.3s;
  inset: 8px;
}
.ring:nth-child(3) {
  border-bottom-color: #fbbf24;
  animation-delay: -0.15s;
  inset: 16px;
}

@keyframes ring-spin {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}

.loading-label {
  color: var(--text-secondary);
  font-size: 15px;
}
</style>
