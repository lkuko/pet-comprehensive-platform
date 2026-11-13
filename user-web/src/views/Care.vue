<template>
  <div class="page">
    <AppHeader />
    <main class="container">
      <h2 class="page-title">洗护 / 寄养预约</h2>

      <el-alert
        title="洗护美容为到店预约；寄养按天计费，请至少提前一天预约。"
        type="info"
        :closable="false"
        class="tip"
      />

      <!-- 服务类型 -->
      <section class="block">
        <h3 class="block-title">1. 选择服务类型</h3>
        <el-radio-group v-model="serviceType" @change="onTypeChange">
          <el-radio-button value="GROOMING">洗护美容</el-radio-button>
          <el-radio-button value="BOARDING">寄养</el-radio-button>
        </el-radio-group>
      </section>

      <!-- 分类 -->
      <section class="block">
        <h3 class="block-title">2. 选择服务分类</h3>
        <div class="cat-list">
          <el-card
            v-for="cat in categories"
            :key="cat.id"
            class="cat-card"
            :class="{ active: form.category_id === cat.id }"
            shadow="hover"
            @click="selectCategory(cat)"
          >
            <div class="cat-name">{{ cat.name }}</div>
            <div class="cat-desc">{{ cat.description || '—' }}</div>
          </el-card>
          <el-empty v-if="!categories.length" description="暂无可用分类" />
        </div>
      </section>

      <!-- 套餐 -->
      <section v-if="form.category_id" class="block">
        <h3 class="block-title">3. 选择服务套餐</h3>
        <div class="pkg-list">
          <el-card
            v-for="pkg in packages"
            :key="pkg.id"
            class="pkg-card"
            :class="{ active: form.package_id === pkg.id }"
            shadow="hover"
            @click="selectPackage(pkg)"
          >
            <div class="pkg-name">{{ pkg.name }}</div>
            <div class="pkg-price">
              ¥{{ pkg.price }}
              <span class="pkg-unit">{{ serviceType === 'BOARDING' ? '/天' : '/次' }}</span>
            </div>
            <div class="pkg-desc">{{ pkg.description || '—' }}</div>
            <div v-if="serviceType === 'GROOMING'" class="pkg-duration">约 {{ pkg.duration_minutes }} 分钟</div>
          </el-card>
          <el-empty v-if="!packages.length" description="该分类暂无套餐" />
        </div>
      </section>

      <!-- 预约信息 -->
      <section v-if="form.package_id" class="block">
        <h3 class="block-title">4. 填写预约信息</h3>
        <el-form :model="form" label-width="100px" class="appoint-form">
          <el-form-item label="我的宠物" required>
            <el-select v-model="form.user_pet_id" placeholder="请选择本人宠物">
              <el-option v-for="p in pets" :key="p.id" :label="p.name" :value="p.id" />
            </el-select>
            <el-button text type="primary" @click="$router.push('/pets')">新增宠物档案</el-button>
          </el-form-item>

          <el-form-item v-if="serviceType === 'GROOMING'" label="预约时间" required>
            <el-date-picker
              v-model="form.appointment_time"
              type="datetime"
              placeholder="选择到店时间"
              value-format="YYYY-MM-DDTHH:mm:ss"
              :disabled-date="disablePastDate"
            />
          </el-form-item>

          <template v-else>
            <el-form-item label="入住日期" required>
              <el-date-picker
                v-model="form.check_in_date"
                type="date"
                placeholder="选择入住日期"
                value-format="YYYY-MM-DD"
                :disabled-date="disablePastDate"
                @change="onCheckInChange"
              />
            </el-form-item>
            <el-form-item label="离店日期" required>
              <el-date-picker
                v-model="form.check_out_date"
                type="date"
                placeholder="选择离店日期"
                value-format="YYYY-MM-DD"
                :disabled-date="disableCheckOutDate"
              />
            </el-form-item>
          </template>

          <el-form-item label="联系电话" required>
            <el-input v-model="form.contact_phone" placeholder="请输入联系电话" maxlength="20" />
          </el-form-item>
          <el-form-item label="备注">
            <el-input v-model="form.note" type="textarea" :rows="3" placeholder="选填：特殊需求说明" />
          </el-form-item>

          <el-form-item v-if="totalPrice !== null" label="预估费用">
            <span class="total-price">¥{{ totalPrice }}</span>
          </el-form-item>

          <el-form-item>
            <el-button type="primary" :loading="submitting" @click="submit">提交预约</el-button>
          </el-form-item>
        </el-form>
      </section>
    </main>
  </div>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue'
import { ElMessage } from 'element-plus'
import AppHeader from '../components/AppHeader.vue'
import { listCategories, listPackages, createAppointment } from '../api/care'
import { listPets } from '../api/pets'

const serviceType = ref('GROOMING')
const categories = ref([])
const packages = ref([])
const pets = ref([])

const form = ref({
  category_id: null,
  package_id: null,
  user_pet_id: null,
  appointment_time: '',
  check_in_date: '',
  check_out_date: '',
  contact_phone: '',
  note: ''
})
const submitting = ref(false)

const selectedPackage = computed(() =>
  packages.value.find((p) => p.id === form.value.package_id) || null
)

const totalPrice = computed(() => {
  const pkg = selectedPackage.value
  if (!pkg) return null
  if (serviceType.value === 'BOARDING' && form.value.check_in_date && form.value.check_out_date) {
    const days = Math.round(
      (new Date(form.value.check_out_date) - new Date(form.value.check_in_date)) / 86400000
    )
    return days > 0 ? Number(pkg.price) * days : null
  }
  return Number(pkg.price)
})

function disablePastDate(d) {
  return d < new Date(new Date().setHours(0, 0, 0, 0))
}
function disableCheckOutDate(d) {
  if (!form.value.check_in_date) return false
  return d <= new Date(form.value.check_in_date)
}

async function onTypeChange() {
  form.value.category_id = null
  form.value.package_id = null
  packages.value = []
  categories.value = (await listCategories(serviceType.value)).data
}

async function selectCategory(cat) {
  form.value.category_id = cat.id
  form.value.package_id = null
  packages.value = (await listPackages(cat.id)).data
}

function selectPackage(pkg) {
  form.value.package_id = pkg.id
}

function onCheckInChange() {
  if (form.value.check_out_date && form.value.check_out_date <= form.value.check_in_date) {
    form.value.check_out_date = ''
  }
}

async function submit() {
  if (!form.value.user_pet_id) return ElMessage.warning('请选择本人宠物')
  if (!form.value.contact_phone.trim()) return ElMessage.warning('请填写联系电话')
  if (serviceType.value === 'GROOMING' && !form.value.appointment_time) {
    return ElMessage.warning('请选择预约时间')
  }
  if (serviceType.value === 'BOARDING') {
    if (!form.value.check_in_date) return ElMessage.warning('请选择入住日期')
    if (!form.value.check_out_date) return ElMessage.warning('请选择离店日期')
  }
  submitting.value = true
  try {
    const payload = {
      user_pet_id: form.value.user_pet_id,
      package_id: form.value.package_id,
      contact_phone: form.value.contact_phone.trim(),
      note: form.value.note || null
    }
    if (serviceType.value === 'GROOMING') {
      payload.appointment_time = form.value.appointment_time
    } else {
      payload.check_in_date = form.value.check_in_date
      payload.check_out_date = form.value.check_out_date
    }
    await createAppointment(payload)
    ElMessage.success('预约提交成功，请等待管理员确认')
    form.value = {
      category_id: null, package_id: null, user_pet_id: null,
      appointment_time: '', check_in_date: '', check_out_date: '',
      contact_phone: '', note: ''
    }
    packages.value = []
  } finally {
    submitting.value = false
  }
}

onMounted(async () => {
  categories.value = (await listCategories('GROOMING')).data
  pets.value = (await listPets()).data
})
</script>

<style scoped>
.page {
  min-height: 100vh;
  background: #f5f7fa;
}
.container {
  max-width: 900px;
  margin: 0 auto;
  padding: 24px;
}
.page-title {
  margin: 0 0 16px;
  color: #303133;
}
.tip {
  margin-bottom: 16px;
}
.block {
  margin-bottom: 24px;
}
.block-title {
  margin: 0 0 12px;
  font-size: 15px;
  color: #303133;
}
.cat-list,
.pkg-list {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(220px, 1fr));
  gap: 12px;
}
.cat-card,
.pkg-card {
  cursor: pointer;
  border: 1px solid #e4e7ed;
}
.cat-card.active,
.pkg-card.active {
  border-color: #409eff;
  background: #ecf5ff;
}
.cat-name,
.pkg-name {
  font-weight: 600;
  color: #303133;
  margin-bottom: 6px;
}
.cat-desc,
.pkg-desc {
  font-size: 13px;
  color: #606266;
  margin-bottom: 6px;
}
.pkg-price {
  color: #f56c6c;
  font-size: 18px;
  font-weight: 700;
  margin-bottom: 6px;
}
.pkg-unit {
  font-size: 12px;
  color: #909399;
  font-weight: 400;
}
.pkg-duration {
  font-size: 12px;
  color: #909399;
}
.appoint-form {
  max-width: 560px;
  background: #fff;
  padding: 24px;
  border-radius: 8px;
}
.total-price {
  color: #f56c6c;
  font-size: 20px;
  font-weight: 700;
}
</style>
