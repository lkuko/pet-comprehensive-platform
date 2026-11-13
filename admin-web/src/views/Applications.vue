<template>
  <div class="page">
    <AdminHeader />
    <main class="container">
      <div class="head">
        <h2>领养申请审核</h2>
      </div>

      <div class="toolbar">
        <el-input v-model="keyword" placeholder="搜索编号/联系人/电话" clearable class="search" @keyup.enter="search" />
        <el-select v-model="statusFilter" placeholder="全部状态" clearable class="status" @change="search">
          <el-option v-for="(v, k) in APP_STATUS" :key="k" :label="v" :value="k" />
        </el-select>
        <el-button type="primary" @click="search">查询</el-button>
      </div>

      <el-table :data="list" v-loading="loading" stripe>
        <el-table-column prop="application_no" label="申请编号" width="180" />
        <el-table-column label="宠物" width="140">
          <template #default="{ row }">
            <div class="pet-cell">
              <img v-if="row.pet_cover_url" :src="row.pet_cover_url" class="pet-cover" />
              <span class="pet-placeholder" v-else>🐾</span>
              <span>{{ row.pet_name }}</span>
            </div>
          </template>
        </el-table-column>
        <el-table-column prop="user_nickname" label="申请人" width="110" />
        <el-table-column prop="contact_phone" label="联系电话" width="130" />
        <el-table-column label="状态" width="90">
          <template #default="{ row }">
            <el-tag :type="APP_STATUS_TAG[row.status] || 'info'" size="small">
              {{ APP_STATUS[row.status] || row.status }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="申请时间" width="170">
          <template #default="{ row }">{{ formatTime(row.created_at) }}</template>
        </el-table-column>
        <el-table-column label="操作" min-width="200">
          <template #default="{ row }">
            <el-button size="small" @click="openDetail(row)">详情</el-button>
            <template v-if="row.status === 'PENDING'">
              <el-button size="small" type="success" @click="approve(row)">通过</el-button>
              <el-button size="small" type="danger" @click="openReject(row)">拒绝</el-button>
            </template>
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
    <el-dialog v-model="detailVisible" title="申请详情" width="560px">
      <template v-if="current">
        <el-descriptions :column="1" border>
          <el-descriptions-item label="申请编号">{{ current.application_no }}</el-descriptions-item>
          <el-descriptions-item label="宠物">{{ current.pet_name }}</el-descriptions-item>
          <el-descriptions-item label="申请人">{{ current.user_nickname }}</el-descriptions-item>
          <el-descriptions-item label="联系人">{{ current.contact_name }}</el-descriptions-item>
          <el-descriptions-item label="联系电话">{{ current.contact_phone }}</el-descriptions-item>
          <el-descriptions-item label="居住环境">{{ current.living_environment }}</el-descriptions-item>
          <el-descriptions-item label="养宠经验">{{ current.pet_experience || '—' }}</el-descriptions-item>
          <el-descriptions-item label="申请理由">{{ current.application_reason }}</el-descriptions-item>
          <el-descriptions-item label="状态">
            <el-tag :type="APP_STATUS_TAG[current.status] || 'info'" size="small">
              {{ APP_STATUS[current.status] || current.status }}
            </el-tag>
          </el-descriptions-item>
          <el-descriptions-item v-if="current.review_comment" label="审核意见">{{ current.review_comment }}</el-descriptions-item>
        </el-descriptions>
      </template>
    </el-dialog>

    <!-- 拒绝弹窗 -->
    <el-dialog v-model="rejectVisible" title="拒绝申请" width="480px">
      <el-form label-width="80px">
        <el-form-item label="拒绝原因" required>
          <el-input
            v-model="rejectComment"
            type="textarea"
            :rows="3"
            maxlength="500"
            show-word-limit
            placeholder="请填写拒绝原因（必填）"
          />
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
import { listApplications, approveApplication, rejectApplication } from '../api/adoption'
import { APP_STATUS, APP_STATUS_TAG } from '../utils/dict'

const list = ref([])
const total = ref(0)
const page = ref(1)
const pageSize = ref(10)
const keyword = ref('')
const statusFilter = ref('')
const loading = ref(false)

const detailVisible = ref(false)
const current = ref(null)

const rejectVisible = ref(false)
const rejectComment = ref('')
const rejectId = ref(null)
const rejecting = ref(false)

function formatTime(iso) {
  if (!iso) return '—'
  return iso.replace('T', ' ').replace('+00:00', '').slice(0, 19)
}

async function load() {
  loading.value = true
  try {
    const res = await listApplications({
      page: page.value,
      page_size: pageSize.value,
      keyword: keyword.value || undefined,
      status: statusFilter.value || undefined
    })
    list.value = res.data.items || []
    total.value = res.data.total || 0
  } finally {
    loading.value = false
  }
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

async function approve(row) {
  await ElMessageBox.confirm(`确定通过「${row.pet_name}」的领养申请吗？通过后该宠物将变为已领养，同宠物其他待审核申请将自动关闭。`, '审核确认', { type: 'warning' })
  await approveApplication(row.id)
  ElMessage.success('已通过')
  load()
}

function openReject(row) {
  rejectId.value = row.id
  rejectComment.value = ''
  rejectVisible.value = true
}

async function doReject() {
  if (!rejectComment.value.trim()) {
    ElMessage.warning('请填写拒绝原因')
    return
  }
  rejecting.value = true
  try {
    await rejectApplication(rejectId.value, rejectComment.value.trim())
    ElMessage.success('已拒绝')
    rejectVisible.value = false
    load()
  } finally {
    rejecting.value = false
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
  max-width: 1100px;
  margin: 0 auto;
  padding: 24px;
}
.head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 16px;
}
.head h2 {
  margin: 0;
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
.pet-cell {
  display: flex;
  align-items: center;
  gap: 8px;
}
.pet-cover,
.pet-placeholder {
  width: 32px;
  height: 32px;
  border-radius: 6px;
  object-fit: cover;
  background: #eef2f7;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  font-size: 18px;
}
.pager {
  display: flex;
  justify-content: center;
  margin-top: 16px;
}
</style>
