<template>
  <div class="page">
    <AppHeader />
    <main class="container">
      <h2 class="page-title">宠物医疗预约</h2>

      <el-alert
        title="仅提供体检、疫苗、驱虫等基础诊疗的到店预约，不含在线问诊。"
        type="info"
        :closable="false"
        class="tip"
      />

      <!-- 医疗点 -->
      <section class="block">
        <h3 class="block-title">1. 选择医疗点</h3>
        <div class="location-list">
          <el-card
            v-for="loc in locations"
            :key="loc.id"
            class="loc-card"
            :class="{ active: form.location_id === loc.id }"
            shadow="hover"
            @click="selectLocation(loc)"
          >
            <div class="loc-name">{{ loc.name }}</div>
            <div class="loc-addr">{{ loc.address }}</div>
            <div class="loc-phone">{{ loc.phone }}</div>
          </el-card>
          <el-empty v-if="!locations.length" description="暂无可用医疗点" />
        </div>
      </section>

      <!-- 医生 -->
      <section v-if="form.location_id" class="block">
        <h3 class="block-title">2. 选择医生</h3>
        <div class="doctor-list">
          <el-card
            v-for="doc in doctors"
            :key="doc.id"
            class="doctor-card"
            :class="{ active: selectedDoctorId === doc.id }"
            shadow="hover"
            @click="selectDoctor(doc)"
          >
            <div class="doctor-name">{{ doc.name }}</div>
            <div class="doctor-title">{{ doc.title }}</div>
            <div class="doctor-specialty">{{ doc.specialty }}</div>
          </el-card>
          <el-empty v-if="!doctors.length" description="该医疗点暂无医生" />
        </div>
      </section>

      <!-- 时段 -->
      <section v-if="selectedDoctorId" class="block">
        <h3 class="block-title">3. 选择可预约时段</h3>
        <div v-if="scheduleGroups.length" class="schedule-groups">
          <div v-for="g in scheduleGroups" :key="g.date" class="schedule-group">
            <div class="schedule-date">{{ g.date }}</div>
            <div class="slot-list">
              <el-button
                v-for="slot in g.slots"
                :key="slot.id"
                :type="form.schedule_id === slot.id ? 'primary' : 'default'"
                :disabled="slot.remaining <= 0"
                @click="form.schedule_id = slot.id"
              >
                {{ fmtTime(slot.start_time) }} - {{ fmtTime(slot.end_time) }}
                <span class="remaining">剩 {{ slot.remaining }} 位</span>
              </el-button>
            </div>
          </div>
        </div>
        <el-empty v-else description="该医生暂无可用时段" />
      </section>

      <!-- 预约信息 -->
      <section v-if="form.schedule_id" class="block">
        <h3 class="block-title">4. 填写预约信息</h3>
        <el-form :model="form" label-width="100px" class="appoint-form">
          <el-form-item label="我的宠物" required>
            <el-select v-model="form.user_pet_id" placeholder="请选择本人宠物">
              <el-option v-for="p in pets" :key="p.id" :label="p.name" :value="p.id" />
            </el-select>
            <el-button text type="primary" @click="$router.push('/pets')">新增宠物档案</el-button>
          </el-form-item>
          <el-form-item label="医疗项目" required>
            <el-select v-model="form.service_id" placeholder="请选择医疗项目">
              <el-option
                v-for="s in services"
                :key="s.id"
                :label="`${s.name}（¥${s.reference_price}，约${s.duration_minutes}分钟）`"
                :value="s.id"
              />
            </el-select>
          </el-form-item>
          <el-form-item label="联系电话" required>
            <el-input v-model="form.contact_phone" placeholder="请输入联系电话" maxlength="20" />
          </el-form-item>
          <el-form-item label="症状说明">
            <el-input v-model="form.symptom_note" type="textarea" :rows="3" placeholder="选填：简要描述宠物症状" />
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
import { listLocations, listDoctors, listServices, listSchedules, createAppointment } from '../api/medical'
import { listPets } from '../api/pets'

const locations = ref([])
const doctors = ref([])
const services = ref([])
const schedules = ref([])
const pets = ref([])

const form = ref({
  location_id: null,
  schedule_id: null,
  user_pet_id: null,
  service_id: null,
  contact_phone: '',
  symptom_note: ''
})
const selectedDoctorId = ref(null)
const submitting = ref(false)

const scheduleGroups = computed(() => {
  const map = new Map()
  for (const s of schedules.value) {
    if (!map.has(s.schedule_date)) map.set(s.schedule_date, [])
    map.get(s.schedule_date).push(s)
  }
  return Array.from(map.entries()).map(([date, slots]) => ({ date, slots }))
})

function fmtTime(t) {
  return t ? t.slice(0, 5) : ''
}

async function selectLocation(loc) {
  form.value.location_id = loc.id
  selectedDoctorId.value = null
  schedules.value = []
  form.value.schedule_id = null
  doctors.value = (await listDoctors(loc.id)).data
}

async function selectDoctor(doc) {
  selectedDoctorId.value = doc.id
  form.value.schedule_id = null
  const res = await listSchedules({ doctor_id: doc.id })
  schedules.value = res.data
}

async function submit() {
  if (!form.value.user_pet_id) return ElMessage.warning('请选择本人宠物')
  if (!form.value.service_id) return ElMessage.warning('请选择医疗项目')
  if (!form.value.contact_phone.trim()) return ElMessage.warning('请填写联系电话')
  submitting.value = true
  try {
    await createAppointment({
      user_pet_id: form.value.user_pet_id,
      schedule_id: form.value.schedule_id,
      service_id: form.value.service_id,
      contact_phone: form.value.contact_phone.trim(),
      symptom_note: form.value.symptom_note || null
    })
    ElMessage.success('预约提交成功，请等待管理员确认')
    form.value = { location_id: null, schedule_id: null, user_pet_id: null, service_id: null, contact_phone: '', symptom_note: '' }
    selectedDoctorId.value = null
    schedules.value = []
    doctors.value = []
  } finally {
    submitting.value = false
  }
}

onMounted(async () => {
  locations.value = (await listLocations()).data
  services.value = (await listServices()).data
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
.location-list,
.doctor-list {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(240px, 1fr));
  gap: 12px;
}
.loc-card,
.doctor-card {
  cursor: pointer;
  border: 1px solid #e4e7ed;
}
.loc-card.active,
.doctor-card.active {
  border-color: var(--brand-forest);
  background: var(--brand-sage);
}
.loc-name,
.doctor-name {
  font-weight: 600;
  color: #303133;
  margin-bottom: 6px;
}
.loc-addr,
.doctor-title {
  font-size: 13px;
  color: #606266;
  margin-bottom: 4px;
}
.loc-phone,
.doctor-specialty {
  font-size: 12px;
  color: #909399;
}
.schedule-groups {
  display: flex;
  flex-direction: column;
  gap: 12px;
}
.schedule-group {
  border: 1px solid #ebeef5;
  border-radius: 6px;
  padding: 12px;
  background: #fff;
}
.schedule-date {
  font-weight: 600;
  color: #303133;
  margin-bottom: 8px;
}
.slot-list {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}
.remaining {
  font-size: 12px;
  opacity: 0.8;
}
.appoint-form {
  max-width: 520px;
  background: #fff;
  padding: 24px;
  border-radius: 8px;
}
</style>
