<template>
  <div class="smart-analysis-controls">
    <div class="file-upload-container">
      <label for="file-upload" class="custom-file-upload">选择财报PDF</label>
      <input id="file-upload" type="file" @change="handleFileUpload" accept=".pdf" />
    </div>
    <div class="report-selector-container">
      <select v-model="currentReportId" @change="onReportSelect">
        <option disabled value="">已生成报告列表</option>
        <option v-for="report in reports" :key="report.id" :value="report.id">
          {{ report.name }}
        </option>
      </select>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue';
import axios from 'axios';

const emit = defineEmits(['analysis-started', 'analysis-completed', 'report-switched']);

const reports = ref<{ id: string; name: string; }[]>([]);
const currentReportId = ref("");

// 处理文件上传
const handleFileUpload = async (event: Event) => {
  const file = (event.target as HTMLInputElement).files?.[0];
  if (!file) return;

  emit('analysis-started');

  const formData = new FormData();
  formData.append('file', file);

  try {
    const uploadResponse = await axios.post('http://localhost:5000/api/smart/upload', formData, { headers: { 'Content-Type': 'multipart/form-data' } });
    if (!uploadResponse.data.path) throw new Error('文件上传失败');

    const analyzeResponse = await axios.post('http://localhost:5000/api/smart/analyze', { file_path: uploadResponse.data.path });
    if (!analyzeResponse.data || !analyzeResponse.data.report_id) throw new Error('智能分析失败');

    const { report_id, analysis } = analyzeResponse.data;
    const newReport = { id: report_id, name: file.name, analysis };

    localStorage.setItem(report_id, JSON.stringify(newReport));
    reports.value.push({ id: report_id, name: file.name });
    currentReportId.value = report_id;

    emit('analysis-completed', { id: report_id, analysis });

  } catch (error) {
    console.error('处理文件时出错:', error);
    alert('处理失败');
    emit('analysis-completed', { id: '', analysis: null }); // 发出完成信号以重置状态
  }
};

// 从本地加载报告列表
const loadReportsFromLocal = () => {
  const loadedReports = Object.keys(localStorage)
    .map(key => {
      try {
        if (key.match(/^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i)) {
          const data = JSON.parse(localStorage.getItem(key)!);
          return { id: data.id, name: data.name };
        }
        return null;
      } catch { return null; }
    })
    .filter(Boolean) as { id: string; name: string }[];
  reports.value = loadedReports;
};

// 切换报告
const onReportSelect = () => {
  if (currentReportId.value) {
    const reportData = JSON.parse(localStorage.getItem(currentReportId.value) || '{}');
    emit('report-switched', { id: currentReportId.value, analysis: reportData.analysis || null });
  }
};

onMounted(loadReportsFromLocal);
</script>

<style scoped>
.smart-analysis-controls {
  display: flex;
  align-items: center;
}

.custom-file-upload {
  display: inline-block;
  padding: 8px 15px;
  cursor: pointer;
  background-color: #409eff;
  color: white;
  border-radius: 4px;
  font-size: 14px;
}

input[type="file"] {
  display: none;
}

.report-selector-container {
  margin-left: 20px;
}

select {
  padding: 8px 12px;
  border-radius: 4px;
  border: 1px solid #dcdfe6;
  font-size: 14px;
  min-width: 200px;
}
</style>