<template>
  <div class="report-panel">
    <div v-if="isLoading" class="loading-overlay">
      <div class="spinner"></div>
      <p>正在分析财报，请稍候... 大型财报分析需 1-2 分钟</p>
    </div>
    <div v-else-if="analysisResult" class="report-content">
      <!-- 在这里渲染分析结果 -->
      <pre>{{ JSON.stringify(analysisResult, null, 2) }}</pre>
    </div>
    <div v-else class="placeholder">
      <p>上传PDF财报后，将在此处查看智能分析结果。</p>
    </div>
  </div>
</template>

<script setup lang="ts">
import { defineProps } from 'vue';

defineProps<{ 
  analysisResult: any; 
  isLoading: boolean; 
}>();
</script>

<style scoped>
.report-panel {
  position: relative;
  width: 100%;
  height: 100%;
  padding: 20px;
  overflow-y: auto;
}
.loading-overlay {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  display: flex;
  flex-direction: column;
  justify-content: center;
  align-items: center;
  background-color: rgba(255, 255, 255, 0.8);
  z-index: 10;
}
.spinner {
  border: 4px solid #f3f3f3;
  border-top: 4px solid #3498db;
  border-radius: 50%;
  width: 40px;
  height: 40px;
  animation: spin 1s linear infinite;
}
@keyframes spin {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}
.placeholder {
  display: flex;
  justify-content: center;
  align-items: center;
  height: 100%;
  color: #999;
}
.report-content {
  /* 报告内容的样式 */
}
</style>