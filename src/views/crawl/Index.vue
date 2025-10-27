<template>
  <div class="page-container">
    <el-row :gutter="20" class="mb-4">
      <el-col :span="12">
        <el-card class="input-card">
          <template #header>
            <div class="card-header">
              <span>输入爬取信息</span>
            </div>
          </template>
          <el-form label-position="top">
            <el-form-item label="股票代码 *">
              <el-input v-model.trim="stockCode" placeholder="例如：000001" />
              <el-text type="info" size="small">输入6位股票代码，沪市以6开头，深市以0或3开头</el-text>
            </el-form-item>
            <el-form-item label="报告年份 *">
              <el-select v-model="reportYear" placeholder="选择年份" style="width: 100%">
                <el-option v-for="year in availableYears" :key="year" :label="year" :value="year" />
              </el-select>
            </el-form-item>
            <el-form-item label="报告类型 *">
              <el-select v-model="reportType" placeholder="选择报告类型" style="width: 100%">
                <el-option label="年度报告" value="annual" />
                <el-option label="半年度报告" value="semi-annual" />
                <el-option label="季度报告" value="quarterly" />
              </el-select>
            </el-form-item>
            <el-button type="primary" @click="startCrawl" :loading="isCrawling" style="width: 100%">
              {{ isCrawling ? '爬取中...' : '开始爬取' }}
            </el-button>
          </el-form>
        </el-card>
      </el-col>
      <el-col :span="12">
        <el-card class="status-card">
          <template #header>
            <div class="card-header">
              <span>爬取状态</span>
            </div>
          </template>
          <div class="status-content">
            <el-empty v-if="!isCrawling && !crawlError && !crawledReport" description="请在左侧填写信息并开始爬取" />
            <el-result v-else-if="isCrawling" icon="info" title="正在爬取中..." sub-title="请稍候...">
              <template #icon>
                <el-icon class="is-loading"><Loading /></el-icon>
              </template>
            </el-result>
            <el-result v-else-if="crawlError" icon="error" title="爬取失败" :sub-title="crawlError" />
            <el-result v-else-if="crawledReport" icon="success" title="爬取成功！">
              <template #extra>
                <el-descriptions :column="1" border>
                  <el-descriptions-item label="公司名称">{{ crawledReport.company_name }}</el-descriptions-item>
                  <el-descriptions-item label="报告类型">{{ crawledReport.report_type }}</el-descriptions-item>
                </el-descriptions>
              </template>
            </el-result>
          </div>
        </el-card>
      </el-col>
    </el-row>
    
    <el-card class="reports-card">
      <template #header>
        <div class="card-header">
          <span>已爬取的报告</span>
        </div>
      </template>
      <el-empty v-if="crawledReports.length === 0" description="暂无爬取记录" />
      <el-table v-else :data="crawledReports" style="width: 100%" max-height="400">
        <el-table-column prop="company_name" label="公司名称" />
        <el-table-column prop="report_type" label="报告类型" />
        <el-table-column prop="crawl_time" label="爬取时间" width="180" />
        <el-table-column label="操作" width="180">
          <template #default="scope">
            <el-button-group>
              <el-button type="primary" size="small" @click="downloadReport(scope.row.id)">
                <el-icon><Download /></el-icon> 下载
              </el-button>
              <el-button type="success" size="small" @click="analyzeReport(scope.row.id)">
                <el-icon><DataAnalysis /></el-icon> 分析
              </el-button>
            </el-button-group>
          </template>
        </el-table-column>
      </el-table>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue';
import axios from 'axios';
import { Loading, Download, DataAnalysis } from '@element-plus/icons-vue';

interface CrawledReport {
  id: number;
  company_name: string;
  stock_code: string;
  report_date: string;
  report_type: string;
  crawl_time: string;
}

const stockCode = ref('');
const reportYear = ref(new Date().getFullYear());
const reportType = ref('annual');
const isCrawling = ref(false);
const crawlError = ref<string | null>(null);
const crawledReport = ref<CrawledReport | null>(null);
const crawledReports = ref<CrawledReport[]>([]);

const availableYears = computed(() => {
  const currentYear = new Date().getFullYear();
  const years = [];
  for (let i = currentYear; i >= 2000; i--) {
    years.push(i);
  }
  return years;
});

const fetchCrawledReports = async () => {
  try {
    const response = await axios.get('http://127.0.0.1:8000/api/financial-reports');
    crawledReports.value = response.data.data;
  } catch (error) {
    console.error('获取已爬取报告失败:', error);
    // 添加模拟数据以便于测试UI
    crawledReports.value = [
      {
        id: 1,
        company_name: '平安银行',
        stock_code: '000001',
        report_date: '2023-12-31',
        report_type: '年度报告',
        crawl_time: '2024-01-15 14:30:00'
      },
      {
        id: 2,
        company_name: '招商银行',
        stock_code: '600036',
        report_date: '2023-06-30',
        report_type: '半年度报告',
        crawl_time: '2023-08-20 09:15:00'
      }
    ];
  }
};

const startCrawl = async () => {
  isCrawling.value = true;
  crawlError.value = null;
  crawledReport.value = null;
  try {
    const response = await axios.post('http://127.0.0.1:8000/api/crawl', {
      code: stockCode.value,
      year: reportYear.value,
      type: reportType.value
    });
    crawledReport.value = response.data;
    fetchCrawledReports(); // 重新获取列表
  } catch (error: any) {
    crawlError.value = error.response?.data?.detail || error.message || '未知错误';
  } finally {
    isCrawling.value = false;
  }
};

const downloadReport = (id: number) => {
  // 下载逻辑
  console.log('下载报告:', id);
};

const analyzeReport = (id: number) => {
  // 分析逻辑
  console.log('分析报告:', id);
};

onMounted(() => {
  fetchCrawledReports();
});
</script>

<style scoped>
.page-container {
  padding: 20px;
}
.mb-4 {
  margin-bottom: 16px;
}
.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}
.input-card, .status-card, .reports-card {
  width: 100%;
  margin-bottom: 16px;
}
.status-content {
  min-height: 200px;
  display: flex;
  align-items: center;
  justify-content: center;
}
:deep(.el-card__header) {
  font-weight: bold;
}
:deep(.el-form-item__label) {
  font-weight: 500;
}
</style>