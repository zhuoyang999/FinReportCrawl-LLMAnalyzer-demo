<template>
  <Hero :actions="actions" @navigate="go" />
  <FeatureCards :cards="cards" @navigate="go" />
</template>

<script setup lang="ts">
import { useRouter } from 'vue-router'
import Hero from '../components/home/Hero.vue'
import FeatureCards from '../components/home/FeatureCards.vue'

const router = useRouter()
const go = (path: string) => router.push(path)

const actions = [
  { label: '开始爬取', icon: 'Upload', path: '/crawl' },
  { label: '开始分析', icon: 'TrendCharts', path: '/analysis', plain: true },
  { label: '智能分析', icon: 'Cpu', path: '/smart', plain: true },
]

const cards = [
  {
    title: '爬取财报',
    desc: '从巨潮资讯网、上交所、深交所等公开渠道获取企业财务报告原始文件，支持多种报告类型和时间范围。',
    icon: 'Upload',
    color: '#3aa675',
    path: '/crawl',
  },
  {
    title: '财报分析',
    desc: '对已爬取的财务报告进行智能分析，提取关键财务指标，生成可视化图表，帮助您快速了解公司财务状况。',
    icon: 'TrendCharts',
    color: '#409eff',
    path: '/analysis',
  },
  {
    title: 'LLM智能分析',
    desc: '基于大语言模型的智能财报分析，提供深度洞察和投资建议，帮助您全面地理解公司价值和投资机会。',
    icon: 'Cpu',
    color: '#8a7bd9',
    path: '/smart',
  },
]
</script>

<style scoped></style>