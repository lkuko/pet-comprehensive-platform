<template>
  <div class="page">
    <AdminHeader />
    <main class="dashboard">
      <div class="head">
        <div>
          <h1 class="title">工作台</h1>
          <p class="sub">实时掌握平台待办与业务动态</p>
        </div>
        <div class="head-actions">
          <el-badge :value="summary.unread_notifications" :hidden="!summary.unread_notifications">
            <el-button @click="goNotifications" text>通知中心</el-button>
          </el-badge>
          <el-button type="primary" plain @click="load">刷新数据</el-button>
        </div>
      </div>

      <!-- 统计卡片 -->
      <el-row :gutter="16" class="stats">
        <el-col :span="24" :sm="12" :md="8" :lg="5" v-for="card in statCards" :key="card.key">
          <el-card class="stat-card" shadow="never" @click="go(card.to)">
            <div class="stat-icon" :style="{ background: card.bg, color: card.color }">
              <span v-html="card.icon"></span>
            </div>
            <div class="stat-info">
              <div class="stat-value">{{ card.value }}</div>
              <div class="stat-label">{{ card.label }}</div>
            </div>
          </el-card>
        </el-col>
      </el-row>

      <!-- 最近业务动态 -->
      <el-card class="recent-card" shadow="never">
        <template #header>
          <div class="recent-header">
            <span class="recent-title">最近业务动态</span>
            <el-tag v-if="wsConnected" type="success" size="small" effect="light">实时连接中</el-tag>
            <el-tag v-else type="info" size="small" effect="light">连接已断开</el-tag>
          </div>
        </template>

        <el-empty v-if="!summary.recent_business?.length" description="暂无业务动态" :image-size="80" />
        <ul v-else class="timeline">
          <li
            v-for="item in summary.recent_business"
            :key="item.id"
            class="timeline-item"
            :title="`前往处理：${businessText(item.business_type)}`"
            @click="goBusiness(item)"
          >
            <el-tag :type="businessTag(item.business_type)" size="small" effect="light">
              {{ businessText(item.business_type) }}
            </el-tag>
            <span class="timeline-title">{{ item.title }}</span>
            <span class="timeline-time">{{ formatTime(item.created_at) }}</span>
            <span class="timeline-arrow">›</span>
          </li>
        </ul>
      </el-card>
    </main>
  </div>
</template>

<script setup>
import { computed, onMounted, onUnmounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { ElNotification } from 'element-plus'
import AdminHeader from '../components/AdminHeader.vue'
import { getSummary } from '../api/dashboard'
import { markRead } from '../api/notification'
import { BUSINESS_TYPE, BUSINESS_TYPE_TAG } from '../utils/dict'

const router = useRouter()
const summary = ref({})
const wsConnected = ref(false)

let ws = null
let reconnectTimer = null

const statCards = computed(() => [
  { key: 'users', label: '注册用户', value: summary.value.user_count ?? 0, to: '/', icon: iconUser(), bg: '#e7efe9', color: '#2f6b4f' },
  { key: 'adoption', label: '待审核领养', value: summary.value.pending_adoption ?? 0, to: '/applications', icon: iconPaw(), bg: '#fbead9', color: '#e07b34' },
  { key: 'medical', label: '待处理医疗预约', value: summary.value.pending_medical ?? 0, to: '/medical/appointments', icon: iconMed(), bg: '#e3eef5', color: '#3a6ea5' },
  { key: 'care', label: '待处理洗护预约', value: summary.value.pending_care ?? 0, to: '/care/appointments', icon: iconBath(), bg: '#e9f0f3', color: '#2f8f8f' },
  { key: 'ship', label: '待发货订单', value: summary.value.pending_ship ?? 0, to: '/mall/orders', icon: iconBox(), bg: '#f4ecf7', color: '#7a5aa0' }
])

function iconUser() {
  return '<svg viewBox="0 0 24 24" width="22" height="22" fill="currentColor"><path d="M12 12a4 4 0 1 0 0-8 4 4 0 0 0 0 8zm0 2c-4.42 0-8 1.79-8 4v2h16v-2c0-2.21-3.58-4-8-4z"/></svg>'
}
function iconPaw() {
  return '<svg viewBox="0 0 24 24" width="22" height="22" fill="currentColor"><ellipse cx="12" cy="16" rx="6" ry="5"/><ellipse cx="5" cy="9" rx="2.6" ry="3"/><ellipse cx="9.5" cy="6" rx="2.6" ry="3"/><ellipse cx="14.5" cy="6" rx="2.6" ry="3"/><ellipse cx="19" cy="9" rx="2.6" ry="3"/></svg>'
}
function iconMed() {
  return '<svg viewBox="0 0 24 24" width="22" height="22" fill="currentColor"><path d="M12 3a1 1 0 0 1 1 1v7h7a1 1 0 1 1 0 2h-7v7a1 1 0 1 1-2 0v-7H4a1 1 0 1 1 0-2h7V4a1 1 0 0 1 1-1z"/></svg>'
}
function iconBath() {
  return '<svg viewBox="0 0 24 24" width="22" height="22" fill="currentColor"><path d="M12 3a3 3 0 0 1 3 3c0 1.2-.7 2.2-1.7 2.7L14 10h6v2h-1.2c.1.5.2 1 .2 1.5V15h-1a2 2 0 0 1-4 0h-4a2 2 0 0 1-4 0H5v-1.5c0-.5.07-1 .2-1.5H4V10h6l.7-1.3A3 3 0 0 1 9 6a3 3 0 0 1 3-3z"/></svg>'
}
function iconBox() {
  return '<svg viewBox="0 0 24 24" width="22" height="22" fill="currentColor"><path d="M12 2 2 7v10l10 5 10-5V7L12 2zm0 2.3 7 3.5-7 3.5-7-3.5 7-3.5zM4 9.4l7 3.5v7.2l-7-3.5V9.4zm9 10.7v-7.2l7-3.5v7.2l-7 3.5z"/></svg>'
}

function businessText(type) {
  return BUSINESS_TYPE[type] || type
}
function businessTag(type) {
  return BUSINESS_TYPE_TAG[type] || 'info'
}
function businessRoute(type) {
  return {
    ADOPTION_APPLICATION: '/applications',
    MEDICAL_APPOINTMENT: '/medical/appointments',
    SERVICE_BOOKING: '/care/appointments',
    PRODUCT_ORDER: '/mall/orders'
  }[type]
}
async function goBusiness(item) {
  const path = businessRoute(item.business_type)
  if (path) router.push(path)
  // 顺带将对应通知标记为已读，使工作台红点随处理推进而减少
  try {
    await markRead(item.id)
    load()
  } catch {
    /* 标记失败不影响跳转 */
  }
}
function formatTime(iso) {
  if (!iso) return ''
  const d = new Date(iso)
  const pad = (n) => String(n).padStart(2, '0')
  return `${pad(d.getMonth() + 1)}-${pad(d.getDate())} ${pad(d.getHours())}:${pad(d.getMinutes())}`
}

function go(path) {
  if (path && path !== '/') router.push(path)
}
function goNotifications() {
  ElNotification({ title: '通知中心', message: '待办通知已汇总在下方动态中，可前往对应模块处理', type: 'info' })
}

async function load() {
  try {
    const res = await getSummary()
    summary.value = res.data
  } catch (e) {
    // 错误已由请求拦截器统一提示
  }
}

function connectWs() {
  const token = localStorage.getItem('token')
  if (!token) return
  const proto = location.protocol === 'https:' ? 'wss://' : 'ws://'
  ws = new WebSocket(`${proto}${location.host}/ws/admin/notifications`)
  ws.onopen = () => {
    ws.send(JSON.stringify({ token }))
  }
  ws.onmessage = (e) => {
    try {
      const data = JSON.parse(e.data)
      if (data.event === 'NEW_BUSINESS') {
        ElNotification({
          title: data.title,
          message: `业务类型：${businessText(data.business_type)}`,
          type: 'warning',
          duration: 6000
        })
        load()
      }
    } catch {
      /* 忽略非 JSON 消息 */
    }
  }
  ws.onclose = () => {
    wsConnected.value = false
    scheduleReconnect()
  }
  ws.onerror = () => {
    ws?.close()
  }
}

function scheduleReconnect() {
  clearTimeout(reconnectTimer)
  reconnectTimer = setTimeout(connectWs, 5000)
}

onMounted(() => {
  load()
  connectWs()
  // 每 30 秒兜底刷新一次统计（WebSocket 断开时也能保持数据不过时）
  setInterval(load, 30000)
})

onUnmounted(() => {
  clearTimeout(reconnectTimer)
  ws?.close()
})
</script>

<style scoped>
.page {
  min-height: 100vh;
  background: var(--brand-paper);
}
.dashboard {
  max-width: 1200px;
  margin: 0 auto;
  padding: 28px 24px 48px;
}
.head {
  display: flex;
  align-items: flex-end;
  justify-content: space-between;
  margin-bottom: 20px;
}
.title {
  font-size: 26px;
}
.sub {
  margin: 6px 0 0;
  color: var(--el-text-color-secondary);
  font-size: 13px;
}
.head-actions {
  display: flex;
  align-items: center;
  gap: 8px;
}
.stats {
  row-gap: 16px;
}
.stat-card {
  cursor: pointer;
  transition: transform 0.15s, box-shadow 0.15s;
}
.stat-card:hover {
  transform: translateY(-3px);
  box-shadow: 0 10px 24px rgba(35, 48, 42, 0.1);
}
.stat-card :deep(.el-card__body) {
  display: flex;
  align-items: center;
  gap: 14px;
  padding: 18px;
}
.stat-icon {
  width: 46px;
  height: 46px;
  border-radius: 12px;
  display: grid;
  place-items: center;
  flex-shrink: 0;
}
.stat-value {
  font-size: 26px;
  font-weight: 700;
  line-height: 1.1;
  color: var(--brand-ink);
}
.stat-label {
  margin-top: 4px;
  font-size: 13px;
  color: var(--el-text-color-secondary);
}
.recent-card {
  margin-top: 20px;
}
.recent-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
}
.recent-title {
  font-family: var(--font-display);
  font-weight: 600;
  font-size: 16px;
}
.timeline {
  list-style: none;
  margin: 0;
  padding: 0;
}
.timeline-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px 4px;
  border-bottom: 1px dashed var(--brand-line);
  cursor: pointer;
  transition: background 0.15s;
}
.timeline-item:hover {
  background: var(--brand-paper);
}
.timeline-item:last-child {
  border-bottom: none;
}
.timeline-title {
  flex: 1;
  color: var(--brand-ink);
  font-size: 14px;
}
.timeline-time {
  color: var(--el-text-color-placeholder);
  font-size: 12px;
}
.timeline-arrow {
  color: var(--el-text-color-placeholder);
  font-size: 18px;
  line-height: 1;
}
</style>
