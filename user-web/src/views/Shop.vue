<template>
  <div class="page">
    <AppHeader />
    <main class="container">
      <h2 class="page-title">宠物商城</h2>

      <div class="toolbar">
        <el-radio-group v-model="categoryId" @change="search">
          <el-radio-button :value="null">全部</el-radio-button>
          <el-radio-button v-for="c in categories" :key="c.id" :value="c.id">{{ c.name }}</el-radio-button>
        </el-radio-group>
        <el-input v-model="keyword" placeholder="搜索商品" clearable class="search" @keyup.enter="search" />
        <el-button type="primary" @click="search">查询</el-button>
      </div>

      <div class="layout">
        <!-- 商品列表 -->
        <section class="products">
          <el-empty v-if="!products.length && !loading" description="暂无商品" />
          <div v-else class="grid">
            <el-card v-for="p in products" :key="p.id" class="product-card" shadow="hover">
              <div class="cover">{{ p.cover_image ? '' : '🐾' }}</div>
              <div class="p-name">{{ p.name }}</div>
              <div class="p-subtitle">{{ p.subtitle || '—' }}</div>
              <div class="p-meta">
                <span class="p-price">¥{{ p.price }}</span>
                <span class="p-stock">库存 {{ p.stock }}</span>
              </div>
              <el-button
                type="primary"
                class="add-btn"
                :disabled="p.stock <= 0"
                @click="add(p)"
              >{{ p.stock > 0 ? '加入购物车' : '已售罄' }}</el-button>
            </el-card>
          </div>
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
        </section>

        <!-- 购物车 -->
        <aside class="cart">
          <div class="cart-head">
            <span>购物车</span>
            <el-button v-if="cart.length" size="small" text type="danger" @click="clear">清空</el-button>
          </div>
          <el-empty v-if="!cart.length" description="购物车为空" :image-size="60" />
          <ul v-else class="cart-list">
            <li v-for="item in cart" :key="item.product_id" class="cart-item">
              <div class="ci-name">{{ item.name }}</div>
              <div class="ci-price">¥{{ item.price }}</div>
              <div class="ci-ops">
                <el-input-number
                  :model-value="item.quantity"
                  :min="1"
                  :max="item.stock"
                  size="small"
                  @change="(v) => changeQty(item, v)"
                />
                <el-button size="small" text type="danger" @click="removeItem(item)">删除</el-button>
              </div>
            </li>
          </ul>
          <div v-if="cart.length" class="cart-foot">
            <div class="cf-total">合计：<span class="cf-amount">¥{{ cartTotal }}</span></div>
            <el-button type="primary" class="checkout-btn" @click="openCheckout">去结算</el-button>
          </div>
        </aside>
      </div>
    </main>

    <!-- 结算弹窗 -->
    <el-dialog v-model="checkoutVisible" title="确认订单" width="520px">
      <el-form :model="receiver" label-width="90px">
        <el-form-item label="收货人" required><el-input v-model="receiver.receiver_name" maxlength="50" /></el-form-item>
        <el-form-item label="联系电话" required><el-input v-model="receiver.receiver_phone" maxlength="20" /></el-form-item>
        <el-form-item label="收货地址" required><el-input v-model="receiver.receiver_address" type="textarea" :rows="2" maxlength="200" /></el-form-item>
        <el-form-item label="备注"><el-input v-model="receiver.remark" type="textarea" :rows="2" placeholder="选填" /></el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="checkoutVisible = false">取消</el-button>
        <el-button type="primary" :loading="submitting" @click="submitCheckout">提交订单（¥{{ cartTotal }}）</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import AppHeader from '../components/AppHeader.vue'
import { listCategories, listProducts, listCart, addToCart, updateCartItem, removeCartItem, clearCart, checkout } from '../api/mall'

const router = useRouter()

const categories = ref([])
const products = ref([])
const total = ref(0)
const page = ref(1)
const pageSize = ref(12)
const categoryId = ref(null)
const keyword = ref('')
const loading = ref(false)

const cart = ref([])
const checkoutVisible = ref(false)
const submitting = ref(false)
const receiver = ref({ receiver_name: '', receiver_phone: '', receiver_address: '', remark: '' })

const cartTotal = computed(() => cart.value.reduce((s, i) => s + Number(i.subtotal || 0), 0).toFixed(2))

async function loadProducts() {
  loading.value = true
  try {
    const res = await listProducts({
      page: page.value,
      page_size: pageSize.value,
      category_id: categoryId.value || undefined,
      keyword: keyword.value || undefined
    })
    products.value = res.data.items || []
    total.value = res.data.total || 0
  } finally {
    loading.value = false
  }
}

async function loadCart() {
  cart.value = (await listCart()).data || []
}

function search() {
  page.value = 1
  loadProducts()
}

function onPageChange(p) {
  page.value = p
  loadProducts()
}

async function add(p) {
  await addToCart({ product_id: p.id, quantity: 1 })
  ElMessage.success('已加入购物车')
  loadCart()
}

async function changeQty(item, v) {
  await updateCartItem(item.product_id, v)
  loadCart()
}

async function removeItem(item) {
  await removeCartItem(item.product_id)
  loadCart()
}

async function clear() {
  await ElMessageBox.confirm('确定清空购物车吗？', '提示', { type: 'warning' })
  await clearCart()
  loadCart()
}

function openCheckout() {
  if (!cart.value.length) return ElMessage.warning('购物车为空')
  checkoutVisible.value = true
}

async function submitCheckout() {
  if (!receiver.value.receiver_name.trim()) return ElMessage.warning('请填写收货人')
  if (!receiver.value.receiver_phone.trim()) return ElMessage.warning('请填写联系电话')
  if (!receiver.value.receiver_address.trim()) return ElMessage.warning('请填写收货地址')
  submitting.value = true
  try {
    await checkout({
      receiver_name: receiver.value.receiver_name.trim(),
      receiver_phone: receiver.value.receiver_phone.trim(),
      receiver_address: receiver.value.receiver_address.trim(),
      remark: receiver.value.remark || null
    })
    ElMessage.success('下单成功，请尽快支付')
    checkoutVisible.value = false
    router.push('/orders')
  } finally {
    submitting.value = false
  }
}

onMounted(async () => {
  categories.value = (await listCategories()).data
  await loadProducts()
  await loadCart()
})
</script>

<style scoped>
.page {
  min-height: 100vh;
  background: #f5f7fa;
}
.container {
  max-width: 1200px;
  margin: 0 auto;
  padding: 24px;
}
.page-title {
  margin: 0 0 16px;
  color: #303133;
}
.toolbar {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 16px;
}
.search {
  width: 240px;
  margin-left: auto;
}
.layout {
  display: flex;
  gap: 16px;
  align-items: flex-start;
}
.products {
  flex: 1;
  min-width: 0;
}
.grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
  gap: 14px;
}
.product-card {
  text-align: center;
}
.cover {
  height: 90px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 40px;
  background: #f5f7fa;
  border-radius: 6px;
  margin-bottom: 10px;
}
.p-name {
  font-weight: 600;
  color: #303133;
  margin-bottom: 4px;
}
.p-subtitle {
  font-size: 12px;
  color: #909399;
  min-height: 18px;
  margin-bottom: 8px;
}
.p-meta {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 10px;
}
.p-price {
  color: #f56c6c;
  font-size: 18px;
  font-weight: 700;
}
.p-stock {
  font-size: 12px;
  color: #909399;
}
.add-btn {
  width: 100%;
}
.pager {
  display: flex;
  justify-content: center;
  margin-top: 16px;
}

.cart {
  width: 320px;
  flex-shrink: 0;
  background: #fff;
  border-radius: 8px;
  padding: 16px;
  position: sticky;
  top: 16px;
}
.cart-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  font-weight: 600;
  color: #303133;
  margin-bottom: 12px;
}
.cart-list {
  list-style: none;
  margin: 0;
  padding: 0;
  max-height: 480px;
  overflow-y: auto;
}
.cart-item {
  padding: 10px 0;
  border-bottom: 1px solid #f0f2f5;
}
.ci-name {
  font-size: 14px;
  color: #303133;
  margin-bottom: 4px;
}
.ci-price {
  color: #f56c6c;
  font-size: 14px;
  margin-bottom: 6px;
}
.ci-ops {
  display: flex;
  align-items: center;
  justify-content: space-between;
}
.cart-foot {
  margin-top: 12px;
}
.cf-total {
  text-align: right;
  color: #606266;
  margin-bottom: 10px;
}
.cf-amount {
  color: #f56c6c;
  font-size: 20px;
  font-weight: 700;
}
.checkout-btn {
  width: 100%;
}
</style>
