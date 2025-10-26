<template>
  <TopNav />
  <main class="py-4">
    <div class="container">
      <router-view />
    </div>
  </main>
</template>

<script setup lang="ts">
import TopNav from './components/TopNav.vue'
</script>

<style scoped>
.container {
  max-width: 1200px;
  margin: 0 auto;
  padding: 0 16px 24px;
}
</style>
