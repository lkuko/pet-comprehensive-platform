<template>
  <div class="page">
    <AdminHeader />
    <main class="container">
      <div class="head">
        <h2>洗护寄养资源管理</h2>
      </div>

      <el-tabs v-model="activeTab">
        <!-- 分类 -->
        <el-tab-pane label="服务分类" name="categories">
          <div class="tab-toolbar">
            <el-button type="primary" @click="openCategory()">新增分类</el-button>
          </div>
          <el-table :data="categories" v-loading="loading" stripe>
            <el-table-column prop="id" label="ID" width="70" />
            <el-table-column prop="name" label="名称" width="140" />
            <el-table-column label="类型" width="120">
              <template #default="{ row }">
                <el-tag :type="row.service_type === 'BOARDING' ? 'success' : 'primary'" size="small">
                  {{ SERVICE_TYPE[row.service_type] || row.service_type }}
                </el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="description" label="说明" min-width="240" />
            <el-table-column prop="sort" label="排序" width="80" />
            <el-table-column label="状态" width="80">
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

        <!-- 套餐 -->
        <el-tab-pane label="服务套餐" name="packages">
          <div class="tab-toolbar">
            <el-button type="primary" @click="openPackage()">新增套餐</el-button>
            <el-select v-model="packageCategoryFilter" placeholder="按分类筛选" clearable class="filter" @change="loadPackages">
              <el-option v-for="c in categories" :key="c.id" :label="c.name" :value="c.id" />
            </el-select>
          </div>
          <el-table :data="packages" v-loading="loading" stripe>
            <el-table-column prop="id" label="ID" width="70" />
            <el-table-column prop="name" label="名称" width="150" />
            <el-table-column label="所属分类" width="140">
              <template #default="{ row }">{{ categoryName(row.category_id) }}</template>
            </el-table-column>
            <el-table-column prop="description" label="说明" min-width="240" />
            <el-table-column label="价格" width="100">
              <template #default="{ row }">¥{{ row.price }}</template>
            </el-table-column>
            <el-table-column label="时长(分)" width="90">
              <template #default="{ row }">{{ row.duration_minutes > 0 ? row.duration_minutes : '按天' }}</template>
            </el-table-column>
            <el-table-column label="状态" width="80">
              <template #default="{ row }">
                <el-tag :type="ENABLE_STATUS_TAG[row.status] || 'info'" size="small">{{ ENABLE_STATUS[row.status] || row.status }}</el-tag>
              </template>
            </el-table-column>
            <el-table-column label="操作" width="150">
              <template #default="{ row }">
                <el-button size="small" @click="openPackage(row)">编辑</el-button>
                <el-button size="small" type="danger" @click="removePackage(row)">删除</el-button>
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
        <el-form-item label="类型" required>
          <el-radio-group v-model="categoryForm.service_type">
            <el-radio-button value="GROOMING">洗护美容</el-radio-button>
            <el-radio-button value="BOARDING">寄养</el-radio-button>
          </el-radio-group>
        </el-form-item>
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

    <!-- 套餐弹窗 -->
    <el-dialog v-model="packageVisible" :title="packageForm.id ? '编辑套餐' : '新增套餐'" width="520px">
      <el-form :model="packageForm" label-width="90px">
        <el-form-item label="所属分类" required>
          <el-select v-model="packageForm.category_id" placeholder="请选择">
            <el-option v-for="c in categories" :key="c.id" :label="c.name" :value="c.id" />
          </el-select>
        </el-form-item>
        <el-form-item label="名称" required><el-input v-model="packageForm.name" maxlength="50" /></el-form-item>
        <el-form-item label="说明"><el-input v-model="packageForm.description" type="textarea" :rows="2" /></el-form-item>
        <el-form-item label="价格">
          <el-input-number v-model="packageForm.price" :min="0" :precision="2" :step="10" />
        </el-form-item>
        <el-form-item label="时长(分)">
          <el-input-number v-model="packageForm.duration_minutes" :min="0" />
          <div class="form-hint">寄养套餐填 0 表示按天计费</div>
        </el-form-item>
        <el-form-item label="状态">
          <el-switch v-model="packageForm.status" active-value="ACTIVE" inactive-value="INACTIVE" active-text="启用" inactive-text="停用" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="packageVisible = false">取消</el-button>
        <el-button type="primary" @click="savePackage">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { onMounted, ref } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import AdminHeader from '../components/AdminHeader.vue'
import * as api from '../api/care'
import { SERVICE_TYPE, ENABLE_STATUS, ENABLE_STATUS_TAG } from '../utils/dict'

const activeTab = ref('categories')
const loading = ref(false)

const categories = ref([])
const packages = ref([])
const packageCategoryFilter = ref(null)

const categoryVisible = ref(false)
const packageVisible = ref(false)
const categoryForm = ref({})
const packageForm = ref({})

function categoryName(id) {
  return categories.value.find((c) => c.id === id)?.name || '—'
}

async function loadAll() {
  loading.value = true
  try {
    categories.value = (await api.listCategories()).data
  } finally {
    loading.value = false
  }
}

async function loadPackages() {
  loading.value = true
  try {
    const res = await api.listPackages(packageCategoryFilter.value || undefined)
    packages.value = res.data
  } finally {
    loading.value = false
  }
}

// 分类
function openCategory(row) {
  categoryForm.value = row
    ? { ...row }
    : { name: '', service_type: 'GROOMING', description: '', sort: 0, status: 'ACTIVE' }
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
  loadAll()
}
async function removeCategory(row) {
  await ElMessageBox.confirm(`确定删除分类「${row.name}」吗？`, '提示', { type: 'warning' })
  await api.deleteCategory(row.id)
  ElMessage.success('已删除')
  loadAll()
}

// 套餐
function openPackage(row) {
  packageForm.value = row
    ? { ...row, price: Number(row.price) }
    : { category_id: null, name: '', description: '', price: 0, duration_minutes: 60, status: 'ACTIVE' }
  packageVisible.value = true
}
async function savePackage() {
  if (!packageForm.value.name?.trim()) return ElMessage.warning('请填写名称')
  if (!packageForm.value.category_id) return ElMessage.warning('请选择所属分类')
  if (packageForm.value.id) {
    await api.updatePackage(packageForm.value.id, packageForm.value)
  } else {
    await api.createPackage(packageForm.value)
  }
  ElMessage.success('已保存')
  packageVisible.value = false
  loadPackages()
}
async function removePackage(row) {
  await ElMessageBox.confirm(`确定删除套餐「${row.name}」吗？`, '提示', { type: 'warning' })
  await api.deletePackage(row.id)
  ElMessage.success('已删除')
  loadPackages()
}

onMounted(async () => {
  await loadAll()
  await loadPackages()
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
.tab-toolbar {
  display: flex;
  gap: 12px;
  margin-bottom: 16px;
}
.filter {
  width: 180px;
}
.form-hint {
  font-size: 12px;
  color: var(--el-text-color-secondary);
  line-height: 1.4;
}
</style>
