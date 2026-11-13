<template>
  <div class="page">
    <AdminHeader />
    <main class="container">
      <div class="head">
        <h2>商城订单处理</h2>
      </div>

      <div class="toolbar">
        <el-input v-model="keyword" placeholder="搜索订单号/收货人/电话" clearable class="search" @keyup.enter="search" />
        <el-select v-model="statusFilter" placeholder="全部状态" clearable class="status" @change="search">
          <el-option v-for="(v, k) in ORDER_STATUS" :key="k" :label="v" :value="k" />
        </el-select>
        <el-button type="primary" @click="search">查询</el-button>
      </div>

      <el-table :data="list" v-loading="loading" stripe>
        <el-table-column prop="order_no" label="订单号" width="200" />
        <el-table-column prop="user_nickname" label="用户" width="100" />
        <el-table-column label="商品" min-width="200">
          <template #default="{ row }">{{ row.items.map((i) => `${i.product_name}×${i.quantity}`).join('、') }}</template>
        </el-table-column>
        <el-table-column label="金额" width="100">
          <template #default="{ row }">¥{{ row.total_amount }}</template>
        </el-table-column>
        <el-table-column prop="receiver_phone" label="联系电话" width="130" />
        <el-table-column label="状态" width="90">
          <template #default="{ row }">
            <el-tag :type="ORDER_STATUS_TAG[row.status] || 'info'" size="small">
              {{ ORDER_STATUS[row.status] || row.status }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="操作" min-width="180">
          <template #default="{ row }">
            <el-button size="small" @click="openDetail(row)">详情</el-button>
            <el-button v-if="row.status === 'PAID'" size="small" type="primary" @click="ship(row)">发货</el-button>
            <el-button v-if="row.status === 'SHIPPED'" size="small" type="success" @click="complete(row)">完成</el-button>
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
    <el-dialog v-model="detailVisible" title="订单详情" width="560px">
      <template v-if="current">
        <el-descriptions :column="1" border>
          <el-descriptions-item label="订单号">{{ current.order_no }}</el-descriptions-item>
          <el-descriptions-item label="用户">{{ current.user_nickname }}</el-descriptions-item>
          <el-descriptions-item label="状态">
            <el-tag :type="ORDER_STATUS_TAG[current.status] || 'info'" size="small">
              {{ ORDER_STATUS[current.status] || current.status }}
            </el-tag>
          </el-descriptions-item>
          <el-descriptions-item label="收货信息">
            {{ current.receiver_name }} {{ current.receiver_phone }} {{ current.receiver_address }}
          </el-descriptions-item>
          <el-descriptions-item label="备注">{{ current.remark || '—' }}</el-descriptions-item>
          <el-descriptions-item label="下单时间">{{ fmt(current.created_at) }}</el-descriptions-item>
          <el-descriptions-item label="商品明细">
            <div v-for="it in current.items" :key="it.id" class="detail-item">
              {{ it.product_name }} ×{{ it.quantity }} — ¥{{ it.subtotal }}
            </div>
          </el-descriptions-item>
          <el-descriptions-item label="订单总额">¥{{ current.total_amount }}</el-descriptions-item>
        </el-descriptions>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { onMounted, ref } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import AdminHeader from '../components/AdminHeader.vue'
import { listOrders, shipOrder, completeOrder } from '../api/mall'
import { ORDER_STATUS, ORDER_STATUS_TAG } from '../utils/dict'

const list = ref([])
const total = ref(0)
const page = ref(1)
const pageSize = ref(10)
const keyword = ref('')
const statusFilter = ref('')
const loading = ref(false)

const detailVisible = ref(false)
const current = ref(null)

function fmt(t) {
  if (!t) return '—'
  return t.replace('T', ' ').slice(0, 16)
}

async function load() {
  loading.value = true
  try {
    const res = await listOrders({
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

async function ship(row) {
  await ElMessageBox.confirm(`确定对订单「${row.order_no}」发货吗？`, '发货', { type: 'warning' })
  await shipOrder(row.id)
  ElMessage.success('已发货')
  load()
}

async function complete(row) {
  await ElMessageBox.confirm(`确定将订单「${row.order_no}」标记为完成吗？`, '完成订单', { type: 'warning' })
  await completeOrder(row.id)
  ElMessage.success('已完成')
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
.detail-item {
  padding: 2px 0;
}
</style>
