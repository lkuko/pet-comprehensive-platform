<template>
  <div class="auth-page">
    <el-card class="auth-card">
      <h2>用户登录</h2>
      <el-form label-width="60px" @submit.prevent="onSubmit">
        <el-form-item label="用户名">
          <el-input v-model="form.username" placeholder="请输入用户名" />
        </el-form-item>
        <el-form-item label="密码">
          <el-input v-model="form.password" type="password" placeholder="请输入密码" show-password />
        </el-form-item>
        <div class="actions">
          <el-button type="primary" :loading="loading" @click="onSubmit">登录</el-button>
          <el-button text @click="$router.push('/register')">没有账号？去注册</el-button>
        </div>
      </el-form>
    </el-card>
  </div>
</template>

<script setup>
import { reactive, ref } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { ElMessage } from 'element-plus'
import { useAuthStore } from '../stores/auth'

const router = useRouter()
const route = useRoute()
const auth = useAuthStore()
const loading = ref(false)
const form = reactive({ username: '', password: '' })

async function onSubmit() {
  if (!form.username || !form.password) {
    ElMessage.warning('请输入用户名和密码')
    return
  }
  loading.value = true
  try {
    await auth.login({ username: form.username, password: form.password })
    ElMessage.success('登录成功')
    router.push(route.query.redirect || '/')
  } catch {
    // 错误已由 request.js 统一提示
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.auth-page {
  display: flex;
  justify-content: center;
  padding: 60px 20px;
}
.auth-card {
  width: 400px;
}
.actions {
  display: flex;
  align-items: center;
  justify-content: space-between;
}
</style>
