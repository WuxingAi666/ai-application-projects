<script setup>
import { ref, watch, onUnmounted } from 'vue'
import { ElMessage } from 'element-plus'
import api from '@/api/index'

const props = defineProps({
  taskId: { type: String, default: '' },
  autoPlay: { type: Boolean, default: false },
})

const loading = ref(false)
const feedbackText = ref('')
const isSpeaking = ref(false)

// Web Speech API 实例
let utterance = null

// 监听 taskId 变化，自动获取并播报
watch(() => props.taskId, async (id) => {
  if (!id) return
  await fetchVoiceText(id)
  if (props.autoPlay && feedbackText.value) {
    speakText()
  }
})

async function fetchVoiceText(taskId) {
  loading.value = true
  feedbackText.value = ''
  try {
    const res = await api.post(`/voice/${taskId}`)
    feedbackText.value = res.data.text
  } catch (e) {
    console.error('获取语音文本失败:', e)
    ElMessage.warning('语音分析生成失败')
  } finally {
    loading.value = false
  }
}

function speakText() {
  if (!feedbackText.value) return
  // 停止之前的播报
  stopSpeaking()

  // 使用浏览器 Web Speech API
  utterance = new SpeechSynthesisUtterance(feedbackText.value)
  utterance.lang = 'zh-CN'
  utterance.rate = 1.0    // 语速
  utterance.pitch = 1.1   // 音调
  utterance.volume = 1.0

  // 尝试使用更好的中文语音
  const voices = speechSynthesis.getVoices()
  const zhVoice = voices.find(v => v.lang.startsWith('zh-CN'))
    || voices.find(v => v.lang.startsWith('zh'))
    || voices.find(v => v.lang.startsWith('zh-HK'))
  if (zhVoice) {
    utterance.voice = zhVoice
  }

  utterance.onstart = () => { isSpeaking.value = true }
  utterance.onend = () => { isSpeaking.value = false }
  utterance.onerror = () => { isSpeaking.value = false }

  speechSynthesis.speak(utterance)
}

function stopSpeaking() {
  speechSynthesis.cancel()
  isSpeaking.value = false
}

function toggleSpeak() {
  if (isSpeaking.value) {
    stopSpeaking()
  } else {
    speakText()
  }
}

onUnmounted(() => {
  stopSpeaking()
})
</script>

<template>
  <div class="voice-assistant glass-card" v-if="taskId">
    <div class="va-header">
      <span class="va-icon">🤖</span>
      <div>
        <h3>智能语音助手</h3>
        <p class="va-subtitle">AI 情感分析 + 个性化建议</p>
      </div>
    </div>

    <!-- 加载中 -->
    <div v-if="loading" class="va-loading">
      <el-icon class="is-loading"><Loading /></el-icon>
      <span>正在生成智能分析...</span>
    </div>

    <!-- 未加载 -->
    <div v-if="!feedbackText && !loading" class="va-idle">
      <el-button type="primary" @click="fetchVoiceText(taskId)" :loading="loading" round>
        <el-icon><MagicStick /></el-icon>
        生成语音分析
      </el-button>
    </div>

    <!-- 结果展示 -->
    <div v-if="feedbackText && !loading" class="va-result">
      <div class="va-text bubble">
        <span class="quote-mark">"</span>
        {{ feedbackText }}
      </div>

      <div class="va-controls">
        <el-button
          :type="isSpeaking ? 'danger' : 'success'"
          @click="toggleSpeak"
          round
        >
          <el-icon><Headset /></el-icon>
          {{ isSpeaking ? '停止播报' : '播报分析' }}
        </el-button>
        <span class="va-hint">使用浏览器语音引擎，无需联网</span>
      </div>
    </div>
  </div>
</template>

<style scoped>
.voice-assistant {
  padding: 20px;
}

.va-header {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 16px;
}

.va-icon { font-size: 28px; }

.va-header h3 {
  margin: 0;
  font-size: 16px;
  color: var(--text-primary);
}

.va-subtitle {
  margin: 2px 0 0;
  font-size: 12px;
  color: var(--text-muted);
}

.va-idle, .va-loading {
  text-align: center;
  padding: 20px 0;
}

.va-loading {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  color: var(--text-secondary);
}

.va-result {
  display: flex;
  flex-direction: column;
  gap: 14px;
}

.va-text.bubble {
  padding: 16px 18px;
  background: linear-gradient(135deg, rgba(52,211,153,0.08), rgba(124,92,252,0.08));
  border-radius: 14px;
  font-size: 15px;
  line-height: 1.7;
  color: var(--text-primary);
}

.quote-mark {
  font-size: 28px;
  color: var(--accent-light);
  font-family: serif;
  line-height: 0;
}

.va-controls {
  display: flex;
  align-items: center;
  gap: 10px;
}

.va-hint {
  font-size: 11px;
  color: var(--text-muted);
}
</style>
