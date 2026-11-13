<template>
  <div class="page">
    <AdminHeader />
    <main class="dashboard">
      <el-card class="welcome-card">
        <h1>智能宠物综合服务平台 · 管理端</h1>
        <p>欢迎，{{ auth.user?.nickname || auth.user?.username }}</p>
        <p class="hint">领养宠物维护与申请审核已上线，其余业务模块（医疗、洗护寄养、商城）将在后续阶段逐步接入。</p>
        <div class="actions">
          <el-button type="primary" @click="$router.push('/pets')">进入宠物管理</el-button>
          <el-button type="primary" plain @click="$router.push('/applications')">进入申请审核</el-button>
          <el-button text @click="ping">测试后端连通</el-button>
        </div>
        <div v-if="pingResult" class="ping-result">{{ pingResult }}</div>
      </el-card>
    </main>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import AdminHeader from '../components/AdminHeader.vue'
import request from '../api/request'
import { useAuthStore } from '../stores/auth'

const auth = useAuthStore()
const pingResult = ref('')

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
.page {
  min-height: 100vh;
  background: #f5f7fa;
}
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
