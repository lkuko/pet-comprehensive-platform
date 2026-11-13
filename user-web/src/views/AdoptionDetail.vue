<template>
  <div class="page">
    <AppHeader />
    <main class="container" v-loading="loading">
      <el-page-header content="宠物详情" @back="$router.back()" class="back" />

      <template v-if="pet">
        <div class="detail-card">
          <div class="gallery">
            <el-image v-if="pet.images.length" :src="activeImage" fit="cover" class="main-img" />
            <div v-else class="main-img placeholder">🐾</div>
            <div v-if="pet.images.length > 1" class="thumbs">
              <img
                v-for="(img, i) in pet.images"
                :key="i"
                :src="img"
                :class="{ active: activeImage === img }"
                @click="activeImage = img"
              />
            </div>
          </div>

          <div class="side">
            <div class="title-row">
              <h2>{{ pet.name }}</h2>
              <el-tag>{{ ADOPT_STATUS[pet.status] || pet.status }}</el-tag>
            </div>
            <el-descriptions :column="1" border>
              <el-descriptions-item label="分类">{{ pet.category_name }}</el-descriptions-item>
              <el-descriptions-item label="品种">{{ pet.breed || '—' }}</el-descriptions-item>
              <el-descriptions-item label="性别">{{ GENDER[pet.gender] }}</el-descriptions-item>
              <el-descriptions-item label="年龄">{{ pet.age_months != null ? pet.age_months + ' 个月' : '—' }}</el-descriptions-item>
              <el-descriptions-item label="体重">{{ pet.weight != null ? pet.weight + ' kg' : '—' }}</el-descriptions-item>
              <el-descriptions-item label="健康状态">{{ pet.health_status || '—' }}</el-descriptions-item>
              <el-descriptions-item label="疫苗">{{ pet.vaccinated ? '已完成' : '未完成' }}</el-descriptions-item>
              <el-descriptions-item label="绝育">{{ pet.neutered ? '已绝育' : '未绝育' }}</el-descriptions-item>
              <el-descriptions-item label="地区">{{ pet.region || '—' }}</el-descriptions-item>
            </el-descriptions>

            <div class="apply-bar">
              <el-button
                v-if="pet.status === 'AVAILABLE'"
                type="primary"
                size="large"
                @click="openApply"
              >申请领养</el-button>
              <el-tag v-else type="info" size="large">该宠物当前不可申请</el-tag>
            </div>
          </div>
        </div>

        <div class="section">
          <h3>性格特点</h3>
          <p>{{ pet.personality || '暂无描述' }}</p>
        </div>
        <div class="section">
          <h3>领养要求</h3>
          <p>{{ pet.adoption_requirements || '暂无要求' }}</p>
        </div>
        <div class="section">
          <h3>详细介绍</h3>
          <p>{{ pet.description || '暂无介绍' }}</p>
        </div>
      </template>
    </main>

    <el-dialog v-model="applyVisible" title="申请领养" width="520px" @closed="resetForm">
      <el-form ref="formRef" :model="form" :rules="rules" label-width="90px">
        <el-form-item label="联系人" prop="contact_name">
          <el-input v-model="form.contact_name" placeholder="请输入联系人姓名" />
        </el-form-item>
        <el-form-item label="联系电话" prop="contact_phone">
          <el-input v-model="form.contact_phone" placeholder="请输入联系电话" />
        </el-form-item>
        <el-form-item label="居住环境" prop="living_environment">
          <el-input v-model="form.living_environment" placeholder="如：两居室、有阳台、可封窗等" />
        </el-form-item>
        <el-form-item label="养宠经验" prop="pet_experience">
          <el-input v-model="form.pet_experience" type="textarea" :rows="2" placeholder="可填写过往养宠经历（选填）" />
        </el-form-item>
        <el-form-item label="申请理由" prop="application_reason">
          <el-input v-model="form.application_reason" type="textarea" :rows="3" placeholder="请说明想领养它的原因" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="applyVisible = false">取消</el-button>
        <el-button type="primary" :loading="submitting" @click="submitApply">提交申请</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { computed, onMounted, reactive, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import AppHeader from '../components/AppHeader.vue'
import { getPet } from '../api/adoption'
import { createApplication } from '../api/applications'
import { GENDER, ADOPT_STATUS } from '../utils/dict'
import { useAuthStore } from '../stores/auth'

const route = useRoute()
const router = useRouter()
const auth = useAuthStore()
const pet = ref(null)
const loading = ref(false)
const applyVisible = ref(false)
const submitting = ref(false)
const formRef = ref(null)

const form = reactive({
  contact_name: '',
  contact_phone: '',
  living_environment: '',
  pet_experience: '',
  application_reason: ''
})

const rules = {
  contact_name: [{ required: true, message: '请输入联系人姓名', trigger: 'blur' }],
  contact_phone: [{ required: true, message: '请输入联系电话', trigger: 'blur' }],
  living_environment: [{ required: true, message: '请填写居住环境', trigger: 'blur' }],
  application_reason: [{ required: true, message: '请填写申请理由', trigger: 'blur' }]
}

const activeImage = computed(() => (pet.value && pet.value.images.length ? pet.value.images[0] : ''))

async function load() {
  loading.value = true
  try {
    pet.value = (await getPet(route.params.id)).data
  } finally {
    loading.value = false
  }
}

function openApply() {
  if (!auth.isLoggedIn) {
    ElMessage.warning('请先登录')
    router.push({ name: 'login', query: { redirect: route.fullPath } })
    return
  }
  form.adoption_pet_id = pet.value.id
  applyVisible.value = true
}

function resetForm() {
  form.contact_name = ''
  form.contact_phone = ''
  form.living_environment = ''
  form.pet_experience = ''
  form.application_reason = ''
}

async function submitApply() {
  await formRef.value.validate()
  submitting.value = true
  try {
    await createApplication({
      adoption_pet_id: pet.value.id,
      contact_name: form.contact_name,
      contact_phone: form.contact_phone,
      living_environment: form.living_environment,
      pet_experience: form.pet_experience,
      application_reason: form.application_reason
    })
    ElMessage.success('申请已提交，请耐心等待审核')
    applyVisible.value = false
  } finally {
    submitting.value = false
  }
}

onMounted(load)
</script>

<style scoped>
.page {
  min-height: 100vh;
  background: #f5f7fa;
}
.container {
  max-width: 1000px;
  margin: 0 auto;
  padding: 24px;
}
.back {
  margin-bottom: 16px;
}
.detail-card {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 24px;
  background: #fff;
  padding: 24px;
  border-radius: 8px;
  box-shadow: 0 1px 4px rgba(0, 0, 0, 0.06);
}
.gallery {
  display: flex;
  flex-direction: column;
  gap: 12px;
}
.main-img {
  width: 100%;
  height: 360px;
  border-radius: 8px;
  background: #eef2f7;
}
.main-img.placeholder {
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 80px;
  color: #c0c4cc;
}
.thumbs {
  display: flex;
  gap: 8px;
}
.thumbs img {
  width: 64px;
  height: 64px;
  object-fit: cover;
  border-radius: 6px;
  cursor: pointer;
  border: 2px solid transparent;
}
.thumbs img.active {
  border-color: #409eff;
}
.title-row {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 16px;
}
.title-row h2 {
  margin: 0;
}
.apply-bar {
  margin-top: 16px;
}
.section {
  background: #fff;
  padding: 20px 24px;
  border-radius: 8px;
  margin-top: 16px;
}
.section h3 {
  margin: 0 0 12px;
  color: #303133;
}
.section p {
  margin: 0;
  color: #606266;
  line-height: 1.7;
  white-space: pre-wrap;
}
</style>
