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
          <h2 class="side-title">加入我们</h2>
          <p class="side-sub">注册一个账号，开启你与毛孩子的缘分。</p>
        </div>
      </div>

      <div class="auth-form">
        <h2 class="form-title">创建账号</h2>
        <p class="form-sub">几步即可开启领养与陪伴之旅</p>
        <el-form label-position="top" @submit.prevent="onSubmit">
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
          <el-button type="primary" size="large" class="submit" :loading="loading" @click="onSubmit">注册</el-button>
          <div class="foot">
            <span class="foot-hint">已有账号？</span>
            <el-button text type="primary" @click="$router.push('/login')">去登录</el-button>
          </div>
        </el-form>
      </div>
    </div>
  </div>
</template>

<script setup>
import { reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { useAuthStore } from '../stores/auth'
import sideImg from '../assets/auth-side.jpg'

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
  min-height: 560px;
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
  padding: 44px 44px;
  display: flex;
  flex-direction: column;
  justify-content: center;
}
.form-title {
  font-size: 28px;
  margin: 0 0 6px;
}
.form-sub {
  margin: 0 0 24px;
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
