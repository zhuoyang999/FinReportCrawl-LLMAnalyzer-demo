<template>
  <div class="page">
    <h2>财报分析</h2>
    
    <!-- 选项卡 -->
    <div class="tabs">
      <button 
        :class="['tab', { active: activeTab === 'files' }]" 
        @click="switchTab('files')"
      >
        PDF文件列表
      </button>
      <button 
        :class="['tab', { active: activeTab === 'reports' }]" 
        @click="switchTab('reports')"
      >
        已处理报告
      </button>
    </div>

    <!-- PDF文件列表 -->
    <div v-if="activeTab === 'files'" class="pdf-files-section">
      <div class="section-header">
        <h3>已爬取的PDF文件</h3>
        <button @click="loadPdfFiles" :disabled="loadingFiles" class="btn-primary">
          {{ loadingFiles ? '加载中...' : '刷新列表' }}
        </button>
      </div>
      
      <div v-if="pdfFiles.length > 0" class="pdf-files-grid">
        <div 
          v-for="file in pdfFiles" 
          :key="file.id" 
          class="pdf-file-card"
          :class="{ analyzing: file.analyzing }"
        >
          <div class="file-info">
            <div class="file-header">
              <h4>{{ file.company_name }}</h4>
              <span class="stock-code">{{ file.stock_code }}</span>
            </div>
            <div class="file-details">
              <span class="year">{{ file.year }}年</span>
              <span class="report-type">{{ getReportTypeName(file.report_type) }}</span>
              <span class="file-size">{{ formatFileSize(file.file_size) }}</span>
            </div>
            <div class="file-name">{{ file.file_name }}</div>
            <div class="file-time">{{ formatDate(file.modified_time) }}</div>
          </div>
          <div class="file-actions">
            <button 
              @click="analyzePdfFile(file)" 
              :disabled="file.analyzing"
              class="btn-analyze"
            >
              {{ file.analyzing ? '分析中...' : '分析' }}
            </button>
          </div>
        </div>
      </div>
      
      <div v-else-if="!loadingFiles" class="empty-state">
        <p>暂无PDF文件，请先进行财报爬取</p>
      </div>
    </div>

    <!-- 已处理报告 -->
    <div v-if="activeTab === 'reports'">
      <!-- 查询表单 -->
      <div class="form-row">
        <label>
          股票代码
          <input v-model.trim="queryForm.stockCode" placeholder="如 000001" />
        </label>
        <label>
          公司名称
          <input v-model.trim="queryForm.companyName" placeholder="可选" />
        </label>
        <label>
          报告类型
          <select v-model="queryForm.reportType">
            <option value="">全部</option>
            <option value="annual">年报</option>
            <option value="interim">中报</option>
            <option value="quarterly">季报</option>
          </select>
        </label>
      </div>
      <div class="form-row">
        <label>
          开始年份
          <input type="number" v-model.number="queryForm.startYear" min="2000" max="2030" placeholder="可选" />
        </label>
        <label>
          结束年份
          <input type="number" v-model.number="queryForm.endYear" min="2000" max="2030" placeholder="可选" />
        </label>
        <div class="form-actions">
          <button :disabled="loading" @click="searchReports(1)" class="btn-primary">
            {{ loading ? '查询中...' : '查询' }}
          </button>
          <button @click="clearForm" class="btn-secondary">清空</button>
        </div>
      </div>
    </div>

    <!-- 统计信息 -->
    <div v-if="stats" class="stats-section">
      <h3>系统统计</h3>
      <div class="stats-grid">
        <div class="stat-card">
          <div class="stat-number">{{ stats.totalReports || 0 }}</div>
          <div class="stat-label">总报告数</div>
        </div>
        <div class="stat-card">
          <div class="stat-number">{{ stats.totalCompanies || 0 }}</div>
          <div class="stat-label">公司数量</div>
        </div>
        <div class="stat-card">
          <div class="stat-number">{{ stats.latestYear || '-' }}</div>
          <div class="stat-label">最新年份</div>
        </div>
      </div>
    </div>

    <!-- 查询结果 -->
    <div v-if="reports.length > 0" class="results-section">
      <h3>查询结果 (共 {{ pagination.total }} 条)</h3>
      <div class="table-container">
        <table class="reports-table">
          <thead>
            <tr>
              <th>股票代码</th>
              <th>公司名称</th>
              <th>报告类型</th>
              <th>年份</th>
              <th>报告期</th>
              <th>处理时间</th>
              <th>状态</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="report in reports" :key="report.id">
              <td>{{ report.stockCode }}</td>
              <td>{{ report.companyName || '-' }}</td>
              <td>
                <span class="report-type" :class="getReportTypeClass(report.reportType)">
                  {{ getReportTypeName(report.reportType) }}
                </span>
              </td>
              <td>{{ report.year }}</td>
              <td>{{ report.reportPeriod || '-' }}</td>
              <td>{{ formatDate(report.processedAt) }}</td>
              <td>
                <span class="status" :class="report.status === 'success' ? 'status-success' : 'status-error'">
                  {{ report.status === 'success' ? '成功' : '失败' }}
                </span>
              </td>
            </tr>
          </tbody>
        </table>
      </div>

      <!-- 分页 -->
      <div class="pagination">
        <button 
          :disabled="!pagination.hasPrevious" 
          @click="changePage(pagination.page - 1)"
          class="btn-page"
        >
          上一页
        </button>
        <span class="page-info">
          第 {{ pagination.page }} 页 / 共 {{ pagination.totalPages }} 页
        </span>
        <button 
          :disabled="!pagination.hasNext" 
          @click="changePage(pagination.page + 1)"
          class="btn-page"
        >
          下一页
        </button>
      </div>
    </div>

    <!-- 空状态 -->
    <div v-else-if="!loading && searched" class="empty-state">
      <p>未找到符合条件的财务报告</p>
    </div>

    <!-- 错误信息 -->
    <div v-if="error" class="error">
      错误：{{ error }}
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { ElMessage } from 'element-plus'

// 类型定义
interface FinancialReport {
  id: number
  stockCode: string
  companyName?: string
  reportType: string
  year: number
  reportPeriod?: string
  processedAt: string
  status: string
}

interface PdfFile {
  id: string
  stock_code: string
  company_name: string
  year: string
  report_type: string
  file_name: string
  file_path: string
  file_size: number
  modified_time: string
  relative_path: string
  analyzing?: boolean
}

interface QueryForm {
  stockCode: string
  companyName: string
  reportType: string
  startYear?: number
  endYear?: number
}

interface Pagination {
  page: number
  size: number
  total: number
  totalPages: number
  hasNext: boolean
  hasPrevious: boolean
}

interface Stats {
  totalReports: number
  totalCompanies: number
  latestYear: number
}

// 响应式数据
const activeTab = ref('files')
const loading = ref(false)
const loadingFiles = ref(false)
const searched = ref(false)
const error = ref('')
const reports = ref<FinancialReport[]>([])
const pdfFiles = ref<PdfFile[]>([])
const stats = ref<Stats | null>(null)

const queryForm = ref<QueryForm>({
  stockCode: '',
  companyName: '',
  reportType: '',
  startYear: undefined,
  endYear: undefined
})

const pagination = ref<Pagination>({
  page: 1,
  size: 10,
  total: 0,
  totalPages: 0,
  hasNext: false,
  hasPrevious: false
})

// 方法
async function searchReports(page = 1) {
  loading.value = true
  error.value = ''
  
  try {
    const params = new URLSearchParams()
    
    if (queryForm.value.stockCode) params.append('stockCode', queryForm.value.stockCode)
    if (queryForm.value.companyName) params.append('companyName', queryForm.value.companyName)
    if (queryForm.value.reportType) params.append('reportType', queryForm.value.reportType)
    if (queryForm.value.startYear) params.append('startYear', queryForm.value.startYear.toString())
    if (queryForm.value.endYear) params.append('endYear', queryForm.value.endYear.toString())
    
    params.append('page', page.toString())
    params.append('size', pagination.value.size.toString())
    
    // 修改参数名以适配Python后端
    const pythonParams = new URLSearchParams()
    
    if (queryForm.value.stockCode) pythonParams.append('stock_code', queryForm.value.stockCode)
    if (queryForm.value.companyName) pythonParams.append('company_name', queryForm.value.companyName)
    if (queryForm.value.startYear) pythonParams.append('start_date', `${queryForm.value.startYear}-01-01`)
    if (queryForm.value.endYear) pythonParams.append('end_date', `${queryForm.value.endYear}-12-31`)
    
    pythonParams.append('page', page.toString())
    pythonParams.append('page_size', pagination.value.size.toString())
    
    const res = await fetch(`/api/financial-reports?${pythonParams}`)
    console.log("Fetch response:", res); // 添加日志：打印原始响应对象
    
    let data: any = null;
    try {
      data = await res.json();
    } catch (jsonError) {
      // 如果 res.json() 解析失败，说明响应体不是有效的 JSON。
      // 这可能是因为服务器返回了非 JSON 错误页面或空响应。
      console.error("Failed to parse JSON response:", jsonError); // 添加日志：打印 JSON 解析错误
      // 此时，我们使用 res.statusText 或一个通用错误消息
      throw new Error(`服务器返回了非JSON格式的响应。状态码: ${res.status}, 状态文本: ${res.statusText || '无'}. 错误详情: ${jsonError instanceof Error ? jsonError.message : String(jsonError)}`); 
    }

    if (!res.ok) {
      console.log("Backend returned non-OK response, data:", data); // 添加日志：打印后端返回的非成功响应数据
      throw new Error(data?.detail || res.statusText || "服务器错误，请检查后端日志。");
    }
    
    // 适配Python后端的响应格式
    const reportData = data.data || []
    const paginationData = data.pagination || {}
    
    // 转换数据格式以适配前端显示
    reports.value = reportData.map((item: any) => ({
      id: item.id,
      stockCode: item.stock_code || '',
      companyName: item.company_name || '',
      reportType: 'annual', // 暂时固定为年报，因为Python后端数据中没有这个字段
      year: item.report_date ? new Date(item.report_date).getFullYear() : 0,
      reportPeriod: item.report_date || '',
      processedAt: item.crawl_time || '',
      status: 'success' // 暂时固定为成功状态
    }))
    
    pagination.value = {
      page: paginationData.page || 1,
      size: paginationData.page_size || 10,
      total: paginationData.total || 0,
      totalPages: paginationData.total_pages || 0,
      hasNext: (paginationData.page || 1) < (paginationData.total_pages || 0),
      hasPrevious: (paginationData.page || 1) > 1
    }
    searched.value = true
  } catch (e: any) {
    console.error("Caught error in searchReports:", e); // 添加日志：打印最终捕获的错误对象
    error.value = e?.message || String(e)
  } finally {
    loading.value = false
  }
}

async function loadStats() {
  try {
    const res = await fetch('/api/stats')
    const data = await res.json()
    
    if (res.ok) {
      // 适配Python后端的统计数据格式
      stats.value = {
        totalReports: data.total_reports || 0,
        totalCompanies: data.total_companies || 0,
        latestYear: data.latest_report_date ? new Date(data.latest_report_date).getFullYear() : 0
      }
    }
  } catch (e) {
    console.warn('加载统计信息失败:', e)
  }
}

function changePage(page: number) {
  if (page >= 1 && page <= pagination.value.totalPages) {
    searchReports(page)
  }
}

function clearForm() {
  queryForm.value = {
    stockCode: '',
    companyName: '',
    reportType: '',
    startYear: undefined,
    endYear: undefined
  }
  reports.value = []
  searched.value = false
  error.value = ''
}

function getReportTypeName(type: string): string {
  const typeMap: Record<string, string> = {
    annual: '年报',
    interim: '中报',
    quarterly: '季报'
  }
  return typeMap[type] || type
}

function getReportTypeClass(type: string): string {
  const classMap: Record<string, string> = {
    annual: 'type-annual',
    interim: 'type-interim',
    quarterly: 'type-quarterly'
  }
  return classMap[type] || ''
}

function formatDate(dateStr: string): string {
  if (!dateStr) return '-'
  try {
    return new Date(dateStr).toLocaleString('zh-CN')
  } catch {
    return dateStr
  }
}

// PDF文件相关方法
async function loadPdfFiles() {
  loadingFiles.value = true
  error.value = ''
  
  try {
    const res = await fetch('/api/pdf-files')
    const data = await res.json()
    
    if (!res.ok) {
      throw new Error(data?.detail || res.statusText || "加载PDF文件列表失败")
    }
    
    pdfFiles.value = data.data || []
  } catch (e: any) {
    console.error("加载PDF文件列表失败:", e)
    error.value = e?.message || String(e)
  } finally {
    loadingFiles.value = false
  }
}

async function analyzePdfFile(file: PdfFile) {
  try {
    // 显示加载状态
    const loadingMessage = ElMessage.loading('正在启动PDF分析任务...')
    
    const requestBody = {
      file_path: file.file_path,
      stock_code: file.stock_code,
      company_name: file.company_name,
      year: file.year,
      report_type: file.report_type
    }
    
    const res = await fetch('/api/analyze-pdf-by-path', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify(requestBody)
    })
    
    const data = await res.json()
    loadingMessage.close()
    
    if (!res.ok) {
      throw new Error(data?.detail || res.statusText || "启动分析任务失败")
    }
    
    ElMessage.success(`分析任务已启动，任务ID: ${data.task_id}`)
    
    // 可以选择切换到已处理报告选项卡
    // activeTab.value = 'processed'
    
  } catch (e: any) {
    console.error("分析PDF文件失败:", e)
    ElMessage.error(e?.message || "分析PDF文件失败")
  }
}

function formatFileSize(bytes: number): string {
  if (bytes === 0) return '0 B'
  const k = 1024
  const sizes = ['B', 'KB', 'MB', 'GB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i]
}

function switchTab(tab: string) {
  activeTab.value = tab
  if (tab === 'files' && pdfFiles.value.length === 0) {
    loadPdfFiles()
  }
}

// 生命周期
onMounted(() => {
  loadStats()
  // 默认加载PDF文件列表
  loadPdfFiles()
})
</script>

<style scoped>
.page {
  padding: 16px;
  max-width: 1200px;
  margin: 0 auto;
}

.page h2 {
  margin: 0 0 24px;
  font-size: 24px;
  color: #333;
}

.page h3 {
  margin: 0 0 16px;
  font-size: 18px;
  color: #555;
}

/* 查询表单 */
.query-form {
  background: #f8f9fa;
  padding: 20px;
  border-radius: 8px;
  margin-bottom: 24px;
}

.form-row {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 16px;
  margin-bottom: 16px;
  align-items: end;
}

.form-row:last-child {
  margin-bottom: 0;
}

label {
  display: flex;
  flex-direction: column;
  gap: 6px;
  font-size: 14px;
  font-weight: 500;
}

input, select {
  height: 36px;
  padding: 8px 12px;
  border: 1px solid #ddd;
  border-radius: 6px;
  font-size: 14px;
}

input:focus, select:focus {
  outline: none;
  border-color: #4f79ff;
  box-shadow: 0 0 0 2px rgba(79, 121, 255, 0.1);
}

.form-actions {
  display: flex;
  gap: 12px;
  align-items: center;
}

.btn-primary, .btn-secondary {
  height: 36px;
  padding: 0 16px;
  border: none;
  border-radius: 6px;
  font-size: 14px;
  cursor: pointer;
  transition: all 0.2s;
}

.btn-primary {
  background: #4f79ff;
  color: white;
}

.btn-primary:hover:not(:disabled) {
  background: #3d63e6;
}

.btn-primary:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.btn-secondary {
  background: #6c757d;
  color: white;
}

.btn-secondary:hover {
  background: #5a6268;
}

/* 统计信息 */
.stats-section {
  margin-bottom: 24px;
}

.stats-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
  gap: 16px;
}

.stat-card {
  background: white;
  padding: 20px;
  border-radius: 8px;
  text-align: center;
  box-shadow: 0 2px 4px rgba(0,0,0,0.1);
}

.stat-number {
  font-size: 24px;
  font-weight: bold;
  color: #4f79ff;
  margin-bottom: 8px;
}

.stat-label {
  font-size: 14px;
  color: #666;
}

/* 结果表格 */
.results-section {
  margin-bottom: 24px;
}

.table-container {
  background: white;
  border-radius: 8px;
  overflow: hidden;
  box-shadow: 0 2px 4px rgba(0,0,0,0.1);
  margin-bottom: 16px;
}

.reports-table {
  width: 100%;
  border-collapse: collapse;
}

.reports-table th,
.reports-table td {
  padding: 12px;
  text-align: left;
  border-bottom: 1px solid #eee;
}

.reports-table th {
  background: #f8f9fa;
  font-weight: 600;
  color: #555;
}

.reports-table tbody tr:hover {
  background: #f8f9fa;
}

.report-type {
  padding: 4px 8px;
  border-radius: 4px;
  font-size: 12px;
  font-weight: 500;
}

.type-annual {
  background: #e3f2fd;
  color: #1976d2;
}

.type-interim {
  background: #f3e5f5;
  color: #7b1fa2;
}

.type-quarterly {
  background: #e8f5e8;
  color: #388e3c;
}

.status {
  padding: 4px 8px;
  border-radius: 4px;
  font-size: 12px;
  font-weight: 500;
}

.status-success {
  background: #e8f5e8;
  color: #388e3c;
}

.status-error {
  background: #ffebee;
  color: #d32f2f;
}

/* 分页 */
.pagination {
  display: flex;
  justify-content: center;
  align-items: center;
  gap: 16px;
}

.btn-page {
  height: 36px;
  padding: 0 16px;
  border: 1px solid #ddd;
  border-radius: 6px;
  background: white;
  cursor: pointer;
  transition: all 0.2s;
}

.btn-page:hover:not(:disabled) {
  border-color: #4f79ff;
  color: #4f79ff;
}

.btn-page:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.page-info {
  font-size: 14px;
  color: #666;
}

/* 空状态和错误 */
.empty-state {
  text-align: center;
  padding: 40px;
  color: #666;
}

.error {
  background: #ffebee;
  color: #d32f2f;
  padding: 12px;
  border-radius: 6px;
  margin-top: 16px;
}

/* 选项卡样式 */
.tabs {
  display: flex;
  margin-bottom: 24px;
  border-bottom: 1px solid #e0e0e0;
}

.tab {
  padding: 12px 24px;
  border: none;
  background: none;
  cursor: pointer;
  font-size: 16px;
  color: #666;
  border-bottom: 2px solid transparent;
  transition: all 0.2s;
}

.tab:hover {
  color: #4f79ff;
}

.tab.active {
  color: #4f79ff;
  border-bottom-color: #4f79ff;
  font-weight: 500;
}

/* PDF文件列表样式 */
.pdf-files-section {
  margin-bottom: 24px;
}

.section-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
}

.pdf-files-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(350px, 1fr));
  gap: 16px;
}

.pdf-file-card {
  border: 1px solid #e0e0e0;
  border-radius: 8px;
  padding: 16px;
  background: white;
  transition: all 0.2s;
}

.pdf-file-card:hover {
  border-color: #4f79ff;
  box-shadow: 0 2px 8px rgba(79, 121, 255, 0.1);
}

.file-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 12px;
}

.company-info h4 {
  margin: 0 0 4px;
  font-size: 16px;
  color: #333;
}

.company-info .stock-code {
  font-size: 14px;
  color: #666;
}

.file-meta {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 8px;
  margin-bottom: 12px;
  font-size: 14px;
}

.meta-item {
  display: flex;
  justify-content: space-between;
}

.meta-label {
  color: #666;
}

.meta-value {
  color: #333;
  font-weight: 500;
}

.file-details {
  font-size: 12px;
  color: #888;
  margin-bottom: 12px;
}

.file-actions {
  display: flex;
  justify-content: flex-end;
}

.btn-analyze {
  padding: 8px 16px;
  background: #4f79ff;
  color: white;
  border: none;
  border-radius: 6px;
  cursor: pointer;
  font-size: 14px;
  transition: all 0.2s;
}

.btn-analyze:hover {
  background: #3d63e6;
}
</style>