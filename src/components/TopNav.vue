<template>
  <nav class="navbar navbar-expand-lg navbar-dark bg-primary">
    <div class="container">
      <router-link to="/" class="navbar-brand d-flex align-items-center gap-2">
        <i class="bi bi-graph-up"></i>
        <span>智能财报分析平台</span>
      </router-link>

      <button
        class="navbar-toggler"
        type="button"
        data-bs-toggle="collapse"
        data-bs-target="#navbarNav"
        aria-controls="navbarNav"
        aria-expanded="false"
        aria-label="Toggle navigation"
      >
        <span class="navbar-toggler-icon"></span>
      </button>

      <div class="collapse navbar-collapse" id="navbarNav">
        <ul class="navbar-nav me-auto mb-2 mb-lg-0">
          <li class="nav-item" v-for="item in navItems" :key="item.path">
            <router-link :to="item.path" class="nav-link" :class="{ active: active === item.path }">
              <i v-if="item.iconClass" :class="item.iconClass" class="me-1"></i>
              {{ item.title }}
            </router-link>
          </li>
        </ul>

        <div class="d-flex align-items-center gap-2">
          <button class="btn btn-outline-light rounded-circle" @click="toggleTheme" :title="isDark ? '切换为浅色' : '切换为深色'">
            <i :class="isDark ? 'bi bi-moon' : 'bi bi-sun'"></i>
          </button>
          <button class="btn btn-outline-light rounded-circle" title="通知">
            <i class="bi bi-bell"></i>
          </button>
          <div class="avatar bg-light rounded-circle d-flex align-items-center justify-content-center">
            <i class="bi bi-person"></i>
          </div>
        </div>
      </div>
    </div>
  </nav>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'

const route = useRoute()
const active = computed(() => route.path)
const router = useRouter()

const iconMap: Record<string, string> = {
  House: 'bi bi-house',
  Upload: 'bi bi-cloud-arrow-up',
  TrendCharts: 'bi bi-graph-up',
  Histogram: 'bi bi-bar-chart',
  Cpu: 'bi bi-cpu',
}

const navItems = computed(() => {
  return router
    .getRoutes()
    .filter(r => r.meta && (r.meta as any).nav)
    .map(r => ({
      path: r.path,
      title: (r.meta as any).title as string,
      order: ((r.meta as any).order ?? 999) as number,
      iconClass: iconMap[(r.meta as any).icon as string] ?? undefined,
    }))
    .sort((a, b) => a.order - b.order)
})

const isDark = ref(false)
onMounted(() => {
  const saved = localStorage.getItem('theme')
  isDark.value = saved === 'dark'
  document.documentElement.classList.toggle('dark', isDark.value)
})

function toggleTheme() {
  isDark.value = !isDark.value
  document.documentElement.classList.toggle('dark', isDark.value)
  localStorage.setItem('theme', isDark.value ? 'dark' : 'light')
}
</script>

<style scoped>
.avatar {
  width: 32px;
  height: 32px;
}
</style>