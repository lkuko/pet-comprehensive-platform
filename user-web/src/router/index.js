import { createRouter, createWebHistory } from 'vue-router'

const routes = [
  { path: '/', name: 'home', component: () => import('../views/Home.vue') },
  { path: '/adoption/:id', name: 'adoptionDetail', component: () => import('../views/AdoptionDetail.vue') },
  { path: '/login', name: 'login', component: () => import('../views/Login.vue') },
  { path: '/register', name: 'register', component: () => import('../views/Register.vue') },
  {
    path: '/profile',
    name: 'profile',
    component: () => import('../views/Profile.vue'),
    meta: { requiresAuth: true }
  },
  {
    path: '/pets',
    name: 'pets',
    component: () => import('../views/MyPets.vue'),
    meta: { requiresAuth: true }
  },
  {
    path: '/applications',
    name: 'applications',
    component: () => import('../views/MyApplications.vue'),
    meta: { requiresAuth: true }
  },
  {
    path: '/medical',
    name: 'medical',
    component: () => import('../views/Medical.vue'),
    meta: { requiresAuth: true }
  },
  {
    path: '/medical/mine',
    name: 'myMedical',
    component: () => import('../views/MyMedical.vue'),
    meta: { requiresAuth: true }
  },
  {
    path: '/care',
    name: 'care',
    component: () => import('../views/Care.vue'),
    meta: { requiresAuth: true }
  },
  {
    path: '/care/mine',
    name: 'myCare',
    component: () => import('../views/MyCare.vue'),
    meta: { requiresAuth: true }
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

// 路由守卫：需要登录的页面重定向到登录页
router.beforeEach((to) => {
  const token = localStorage.getItem('token')
  if (to.meta.requiresAuth && !token) {
    return { name: 'login', query: { redirect: to.fullPath } }
  }
  return true
})

export default router
