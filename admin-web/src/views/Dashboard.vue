<template>
  <div class="dashboard">
    <el-card class="welcome-card">
      <h1>智能宠物综合服务平台 · 管理端</h1>
      <p>欢迎，{{ auth.user?.nickname || auth.user?.username }}</p>
      <p class="hint">工作台统计与各业务管理模块将在后续阶段逐步接入。</p>
      <div class="actions">
        <el-button text @click="ping">测试后端连通</el-button>
        <el-button type="danger" @click="logout">退出登录</el-button>
      </div>
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
  router.push('/login')
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
.dashboard {
  display: flex;
  justify-content: center;
  padding: 40px;
}
.welcome-card {
  width: 560px;
  text-align: center;
}
.hint {
  color: #909399;
  font-size: 13px;
}
.actions {
  margin-top: 16px;
}
.ping-result {
  margin-top: 16px;
  font-size: 12px;
  word-break: break-all;
}
</style>
