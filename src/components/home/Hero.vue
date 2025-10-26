<template>
  <section class="hero">
    <div class="hero-content">
      <h1>智能财报分析平台</h1>
      <p>专注于从各种公开渠道获取企业财务报告原始文件，提供智能分析服务</p>
      <div class="hero-actions">
        <button
          v-for="action in actions"
          :key="action.label"
          class="btn btn-lg hero-btn"
          :class="action.plain ? 'btn-outline-light' : 'btn-light text-primary'"
          @click="$emit('navigate', action.path)"
        >
          <i :class="iconClass(action.icon)" class="me-2"></i>{{ action.label }}
        </button>
      </div>
    </div>
  </section>
</template>

<script setup lang="ts">
interface Action {
  label: string
  icon: string
  path: string
  plain?: boolean
}
const props = defineProps<{ actions: Action[] }>()
defineEmits<{ (e: 'navigate', path: string): void }>()

function iconClass(icon: string) {
  switch (icon) {
    case 'Upload':
      return 'bi bi-cloud-arrow-up'
    case 'TrendCharts':
      return 'bi bi-graph-up'
    case 'Cpu':
      return 'bi bi-cpu'
    default:
      return 'bi bi-circle'
  }
}
</script>

<style scoped>
.hero {
  margin-top: 16px;
  background: linear-gradient(135deg, var(--brand-primary) 0%, var(--brand-primary-dark) 100%);
  border-radius: 12px;
  padding: 40px 32px;
  color: #fff;
  box-shadow: 0 2px 8px rgba(0,0,0,0.08);
}
.hero-content {
  max-width: 1000px;
  margin: 0 auto;
}
.hero h1 {
  font-size: 32px;
  margin: 0 0 12px;
  font-weight: 700;
}
.hero p {
  font-size: 16px;
  opacity: 0.9;
  margin-bottom: 20px;
}
.hero-actions {
  display: flex;
  flex-wrap: wrap;
  gap: 12px;
}
.hero-btn {
  border-radius: 8px;
}
</style>