<template>
  <div class="page">
    <AdminHeader />
    <main class="container">
      <div class="head">
        <h2>医疗资源管理</h2>
      </div>

      <el-tabs v-model="activeTab">
        <!-- 医疗点 -->
        <el-tab-pane label="医疗点" name="locations">
          <div class="tab-toolbar">
            <el-button type="primary" @click="openLocation()">新增医疗点</el-button>
          </div>
          <el-table :data="locations" v-loading="loading" stripe>
            <el-table-column prop="id" label="ID" width="70" />
            <el-table-column prop="name" label="名称" min-width="180" />
            <el-table-column prop="address" label="地址" min-width="220" />
            <el-table-column prop="phone" label="电话" width="140" />
            <el-table-column label="状态" width="80">
              <template #default="{ row }">
                <el-tag :type="ENABLE_STATUS_TAG[row.status] || 'info'" size="small">{{ ENABLE_STATUS[row.status] || row.status }}</el-tag>
              </template>
            </el-table-column>
            <el-table-column label="操作" width="150">
              <template #default="{ row }">
                <el-button size="small" @click="openLocation(row)">编辑</el-button>
                <el-button size="small" type="danger" @click="removeLocation(row)">删除</el-button>
              </template>
            </el-table-column>
          </el-table>
        </el-tab-pane>

        <!-- 医生 -->
        <el-tab-pane label="医生" name="doctors">
          <div class="tab-toolbar">
            <el-button type="primary" @click="openDoctor()">新增医生</el-button>
          </div>
          <el-table :data="doctors" v-loading="loading" stripe>
            <el-table-column prop="id" label="ID" width="70" />
            <el-table-column prop="name" label="姓名" width="120" />
            <el-table-column label="所属医疗点" min-width="180">
              <template #default="{ row }">{{ locationName(row.location_id) }}</template>
            </el-table-column>
            <el-table-column prop="title" label="职称" width="120" />
            <el-table-column prop="specialty" label="擅长" min-width="200" />
            <el-table-column label="状态" width="80">
              <template #default="{ row }">
                <el-tag :type="ENABLE_STATUS_TAG[row.status] || 'info'" size="small">{{ ENABLE_STATUS[row.status] || row.status }}</el-tag>
              </template>
            </el-table-column>
            <el-table-column label="操作" width="150">
              <template #default="{ row }">
                <el-button size="small" @click="openDoctor(row)">编辑</el-button>
                <el-button size="small" type="danger" @click="removeDoctor(row)">删除</el-button>
              </template>
            </el-table-column>
          </el-table>
        </el-tab-pane>

        <!-- 医疗项目 -->
        <el-tab-pane label="医疗项目" name="services">
          <div class="tab-toolbar">
            <el-button type="primary" @click="openService()">新增项目</el-button>
          </div>
          <el-table :data="services" v-loading="loading" stripe>
            <el-table-column prop="id" label="ID" width="70" />
            <el-table-column prop="name" label="名称" width="160" />
            <el-table-column prop="description" label="说明" min-width="240" />
            <el-table-column label="参考价" width="100">
              <template #default="{ row }">¥{{ row.reference_price }}</template>
            </el-table-column>
            <el-table-column prop="duration_minutes" label="时长(分)" width="100" />
            <el-table-column label="状态" width="80">
              <template #default="{ row }">
                <el-tag :type="ENABLE_STATUS_TAG[row.status] || 'info'" size="small">{{ ENABLE_STATUS[row.status] || row.status }}</el-tag>
              </template>
            </el-table-column>
            <el-table-column label="操作" width="150">
              <template #default="{ row }">
                <el-button size="small" @click="openService(row)">编辑</el-button>
                <el-button size="small" type="danger" @click="removeService(row)">删除</el-button>
              </template>
            </el-table-column>
          </el-table>
        </el-tab-pane>

        <!-- 排班 -->
        <el-tab-pane label="医生排班" name="schedules">
          <div class="tab-toolbar">
            <el-button type="primary" @click="openSchedule()">新增排班</el-button>
            <el-select v-model="scheduleDoctorFilter" placeholder="按医生筛选" clearable class="filter" @change="loadSchedules">
              <el-option v-for="d in doctors" :key="d.id" :label="d.name" :value="d.id" />
            </el-select>
          </div>
          <el-table :data="schedules" v-loading="loading" stripe>
            <el-table-column prop="id" label="ID" width="70" />
            <el-table-column label="医生" width="120">
              <template #default="{ row }">{{ doctorName(row.doctor_id) }}</template>
            </el-table-column>
            <el-table-column prop="schedule_date" label="日期" width="120" />
            <el-table-column label="时段" width="160">
              <template #default="{ row }">{{ fmtTime(row.start_time) }} - {{ fmtTime(row.end_time) }}</template>
            </el-table-column>
            <el-table-column label="容量" width="120">
              <template #default="{ row }">{{ row.booked_count }} / {{ row.capacity }}</template>
            </el-table-column>
            <el-table-column label="状态" width="80">
              <template #default="{ row }">
                <el-tag :type="ENABLE_STATUS_TAG[row.status] || 'info'" size="small">{{ ENABLE_STATUS[row.status] || row.status }}</el-tag>
              </template>
            </el-table-column>
            <el-table-column label="操作" width="150">
              <template #default="{ row }">
                <el-button size="small" @click="openSchedule(row)">编辑</el-button>
                <el-button size="small" type="danger" @click="removeSchedule(row)">删除</el-button>
              </template>
            </el-table-column>
          </el-table>
        </el-tab-pane>
      </el-tabs>
    </main>

    <!-- 医疗点弹窗 -->
    <el-dialog v-model="locationVisible" :title="locationForm.id ? '编辑医疗点' : '新增医疗点'" width="520px">
      <el-form :model="locationForm" label-width="80px">
        <el-form-item label="名称" required><el-input v-model="locationForm.name" maxlength="100" /></el-form-item>
        <el-form-item label="地址"><el-input v-model="locationForm.address" maxlength="255" /></el-form-item>
        <el-form-item label="电话"><el-input v-model="locationForm.phone" maxlength="20" /></el-form-item>
        <el-form-item label="简介"><el-input v-model="locationForm.description" type="textarea" :rows="2" /></el-form-item>
        <el-form-item label="状态">
          <el-switch v-model="locationForm.status" active-value="ACTIVE" inactive-value="INACTIVE" active-text="启用" inactive-text="停用" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="locationVisible = false">取消</el-button>
        <el-button type="primary" @click="saveLocation">保存</el-button>
      </template>
    </el-dialog>

    <!-- 医生弹窗 -->
    <el-dialog v-model="doctorVisible" :title="doctorForm.id ? '编辑医生' : '新增医生'" width="520px">
      <el-form :model="doctorForm" label-width="90px">
        <el-form-item label="所属医疗点" required>
          <el-select v-model="doctorForm.location_id" placeholder="请选择">
            <el-option v-for="l in locations" :key="l.id" :label="l.name" :value="l.id" />
          </el-select>
        </el-form-item>
        <el-form-item label="姓名" required><el-input v-model="doctorForm.name" maxlength="50" /></el-form-item>
        <el-form-item label="职称"><el-input v-model="doctorForm.title" maxlength="50" /></el-form-item>
        <el-form-item label="擅长"><el-input v-model="doctorForm.specialty" maxlength="255" /></el-form-item>
        <el-form-item label="状态">
          <el-switch v-model="doctorForm.status" active-value="ACTIVE" inactive-value="INACTIVE" active-text="启用" inactive-text="停用" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="doctorVisible = false">取消</el-button>
        <el-button type="primary" @click="saveDoctor">保存</el-button>
      </template>
    </el-dialog>

    <!-- 项目弹窗 -->
    <el-dialog v-model="serviceVisible" :title="serviceForm.id ? '编辑项目' : '新增项目'" width="520px">
      <el-form :model="serviceForm" label-width="90px">
        <el-form-item label="名称" required><el-input v-model="serviceForm.name" maxlength="50" /></el-form-item>
        <el-form-item label="说明"><el-input v-model="serviceForm.description" type="textarea" :rows="2" /></el-form-item>
        <el-form-item label="参考价">
          <el-input-number v-model="serviceForm.reference_price" :min="0" :precision="2" :step="10" />
        </el-form-item>
        <el-form-item label="时长(分)">
          <el-input-number v-model="serviceForm.duration_minutes" :min="1" />
        </el-form-item>
        <el-form-item label="状态">
          <el-switch v-model="serviceForm.status" active-value="ACTIVE" inactive-value="INACTIVE" active-text="启用" inactive-text="停用" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="serviceVisible = false">取消</el-button>
        <el-button type="primary" @click="saveService">保存</el-button>
      </template>
    </el-dialog>

    <!-- 排班弹窗 -->
    <el-dialog v-model="scheduleVisible" :title="scheduleForm.id ? '编辑排班' : '新增排班'" width="520px">
      <el-form :model="scheduleForm" label-width="90px">
        <el-form-item label="医生" required>
          <el-select v-model="scheduleForm.doctor_id" placeholder="请选择" @change="onScheduleDoctorChange">
            <el-option v-for="d in doctors" :key="d.id" :label="`${d.name}（${locationName(d.location_id)}）`" :value="d.id" />
          </el-select>
        </el-form-item>
        <el-form-item label="日期" required>
          <el-date-picker v-model="scheduleForm.schedule_date" type="date" value-format="YYYY-MM-DD" placeholder="选择日期" />
        </el-form-item>
        <el-form-item label="开始时间" required>
          <el-time-picker v-model="scheduleForm.start_time" format="HH:mm" value-format="HH:mm:ss" placeholder="开始时间" />
        </el-form-item>
        <el-form-item label="结束时间" required>
          <el-time-picker v-model="scheduleForm.end_time" format="HH:mm" value-format="HH:mm:ss" placeholder="结束时间" />
        </el-form-item>
        <el-form-item label="容量">
          <el-input-number v-model="scheduleForm.capacity" :min="1" />
        </el-form-item>
        <el-form-item label="状态">
          <el-switch v-model="scheduleForm.status" active-value="ACTIVE" inactive-value="INACTIVE" active-text="启用" inactive-text="停用" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="scheduleVisible = false">取消</el-button>
        <el-button type="primary" @click="saveSchedule">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { onMounted, ref } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import AdminHeader from '../components/AdminHeader.vue'
import * as api from '../api/medical'
import { ENABLE_STATUS, ENABLE_STATUS_TAG } from '../utils/dict'

const activeTab = ref('locations')
const loading = ref(false)

const locations = ref([])
const doctors = ref([])
const services = ref([])
const schedules = ref([])
const scheduleDoctorFilter = ref(null)

// 弹窗状态
const locationVisible = ref(false)
const doctorVisible = ref(false)
const serviceVisible = ref(false)
const scheduleVisible = ref(false)

const locationForm = ref({})
const doctorForm = ref({})
const serviceForm = ref({})
const scheduleForm = ref({})

function locationName(id) {
  return locations.value.find((l) => l.id === id)?.name || '—'
}
function doctorName(id) {
  return doctors.value.find((d) => d.id === id)?.name || '—'
}
function fmtTime(t) {
  return t ? t.slice(0, 5) : ''
}

async function loadAll() {
  loading.value = true
  try {
    locations.value = (await api.listLocations()).data
    doctors.value = (await api.listDoctors()).data
    services.value = (await api.listServices()).data
  } finally {
    loading.value = false
  }
}

async function loadSchedules() {
  loading.value = true
  try {
    const res = await api.listSchedules({ doctor_id: scheduleDoctorFilter.value || undefined })
    schedules.value = res.data
  } finally {
    loading.value = false
  }
}

// 医疗点
function openLocation(row) {
  locationForm.value = row
    ? { ...row }
    : { name: '', address: '', phone: '', description: '', status: 'ACTIVE' }
  locationVisible.value = true
}
async function saveLocation() {
  if (!locationForm.value.name?.trim()) return ElMessage.warning('请填写名称')
  if (locationForm.value.id) {
    await api.updateLocation(locationForm.value.id, locationForm.value)
  } else {
    await api.createLocation(locationForm.value)
  }
  ElMessage.success('已保存')
  locationVisible.value = false
  loadAll()
}
async function removeLocation(row) {
  await ElMessageBox.confirm(`确定删除医疗点「${row.name}」吗？`, '提示', { type: 'warning' })
  await api.deleteLocation(row.id)
  ElMessage.success('已删除')
  loadAll()
}

// 医生
function openDoctor(row) {
  doctorForm.value = row
    ? { ...row }
    : { location_id: null, name: '', title: '', specialty: '', status: 'ACTIVE' }
  doctorVisible.value = true
}
async function saveDoctor() {
  if (!doctorForm.value.name?.trim()) return ElMessage.warning('请填写姓名')
  if (!doctorForm.value.location_id) return ElMessage.warning('请选择医疗点')
  if (doctorForm.value.id) {
    await api.updateDoctor(doctorForm.value.id, doctorForm.value)
  } else {
    await api.createDoctor(doctorForm.value)
  }
  ElMessage.success('已保存')
  doctorVisible.value = false
  loadAll()
}
async function removeDoctor(row) {
  await ElMessageBox.confirm(`确定删除医生「${row.name}」吗？`, '提示', { type: 'warning' })
  await api.deleteDoctor(row.id)
  ElMessage.success('已删除')
  loadAll()
}

// 项目
function openService(row) {
  serviceForm.value = row
    ? { ...row, reference_price: Number(row.reference_price) }
    : { name: '', description: '', reference_price: 0, duration_minutes: 30, status: 'ACTIVE' }
  serviceVisible.value = true
}
async function saveService() {
  if (!serviceForm.value.name?.trim()) return ElMessage.warning('请填写名称')
  if (serviceForm.value.id) {
    await api.updateService(serviceForm.value.id, serviceForm.value)
  } else {
    await api.createService(serviceForm.value)
  }
  ElMessage.success('已保存')
  serviceVisible.value = false
  loadAll()
}
async function removeService(row) {
  await ElMessageBox.confirm(`确定删除项目「${row.name}」吗？`, '提示', { type: 'warning' })
  await api.deleteService(row.id)
  ElMessage.success('已删除')
  loadAll()
}

// 排班
function openSchedule(row) {
  if (row) {
    scheduleForm.value = { ...row }
  } else {
    scheduleForm.value = {
      doctor_id: null, schedule_date: '', start_time: '',
      end_time: '', capacity: 1, status: 'ACTIVE'
    }
  }
  scheduleVisible.value = true
}
function onScheduleDoctorChange() {}
async function saveSchedule() {
  if (!scheduleForm.value.doctor_id) return ElMessage.warning('请选择医生')
  if (!scheduleForm.value.schedule_date) return ElMessage.warning('请选择日期')
  if (!scheduleForm.value.start_time || !scheduleForm.value.end_time) return ElMessage.warning('请选择时段')
  const payload = {
    doctor_id: scheduleForm.value.doctor_id,
    location_id: doctors.value.find((d) => d.id === scheduleForm.value.doctor_id)?.location_id,
    schedule_date: scheduleForm.value.schedule_date,
    start_time: scheduleForm.value.start_time,
    end_time: scheduleForm.value.end_time,
    capacity: scheduleForm.value.capacity,
    status: scheduleForm.value.status
  }
  if (scheduleForm.value.id) {
    await api.updateSchedule(scheduleForm.value.id, payload)
  } else {
    await api.createSchedule(payload)
  }
  ElMessage.success('已保存')
  scheduleVisible.value = false
  loadSchedules()
}
async function removeSchedule(row) {
  await ElMessageBox.confirm('确定删除该排班吗？存在未完成预约时只能停用。', '提示', { type: 'warning' })
  await api.deleteSchedule(row.id)
  ElMessage.success('已删除')
  loadSchedules()
}

onMounted(async () => {
  await loadAll()
  await loadSchedules()
})
</script>

<style scoped>
.page {
  min-height: 100vh;
  background: var(--brand-paper);
}
.container {
  max-width: 1100px;
  margin: 0 auto;
  padding: 24px;
}
.head h2 {
  margin: 0 0 16px;
}
.tab-toolbar {
  display: flex;
  gap: 12px;
  margin-bottom: 16px;
}
.filter {
  width: 180px;
}
</style>
