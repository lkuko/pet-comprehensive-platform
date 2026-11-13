<template>
  <div class="home">
    <el-card class="box-card">
      <h1>智能宠物综合服务平台 · 管理端</h1>
      <p>工程骨架已就绪（Day 1）</p>
      <el-button type="primary" @click="ping">测试后端连通</el-button>
      <div v-if="pingResult" class="ping-result">{{ pingResult }}</div>
    </el-card>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import request from '../api/request'

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
.home {
  display: flex;
  justify-content: center;
  padding: 40px;
}
.box-card {
  width: 480px;
}
.ping-result {
  margin-top: 16px;
  font-size: 12px;
  word-break: break-all;
}
</style>
