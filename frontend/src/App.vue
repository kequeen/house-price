<template>
  <div class="app-container">
    <el-container>
      <el-header>
        <div class="header-content">
          <h1>房价分析系统</h1>
          <el-menu mode="horizontal" :default-active="activeIndex" router>
            <el-menu-item index="/">数据概览</el-menu-item>
            <el-menu-item index="/transactions">成交记录</el-menu-item>
            <el-menu-item index="/government">政府数据</el-menu-item>
            <el-menu-item index="/import">数据导入</el-menu-item>
            <el-menu-item index="/crawler">数据采集</el-menu-item>
          </el-menu>
        </div>
      </el-header>
      <el-main>
        <router-view />
      </el-main>
    </el-container>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { useRoute } from 'vue-router'

const route = useRoute()
const activeIndex = computed(() => route.path)
</script>

<style>
* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

body {
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, sans-serif;
  background-color: #f5f7fa;
}

.app-container {
  min-height: 100vh;
}

.el-header {
  background-color: #fff;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  padding: 0 20px;
}

.header-content {
  display: flex;
  align-items: center;
  height: 60px;
  max-width: 1400px;
  margin: 0 auto;
}

.header-content h1 {
  font-size: 20px;
  color: #303133;
  margin-right: 40px;
}

.el-main {
  max-width: 1400px;
  margin: 20px auto;
  padding: 20px;
}
</style>
