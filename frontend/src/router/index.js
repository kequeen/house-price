import { createRouter, createWebHistory } from 'vue-router'

const routes = [
  {
    path: '/',
    name: 'Dashboard',
    component: () => import('../views/Dashboard.vue')
  },
  {
    path: '/transactions',
    name: 'Transactions',
    component: () => import('../views/Transactions.vue')
  },
  {
    path: '/import',
    name: 'DataImport',
    component: () => import('../views/DataImport.vue')
  },
  {
    path: '/crawler',
    name: 'Crawler',
    component: () => import('../views/Crawler.vue')
  },
  {
    path: '/government',
    name: 'GovernmentData',
    component: () => import('../views/GovernmentData.vue')
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

export default router
