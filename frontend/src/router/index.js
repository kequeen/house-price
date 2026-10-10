import { createRouter, createWebHistory } from 'vue-router'

export default createRouter({
  history: createWebHistory(),
  routes: [
    { path: '/', component: () => import('../views/Dashboard.vue') },
    { path: '/housing', component: () => import('../views/Housing.vue') },
    { path: '/sources', component: () => import('../views/Sources.vue') },
    { path: '/government', redirect: '/' },
    { path: '/crawler', redirect: '/sources' },
    { path: '/import', redirect: '/sources' },
    { path: '/transactions', redirect: '/housing' },
    { path: '/:pathMatch(.*)*', redirect: '/' }
  ]
})
