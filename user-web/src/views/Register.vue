<template>
  <div class="auth-page">
    <el-card class="auth-card">
      <h2>用户注册</h2>
      <el-form label-width="60px" @submit.prevent="onSubmit">
        <el-form-item label="用户名">
          <el-input v-model="form.username" placeholder="3-50 位字母/数字/下划线" />
        </el-form-item>
        <el-form-item label="密码">
          <el-input v-model="form.password" type="password" placeholder="至少 6 位" show-password />
        </el-form-item>
        <el-form-item label="昵称">
          <el-input v-model="form.nickname" placeholder="选填" />
        </el-form-item>
        <el-form-item label="手机号">
          <el-input v-model="form.phone" placeholder="选填" />
        </el-form-item>
        <div class="actions">
          <el-button type="primary" :loading="loading" @click="onSubmit">注册</el-button>
          <el-button text @click="$router.push('/login')">已有账号？去登录</el-button>
        </div>
      </el-form>
    </el-card>
  </div>
</template>

<script setup>
import { reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { useAuthStore } from '../stores/auth'

const router = useRouter()
const auth = useAuthStore()
const loading = ref(false)
const form = reactive({ username: '', password: '', nickname: '', phone: '' })

async function onSubmit() {
  if (!form.username || !form.password) {
    ElMessage.warning('请输入用户名和密码')
    return
  }
  loading.value = true
  try {
    await auth.register({
      username: form.username,
      password: form.password,
      nickname: form.nickname || null,
      phone: form.phone || null
    })
    ElMessage.success('注册成功，已自动登录')
    router.push('/')
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
