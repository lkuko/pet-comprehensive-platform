<template>
  <div class="profile-page">
    <el-card class="profile-card">
      <h2>个人中心</h2>
      <el-form label-width="80px">
        <el-form-item label="用户名">
          <span>{{ auth.user?.username }}</span>
        </el-form-item>
        <el-form-item label="角色">
          <el-tag size="small">{{ auth.user?.role === 'ADMIN' ? '管理员' : '普通用户' }}</el-tag>
        </el-form-item>
        <el-form-item label="昵称">
          <el-input v-model="form.nickname" placeholder="请输入昵称" />
        </el-form-item>
        <el-form-item label="手机号">
          <el-input v-model="form.phone" placeholder="选填" />
        </el-form-item>
        <div class="actions">
          <el-button type="primary" :loading="saving" @click="save">保存</el-button>
          <el-button @click="logout">退出登录</el-button>
        </div>
      </el-form>
    </el-card>
  </div>
</template>

<script setup>
import { reactive, ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { useAuthStore } from '../stores/auth'

const router = useRouter()
const auth = useAuthStore()
const saving = ref(false)
const form = reactive({ nickname: '', phone: '' })

onMounted(async () => {
  try {
    await auth.fetchProfile()
    form.nickname = auth.user?.nickname || ''
    form.phone = auth.user?.phone || ''
  } catch {
    // 错误已由 request.js 统一提示
  }
})

async function save() {
  saving.value = true
  try {
    await auth.updateProfile({ nickname: form.nickname, phone: form.phone })
    ElMessage.success('保存成功')
  } catch {
    // 错误已由 request.js 统一提示
  } finally {
    saving.value = false
  }
}

function logout() {
  auth.logout()
  router.push('/')
}
</script>

<style scoped>
.profile-page {
  display: flex;
  justify-content: center;
  padding: 60px 20px;
}
.profile-card {
  width: 480px;
}
.actions {
  margin-top: 8px;
}
</style>
