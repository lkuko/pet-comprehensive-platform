<template>
  <div class="page">
    <AdminHeader />
    <main class="container">
      <div class="head">
        <h2>商城资源管理</h2>
      </div>

      <el-tabs v-model="activeTab">
        <!-- 分类 -->
        <el-tab-pane label="商品分类" name="categories">
          <div class="tab-toolbar">
            <el-button type="primary" @click="openCategory()">新增分类</el-button>
          </div>
          <el-table :data="categories" v-loading="loading" stripe>
            <el-table-column prop="id" label="ID" width="70" />
            <el-table-column prop="name" label="名称" width="160" />
            <el-table-column prop="description" label="说明" min-width="240" />
            <el-table-column prop="sort" label="排序" width="80" />
            <el-table-column label="状态" width="90">
              <template #default="{ row }">
                <el-tag :type="ENABLE_STATUS_TAG[row.status] || 'info'" size="small">{{ ENABLE_STATUS[row.status] || row.status }}</el-tag>
              </template>
            </el-table-column>
            <el-table-column label="操作" width="150">
              <template #default="{ row }">
                <el-button size="small" @click="openCategory(row)">编辑</el-button>
                <el-button size="small" type="danger" @click="removeCategory(row)">删除</el-button>
              </template>
            </el-table-column>
          </el-table>
        </el-tab-pane>

        <!-- 商品 -->
        <el-tab-pane label="商品" name="products">
          <div class="tab-toolbar">
            <el-button type="primary" @click="openProduct()">新增商品</el-button>
            <el-select v-model="productCategoryFilter" placeholder="按分类筛选" clearable class="filter" @change="loadProducts">
              <el-option v-for="c in categories" :key="c.id" :label="c.name" :value="c.id" />
            </el-select>
          </div>
          <el-table :data="products" v-loading="loading" stripe>
            <el-table-column prop="id" label="ID" width="70" />
            <el-table-column prop="name" label="名称" width="180" />
            <el-table-column label="分类" width="120">
              <template #default="{ row }">{{ categoryName(row.category_id) }}</template>
            </el-table-column>
            <el-table-column label="价格" width="100">
              <template #default="{ row }">¥{{ row.price }}</template>
            </el-table-column>
            <el-table-column prop="stock" label="库存" width="90" />
            <el-table-column prop="sales" label="销量" width="90" />
            <el-table-column label="状态" width="90">
              <template #default="{ row }">
                <el-tag :type="ENABLE_STATUS_TAG[row.status] || 'info'" size="small">{{ ENABLE_STATUS[row.status] || row.status }}</el-tag>
              </template>
            </el-table-column>
            <el-table-column label="操作" width="150">
              <template #default="{ row }">
                <el-button size="small" @click="openProduct(row)">编辑</el-button>
                <el-button size="small" type="danger" @click="removeProduct(row)">删除</el-button>
              </template>
            </el-table-column>
          </el-table>
        </el-tab-pane>
      </el-tabs>
    </main>

    <!-- 分类弹窗 -->
    <el-dialog v-model="categoryVisible" :title="categoryForm.id ? '编辑分类' : '新增分类'" width="520px">
      <el-form :model="categoryForm" label-width="90px">
        <el-form-item label="名称" required><el-input v-model="categoryForm.name" maxlength="50" /></el-form-item>
        <el-form-item label="说明"><el-input v-model="categoryForm.description" type="textarea" :rows="2" /></el-form-item>
        <el-form-item label="排序"><el-input-number v-model="categoryForm.sort" :min="0" /></el-form-item>
        <el-form-item label="状态">
          <el-switch v-model="categoryForm.status" active-value="ACTIVE" inactive-value="INACTIVE" active-text="启用" inactive-text="停用" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="categoryVisible = false">取消</el-button>
        <el-button type="primary" @click="saveCategory">保存</el-button>
      </template>
    </el-dialog>

    <!-- 商品弹窗 -->
    <el-dialog v-model="productVisible" :title="productForm.id ? '编辑商品' : '新增商品'" width="520px">
      <el-form :model="productForm" label-width="90px">
        <el-form-item label="所属分类" required>
          <el-select v-model="productForm.category_id" placeholder="请选择">
            <el-option v-for="c in categories" :key="c.id" :label="c.name" :value="c.id" />
          </el-select>
        </el-form-item>
        <el-form-item label="名称" required><el-input v-model="productForm.name" maxlength="100" /></el-form-item>
        <el-form-item label="副标题"><el-input v-model="productForm.subtitle" maxlength="200" /></el-form-item>
        <el-form-item label="描述"><el-input v-model="productForm.description" type="textarea" :rows="2" /></el-form-item>
        <el-form-item label="价格">
          <el-input-number v-model="productForm.price" :min="0" :precision="2" :step="10" />
        </el-form-item>
        <el-form-item label="库存">
          <el-input-number v-model="productForm.stock" :min="0" />
        </el-form-item>
        <el-form-item label="状态">
          <el-switch v-model="productForm.status" active-value="ACTIVE" inactive-value="INACTIVE" active-text="启用" inactive-text="停用" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="productVisible = false">取消</el-button>
        <el-button type="primary" @click="saveProduct">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { onMounted, ref } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import AdminHeader from '../components/AdminHeader.vue'
import * as api from '../api/mall'
import { ENABLE_STATUS, ENABLE_STATUS_TAG } from '../utils/dict'

const activeTab = ref('categories')
const loading = ref(false)

const categories = ref([])
const products = ref([])
const productCategoryFilter = ref(null)

const categoryVisible = ref(false)
const productVisible = ref(false)
const categoryForm = ref({})
const productForm = ref({})

function categoryName(id) {
  return categories.value.find((c) => c.id === id)?.name || '—'
}

async function loadCategories() {
  loading.value = true
  try {
    categories.value = (await api.listCategories()).data
  } finally {
    loading.value = false
  }
}

async function loadProducts() {
  loading.value = true
  try {
    products.value = (await api.listProducts(productCategoryFilter.value || undefined)).data
  } finally {
    loading.value = false
  }
}

// 分类
function openCategory(row) {
  categoryForm.value = row ? { ...row } : { name: '', description: '', sort: 0, status: 'ACTIVE' }
  categoryVisible.value = true
}
async function saveCategory() {
  if (!categoryForm.value.name?.trim()) return ElMessage.warning('请填写名称')
  if (categoryForm.value.id) {
    await api.updateCategory(categoryForm.value.id, categoryForm.value)
  } else {
    await api.createCategory(categoryForm.value)
  }
  ElMessage.success('已保存')
  categoryVisible.value = false
  loadCategories()
}
async function removeCategory(row) {
  await ElMessageBox.confirm(`确定删除分类「${row.name}」吗？`, '提示', { type: 'warning' })
  await api.deleteCategory(row.id)
  ElMessage.success('已删除')
  loadCategories()
}

// 商品
function openProduct(row) {
  productForm.value = row
    ? { ...row, price: Number(row.price) }
    : { category_id: null, name: '', subtitle: '', description: '', price: 0, stock: 0, status: 'ACTIVE' }
  productVisible.value = true
}
async function saveProduct() {
  if (!productForm.value.name?.trim()) return ElMessage.warning('请填写名称')
  if (!productForm.value.category_id) return ElMessage.warning('请选择所属分类')
  if (productForm.value.id) {
    await api.updateProduct(productForm.value.id, productForm.value)
  } else {
    await api.createProduct(productForm.value)
  }
  ElMessage.success('已保存')
  productVisible.value = false
  loadProducts()
}
async function removeProduct(row) {
  await ElMessageBox.confirm(`确定删除商品「${row.name}」吗？`, '提示', { type: 'warning' })
  await api.deleteProduct(row.id)
  ElMessage.success('已删除')
  loadProducts()
}

onMounted(async () => {
  await loadCategories()
  await loadProducts()
})
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
.tab-toolbar {
  display: flex;
  gap: 12px;
  margin-bottom: 16px;
}
.filter {
  width: 180px;
}
</style>
