import { createRouter, createWebHistory } from 'vue-router'
import type { RouteRecordRaw } from 'vue-router'

const routes: Array<RouteRecordRaw> = [
  { path: '/', name: 'Home', component: () => import('../views/Home.vue'), meta: { title: '首页', nav: true, order: 1, icon: 'House' } },
  { path: '/crawl', name: 'Crawl', component: () => import('../views/crawl/Index.vue'), meta: { title: '爬取财报', nav: true, order: 2, icon: 'Upload' } },
  { path: '/analysis', name: 'Analysis', component: () => import('../views/analysis/Index.vue'), meta: { title: '财报分析', nav: true, order: 3, icon: 'TrendCharts' } },
  { path: '/compare', name: 'Compare', component: () => import('../views/compare/Index.vue'), meta: { title: '对比分析', nav: true, order: 4, icon: 'Histogram' } },
  { path: '/smart', name: 'Smart', component: () => import('../views/smart/Index.vue'), meta: { title: '智能分析', nav: true, order: 5, icon: 'Cpu' } },
  {
    path: '/database',
    name: 'Database',
    component: () => import('../views/Database.vue'),
    meta: { title: '数据库', nav: true, order: 6, icon: 'Coin' }
  }
]

export default createRouter({
  history: createWebHistory(),
  routes,
})