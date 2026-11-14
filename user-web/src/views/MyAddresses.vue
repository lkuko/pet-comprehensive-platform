<template>
  <div class="page">
    <AppHeader />
    <main class="container">
      <div class="head">
        <h2 class="page-title">收货地址</h2>
        <el-button type="primary" @click="openCreate">新增地址</el-button>
      </div>

      <el-empty v-if="!list.length && !loading" description="暂无地址" />
      <div v-else class="addr-list">
        <el-card v-for="a in list" :key="a.id" class="addr-card" shadow="hover">
          <div class="addr-main">
            <div class="addr-line1">
              <span class="name">{{ a.receiver_name }}</span>
              <span class="phone">{{ a.receiver_phone }}</span>
              <el-tag v-if="a.is_default" size="small" type="success">默认</el-tag>
            </div>
            <div class="addr-detail">{{ fullAddress(a) }}</div>
          </div>
          <div class="addr-ops">
            <el-button v-if="!a.is_default" size="small" text type="primary" @click="setDefault(a)">设为默认</el-button>
            <el-button size="small" text @click="openEdit(a)">编辑</el-button>
            <el-button size="small" text type="danger" @click="remove(a)">删除</el-button>
          </div>
        </el-card>
      </div>
    </main>

    <el-dialog v-model="dialogVisible" :title="editingId ? '编辑地址' : '新增地址'" width="520px">
      <el-form :model="form" label-width="90px">
        <el-form-item label="收货人" required><el-input v-model="form.receiver_name" maxlength="50" /></el-form-item>
        <el-form-item label="联系电话" required><el-input v-model="form.receiver_phone" maxlength="20" /></el-form-item>
        <el-form-item label="省 / 市 / 区">
          <div class="region">
            <el-input v-model="form.province" placeholder="省" maxlength="50" />
            <el-input v-model="form.city" placeholder="市" maxlength="50" />
            <el-input v-model="form.district" placeholder="区 / 县" maxlength="50" />
          </div>
        </el-form-item>
        <el-form-item label="详细地址" required><el-input v-model="form.detail_address" type="textarea" :rows="2" maxlength="200" /></el-form-item>
        <el-form-item label="设为默认"><el-switch v-model="form.is_default" /></el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="saving" @click="save">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { onMounted, ref } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import AppHeader from '../components/AppHeader.vue'
import { listAddresses, createAddress, updateAddress, deleteAddress, setDefaultAddress } from '../api/mall'

const list = ref([])
const loading = ref(false)
const dialogVisible = ref(false)
const editingId = ref(null)
const saving = ref(false)
const form = ref(emptyForm())

function emptyForm() {
  return {
    receiver_name: '',
    receiver_phone: '',
    province: '',
    city: '',
    district: '',
    detail_address: '',
    is_default: false
  }
}

function fullAddress(a) {
  return [a.province, a.city, a.district, a.detail_address].filter(Boolean).join(' ')
}

async function load() {
  loading.value = true
  try {
    list.value = (await listAddresses()).data || []
  } finally {
    loading.value = false
  }
}

function openCreate() {
  editingId.value = null
  form.value = emptyForm()
  dialogVisible.value = true
}

function openEdit(a) {
  editingId.value = a.id
  form.value = {
    receiver_name: a.receiver_name,
    receiver_phone: a.receiver_phone,
    province: a.province || '',
    city: a.city || '',
    district: a.district || '',
    detail_address: a.detail_address,
    is_default: a.is_default
  }
  dialogVisible.value = true
}

async function save() {
  if (!form.value.receiver_name.trim()) return ElMessage.warning('请填写收货人')
  if (!form.value.receiver_phone.trim()) return ElMessage.warning('请填写联系电话')
  if (!form.value.detail_address.trim()) return ElMessage.warning('请填写详细地址')
  saving.value = true
  try {
    const payload = {
      receiver_name: form.value.receiver_name.trim(),
      receiver_phone: form.value.receiver_phone.trim(),
      province: form.value.province.trim() || null,
      city: form.value.city.trim() || null,
      district: form.value.district.trim() || null,
      detail_address: form.value.detail_address.trim(),
      is_default: form.value.is_default
    }
    if (editingId.value) {
      await updateAddress(editingId.value, payload)
    } else {
      await createAddress(payload)
    }
    ElMessage.success('已保存')
    dialogVisible.value = false
    load()
  } finally {
    saving.value = false
  }
}

async function setDefault(a) {
  await setDefaultAddress(a.id)
  ElMessage.success('已设为默认')
  load()
}

async function remove(a) {
  await ElMessageBox.confirm('确定删除该地址吗？', '提示', { type: 'warning' })
  await deleteAddress(a.id)
  ElMessage.success('已删除')
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
  max-width: 800px;
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
.addr-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}
.addr-card :deep(.el-card__body) {
  display: flex;
  align-items: center;
  justify-content: space-between;
}
.addr-line1 {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 6px;
}
.name {
  font-weight: 600;
  color: var(--brand-ink);
}
.phone {
  color: var(--el-text-color-regular);
}
.addr-detail {
  color: var(--el-text-color-regular);
  font-size: 14px;
}
.addr-ops {
  flex-shrink: 0;
  display: flex;
  align-items: center;
}
.region {
  display: flex;
  gap: 8px;
  width: 100%;
}
</style>
