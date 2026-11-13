<template>
  <header class="admin-header">
    <div class="brand" @click="$router.push('/')">
      <span class="logo">🐾</span>
      <span class="title">智能宠物平台 · 管理端</span>
    </div>
    <nav class="nav">
      <router-link to="/" class="nav-link">工作台</router-link>
      <router-link to="/pets" class="nav-link">宠物管理</router-link>
    </nav>
    <div class="right">
      <span class="nickname">{{ auth.user?.nickname || auth.user?.username }}</span>
      <el-button size="small" @click="logout">退出</el-button>
    </div>
  </header>
</template>

<script setup>
import { useRouter } from 'vue-router'
import { useAuthStore } from '../stores/auth'

const router = useRouter()
const auth = useAuthStore()

function logout() {
  auth.logout()
  router.push('/login')
}
</script>

<style scoped>
.admin-header {
  display: flex;
  align-items: center;
  gap: 24px;
  padding: 0 24px;
  height: 56px;
  background: #fff;
  border-bottom: 1px solid #e4e7ed;
}
.brand {
  display: flex;
  align-items: center;
  gap: 8px;
  cursor: pointer;
  font-weight: 700;
  color: #303133;
}
.logo {
  font-size: 22px;
}
.nav {
  display: flex;
  gap: 4px;
  flex: 1;
}
.nav-link {
  padding: 6px 12px;
  color: #606266;
  text-decoration: none;
  border-radius: 4px;
  font-size: 14px;
}
.nav-link.router-link-active {
  color: #409eff;
  background: #ecf5ff;
}
.right {
  display: flex;
  align-items: center;
  gap: 8px;
}
.nickname {
  color: #303133;
  font-size: 14px;
}
</style>
