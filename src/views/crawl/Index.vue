<template>
  <div class="page">
    <h2>爬取财报</h2>
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
    </div>
    <div v-if="error" class="error">错误：{{ error }}</div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'

type ReportType = 'annual' | 'semi' | 'quarterly'

type CrawlResult = { downloaded: number; save_dir: string }

const code = ref('000001')
const year = ref<number>(2023)
const type = ref<ReportType>('annual')

const loading = ref(false)
const result = ref<CrawlResult | null>(null)
const error = ref('')

async function startCrawl() {
  loading.value = true
  error.value = ''
  result.value = null
  try {
    const res = await fetch('/api/financial-reports/crawl', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        stockCode: code.value.trim(),
        year: Number(year.value),
        reportType: type.value,
      }),
    })
    const data = await res.json()
    if (!res.ok) {
      throw new Error(data?.message || res.statusText)
    }
    
    // 适配Java后端的响应格式
    if (data.code === 200) {
      result.value = {
        downloaded: data.data?.downloaded || 0,
        save_dir: data.data?.save_dir || '未知目录'
      } as CrawlResult
    } else {
      throw new Error(data.message || '爬取失败')
    }
  } catch (e: any) {
    error.value = e?.message || String(e)
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.page { padding: 16px; }
.page h2 { margin: 0 0 12px; font-size: 18px; }
.form { display: grid; grid-template-columns: repeat(2, minmax(220px, 1fr)); gap: 12px; align-items: end; }
label { display: grid; gap: 6px; font-size: 13px; }
input, select { height: 32px; padding: 4px 8px; border: 1px solid #ddd; border-radius: 6px; }
button { height: 34px; padding: 0 14px; border: none; border-radius: 6px; background: #4f79ff; color: #fff; cursor: pointer; }
button[disabled] { opacity: 0.6; cursor: not-allowed; }
.result, .error { margin-top: 16px; }
.error { color: #d93025; }
code { background: #f6f8fa; padding: 2px 6px; border-radius: 4px; }
</style>