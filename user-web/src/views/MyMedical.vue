<template>
  <div class="page">
    <AppHeader />
    <main class="container">
      <h2 class="page-title">我的医疗预约</h2>

      <el-empty v-if="!loading && list.length === 0" description="还没有医疗预约记录">
        <el-button type="primary" @click="$router.push('/medical')">去预约</el-button>
      </el-empty>

      <div v-else class="app-list">
        <el-card v-for="item in list" :key="item.id" class="app-card" shadow="hover">
          <div class="card-body">
            <div class="info">
              <div class="row1">
                <span class="pet-name">{{ item.pet_name }}</span>
                <el-tag :type="MEDICAL_APP_STATUS_TAG[item.status] || 'info'">
                  {{ MEDICAL_APP_STATUS[item.status] || item.status }}
                </el-tag>
              </div>
              <div class="meta">预约编号：{{ item.appointment_no }}</div>
              <div class="meta">
                项目：{{ item.service_name }} ｜ 医生：{{ item.doctor_name }} ｜ {{ item.location_name }}
              </div>
              <div class="meta">
                时段：{{ item.schedule_date }} {{ fmtTime(item.start_time) }} - {{ fmtTime(item.end_time) }}
              </div>
              <div class="meta">联系电话：{{ item.contact_phone }}</div>
              <div v-if="item.symptom_note" class="meta">症状说明：{{ item.symptom_note }}</div>
              <div v-if="item.review_comment" class="comment">处理意见：{{ item.review_comment }}</div>
            </div>
            <div class="actions">
              <el-button
                v-if="item.status === 'PENDING_CONFIRMATION'"
                size="small"
                @click="cancel(item)"
              >取消预约</el-button>
            </div>
          </div>
        </el-card>
      </div>
    </main>
  </div>
</template>

<script setup>
import { onMounted, ref } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import AppHeader from '../components/AppHeader.vue'
import { listMyAppointments, cancelAppointment } from '../api/medical'
import { MEDICAL_APP_STATUS, MEDICAL_APP_STATUS_TAG } from '../utils/dict'

const list = ref([])
const loading = ref(false)

function fmtTime(t) {
  return t ? t.slice(0, 5) : ''
}

async function load() {
  loading.value = true
  try {
    list.value = (await listMyAppointments()).data
  } finally {
    loading.value = false
  }
}

async function cancel(item) {
  await ElMessageBox.confirm('确定取消这条医疗预约吗？', '提示', { type: 'warning' })
  await cancelAppointment(item.id)
  ElMessage.success('已取消')
  load()
}

onMounted(load)
</script>

<style scoped>
.page {
  min-height: 100vh;
  background: var(--brand-paper);
}
.container {
  max-width: 860px;
  margin: 0 auto;
  padding: 24px;
}
.page-title {
  margin: 0 0 16px;
  color: var(--brand-ink);
}
.app-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}
.app-card :deep(.el-card__body) {
  padding: 16px;
}
.card-body {
  display: flex;
  gap: 16px;
  align-items: center;
}
.info {
  flex: 1;
  min-width: 0;
}
.row1 {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 8px;
}
.pet-name {
  font-size: 16px;
  font-weight: 600;
  color: var(--brand-ink);
}
.meta {
  font-size: 13px;
  color: var(--el-text-color-secondary);
  margin-top: 4px;
}
.comment {
  font-size: 13px;
  color: var(--el-color-warning);
  margin-top: 8px;
}
.actions {
  flex-shrink: 0;
}
</style>
