<script setup>
import { computed } from 'vue'

const props = defineProps({ result: { type: Object, required: true } })

const emotions = ['开心', '悲伤', '愤怒', '中性', '惊讶', '恐惧']
const colors = ['#34d399', '#60a5fa', '#f87171', '#a09cbd', '#fbbf24', '#a78bfa']
const emojis = ['😊', '😢', '😠', '😐', '😲', '😨']

const chartOption = computed(() => {
  const probs = props.result?.fused_emotion?.probabilities || {}

  return {
    tooltip: {
      trigger: 'axis',
      backgroundColor: 'rgba(26,23,68,0.95)',
      borderColor: 'rgba(255,255,255,0.1)',
      textStyle: { color: '#e8e6f0' },
      formatter: (params) => {
        const v = params[0]
        return `${v.name} ${emojis[emotions.indexOf(v.name)]}: <b>${(v.value * 100).toFixed(1)}%</b>`
      }
    },
    grid: { left: '3%', right: '8%', top: '5%', bottom: '5%', containLabel: true },
    xAxis: {
      type: 'value',
      max: 1,
      axisLabel: { color: '#6e698f', formatter: (v) => (v * 100).toFixed(0) + '%' },
      splitLine: { lineStyle: { color: 'rgba(255,255,255,0.05)' } },
    },
    yAxis: {
      type: 'category',
      data: emotions.map((e, i) => `${emojis[i]} ${e}`),
      axisLabel: { color: '#a09cbd', fontSize: 13 },
      axisLine: { show: false },
      axisTick: { show: false },
    },
    series: [{
      type: 'bar',
      data: emotions.map((e, i) => ({
        value: probs[e] || 0,
        itemStyle: {
          color: new Function('return "' + colors[i] + '"')(),
          borderRadius: [0, 6, 6, 0],
          shadowBlur: 8,
          shadowColor: colors[i],
        },
      })),
      barWidth: 20,
      label: {
        show: true,
        position: 'right',
        color: '#a09cbd',
        fontSize: 12,
        formatter: (p) => (p.value * 100).toFixed(1) + '%',
      },
    }],
  }
})
</script>

<template>
  <div class="emotion-bar">
    <v-chart :option="chartOption" autoresize style="height: 280px;" />
  </div>
</template>
