<template>
  <header class="app-header">
    <div class="brand" @click="$router.push('/')">
      <span class="logo">🐾</span>
      <span class="title">智能宠物综合服务平台</span>
    </div>
    <nav class="nav">
      <router-link to="/" class="nav-link">首页</router-link>
      <router-link to="/pets" class="nav-link">我的宠物</router-link>
      <router-link to="/applications" class="nav-link">领养申请</router-link>
      <router-link to="/medical" class="nav-link">医疗预约</router-link>
      <router-link to="/care" class="nav-link">洗护寄养</router-link>
      <router-link to="/shop" class="nav-link">商城</router-link>
      <router-link to="/orders" class="nav-link">我的订单</router-link>
      <router-link to="/profile" class="nav-link">个人中心</router-link>
    </nav>
    <div class="right">
      <template v-if="auth.isLoggedIn">
        <span class="nickname">{{ auth.user?.nickname || auth.user?.username }}</span>
        <el-button size="small" @click="logout">退出</el-button>
      </template>
      <template v-else>
        <el-button size="small" @click="$router.push('/login')">登录</el-button>
        <el-button size="small" type="primary" @click="$router.push('/register')">注册</el-button>
      </template>
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
  router.push('/')
}
</script>

<style scoped>
.app-header {
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
