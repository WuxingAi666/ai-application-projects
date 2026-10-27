<script setup>
import { ref } from 'vue'
import { ElMessage } from 'element-plus'
import { useAnalysisStore } from '@/stores/analysis'

const store = useAnalysisStore()
const isDragging = ref(false)
const selectedFile = ref(null)

const allowedExts = ['.wav', '.mp3', '.webm', '.m4a', '.flac', '.ogg', '.aac']

function onDragOver(e) {
  e.preventDefault()
  isDragging.value = true
}

function onDragLeave() {
  isDragging.value = false
}

function onDrop(e) {
  e.preventDefault()
  isDragging.value = false
  const file = e.dataTransfer.files[0]
  if (file) validateAndSet(file)
}

function onFileSelect(e) {
  const file = e.target.files[0]
  if (file) validateAndSet(file)
}

function validateAndSet(file) {
  const ext = '.' + file.name.split('.').pop().toLowerCase()
  if (!allowedExts.includes(ext)) {
    ElMessage.error(`不支持的格式: ${ext}，支持 ${allowedExts.join(', ')}`)
    return
  }
  if (file.size > 50 * 1024 * 1024) {
    ElMessage.error('文件过大（最大50MB）')
    return
  }
  selectedFile.value = file
}

async function submitAnalysis() {
  if (!selectedFile.value) {
    ElMessage.warning('请先选择音频文件')
    return
  }
  try {
    await store.analyze(selectedFile.value, selectedFile.value.name)
  } catch (e) {}
}

function clearFile() {
  selectedFile.value = null
}
</script>

<template>
  <div class="uploader glass-card">
    <div
      :class="['drop-zone', { dragging: isDragging }]"
      @dragover="onDragOver"
      @dragleave="onDragLeave"
      @drop="onDrop"
    >
      <div class="drop-content">
        <el-icon class="upload-icon"><UploadFilled /></el-icon>
        <p class="drop-title">拖拽音频文件到此处</p>
        <p class="drop-sub">或点击下方按钮选择文件</p>
        <p class="drop-hint">支持 WAV / MP3 / WEBM / M4A / FLAC / OGG</p>
      </div>
    </div>

    <div class="file-select">
      <input
        type="file"
        id="audio-file"
        :accept="allowedExts.join(',')"
        @change="onFileSelect"
        hidden
      />
      <label for="audio-file" class="select-btn">
        <el-icon><FolderOpened /></el-icon>
        选择文件
      </label>
    </div>

    <div v-if="selectedFile" class="file-info">
      <el-icon><Document /></el-icon>
      <span class="file-name">{{ selectedFile.name }}</span>
      <span class="file-size">({{ (selectedFile.size / 1024).toFixed(1) }} KB)</span>
      <div class="file-actions">
        <el-button type="primary" size="small" @click="submitAnalysis" :loading="store.isAnalyzing">
          开始分析
        </el-button>
        <el-button size="small" @click="clearFile">
          清除
        </el-button>
      </div>
    </div>
  </div>
</template>

<style scoped>
.uploader {
  padding: 24px;
}

.drop-zone {
  border: 2px dashed rgba(255,255,255,0.15);
  border-radius: var(--radius-sm);
  padding: 40px 20px;
  text-align: center;
  transition: all 0.3s ease;
  cursor: pointer;
}

.drop-zone.dragging {
  border-color: var(--accent);
  background: var(--accent-glow);
}

.drop-content {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 8px;
}

.upload-icon {
  font-size: 48px;
  color: var(--accent-light);
}

.drop-title {
  font-size: 18px;
  color: var(--text-primary);
  font-weight: 600;
}

.drop-sub {
  color: var(--text-secondary);
}

.drop-hint {
  color: var(--text-muted);
  font-size: 12px;
}

.file-select {
  text-align: center;
  margin-top: 16px;
}

.select-btn {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 10px 24px;
  background: var(--accent);
  color: white;
  border-radius: 10px;
  cursor: pointer;
  font-weight: 600;
  transition: all 0.3s;
}

.select-btn:hover {
  background: var(--accent-light);
}

.file-info {
  margin-top: 16px;
  padding: 14px 18px;
  background: rgba(124,92,252,0.1);
  border-radius: 10px;
  display: flex;
  align-items: center;
  gap: 10px;
  flex-wrap: wrap;
}

.file-name {
  color: var(--text-primary);
  font-weight: 600;
  word-break: break-all;
}

.file-size {
  color: var(--text-muted);
  font-size: 13px;
}

.file-actions {
  margin-left: auto;
  display: flex;
  gap: 8px;
}
</style>
