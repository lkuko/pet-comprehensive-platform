<template>
  <div class="page">
    <AppHeader />
    <main class="container">
      <h2 class="page-title">我的洗护寄养预约</h2>

      <el-empty v-if="!loading && list.length === 0" description="还没有洗护/寄养预约记录">
        <el-button type="primary" @click="$router.push('/care')">去预约</el-button>
      </el-empty>

      <div v-else class="app-list">
        <el-card v-for="item in list" :key="item.id" class="app-card" shadow="hover">
          <div class="card-body">
            <div class="info">
              <div class="row1">
                <span class="pet-name">{{ item.pet_name }}</span>
                <el-tag size="small" :type="item.service_type === 'BOARDING' ? 'success' : 'primary'">
                  {{ SERVICE_TYPE[item.service_type] || item.service_type }}
                </el-tag>
                <el-tag :type="CARE_APP_STATUS_TAG[item.status] || 'info'">
                  {{ CARE_APP_STATUS[item.status] || item.status }}
                </el-tag>
              </div>
              <div class="meta">预约编号：{{ item.appointment_no }}</div>
              <div class="meta">
                分类：{{ item.category_name }} ｜ 套餐：{{ item.package_name }}
              </div>
              <div v-if="item.service_type === 'GROOMING'" class="meta">
                到店时间：{{ fmtDateTime(item.appointment_time) }}
              </div>
              <div v-else class="meta">
                寄养时段：{{ item.check_in_date }} 至 {{ item.check_out_date }}
              </div>
              <div class="meta">联系电话：{{ item.contact_phone }}</div>
              <div class="meta">费用：¥{{ item.total_price }}（单价 ¥{{ item.price_snapshot }}）</div>
              <div v-if="item.note" class="meta">备注：{{ item.note }}</div>
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
import { listMyAppointments, cancelAppointment } from '../api/care'
import { SERVICE_TYPE, CARE_APP_STATUS, CARE_APP_STATUS_TAG } from '../utils/dict'

const list = ref([])
const loading = ref(false)

function fmtDateTime(t) {
  if (!t) return ''
  return t.replace('T', ' ').slice(0, 16)
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
  await ElMessageBox.confirm('确定取消这条预约吗？', '提示', { type: 'warning' })
  await cancelAppointment(item.id)
  ElMessage.success('已取消')
  load()
}

onMounted(load)
</script>

<style scoped>
.page {
  min-height: 100vh;
  background: #f5f7fa;
}
.container {
  max-width: 860px;
  margin: 0 auto;
  padding: 24px;
}
.page-title {
  margin: 0 0 16px;
  color: #303133;
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
  color: #303133;
}
.meta {
  font-size: 13px;
  color: #909399;
  margin-top: 4px;
}
.comment {
  font-size: 13px;
  color: #e6a23c;
  margin-top: 8px;
}
.actions {
  flex-shrink: 0;
}
</style>
