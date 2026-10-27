<script setup>
import { ref, onMounted, watch } from 'vue'

const props = defineProps({
  samples: { type: Array, default: () => [] },
  timeAxis: { type: Array, default: () => [] },
  duration: { type: Number, default: 0 },
})

const canvasRef = ref(null)

function drawWaveform() {
  const canvas = canvasRef.value
  if (!canvas || !props.samples.length) return

  const ctx = canvas.getContext('2d')
  const dpr = window.devicePixelRatio || 1
  const rect = canvas.getBoundingClientRect()

  canvas.width = rect.width * dpr
  canvas.height = rect.height * dpr
  ctx.scale(dpr, dpr)

  const w = rect.width
  const h = rect.height
  const mid = h / 2
  const samples = props.samples

  // 渐变填充
  const gradient = ctx.createLinearGradient(0, 0, 0, h)
  gradient.addColorStop(0, 'rgba(124, 92, 252, 0.6)')
  gradient.addColorStop(0.5, 'rgba(124, 92, 252, 0.3)')
  gradient.addColorStop(1, 'rgba(124, 92, 252, 0.1)')

  ctx.clearRect(0, 0, w, h)

  // 绘制网格线
  ctx.strokeStyle = 'rgba(255,255,255,0.05)'
  ctx.lineWidth = 0.5
  for (let i = 0; i < 5; i++) {
    const y = (h / 5) * i
    ctx.beginPath()
    ctx.moveTo(0, y)
    ctx.lineTo(w, y)
    ctx.stroke()
  }

  // 绘制波形
  ctx.beginPath()
  const step = Math.max(1, Math.floor(samples.length / w))
  for (let i = 0; i < w; i++) {
    const idx = Math.floor(i * step)
    const val = samples[Math.min(idx, samples.length - 1)]
    const x = i
    const y = mid + val * mid * 0.8
    if (i === 0) ctx.moveTo(x, y)
    else ctx.lineTo(x, y)
  }
  ctx.strokeStyle = '#7c5cfc'
  ctx.lineWidth = 2
  ctx.stroke()

  // 填充波形下方
  ctx.lineTo(w, mid)
  ctx.lineTo(0, mid)
  ctx.closePath()
  ctx.fillStyle = gradient
  ctx.fill()
}

onMounted(() => drawWaveform())
watch(() => props.samples, () => setTimeout(drawWaveform, 100))
</script>

<template>
  <div class="waveform glass-card">
    <div class="waveform-header">
      <span class="label">📈 音频波形</span>
      <span class="duration">{{ duration.toFixed(1) }}s</span>
    </div>
    <canvas ref="canvasRef" class="waveform-canvas" />
  </div>
</template>

<style scoped>
.waveform {
  padding: 16px;
}

.waveform-header {
  display: flex;
  justify-content: space-between;
  margin-bottom: 8px;
}

.label {
  color: var(--text-secondary);
  font-size: 14px;
}

.duration {
  color: var(--text-muted);
  font-size: 12px;
}

.waveform-canvas {
  width: 100%;
  height: 100px;
  border-radius: 8px;
}
</style>
