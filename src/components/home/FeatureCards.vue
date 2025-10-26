<template>
  <div class="row g-4 features justify-content-center">
    <div class="col-12 col-md-6 col-lg-4" v-for="card in cards" :key="card.title">
      <div class="card feature-card shadow-sm">
        <div class="card-body card-content">
          <div class="card-icon" :style="{ background: card.color }">
            <i :class="iconClass(card.icon)"></i>
          </div>
          <div>
            <h3 class="card-title h5">{{ card.title }}</h3>
            <p class="card-desc">{{ card.desc }}</p>
            <a href="#" class="link-primary" @click.prevent="$emit('navigate', card.path)">
              前往 <i class="bi bi-arrow-right"></i>
            </a>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
interface CardItem {
  title: string
  desc: string
  icon: string
  color: string
  path: string
}
defineProps<{ cards: CardItem[] }>()
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
.features {
  margin-top: 24px;
}
.feature-card {
  border-radius: 12px;
}
.card-content {
  display: grid;
  grid-template-columns: 64px 1fr;
  gap: 16px;
  align-items: start;
}
.card-icon {
  width: 48px;
  height: 48px;
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #fff;
  font-size: 1.25rem;
}
.card-title {
  margin: 0 0 8px;
  font-size: 18px;
}
.card-desc {
  margin: 0 0 12px;
  color: #6c757d;
  line-height: 1.6;
}
</style>