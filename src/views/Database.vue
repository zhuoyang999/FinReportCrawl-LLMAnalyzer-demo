<template>
  <div>
    <h1>财务报告数据</h1>
    <table>
      <thead>
        <tr>
          <th>ID</th>
          <th>公司名称</th>
          <th>股票代码</th>
          <th>报告日期</th>
          <th>营收</th>
          <th>净利润</th>
          <th>每股收益</th>
          <th>爬取时间</th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="report in reports" :key="report.id">
          <td>{{ report.id }}</td>
          <td>{{ report.company_name }}</td>
          <td>{{ report.stock_code }}</td>
          <td>{{ report.report_date }}</td>
          <td>{{ report.revenue }}</td>
          <td>{{ report.net_profit }}</td>
          <td>{{ report.eps }}</td>
          <td>{{ report.crawl_time }}</td>
        </tr>
      </tbody>
    </table>
    <div>
      <button @click="prevPage" :disabled="page === 1">上一页</button>
      <span>第 {{ page }} 页 / 共 {{ totalPages }} 页</span>
      <button @click="nextPage" :disabled="page === totalPages">下一页</button>
    </div>
  </div>
</template>

<script lang="ts">
import { defineComponent, ref, onMounted } from 'vue';
import axios from 'axios';

interface FinancialReport {
  id: number;
  company_name: string;
  stock_code: string;
  report_date: string;
  revenue: number;
  net_profit: number;
  eps: number;
  crawl_time: string;
}

export default defineComponent({
  name: 'Database',
  setup() {
    const reports = ref<FinancialReport[]>([]);
    const page = ref(1);
    const pageSize = ref(20);
    const totalPages = ref(1);

    const fetchReports = async () => {
      try {
        const response = await axios.get('/api/financial-reports/query', {
          params: {
            page: page.value,
            size: pageSize.value,
          },
        });
        
        const data = response.data;
        
        // 适配Java后端的响应格式
        if (data.code === 200) {
          reports.value = data.data.items;
          totalPages.value = Math.ceil(data.data.total / pageSize.value);
        } else {
          throw new Error(data.message || '查询失败');
        }
      } catch (error) {
        console.error('获取财务报告失败:', error);
      }
    };

    const prevPage = () => {
      if (page.value > 1) {
        page.value--;
        fetchReports();
      }
    };

    const nextPage = () => {
      if (page.value < totalPages.value) {
        page.value++;
        fetchReports();
      }
    };

    onMounted(() => {
      fetchReports();
    });

    return {
      reports,
      page,
      totalPages,
      prevPage,
      nextPage,
    };
  },
});
</script>

<style scoped>
table {
  width: 100%;
  border-collapse: collapse;
}
th, td {
  border: 1px solid #ddd;
  padding: 8px;
}
th {
  background-color: #f2f2f2;
}
</style>