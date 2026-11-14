<template>
  <header class="app-header">
    <router-link to="/" class="brand">
      <span class="brand-mark" aria-hidden="true">
        <svg viewBox="0 0 40 40" xmlns="http://www.w3.org/2000/svg">
          <ellipse cx="20" cy="27" rx="9.5" ry="8" />
          <ellipse cx="8.5" cy="15" rx="4.2" ry="5.2" />
          <ellipse cx="16.5" cy="10.5" rx="4.2" ry="5.2" />
          <ellipse cx="23.5" cy="10.5" rx="4.2" ry="5.2" />
          <ellipse cx="31.5" cy="15" rx="4.2" ry="5.2" />
        </svg>
      </span>
      <span class="brand-text">
        <span class="brand-name">爱宠之家</span>
        <span class="brand-tag">领养 · 医疗 · 洗护 · 商城</span>
      </span>
    </router-link>

    <nav class="nav">
      <router-link to="/" class="nav-link">首页</router-link>
      <router-link to="/pets" class="nav-link">我的宠物</router-link>
      <router-link to="/applications" class="nav-link">领养申请</router-link>
      <router-link to="/medical" class="nav-link">医疗预约</router-link>
      <router-link to="/care" class="nav-link">洗护寄养</router-link>
      <router-link to="/shop" class="nav-link">商城</router-link>
      <router-link to="/orders" class="nav-link">我的订单</router-link>
    </nav>

    <div class="right">
      <template v-if="auth.isLoggedIn">
        <router-link to="/profile" class="user-chip">
          <span class="avatar">{{ (auth.user?.nickname || auth.user?.username || '客')[0] }}</span>
          <span class="nickname">{{ auth.user?.nickname || auth.user?.username }}</span>
        </router-link>
        <el-button size="small" text @click="logout">退出</el-button>
      </template>
      <template v-else>
        <el-button size="small" text @click="$router.push('/login')">登录</el-button>
        <el-button size="small" type="primary" round @click="$router.push('/register')">注册</el-button>
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
  position: sticky;
  top: 0;
  z-index: 100;
  display: flex;
  align-items: center;
  gap: 20px;
  padding: 0 28px;
  height: 64px;
  background: rgba(255, 255, 255, 0.92);
  backdrop-filter: blur(10px);
  border-bottom: 1px solid var(--brand-line);
}
.brand {
  display: flex;
  align-items: center;
  gap: 11px;
  text-decoration: none;
  flex-shrink: 0;
}
.brand-mark {
  width: 38px;
  height: 38px;
  display: grid;
  place-items: center;
  border-radius: 12px;
  background: linear-gradient(145deg, #ff385c, var(--brand-forest-deep));
  box-shadow: 0 4px 12px rgba(255, 56, 92, 0.28);
}
.brand-mark svg {
  width: 26px;
  height: 26px;
  fill: #fff;
}
.brand-text {
  display: flex;
  flex-direction: column;
  line-height: 1.1;
}
.brand-name {
  font-family: var(--font-display);
  font-size: 20px;
  font-weight: 700;
  color: var(--brand-ink);
  letter-spacing: 1px;
}
.brand-tag {
  font-size: 10px;
  color: var(--el-text-color-secondary);
  letter-spacing: 0.5px;
}
.nav {
  display: flex;
  gap: 2px;
  flex: 1;
  justify-content: center;
}
.nav-link {
  position: relative;
  padding: 8px 14px;
  color: var(--el-text-color-regular);
  text-decoration: none;
  border-radius: 10px;
  font-size: 14px;
  transition: color 0.15s, background 0.15s;
}
.nav-link:hover {
  color: var(--brand-ink);
  background: var(--brand-sage);
}
.nav-link.router-link-active {
  color: var(--brand-ink);
  background: transparent;
  font-weight: 700;
}
.nav-link.router-link-active::after {
  content: '';
  position: absolute;
  left: 14px;
  right: 14px;
  bottom: 2px;
  height: 2px;
  border-radius: 2px;
  background: var(--brand-forest);
}
.right {
  display: flex;
  align-items: center;
  gap: 10px;
  flex-shrink: 0;
}
.user-chip {
  display: flex;
  align-items: center;
  gap: 8px;
  text-decoration: none;
  padding: 4px 10px 4px 4px;
  border-radius: 999px;
  border: 1px solid var(--brand-line);
  transition: background 0.15s;
}
.user-chip:hover {
  background: var(--brand-sage);
}
.avatar {
  width: 28px;
  height: 28px;
  border-radius: 50%;
  background: var(--brand-apricot-soft);
  color: var(--brand-apricot);
  display: grid;
  place-items: center;
  font-weight: 600;
  font-size: 14px;
}
.nickname {
  color: var(--brand-ink);
  font-size: 14px;
  max-width: 110px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

@media (max-width: 960px) {
  .brand-tag,
  .nav {
    display: none;
  }
}
</style>
