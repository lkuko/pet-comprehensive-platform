<template>
  <div class="page">
    <AppHeader />
    <main class="container">
      <h2 class="page-title">我的领养申请</h2>

      <el-empty v-if="!loading && list.length === 0" description="还没有申请记录" />

      <div v-else class="app-list">
        <el-card v-for="item in list" :key="item.id" class="app-card" shadow="hover">
          <div class="card-body">
            <div class="cover" @click="$router.push(`/adoption/${item.adoption_pet_id}`)">
              <img v-if="item.pet_cover_url" :src="item.pet_cover_url" />
              <span v-else class="placeholder">🐾</span>
            </div>
            <div class="info">
              <div class="row1">
                <span class="pet-name">{{ item.pet_name }}</span>
                <el-tag :type="APP_STATUS_TAG[item.status] || 'info'">
                  {{ APP_STATUS[item.status] || item.status }}
                </el-tag>
              </div>
              <div class="meta">申请编号：{{ item.application_no }}</div>
              <div class="meta">申请时间：{{ item.created_at }}</div>
              <div v-if="item.review_comment" class="comment">
                审核意见：{{ item.review_comment }}
              </div>
            </div>
            <div class="actions">
              <el-button
                v-if="item.status === 'PENDING'"
                size="small"
                @click="cancel(item)"
              >撤回申请</el-button>
              <el-button size="small" @click="$router.push(`/adoption/${item.adoption_pet_id}`)">查看宠物</el-button>
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
import { listMyApplications, cancelApplication } from '../api/applications'
import { APP_STATUS, APP_STATUS_TAG } from '../utils/dict'

const list = ref([])
const loading = ref(false)

async function load() {
  loading.value = true
  try {
    list.value = (await listMyApplications()).data
  } finally {
    loading.value = false
  }
}

async function cancel(item) {
  await ElMessageBox.confirm('确定撤回这条申请吗？', '提示', { type: 'warning' })
  await cancelApplication(item.id)
  ElMessage.success('已撤回')
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
.cover {
  width: 96px;
  height: 96px;
  border-radius: 8px;
  overflow: hidden;
  flex-shrink: 0;
  cursor: pointer;
  background: #eef2f7;
  display: flex;
  align-items: center;
  justify-content: center;
}
.cover img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}
.placeholder {
  font-size: 40px;
  color: #c0c4cc;
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
