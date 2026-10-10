<template>
  <header class="site-header">
    <div class="header-inner">
      <RouterLink to="/" class="brand" aria-label="城市住宅观察首页">
        <svg viewBox="0 0 32 32" aria-hidden="true"><path d="M3 26V12l8-6 8 6v14M11 26V15M19 26V6l10 7v13"/><path d="m4 22 7-3 8 2 10-6" class="brand-line"/></svg>
        <span>城市住宅观察<small>官方数据 · 按月追踪</small></span>
      </RouterLink>
      <nav aria-label="主导航">
        <RouterLink to="/" :class="{ active: route.path === '/' }">价格趋势</RouterLink>
        <RouterLink to="/housing" :class="{ active: route.path === '/housing' }">住建成交</RouterLink>
        <RouterLink to="/sources" :class="{ active: route.path === '/sources' }">数据来源</RouterLink>
      </nav>
      <a class="header-source" href="https://www.stats.gov.cn/sj/zxfb/" target="_blank" rel="noopener noreferrer">国家统计局 ↗</a>
    </div>
  </header>
  <main class="page"><RouterView /></main>
  <footer class="site-footer"><span>城市住宅观察</span><span>指数反映价格变化，成交统计保留当地口径。每个数值均可追溯至官方公告。</span></footer>
</template>

<script setup>
import { useRoute } from 'vue-router'
const route = useRoute()
</script>

<style>
@import './style.css';
</style>
