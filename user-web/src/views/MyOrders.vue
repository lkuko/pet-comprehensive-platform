<template>
  <div class="page">
    <AppHeader />
    <main class="container">
      <div class="head">
        <h2 class="page-title">我的订单</h2>
        <el-button text type="primary" @click="$router.push('/addresses')">收货地址</el-button>
      </div>

      <el-empty v-if="!orders.length && !loading" description="暂无订单" />
      <div v-else class="order-list">
        <el-card v-for="o in orders" :key="o.id" class="order-card" shadow="hover">
          <div class="order-head">
            <div>
              <span class="order-no">订单号：{{ o.order_no }}</span>
              <span class="order-time">{{ fmt(o.created_at) }}</span>
            </div>
            <el-tag :type="ORDER_STATUS_TAG[o.status] || 'info'" size="small">
              {{ ORDER_STATUS[o.status] || o.status }}
            </el-tag>
          </div>

          <ul class="items">
            <li v-for="it in o.items" :key="it.id" class="item">
              <span class="item-name">{{ it.product_name }}</span>
              <span class="item-qty">×{{ it.quantity }}</span>
              <span class="item-sub">¥{{ it.subtotal }}</span>
            </li>
          </ul>

          <div class="order-foot">
            <div class="addr">
              收货：{{ o.receiver_name }} {{ o.receiver_phone }} {{ o.receiver_address }}
            </div>
            <div class="foot-right">
              <span class="total">合计：<b>¥{{ o.total_amount }}</b></span>
              <template v-if="o.status === 'PENDING_PAYMENT'">
                <el-button size="small" type="primary" @click="pay(o)">去支付</el-button>
                <el-button size="small" @click="cancel(o)">取消订单</el-button>
              </template>
              <el-button v-else-if="o.status === 'SHIPPED'" size="small" type="success" @click="receipt(o)">确认收货</el-button>
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
import { listOrders, payOrder, cancelOrder, confirmReceipt } from '../api/mall'
import { ORDER_STATUS, ORDER_STATUS_TAG } from '../utils/dict'

const orders = ref([])
const loading = ref(false)

function fmt(t) {
  if (!t) return '—'
  return t.replace('T', ' ').slice(0, 16)
}

async function load() {
  loading.value = true
  try {
    orders.value = (await listOrders()).data || []
  } finally {
    loading.value = false
  }
}

async function pay(o) {
  await payOrder(o.id)
  ElMessage.success('支付成功（模拟）')
  load()
}

async function cancel(o) {
  await ElMessageBox.confirm('确定取消该订单吗？库存将自动回滚。', '提示', { type: 'warning' })
  await cancelOrder(o.id)
  ElMessage.success('已取消')
  load()
}

async function receipt(o) {
  await ElMessageBox.confirm('确认已收到商品？', '提示', { type: 'warning' })
  await confirmReceipt(o.id)
  ElMessage.success('交易完成')
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
  max-width: 900px;
  margin: 0 auto;
  padding: 24px;
}
.head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 16px;
}
.page-title {
  margin: 0;
  color: var(--brand-ink);
}
.order-list {
  display: flex;
  flex-direction: column;
  gap: 14px;
}
.order-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 12px;
}
.order-no {
  font-weight: 600;
  color: var(--brand-ink);
  margin-right: 12px;
}
.order-time {
  font-size: 12px;
  color: var(--el-text-color-secondary);
}
.items {
  list-style: none;
  margin: 0 0 12px;
  padding: 0;
  border-top: 1px solid var(--brand-line);
}
.item {
  display: flex;
  gap: 12px;
  padding: 8px 0;
  font-size: 14px;
  color: var(--el-text-color-regular);
}
.item-name {
  flex: 1;
}
.item-qty {
  width: 60px;
  text-align: center;
}
.item-sub {
  width: 90px;
  text-align: right;
  color: var(--brand-ink);
}
.order-foot {
  display: flex;
  align-items: center;
  justify-content: space-between;
}
.addr {
  font-size: 12px;
  color: var(--el-text-color-secondary);
  max-width: 60%;
}
.foot-right {
  display: flex;
  align-items: center;
  gap: 10px;
}
.total {
  color: var(--el-text-color-regular);
}
.total b {
  color: var(--brand-apricot);
  font-size: 18px;
}
</style>
