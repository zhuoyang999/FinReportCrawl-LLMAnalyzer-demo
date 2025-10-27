<template>
  <div class="home-container">
    <!-- 头部区域 -->
    <el-row class="hero-section">
      <el-col :span="24" class="text-center">
        <h1 class="hero-title">智能财报分析平台</h1>
        <p class="hero-subtitle">专注于从公开渠道获取企业财务报告原始文件，提供智能分析服务</p>
        <div class="hero-buttons">
          <el-button type="primary" @click="go('/crawl')" size="large">
            <el-icon><Upload /></el-icon>开始爬取
          </el-button>
          <el-button type="success" @click="go('/analysis')" size="large">
            <el-icon><DataAnalysis /></el-icon>开始分析
          </el-button>
          <el-button type="warning" @click="go('/smart')" size="large">
            <el-icon><CPU /></el-icon>智能分析
          </el-button>
        </div>
      </el-col>
    </el-row>

    <!-- 功能卡片区域 -->
    <el-row class="feature-cards-section">
      <el-col :span="8" v-for="card in cards" :key="card.title" class="feature-card-col">
        <el-card class="feature-card" shadow="hover" @click="go(card.path)">
          <template #header>
            <div class="card-header">
              <h3>{{ card.title }}</h3>
            </div>
          </template>
          <div class="card-content">
            <p>{{ card.desc }}</p>
            <el-divider />
            <div class="card-footer">
              <el-button type="text" class="more-link">开始分析 <el-icon><ArrowRight /></el-icon></el-button>
            </div>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <!-- 最近报告区域 -->
    <el-row class="recent-reports-section">
      <el-col :span="24">
        <el-card shadow="never">
          <template #header>
            <div class="card-header">
              <h3>最近爬取的报告</h3>
            </div>
          </template>
          <el-table :data="recentReports" stripe style="width: 100%">
            <el-table-column prop="company_name" label="公司名称" />
            <el-table-column prop="stock_code" label="股票代码" width="120" />
            <el-table-column prop="report_type" label="报告类型" width="180" />
            <el-table-column prop="crawl_time" label="爬取时间" width="180" />
            <el-table-column label="操作" width="180">
              <template #default="scope">
                <el-button size="small" @click="downloadReport(scope.row.id)">
                  <el-icon><Download /></el-icon>下载
                </el-button>
                <el-button size="small" type="primary" @click="analyzeReport(scope.row.id)">
                  <el-icon><View /></el-icon>分析
                </el-button>
              </template>
            </el-table-column>
          </el-table>
        </el-card>
      </el-col>
    </el-row>

    <!-- 统计数据区域 -->
    <el-row class="stats-section">
      <el-col :span="6" v-for="(value, key, index) in statsDisplay" :key="index">
        <el-card class="stat-card" shadow="hover">
          <el-statistic :title="value.title" :value="value.value">
            <template #suffix>
              <el-icon v-if="value.icon"><component :is="value.icon" /></el-icon>
            </template>
          </el-statistic>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, computed } from 'vue';
import { useRouter } from 'vue-router';
import axios from 'axios';

interface RecentReport {
  id: number;
  company_name: string;
  stock_code: string;
  report_type: string;
  crawl_time: string;
}

interface Stats {
  total_reports: number;
  covered_companies: number;
  year_coverage: string;
  analysis_count: number;
}

const router = useRouter();
const go = (path: string) => router.push(path);

const cards = ref([
  {
    title: '爬取财报',
    desc: '从巨潮资讯网、上交所、深交所等公开渠道获取企业财务报告原始文件，支持多种报告类型和时间范围。',
    path: '/crawl',
  },
  {
    title: '财报分析',
    desc: '对已爬取的财务报告进行智能分析，提取关键财务指标，生成可视化图表，帮助您快速了解公司财务状况。',
    path: '/analysis',
  },
  {
    title: 'LLM智能分析',
    desc: '基于大语言模型的智能财报分析，提供深度洞察和投资建议，帮助您全面地理解公司价值和投资机会。',
    path: '/smart',
  },
]);

const recentReports = ref<RecentReport[]>([]);
const stats = ref<Stats>({ total_reports: 0, covered_companies: 0, year_coverage: 'N/A', analysis_count: 0 });

const statsDisplay = computed(() => ({
  total_reports: { title: '总报告数', value: stats.value.total_reports, icon: 'Document' },
  covered_companies: { title: '覆盖公司', value: stats.value.covered_companies, icon: 'OfficeBuilding' },
  year_coverage: { title: '年度覆盖', value: stats.value.year_coverage, icon: 'Calendar' },
  analysis_count: { title: '分析次数', value: stats.value.analysis_count, icon: 'DataAnalysis' },
}));

const fetchRecentReports = async () => {
  try {
    const response = await axios.get('http://127.0.0.1:8000/api/financial-reports?page=1&page_size=10');
    recentReports.value = response.data.data;
  } catch (error) {
    console.error('获取最近报告失败:', error);
    // 添加一些模拟数据用于展示
    recentReports.value = [
      { id: 1, company_name: '平安银行', stock_code: '000001', report_type: '2022年年度报告', crawl_time: '2023-05-20 10:30:00' },
      { id: 2, company_name: 'ST国华', stock_code: '000004', report_type: '2021年年度报告（更正后）', crawl_time: '2023-05-19 15:45:22' },
    ];
  }
};

const fetchStats = async () => {
  try {
    const response = await axios.get('http://127.0.0.1:8000/api/stats'); 
    stats.value = response.data;
  } catch (error) {
    console.error('获取统计数据失败:', error);
    // 使用假数据以进行UI展示
    stats.value = { total_reports: 13, covered_companies: 8, year_coverage: '2023 - 2025', analysis_count: 9 };
  }
};

const downloadReport = (id: number) => {
  console.log('下载报告:', id);
};

const analyzeReport = (id: number) => {
  console.log('分析报告:', id);
};

onMounted(() => {
  fetchRecentReports();
  fetchStats();
});
</script>

<style scoped>
.home-container {
  padding-bottom: 40px;
}

.hero-section {
  padding: 60px 20px;
  background-color: #f0f2f5;
  margin-bottom: 30px;
}

.hero-title {
  font-size: 2.5rem;
  margin-bottom: 16px;
  color: #303133;
}

.hero-subtitle {
  font-size: 1.2rem;
  color: #606266;
  margin-bottom: 30px;
}

.hero-buttons {
  display: flex;
  justify-content: center;
  gap: 16px;
}

.feature-cards-section {
  margin-bottom: 30px;
  padding: 0 20px;
}

.feature-card-col {
  padding: 10px;
}

.feature-card {
  height: 100%;
  cursor: pointer;
  transition: transform 0.3s;
}

.feature-card:hover {
  transform: translateY(-5px);
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.card-content {
  display: flex;
  flex-direction: column;
  height: 100%;
}

.card-footer {
  margin-top: auto;
  text-align: right;
}

.recent-reports-section {
  margin-bottom: 30px;
  padding: 0 20px;
}

.stats-section {
  padding: 0 20px;
}

.stat-card {
  text-align: center;
  padding: 20px 0;
}

.text-center {
  text-align: center;
}

.more-link {
  display: flex;
  align-items: center;
  justify-content: flex-end;
}
</style>