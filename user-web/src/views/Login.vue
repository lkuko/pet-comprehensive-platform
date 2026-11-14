<template>
  <div class="auth-page">
    <div class="auth-card">
      <div class="auth-side">
        <img :src="sideImg" alt="猫狗依偎" class="side-img" />
        <div class="side-overlay">
          <div class="side-brand">
            <span class="side-mark">
              <svg viewBox="0 0 40 40" xmlns="http://www.w3.org/2000/svg"><ellipse cx="20" cy="27" rx="9.5" ry="8" /><ellipse cx="8.5" cy="15" rx="4.2" ry="5.2" /><ellipse cx="16.5" cy="10.5" rx="4.2" ry="5.2" /><ellipse cx="23.5" cy="10.5" rx="4.2" ry="5.2" /><ellipse cx="31.5" cy="15" rx="4.2" ry="5.2" /></svg>
            </span>
            <span class="side-name">爱宠之家</span>
          </div>
          <h2 class="side-title">遇见，就是家</h2>
          <p class="side-sub">领养、医疗、洗护、商城，一站式照顾毛孩子。</p>
        </div>
      </div>

      <div class="auth-form">
        <h2 class="form-title">欢迎回来</h2>
        <p class="form-sub">登录后继续你的领养之旅</p>
        <el-form label-position="top" @submit.prevent="onSubmit">
          <el-form-item label="用户名">
            <el-input v-model="form.username" placeholder="请输入用户名" size="large" />
          </el-form-item>
          <el-form-item label="密码">
            <el-input v-model="form.password" type="password" placeholder="请输入密码" show-password size="large" @keyup.enter="onSubmit" />
          </el-form-item>
          <el-button type="primary" size="large" class="submit" :loading="loading" @click="onSubmit">登录</el-button>
          <div class="foot">
            <span class="foot-hint">还没有账号？</span>
            <el-button text type="primary" @click="$router.push('/register')">去注册</el-button>
          </div>
        </el-form>
      </div>
    </div>
  </div>
</template>

<script setup>
import { reactive, ref } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { ElMessage } from 'element-plus'
import { useAuthStore } from '../stores/auth'
import sideImg from '../assets/auth-side.jpg'

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
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 32px 20px;
  background:
    radial-gradient(1200px 600px at 85% -10%, var(--brand-sage) 0%, transparent 55%),
    var(--brand-paper);
}
.auth-card {
  width: 880px;
  max-width: 100%;
  min-height: 520px;
  display: grid;
  grid-template-columns: 1fr 1fr;
  background: #fff;
  border-radius: 22px;
  overflow: hidden;
  border: 1px solid var(--brand-line);
  box-shadow: 0 24px 60px rgba(35, 48, 42, 0.16);
}
.auth-side {
  position: relative;
}
.side-img {
  position: absolute;
  inset: 0;
  width: 100%;
  height: 100%;
  object-fit: cover;
}
.side-overlay {
  position: relative;
  height: 100%;
  padding: 36px;
  display: flex;
  flex-direction: column;
  justify-content: flex-end;
  background: linear-gradient(180deg, rgba(34, 34, 34, 0.04) 0%, rgba(34, 34, 34, 0.72) 100%);
  color: #fff;
}
.side-brand {
  position: absolute;
  top: 30px;
  left: 36px;
  display: flex;
  align-items: center;
  gap: 10px;
}
.side-mark {
  width: 32px;
  height: 32px;
  display: grid;
  place-items: center;
  border-radius: 10px;
  background: rgba(255, 255, 255, 0.9);
}
.side-mark svg {
  width: 22px;
  height: 22px;
  fill: var(--brand-forest);
}
.side-name {
  font-family: var(--font-display);
  font-size: 18px;
  font-weight: 700;
  color: #fff;
  letter-spacing: 1px;
}
.side-title {
  font-family: var(--font-display);
  font-size: 30px;
  margin: 0 0 10px;
  color: #fff;
}
.side-sub {
  margin: 0;
  font-size: 14px;
  line-height: 1.7;
  color: rgba(255, 255, 255, 0.85);
  max-width: 300px;
}
.auth-form {
  padding: 48px 44px;
  display: flex;
  flex-direction: column;
  justify-content: center;
}
.form-title {
  font-size: 28px;
  margin: 0 0 6px;
}
.form-sub {
  margin: 0 0 28px;
  color: var(--el-text-color-secondary);
  font-size: 14px;
}
.submit {
  width: 100%;
  margin-top: 6px;
}
.foot {
  display: flex;
  align-items: center;
  justify-content: center;
  margin-top: 16px;
}
.foot-hint {
  color: var(--el-text-color-secondary);
  font-size: 14px;
}

@media (max-width: 720px) {
  .auth-card {
    grid-template-columns: 1fr;
    min-height: auto;
  }
  .auth-side {
    display: none;
  }
  .auth-form {
    padding: 36px 28px;
  }
}
</style>
