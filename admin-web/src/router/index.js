import { createRouter, createWebHistory } from 'vue-router'

const routes = [
  { path: '/login', name: 'login', component: () => import('../views/Login.vue') },
  {
    path: '/',
    name: 'dashboard',
    component: () => import('../views/Dashboard.vue'),
    meta: { requiresAuth: true }
  },
  {
    path: '/pets',
    name: 'pets',
    component: () => import('../views/Pets.vue'),
    meta: { requiresAuth: true }
  },
  {
    path: '/applications',
    name: 'applications',
    component: () => import('../views/Applications.vue'),
    meta: { requiresAuth: true }
  },
  {
    path: '/medical',
    name: 'medicalResources',
    component: () => import('../views/MedicalResources.vue'),
    meta: { requiresAuth: true }
  },
  {
    path: '/medical/appointments',
    name: 'medicalAppointments',
    component: () => import('../views/MedicalAppointments.vue'),
    meta: { requiresAuth: true }
  },
  {
    path: '/care',
    name: 'careResources',
    component: () => import('../views/CareResources.vue'),
    meta: { requiresAuth: true }
  },
  {
    path: '/care/appointments',
    name: 'careAppointments',
    component: () => import('../views/CareAppointments.vue'),
    meta: { requiresAuth: true }
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

// 路由守卫：未登录跳转登录页
router.beforeEach((to) => {
  const token = localStorage.getItem('token')
  if (to.meta.requiresAuth && !token) {
    return { name: 'login', query: { redirect: to.fullPath } }
  }
  return true
})

export default router
