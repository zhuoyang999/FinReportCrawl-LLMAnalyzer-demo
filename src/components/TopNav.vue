<template>
  <div class="top-nav">
    <div class="logo-container">
      <router-link to="/" class="logo">
        <el-icon><TrendCharts /></el-icon>
        <span>智能财报分析平台</span>
      </router-link>
    </div>

    <div class="menu-container">
      <el-menu
        :default-active="active"
        mode="horizontal"
        router
        class="nav-menu"
        background-color="transparent"
        text-color="#fff"
        active-text-color="#ffd04b"
      >
        <el-menu-item v-for="item in navItems" :key="item.path" :index="item.path">
          <el-icon v-if="item.icon"><component :is="item.icon" /></el-icon>
          <span>{{ item.title }}</span>
        </el-menu-item>
      </el-menu>
    </div>

    <div class="actions">
      <el-tooltip :content="isDark ? '切换为浅色' : '切换为深色'" placement="bottom">
        <el-button circle @click="toggleTheme">
          <el-icon v-if="isDark"><Moon /></el-icon>
          <el-icon v-else><Sunny /></el-icon>
        </el-button>
      </el-tooltip>
      
      <el-tooltip content="通知" placement="bottom">
        <el-button circle>
          <el-icon><Bell /></el-icon>
        </el-button>
      </el-tooltip>
      
      <el-avatar :size="32" icon="UserFilled" />
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'

const route = useRoute()
const active = computed(() => route.path)
const router = useRouter()

const iconMap: Record<string, string> = {
  House: 'House',
  Upload: 'Upload',
  TrendCharts: 'TrendCharts',
  Histogram: 'Histogram',
  Cpu: 'CPU',
}

const navItems = computed(() => {
  return router
    .getRoutes()
    .filter(r => r.meta && (r.meta as any).nav)
    .map(r => ({
      path: r.path,
      title: (r.meta as any).title as string,
      order: ((r.meta as any).order ?? 999) as number,
      icon: iconMap[(r.meta as any).icon as string] ?? undefined,
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
.top-nav {
  display: flex;
  align-items: center;
  justify-content: space-between;
  height: 60px;
  padding: 0 20px;
  background-color: #409EFF;
  color: white;
}

.logo-container {
  display: flex;
  align-items: center;
}

.logo {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 18px;
  font-weight: bold;
  color: white;
  text-decoration: none;
}

.menu-container {
  flex: 1;
  margin-left: 40px;
}

.nav-menu {
  border-bottom: none;
}

.actions {
  display: flex;
  align-items: center;
  gap: 12px;
}

:deep(.el-button) {
  color: white;
  border-color: rgba(255, 255, 255, 0.5);
}

:deep(.el-menu--horizontal > .el-menu-item) {
  height: 60px;
  line-height: 60px;
}

:deep(.el-menu--horizontal > .el-menu-item.is-active) {
  border-bottom: 2px solid #ffd04b;
  font-weight: bold;
}
</style>