<template>
  <div class="home">
    <el-card class="box-card">
      <h1>智能宠物综合服务平台 · 用户端</h1>
      <template v-if="auth.isLoggedIn">
        <p>欢迎回来，{{ auth.user?.nickname || auth.user?.username }}</p>
        <el-button type="primary" @click="$router.push('/profile')">个人中心</el-button>
        <el-button @click="logout">退出登录</el-button>
      </template>
      <template v-else>
        <p>领养、医疗预约、洗护寄养、宠物用品一站式服务</p>
        <el-button type="primary" @click="$router.push('/login')">登录</el-button>
        <el-button @click="$router.push('/register')">注册</el-button>
      </template>
      <div class="divider"></div>
      <el-button text @click="ping">测试后端连通</el-button>
      <div v-if="pingResult" class="ping-result">{{ pingResult }}</div>
    </el-card>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import request from '../api/request'
import { useAuthStore } from '../stores/auth'

const router = useRouter()
const auth = useAuthStore()
const pingResult = ref('')

function logout() {
  auth.logout()
  router.push('/')
}

async function ping() {
  try {
    const res = await request.get('/ping')
    pingResult.value = JSON.stringify(res)
  } catch (e) {
    pingResult.value = '请求失败：' + e.message
  }
}
</script>

<style scoped>
.home {
  display: flex;
  justify-content: center;
  padding: 40px;
}
.box-card {
  width: 480px;
  text-align: center;
}
.divider {
  margin: 16px 0;
}
.ping-result {
  margin-top: 16px;
  font-size: 12px;
  word-break: break-all;
}
</style>
