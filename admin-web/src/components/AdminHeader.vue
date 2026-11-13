<template>
  <header class="admin-header">
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
        <span class="brand-tag">管理台</span>
      </span>
    </router-link>

    <nav class="nav">
      <router-link to="/" class="nav-link">工作台</router-link>
      <router-link to="/pets" class="nav-link">宠物管理</router-link>
      <router-link to="/applications" class="nav-link">申请审核</router-link>
      <router-link to="/medical" class="nav-link">医疗管理</router-link>
      <router-link to="/medical/appointments" class="nav-link">医疗预约</router-link>
      <router-link to="/care" class="nav-link">洗护管理</router-link>
      <router-link to="/care/appointments" class="nav-link">洗护预约</router-link>
      <router-link to="/mall" class="nav-link">商城管理</router-link>
      <router-link to="/mall/orders" class="nav-link">商城订单</router-link>
    </nav>

    <div class="right">
      <span class="user-chip">
        <span class="avatar">{{ (auth.user?.nickname || auth.user?.username || '管')[0] }}</span>
        <span class="nickname">{{ auth.user?.nickname || auth.user?.username }}</span>
      </span>
      <el-button size="small" text @click="logout">退出</el-button>
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
  position: sticky;
  top: 0;
  z-index: 100;
  display: flex;
  align-items: center;
  gap: 20px;
  padding: 0 24px;
  height: 60px;
  background: #1e352b;
  border-bottom: 1px solid rgba(255, 255, 255, 0.08);
}
.brand {
  display: flex;
  align-items: center;
  gap: 11px;
  text-decoration: none;
  flex-shrink: 0;
}
.brand-mark {
  width: 36px;
  height: 36px;
  display: grid;
  place-items: center;
  border-radius: 11px;
  background: linear-gradient(145deg, #e88a45, var(--brand-apricot));
  box-shadow: 0 4px 12px rgba(224, 123, 52, 0.3);
}
.brand-mark svg {
  width: 24px;
  height: 24px;
  fill: #fff;
}
.brand-text {
  display: flex;
  flex-direction: column;
  line-height: 1.1;
}
.brand-name {
  font-family: var(--font-display);
  font-size: 19px;
  font-weight: 700;
  color: #fff;
  letter-spacing: 1px;
}
.brand-tag {
  font-size: 10px;
  color: rgba(255, 255, 255, 0.55);
  letter-spacing: 2px;
}
.nav {
  display: flex;
  gap: 2px;
  flex: 1;
  justify-content: center;
}
.nav-link {
  padding: 6px 12px;
  color: rgba(255, 255, 255, 0.72);
  text-decoration: none;
  border-radius: 9px;
  font-size: 13px;
  transition: color 0.15s, background 0.15s;
}
.nav-link:hover {
  color: #fff;
  background: rgba(255, 255, 255, 0.1);
}
.nav-link.router-link-active {
  color: #fff;
  background: var(--brand-forest);
  font-weight: 600;
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
  padding: 4px 12px 4px 4px;
  border-radius: 999px;
  background: rgba(255, 255, 255, 0.08);
}
.avatar {
  width: 26px;
  height: 26px;
  border-radius: 50%;
  background: var(--brand-apricot-soft);
  color: var(--brand-apricot);
  display: grid;
  place-items: center;
  font-weight: 600;
  font-size: 13px;
}
.nickname {
  color: #fff;
  font-size: 13px;
  max-width: 110px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.right :deep(.el-button) {
  color: rgba(255, 255, 255, 0.8);
}
.right :deep(.el-button:hover) {
  color: #fff;
}

@media (max-width: 1080px) {
  .nav-link {
    padding: 6px 8px;
    font-size: 12px;
  }
  .brand-tag {
    display: none;
  }
}
</style>
