<script setup>
import { useRouter, useRoute } from 'vue-router'

const router = useRouter()
const route = useRoute()

const isHome = () => route.path === '/'
</script>

<template>
  <header class="app-header glass-card">
    <div class="header-left" @click="router.push('/')" style="cursor: pointer;">
      <span class="logo-icon">🎙️</span>
      <div class="logo-text">
        <h1 class="text-gradient">中文语音情感识别系统</h1>
        <span class="subtitle">基于大语言模型的多模态情感分析</span>
      </div>
    </div>
    <nav class="header-nav">
      <el-button
        :type="isHome() ? 'primary' : 'default'"
        :class="{ 'nav-btn': true, active: isHome() }"
        @click="router.push('/')"
        round
      >
        <el-icon><Microphone /></el-icon>
        分析
      </el-button>
      <el-button
        :type="!isHome() ? 'primary' : 'default'"
        :class="{ 'nav-btn': true, active: !isHome() }"
        @click="router.push('/history')"
        round
      >
        <el-icon><Clock /></el-icon>
        历史记录
      </el-button>
    </nav>
  </header>
</template>

<style scoped>
.app-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 16px 32px;
  margin: 16px 24px 0;
  border-radius: var(--radius);
  flex-wrap: wrap;
  gap: 16px;
}

.header-left {
  display: flex;
  align-items: center;
  gap: 14px;
}

.logo-icon {
  font-size: 36px;
  animation: float 3s ease-in-out infinite;
}

.logo-text h1 {
  font-size: 22px;
  font-weight: 700;
  margin: 0;
  line-height: 1.3;
}

.subtitle {
  font-size: 12px;
  color: var(--text-secondary);
  letter-spacing: 0.5px;
}

.header-nav {
  display: flex;
  gap: 12px;
}

.nav-btn {
  font-weight: 600;
}
</style>
