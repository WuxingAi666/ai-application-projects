<script setup>
import { ref } from 'vue'
import { useAnalysisStore } from '@/stores/analysis'
import AudioRecorder from '@/components/audio/AudioRecorder.vue'
import AudioUploader from '@/components/audio/AudioUploader.vue'
import WaveformViewer from '@/components/audio/WaveformViewer.vue'
import SpectrogramViewer from '@/components/audio/SpectrogramViewer.vue'
import EmotionResult from '@/components/emotion/EmotionResult.vue'
import EmotionBar from '@/components/emotion/EmotionBar.vue'
import EmotionRadar from '@/components/emotion/EmotionRadar.vue'
import ComparisonView from '@/components/emotion/ComparisonView.vue'
import LLMAnalysis from '@/components/emotion/LLMAnalysis.vue'
import VoiceAssistant from '@/components/emotion/VoiceAssistant.vue'
import LoadingSpinner from '@/components/common/LoadingSpinner.vue'

const store = useAnalysisStore()
const activeTab = ref('record')
</script>

<template>
  <div class="home-page">
    <!-- 输入区域 -->
    <section class="input-section">
      <el-tabs v-model="activeTab" class="input-tabs">
        <el-tab-pane label="🎤 实时录音" name="record">
          <AudioRecorder />
        </el-tab-pane>
        <el-tab-pane label="📁 上传文件" name="upload">
          <AudioUploader />
        </el-tab-pane>
      </el-tabs>
    </section>

    <!-- 加载状态 -->
    <section v-if="store.isAnalyzing" class="loading-section">
      <LoadingSpinner />
      <p class="loading-text">正在分析中，请稍候...</p>
    </section>

    <!-- 分析结果 -->
    <section v-if="store.hasResult && !store.isAnalyzing" class="results-section">
      <!-- 转录文本 -->
      <div class="transcript-bar glass-card" v-if="store.currentResult.transcript">
        <span class="transcript-label">📝 转录文本：</span>
        <span class="transcript-text">{{ store.currentResult.transcript }}</span>
      </div>

      <!-- 音频可视化 -->
      <div class="audio-visual-row">
        <WaveformViewer
          v-if="store.currentResult.waveform"
          :samples="store.currentResult.waveform.samples"
          :time-axis="store.currentResult.waveform.time_axis"
          :duration="store.currentResult.duration"
        />
        <SpectrogramViewer
          v-if="store.currentResult.spectrogram_url"
          :url="store.currentResult.spectrogram_url"
        />
      </div>

      <!-- 情感结果 -->
      <div class="emotion-main-row">
        <EmotionResult :result="store.currentResult" />
      </div>

      <!-- 图表对比 -->
      <div class="charts-row">
        <div class="chart-card glass-card">
          <h3>📊 情感概率分布</h3>
          <EmotionBar :result="store.currentResult" />
        </div>
        <div class="chart-card glass-card">
          <h3>🎯 三通道对比</h3>
          <EmotionRadar :result="store.currentResult" />
        </div>
      </div>

      <!-- 三通道对比视图 -->
      <ComparisonView :result="store.currentResult" />

      <!-- LLM推理展示 -->
      <LLMAnalysis
        v-if="store.currentResult.semantic_emotion?.reasoning"
        :semantic="store.currentResult.semantic_emotion"
      />

      <!-- 智能语音播报助手 -->
      <VoiceAssistant
        v-if="store.currentResult.task_id"
        :taskId="store.currentResult.task_id"
        :autoPlay="true"
      />

      <!-- 处理信息 -->
      <div class="meta-info">
        <span>⏱ 处理耗时: {{ store.currentResult.processing_time }}s</span>
        <span>🔗 融合方法: {{ store.currentResult.fused_emotion?.fusion_method }}</span>
        <span>📍 音频时长: {{ store.currentResult.duration }}s</span>
      </div>
    </section>

    <!-- 空状态 -->
    <section v-if="!store.hasResult && !store.isAnalyzing" class="empty-state">
      <div class="empty-icon">🎙️</div>
      <h2>开始分析你的语音情感</h2>
      <p>录制一段语音或上传音频文件，系统将使用 <strong>声学分析 + 大语言模型</strong> 双通道识别情感</p>
      <div class="emotion-tags">
        <span class="tag happy">😊 开心</span>
        <span class="tag sad">😢 悲伤</span>
        <span class="tag angry">😠 愤怒</span>
        <span class="tag neutral">😐 中性</span>
        <span class="tag surprise">😲 惊讶</span>
        <span class="tag fear">😨 恐惧</span>
      </div>
    </section>
  </div>
</template>

<style scoped>
.home-page {
  display: flex;
  flex-direction: column;
  gap: 24px;
}

.input-section {
  max-width: 700px;
  margin: 0 auto;
  width: 100%;
}

.input-tabs {
  --el-text-color-primary: var(--text-primary);
}

.loading-section {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 16px;
  padding: 60px 0;
}

.loading-text {
  color: var(--text-secondary);
  font-size: 15px;
}

.results-section {
  display: flex;
  flex-direction: column;
  gap: 24px;
}

.transcript-bar {
  padding: 16px 24px;
  font-size: 15px;
}

.transcript-label {
  color: var(--accent-light);
  font-weight: 600;
}

.transcript-text {
  color: var(--text-primary);
  margin-left: 8px;
}

.audio-visual-row {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 20px;
}

.charts-row {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 20px;
}

.chart-card {
  padding: 20px;
}

.chart-card h3 {
  margin-bottom: 12px;
  color: var(--text-secondary);
  font-size: 16px;
}

.meta-info {
  display: flex;
  gap: 24px;
  color: var(--text-muted);
  font-size: 13px;
  justify-content: center;
  padding: 12px;
}

/* 空状态 */
.empty-state {
  text-align: center;
  padding: 60px 20px;
}

.empty-icon {
  font-size: 72px;
  animation: float 3s ease-in-out infinite;
  margin-bottom: 20px;
}

.empty-state h2 {
  font-size: 24px;
  margin-bottom: 12px;
  color: var(--text-primary);
}

.empty-state p {
  color: var(--text-secondary);
  max-width: 500px;
  margin: 0 auto 24px;
  line-height: 1.6;
}

.emotion-tags {
  display: flex;
  gap: 12px;
  justify-content: center;
  flex-wrap: wrap;
}

.tag {
  padding: 8px 18px;
  border-radius: 20px;
  font-size: 14px;
  font-weight: 600;
  border: 1px solid rgba(255,255,255,0.1);
}
.tag.happy { background: rgba(52,211,153,0.15); color: #34d399; }
.tag.sad { background: rgba(96,165,250,0.15); color: #60a5fa; }
.tag.angry { background: rgba(248,113,113,0.15); color: #f87171; }
.tag.neutral { background: rgba(160,156,189,0.15); color: #a09cbd; }
.tag.surprise { background: rgba(251,191,36,0.15); color: #fbbf24; }
.tag.fear { background: rgba(167,139,250,0.15); color: #a78bfa; }

@media (max-width: 768px) {
  .audio-visual-row,
  .charts-row {
    grid-template-columns: 1fr;
  }
}
</style>
