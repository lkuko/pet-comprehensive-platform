<template>
  <div class="page">
    <AdminHeader />
    <main class="container">
      <div class="head">
        <h2>医疗预约处理</h2>
      </div>

      <div class="toolbar">
        <el-input v-model="keyword" placeholder="搜索编号/宠物/电话" clearable class="search" @keyup.enter="search" />
        <el-select v-model="locationFilter" placeholder="全部医疗点" clearable class="status" @change="onLocationChange">
          <el-option v-for="l in locations" :key="l.id" :label="l.name" :value="l.id" />
        </el-select>
        <el-select v-model="doctorFilter" placeholder="全部医生" clearable class="status" @change="search">
          <el-option v-for="d in doctors" :key="d.id" :label="d.name" :value="d.id" />
        </el-select>
        <el-select v-model="statusFilter" placeholder="全部状态" clearable class="status" @change="search">
          <el-option v-for="(v, k) in MEDICAL_APP_STATUS" :key="k" :label="v" :value="k" />
        </el-select>
        <el-button type="primary" @click="search">查询</el-button>
      </div>

      <el-table :data="list" v-loading="loading" stripe>
        <el-table-column prop="appointment_no" label="预约编号" width="180" />
        <el-table-column prop="pet_name" label="宠物" width="110" />
        <el-table-column prop="user_nickname" label="用户" width="110" />
        <el-table-column prop="service_name" label="项目" width="120" />
        <el-table-column label="医生" width="110">
          <template #default="{ row }">{{ row.doctor_name }}</template>
        </el-table-column>
        <el-table-column label="时段" width="170">
          <template #default="{ row }">{{ row.schedule_date }} {{ fmtTime(row.start_time) }}-{{ fmtTime(row.end_time) }}</template>
        </el-table-column>
        <el-table-column label="状态" width="90">
          <template #default="{ row }">
            <el-tag :type="MEDICAL_APP_STATUS_TAG[row.status] || 'info'" size="small">
              {{ MEDICAL_APP_STATUS[row.status] || row.status }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="操作" min-width="220">
          <template #default="{ row }">
            <el-button size="small" @click="openDetail(row)">详情</el-button>
            <template v-if="row.status === 'PENDING_CONFIRMATION'">
              <el-button size="small" type="success" @click="confirm(row)">确认</el-button>
              <el-button size="small" type="danger" @click="openReject(row)">拒绝</el-button>
            </template>
            <el-button v-if="row.status === 'CONFIRMED'" size="small" type="primary" @click="complete(row)">完成</el-button>
          </template>
        </el-table-column>
      </el-table>

      <div class="pager">
        <el-pagination
          background
          layout="prev, pager, next, total"
          :total="total"
          :page-size="pageSize"
          :current-page="page"
          @current-change="onPageChange"
        />
      </div>
    </main>

    <!-- 详情弹窗 -->
    <el-dialog v-model="detailVisible" title="预约详情" width="560px">
      <template v-if="current">
        <el-descriptions :column="1" border>
          <el-descriptions-item label="预约编号">{{ current.appointment_no }}</el-descriptions-item>
          <el-descriptions-item label="宠物">{{ current.pet_name }}</el-descriptions-item>
          <el-descriptions-item label="用户">{{ current.user_nickname }}</el-descriptions-item>
          <el-descriptions-item label="医疗点">{{ current.location_name }}</el-descriptions-item>
          <el-descriptions-item label="医生">{{ current.doctor_name }}</el-descriptions-item>
          <el-descriptions-item label="项目">{{ current.service_name }}</el-descriptions-item>
          <el-descriptions-item label="时段">{{ current.schedule_date }} {{ fmtTime(current.start_time) }}-{{ fmtTime(current.end_time) }}</el-descriptions-item>
          <el-descriptions-item label="联系电话">{{ current.contact_phone }}</el-descriptions-item>
          <el-descriptions-item label="症状说明">{{ current.symptom_note || '—' }}</el-descriptions-item>
          <el-descriptions-item label="状态">
            <el-tag :type="MEDICAL_APP_STATUS_TAG[current.status] || 'info'" size="small">
              {{ MEDICAL_APP_STATUS[current.status] || current.status }}
            </el-tag>
          </el-descriptions-item>
          <el-descriptions-item v-if="current.review_comment" label="处理意见">{{ current.review_comment }}</el-descriptions-item>
        </el-descriptions>
      </template>
    </el-dialog>

    <!-- 拒绝弹窗 -->
    <el-dialog v-model="rejectVisible" title="拒绝预约" width="480px">
      <el-form label-width="80px">
        <el-form-item label="拒绝原因" required>
          <el-input v-model="rejectComment" type="textarea" :rows="3" maxlength="500" show-word-limit placeholder="请填写拒绝原因（必填）" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="rejectVisible = false">取消</el-button>
        <el-button type="danger" :loading="rejecting" @click="doReject">确认拒绝</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { onMounted, ref } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import AdminHeader from '../components/AdminHeader.vue'
import { listAppointments, confirmAppointment, rejectAppointment, completeAppointment, listLocations, listDoctors } from '../api/medical'
import { MEDICAL_APP_STATUS, MEDICAL_APP_STATUS_TAG } from '../utils/dict'

const list = ref([])
const total = ref(0)
const page = ref(1)
const pageSize = ref(10)
const keyword = ref('')
const statusFilter = ref('')
const locationFilter = ref(null)
const doctorFilter = ref(null)
const locations = ref([])
const doctors = ref([])
const loading = ref(false)

const detailVisible = ref(false)
const current = ref(null)

const rejectVisible = ref(false)
const rejectComment = ref('')
const rejectId = ref(null)
const rejecting = ref(false)

function fmtTime(t) {
  return t ? t.slice(0, 5) : ''
}

async function load() {
  loading.value = true
  try {
    const res = await listAppointments({
      page: page.value,
      page_size: pageSize.value,
      keyword: keyword.value || undefined,
      status: statusFilter.value || undefined,
      location_id: locationFilter.value || undefined,
      doctor_id: doctorFilter.value || undefined
    })
    list.value = res.data.items || []
    total.value = res.data.total || 0
  } finally {
    loading.value = false
  }
}

async function loadLocations() {
  try {
    locations.value = (await listLocations()).data || []
  } catch {}
}

async function loadDoctors() {
  try {
    doctors.value = (await listDoctors(locationFilter.value || undefined)).data || []
  } catch {}
}

function onLocationChange() {
  doctorFilter.value = null
  loadDoctors().then(search)
}

function search() {
  page.value = 1
  load()
}
function onPageChange(p) {
  page.value = p
  load()
}
function openDetail(row) {
  current.value = row
  detailVisible.value = true
}
async function confirm(row) {
  await ElMessageBox.confirm(`确定确认「${row.pet_name}」的医疗预约吗？`, '确认预约', { type: 'warning' })
  await confirmAppointment(row.id)
  ElMessage.success('已确认')
  load()
}
async function complete(row) {
  await ElMessageBox.confirm(`确定将「${row.pet_name}」的预约标记为完成吗？`, '完成预约', { type: 'warning' })
  await completeAppointment(row.id)
  ElMessage.success('已完成')
  load()
}
function openReject(row) {
  rejectId.value = row.id
  rejectComment.value = ''
  rejectVisible.value = true
}
async function doReject() {
  if (!rejectComment.value.trim()) return ElMessage.warning('请填写拒绝原因')
  rejecting.value = true
  try {
    await rejectAppointment(rejectId.value, rejectComment.value.trim())
    ElMessage.success('已拒绝')
    rejectVisible.value = false
    load()
  } finally {
    rejecting.value = false
  }
}

onMounted(async () => {
  await loadLocations()
  await loadDoctors()
  load()
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
.toolbar {
  display: flex;
  gap: 12px;
  margin-bottom: 16px;
}
.search {
  width: 260px;
}
.status {
  width: 150px;
}
.pager {
  display: flex;
  justify-content: center;
  margin-top: 16px;
}
</style>
