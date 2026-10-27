<script setup>
import { computed } from 'vue'

const props = defineProps({ result: { type: Object, required: true } })

const emotions = ['开心', '悲伤', '愤怒', '中性', '惊讶', '恐惧']

const chartOption = computed(() => {
  const acoustic = props.result?.acoustic_emotion?.probabilities || {}
  const semantic = props.result?.semantic_emotion?.probabilities || {}
  const fused = props.result?.fused_emotion?.probabilities || {}

  return {
    tooltip: {
      backgroundColor: 'rgba(26,23,68,0.95)',
      borderColor: 'rgba(255,255,255,0.1)',
      textStyle: { color: '#e8e6f0' },
    },
    legend: {
      data: ['声学分析', 'LLM语义', '多模态融合'],
      bottom: 0,
      textStyle: { color: '#a09cbd', fontSize: 12 },
    },
    radar: {
      center: ['50%', '50%'],
      radius: '65%',
      indicator: emotions.map(e => ({ name: e, max: 1 })),
      axisName: { color: '#a09cbd', fontSize: 12 },
      splitArea: {
        areaStyle: { color: ['rgba(124,92,252,0.02)', 'rgba(124,92,252,0.04)'] },
      },
      splitLine: { lineStyle: { color: 'rgba(255,255,255,0.08)' } },
      axisLine: { lineStyle: { color: 'rgba(255,255,255,0.1)' } },
    },
    series: [{
      type: 'radar',
      data: [
        {
          name: '声学分析',
          value: emotions.map(e => acoustic[e] || 0),
          lineStyle: { color: '#60a5fa', width: 2 },
          areaStyle: { color: 'rgba(96,165,250,0.15)' },
          itemStyle: { color: '#60a5fa' },
          symbol: 'circle',
          symbolSize: 4,
        },
        {
          name: 'LLM语义',
          value: emotions.map(e => semantic[e] || 0),
          lineStyle: { color: '#34d399', width: 2 },
          areaStyle: { color: 'rgba(52,211,153,0.15)' },
          itemStyle: { color: '#34d399' },
          symbol: 'circle',
          symbolSize: 4,
        },
        {
          name: '多模态融合',
          value: emotions.map(e => fused[e] || 0),
          lineStyle: { color: '#fbbf24', width: 3 },
          areaStyle: { color: 'rgba(251,191,36,0.2)' },
          itemStyle: { color: '#fbbf24' },
          symbol: 'diamond',
          symbolSize: 6,
        },
      ],
    }],
  }
})
</script>

<template>
  <div class="emotion-radar">
    <v-chart :option="chartOption" autoresize style="height: 320px;" />
  </div>
</template>
