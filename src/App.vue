<template>
  <el-config-provider>
    <el-container class="app-container">
      <el-header height="60px" class="app-header">
        <TopNav />
      </el-header>
      <el-main class="app-main">
        <router-view />
      </el-main>
    </el-container>
  </el-config-provider>
</template>

<script setup lang="ts">
import TopNav from './components/TopNav.vue'
</script>

<style>
html, body {
  margin: 0;
  padding: 0;
  height: 100%;
  font-family: 'Helvetica Neue', Helvetica, 'PingFang SC', 'Hiragino Sans GB', 'Microsoft YaHei', Arial, sans-serif;
}

#app {
  height: 100vh;
}

.app-container {
  height: 100%;
  display: flex;
  flex-direction: column;
}

.app-header {
  padding: 0;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  z-index: 999;
}

.app-main {
  padding: 20px;
  background-color: #f5f7fa;
}
</style>
