<template>
  <div class="page">
    <h2>爬取财报</h2>
    <div class="content-layout">
      <!-- 左侧：爬取表单 -->
      <div class="form-section">
        <div class="form">
          <label>
            股票代码
            <input v-model.trim="code" placeholder="如 000001 或 600519" />
          </label>
          <label>
            报告年份
            <input type="number" v-model.number="year" min="2000" max="2100" />
          </label>
          <label>
            报告类型
            <select v-model="type">
              <option value="annual">年报</option>
              <option value="semi">中报</option>
              <option value="quarterly">季报</option>
            </select>
          </label>

          <button :disabled="loading" @click="startCrawl">
            {{ loading ? '正在抓取...' : '开始爬取' }}
          </button>
        </div>

        <div v-if="result" class="result">
          <p>已下载 <b>{{ result.downloaded }}</b> 个文件</p>
          <p>保存目录：<code>{{ result.save_dir }}</code></p>
          
          <!-- 分析报告按钮 -->
          <div class="analysis-section">
            <button 
              :disabled="analysisLoading || !result.downloaded" 
              @click="startAnalysis"
              class="analysis-btn"
            >
              {{ analysisLoading ? '正在提取 PDF 内容...' : '分析报告' }}
            </button>
          </div>
        </div>
        <div v-if="error" class="error">错误：{{ error }}</div>
      </div>

      <!-- 右侧：分析结果展示 -->
      <div class="analysis-section" v-if="showAnalysisResults">
        <div class="analysis-header">
          <h3>PDF 提取结果</h3>
        </div>

        <!-- 进度条 -->
        <div v-if="analysisLoading" class="progress-container">
          <div class="progress-bar">
            <div 
              class="progress-fill" 
              :style="{ width: analysisProgress + '%' }"
            ></div>
          </div>
          <p class="progress-text">{{ analysisMessage }} ({{ analysisProgress }}%)</p>
        </div>

        <!-- 错误提示 -->
        <div v-if="analysisError" class="analysis-error">
          <p class="error-message">
            <span class="error-icon">⚠️</span>
            {{ analysisError }}
          </p>
          <button @click="retryAnalysis" class="retry-btn">重新提取</button>
        </div>

        <!-- 分析结果标签页 -->
        <div v-if="analysisResult && !analysisLoading" class="result-tabs">
          <div class="tab-headers">
            <button 
              :class="{ active: activeTab === 'text' }"
              @click="activeTab = 'text'"
              class="tab-btn"
            >
              文本结果
            </button>
            <button 
              :class="{ active: activeTab === 'table' }"
              @click="activeTab = 'table'"
              class="tab-btn"
            >
              表格结果
            </button>
          </div>

          <!-- 文本结果页 -->
          <div v-if="activeTab === 'text'" class="tab-content text-results">
            <div v-if="analysisResult.text_results && analysisResult.text_results.length > 0">
              <div 
                v-for="pageResult in analysisResult.text_results" 
                :key="pageResult.page"
                class="text-page"
              >
                <h4 class="page-header">【第 {{ pageResult.page }} 页】</h4>
                <div 
                  class="page-content"
                  v-html="pageResult.highlighted_text || pageResult.text"
                ></div>
              </div>
            </div>
            <div v-else class="no-data">暂无文本内容</div>
          </div>

          <!-- 表格结果页 -->
          <div v-if="activeTab === 'table'" class="tab-content table-results">
            <div v-if="analysisResult.table_results && analysisResult.table_results.length > 0">
              <div 
                v-for="(table, index) in analysisResult.table_results" 
                :key="index"
                class="table-container"
              >
                <h4 class="table-title">{{ table.title }}</h4>
                <table class="financial-table">
                  <thead>
                    <tr>
                      <th 
                        v-for="(header, headerIndex) in table.headers" 
                        :key="headerIndex"
                        @click="sortTable(index, headerIndex)"
                        class="sortable-header"
                      >
                        {{ header }}
                        <span class="sort-indicator">↕</span>
                      </th>
                    </tr>
                  </thead>
                  <tbody>
                    <tr v-for="(row, rowIndex) in table.rows" :key="rowIndex">
                      <td v-for="(cell, cellIndex) in row" :key="cellIndex">
                        {{ cell }}
                      </td>
                    </tr>
                  </tbody>
                </table>
              </div>
            </div>
            <div v-else class="no-data">暂无表格数据</div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'

type ReportType = 'annual' | 'semi' | 'quarterly'

type CrawlResult = { downloaded: number; save_dir: string }

interface AnalysisResult {
  task_id: string
  status: string
  progress: number
  message: string
  text_results?: Array<{
    page: number
    text: string
    highlighted_text?: string
  }>
  table_results?: Array<{
    title: string
    headers: string[]
    rows: string[][]
  }>
  error?: string
}

const code = ref('000001')
const year = ref<number>(2023)
const type = ref<ReportType>('annual')

const loading = ref(false)
const result = ref<CrawlResult | null>(null)
const error = ref('')

// 分析相关状态
const analysisLoading = ref(false)
const analysisProgress = ref(0)
const analysisMessage = ref('')
const analysisResult = ref<AnalysisResult | null>(null)
const analysisError = ref('')
const activeTab = ref<'text' | 'table'>('text')
const currentTaskId = ref('')

// 计算属性
const showAnalysisResults = computed(() => {
  return analysisLoading.value || analysisResult.value || analysisError.value
})

async function startCrawl() {
  loading.value = true
  error.value = ''
  result.value = null
  // 重置分析状态
  resetAnalysisState()
  
  try {
    const res = await fetch('/api/crawl', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        code: code.value.trim(),
        year: Number(year.value),
        type: type.value,
      }),
    })
    const data = await res.json()
    if (!res.ok) {
      throw new Error(data?.detail || res.statusText)
    }
    
    // Python FastAPI 后端直接返回结果
    result.value = {
      downloaded: data.downloaded || 0,
      save_dir: data.save_dir || '未知目录'
    } as CrawlResult
  } catch (e: any) {
    error.value = e?.message || String(e)
  } finally {
    loading.value = false
  }
}

async function startAnalysis() {
  if (!result.value?.downloaded) {
    analysisError.value = '请先成功爬取财报文件'
    return
  }

  analysisLoading.value = true
  analysisError.value = ''
  analysisResult.value = null
  analysisProgress.value = 0
  analysisMessage.value = '正在启动分析任务...'

  try {
    // 启动分析任务
    const res = await fetch('/api/analyze-pdf', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        stock_code: code.value.trim(),
        year: Number(year.value),
        report_type: type.value,
      }),
    })

    const data = await res.json()
    if (!res.ok) {
      throw new Error(data?.detail || res.statusText)
    }

    currentTaskId.value = data.task_id
    
    // 开始轮询任务状态
    pollAnalysisStatus()

  } catch (e: any) {
    analysisError.value = e?.message || String(e)
    analysisLoading.value = false
  }
}

async function pollAnalysisStatus() {
  if (!currentTaskId.value) return

  try {
    const res = await fetch(`/api/analyze-pdf/${currentTaskId.value}`)
    const data = await res.json()

    if (!res.ok) {
      throw new Error(data?.detail || res.statusText)
    }

    analysisProgress.value = data.progress || 0
    analysisMessage.value = data.message || '处理中...'

    if (data.status === 'completed') {
      analysisResult.value = data
      analysisLoading.value = false
    } else if (data.status === 'failed') {
      analysisError.value = 'PDF 提取失败，请检查文件完整性'
      analysisLoading.value = false
    } else {
      // 继续轮询
      setTimeout(pollAnalysisStatus, 1000)
    }

  } catch (e: any) {
    analysisError.value = e?.message || '轮询状态失败'
    analysisLoading.value = false
  }
}

function retryAnalysis() {
  analysisError.value = ''
  startAnalysis()
}

function resetAnalysisState() {
  analysisLoading.value = false
  analysisProgress.value = 0
  analysisMessage.value = ''
  analysisResult.value = null
  analysisError.value = ''
  currentTaskId.value = ''
  activeTab.value = 'text'
}

function sortTable(tableIndex: number, columnIndex: number) {
  if (!analysisResult.value?.table_results?.[tableIndex]) return
  
  const table = analysisResult.value.table_results[tableIndex]
  const rows = [...table.rows]
  
  // 简单的字符串排序
  rows.sort((a, b) => {
    const aVal = a[columnIndex] || ''
    const bVal = b[columnIndex] || ''
    return aVal.localeCompare(bVal)
  })
  
  table.rows = rows
}
</script>

<style scoped>
.page { 
  padding: 16px; 
  max-width: 1400px; 
  margin: 0 auto; 
}

.page h2 { 
  margin: 0 0 20px; 
  font-size: 24px; 
  color: #1e3a8a; 
  font-weight: 600; 
}

.content-layout {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 24px;
  align-items: start;
}

.form-section {
  background: #fff;
  border-radius: 8px;
  padding: 20px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.form { 
  display: grid; 
  grid-template-columns: repeat(2, minmax(220px, 1fr)); 
  gap: 16px; 
  align-items: end; 
  margin-bottom: 20px;
}

label { 
  display: grid; 
  gap: 8px; 
  font-size: 14px; 
  font-weight: 500;
  color: #374151;
}

input, select { 
  height: 40px; 
  padding: 8px 12px; 
  border: 2px solid #e5e7eb; 
  border-radius: 8px; 
  font-size: 14px;
  transition: border-color 0.2s;
}

input:focus, select:focus {
  outline: none;
  border-color: #1e3a8a;
}

button { 
  height: 42px; 
  padding: 0 20px; 
  border: none; 
  border-radius: 8px; 
  background: #1e3a8a; 
  color: #fff; 
  cursor: pointer; 
  font-size: 14px;
  font-weight: 500;
  transition: background-color 0.2s;
}

button:hover:not([disabled]) {
  background: #1e40af;
}

button[disabled] { 
  opacity: 0.6; 
  cursor: not-allowed; 
}

.result { 
  margin-top: 20px; 
  padding: 16px;
  background: #f0f9ff;
  border-radius: 8px;
  border-left: 4px solid #1e3a8a;
}

.result p {
  margin: 8px 0;
  color: #374151;
}

.error { 
  margin-top: 16px; 
  color: #dc2626; 
  background: #fef2f2;
  padding: 12px;
  border-radius: 8px;
  border-left: 4px solid #dc2626;
}

code { 
  background: #f6f8fa; 
  padding: 4px 8px; 
  border-radius: 4px; 
  font-family: 'Courier New', monospace;
  font-size: 13px;
}

/* 分析按钮样式 */
.analysis-btn {
  background: #10b981;
  margin-top: 12px;
  width: 100%;
}

.analysis-btn:hover:not([disabled]) {
  background: #059669;
}

/* 分析结果区域 */
.analysis-section {
  background: #fff;
  border-radius: 8px;
  padding: 20px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  min-height: 400px;
}

.analysis-header h3 {
  margin: 0 0 20px;
  font-size: 18px;
  color: #1e3a8a;
  font-weight: 600;
}

/* 进度条样式 */
.progress-container {
  margin: 20px 0;
}

.progress-bar {
  width: 100%;
  height: 8px;
  background: #e5e7eb;
  border-radius: 4px;
  overflow: hidden;
}

.progress-fill {
  height: 100%;
  background: #1e3a8a;
  transition: width 0.3s ease;
}

.progress-text {
  margin: 8px 0 0;
  font-size: 14px;
  color: #6b7280;
  text-align: center;
}

/* 标签页样式 */
.result-tabs {
  margin-top: 20px;
}

.tab-headers {
  display: flex;
  border-bottom: 2px solid #e5e7eb;
  margin-bottom: 20px;
}

.tab-btn {
  background: none;
  border: none;
  padding: 12px 24px;
  font-size: 14px;
  font-weight: 500;
  color: #6b7280;
  cursor: pointer;
  border-bottom: 2px solid transparent;
  transition: all 0.2s;
}

.tab-btn.active {
  color: #1e3a8a;
  border-bottom-color: #1e3a8a;
}

.tab-btn:hover {
  color: #1e3a8a;
}

.tab-content {
  max-height: 500px;
  overflow-y: auto;
}

/* 文本结果样式 */
.text-results {
  padding: 0;
}

.text-page {
  margin-bottom: 24px;
  border: 1px solid #e5e7eb;
  border-radius: 8px;
  overflow: hidden;
}

.page-header {
  background: #f9fafb;
  padding: 12px 16px;
  margin: 0;
  font-size: 14px;
  font-weight: 600;
  color: #1e3a8a;
  border-bottom: 1px solid #e5e7eb;
}

.page-content {
  padding: 16px;
  line-height: 1.6;
  font-size: 14px;
  color: #374151;
  white-space: pre-wrap;
}

/* 财务术语高亮 */
.page-content :deep(.financial-term) {
  background: #dcfce7;
  color: #166534;
  padding: 2px 4px;
  border-radius: 3px;
  font-weight: 500;
}

/* 表格结果样式 */
.table-results {
  padding: 0;
}

.table-container {
  margin-bottom: 24px;
}

.table-title {
  margin: 0 0 12px;
  font-size: 16px;
  font-weight: 600;
  color: #1e3a8a;
}

.financial-table {
  width: 100%;
  border-collapse: collapse;
  background: #fff;
  border-radius: 8px;
  overflow: hidden;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
}

.financial-table th {
  background: #f9fafb;
  padding: 12px;
  text-align: left;
  font-weight: 600;
  color: #374151;
  border-bottom: 2px solid #e5e7eb;
}

.sortable-header {
  cursor: pointer;
  user-select: none;
  transition: background-color 0.2s;
}

.sortable-header:hover {
  background: #f3f4f6;
}

.sort-indicator {
  margin-left: 8px;
  color: #9ca3af;
  font-size: 12px;
}

.financial-table td {
  padding: 12px;
  border-bottom: 1px solid #f3f4f6;
  color: #374151;
}

.financial-table tbody tr:nth-child(even) {
  background: #f9fafb;
}

.financial-table tbody tr:hover {
  background: #f0f9ff;
}

/* 无数据提示 */
.no-data {
  text-align: center;
  padding: 40px;
  color: #9ca3af;
  font-size: 14px;
}

/* 错误提示样式 */
.analysis-error {
  background: #fef2f2;
  border: 1px solid #fecaca;
  border-radius: 8px;
  padding: 16px;
  margin-top: 20px;
}

.error-message {
  color: #dc2626;
  margin: 0 0 12px;
  font-size: 14px;
  display: flex;
  align-items: center;
}

.error-icon {
  margin-right: 8px;
  font-size: 18px;
}

.retry-btn {
  background: #dc2626;
  font-size: 14px;
  padding: 8px 16px;
  height: auto;
}

.retry-btn:hover:not([disabled]) {
  background: #b91c1c;
}

/* 响应式设计 */
@media (max-width: 1024px) {
  .content-layout {
    grid-template-columns: 1fr;
    gap: 20px;
  }
  
  .form {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 768px) {
  .page {
    padding: 12px;
  }
  
  .form-section,
  .analysis-section {
    padding: 16px;
  }
  
  .tab-headers {
    flex-wrap: wrap;
  }
  
  .tab-btn {
    flex: 1;
    min-width: 120px;
  }
}
</style>