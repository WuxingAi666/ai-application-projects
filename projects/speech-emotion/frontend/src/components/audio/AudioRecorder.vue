<script setup>
import { ref, onUnmounted } from 'vue'
import { ElMessage } from 'element-plus'
import { useAnalysisStore } from '@/stores/analysis'

const store = useAnalysisStore()

const isRecording = ref(false)
const recordingTime = ref(0)
const audioBlob = ref(null)
const audioUrl = ref('')
let mediaRecorder = null
let timerInterval = null
let audioChunks = []

async function startRecording() {
  try {
    const stream = await navigator.mediaDevices.getUserMedia({
      audio: {
        channelCount: 1,
        sampleRate: 16000,
        echoCancellation: true,
        noiseSuppression: true,
      }
    })

    audioChunks = []
    const mimeType = MediaRecorder.isTypeSupported('audio/webm;codecs=opus')
      ? 'audio/webm;codecs=opus'
      : 'audio/webm'

    mediaRecorder = new MediaRecorder(stream, { mimeType })

    mediaRecorder.ondataavailable = (e) => {
      if (e.data.size > 0) audioChunks.push(e.data)
    }

    mediaRecorder.onstop = () => {
      stream.getTracks().forEach(t => t.stop())
      audioBlob.value = new Blob(audioChunks, { type: mimeType })
      audioUrl.value = URL.createObjectURL(audioBlob.value)
    }

    mediaRecorder.start()
    isRecording.value = true
    recordingTime.value = 0

    timerInterval = setInterval(() => {
      recordingTime.value++
      if (recordingTime.value >= 30) stopRecording()
    }, 1000)

  } catch (e) {
    ElMessage.error('无法访问麦克风，请检查权限设置')
    console.error('录音失败:', e)
  }
}

function stopRecording() {
  if (mediaRecorder && isRecording.value) {
    mediaRecorder.stop()
    isRecording.value = false
    clearInterval(timerInterval)
  }
}

async function submitAnalysis() {
  if (!audioBlob.value) {
    ElMessage.warning('请先录制音频')
    return
  }
  try {
    await store.analyze(audioBlob.value, `recording_${Date.now()}.webm`)
  } catch (e) {
    // 错误已在 store 中处理
  }
}

function formatTime(s) {
  const m = Math.floor(s / 60)
  const sec = s % 60
  return `${String(m).padStart(2, '0')}:${String(sec).padStart(2, '0')}`
}

function resetRecording() {
  audioBlob.value = null
  audioUrl.value = ''
  recordingTime.value = 0
}

onUnmounted(() => {
  clearInterval(timerInterval)
  if (mediaRecorder && isRecording.value) {
    mediaRecorder.stop()
    mediaRecorder.stream.getTracks().forEach(t => t.stop())
  }
})
</script>

<template>
  <div class="recorder glass-card">
    <!-- 录音按钮 -->
    <div class="recorder-center">
      <button
        :class="['record-btn', { recording: isRecording }]"
        @click="isRecording ? stopRecording() : startRecording()"
        :disabled="store.isAnalyzing"
      >
        <span class="btn-icon">{{ isRecording ? '⏹' : '🎤' }}</span>
      </button>
      <p class="btn-label">
        {{ isRecording ? '点击停止' : '点击录音' }}
      </p>
      <p v-if="isRecording" class="recording-timer">
        <span class="dot" /> {{ formatTime(recordingTime) }} / 00:30
      </p>
    </div>

    <!-- 录音预览 -->
    <div v-if="audioBlob && !isRecording" class="preview-section">
      <audio :src="audioUrl" controls class="audio-preview" />
      <div class="preview-actions">
        <el-button type="primary" size="large" @click="submitAnalysis" :loading="store.isAnalyzing">
          <el-icon><MagicStick /></el-icon>
          开始分析
        </el-button>
        <el-button size="large" @click="resetRecording">
          <el-icon><Refresh /></el-icon>
          重新录制
        </el-button>
      </div>
    </div>
  </div>
</template>

<style scoped>
.recorder {
  padding: 32px;
  text-align: center;
}

.recorder-center {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 12px;
}

.record-btn {
  width: 100px;
  height: 100px;
  border-radius: 50%;
  border: 3px solid var(--accent);
  background: var(--accent-glow);
  cursor: pointer;
  transition: all 0.3s ease;
  display: flex;
  align-items: center;
  justify-content: center;
}

.record-btn:hover {
  transform: scale(1.05);
  box-shadow: 0 0 30px var(--accent-glow);
}

.record-btn.recording {
  animation: recording-pulse 1.5s ease-in-out infinite;
  border-color: #f87171;
  background: rgba(248, 113, 113, 0.2);
  box-shadow: 0 0 30px rgba(248, 113, 113, 0.3);
}

.record-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.btn-icon {
  font-size: 36px;
}

.btn-label {
  color: var(--text-secondary);
  font-size: 14px;
}

.recording-timer {
  color: #f87171;
  font-size: 18px;
  font-weight: 700;
  display: flex;
  align-items: center;
  gap: 8px;
}

.dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: #f87171;
  animation: recording-pulse 1s infinite;
}

.preview-section {
  margin-top: 20px;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 16px;
}

.audio-preview {
  width: 100%;
  max-width: 500px;
  border-radius: 10px;
}

.preview-actions {
  display: flex;
  gap: 12px;
}
</style>
