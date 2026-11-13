<template>
  <div class="page">
    <AppHeader />
    <main class="container">
      <div class="head">
        <h2>我的宠物</h2>
        <el-button type="primary" @click="openCreate">+ 新增宠物</el-button>
      </div>

      <div v-loading="loading" class="list">
        <el-card v-for="pet in list" :key="pet.id" class="pet-item">
          <div class="pet-main">
            <el-image v-if="pet.avatar_url" :src="pet.avatar_url" fit="cover" class="avatar" />
            <div v-else class="avatar placeholder">🐾</div>
            <div class="pet-info">
              <div class="name-row">
                <span class="name">{{ pet.name }}</span>
                <el-tag size="small">{{ SPECIES[pet.category] || pet.category }}</el-tag>
                <el-tag v-if="pet.status === 'INACTIVE'" size="small" type="info">已停用</el-tag>
              </div>
              <div class="meta">
                {{ GENDER[pet.gender] }}
                <span v-if="pet.breed"> · {{ pet.breed }}</span>
                <span v-if="pet.weight != null"> · {{ pet.weight }} kg</span>
                <span v-if="pet.is_neutered"> · 已绝育</span>
              </div>
              <div v-if="pet.health_note" class="note">{{ pet.health_note }}</div>
            </div>
          </div>
          <div class="ops">
            <el-button size="small" @click="openEdit(pet)">编辑</el-button>
            <el-button size="small" type="danger" @click="onDelete(pet)">删除</el-button>
          </div>
        </el-card>
        <el-empty v-if="!loading && list.length === 0" description="还没有宠物档案，点击右上角新增" />
      </div>
    </main>

    <el-dialog v-model="dialogVisible" :title="isEdit ? '编辑宠物' : '新增宠物'" width="520px">
      <el-form :model="form" label-width="90px">
        <el-form-item label="名字" required>
          <el-input v-model="form.name" placeholder="宠物名字" />
        </el-form-item>
        <el-form-item label="类别">
          <el-select v-model="form.category" style="width: 100%">
            <el-option v-for="(v, k) in SPECIES" :key="k" :label="v" :value="k" />
          </el-select>
        </el-form-item>
        <el-form-item label="品种">
          <el-input v-model="form.breed" placeholder="如：金毛、英短" />
        </el-form-item>
        <el-form-item label="性别">
          <el-radio-group v-model="form.gender">
            <el-radio v-for="(v, k) in GENDER" :key="k" :value="k">{{ v }}</el-radio>
          </el-radio-group>
        </el-form-item>
        <el-form-item label="出生日期">
          <el-date-picker v-model="form.birthday" type="date" value-format="YYYY-MM-DD" style="width: 100%" />
        </el-form-item>
        <el-form-item label="体重(kg)">
          <el-input-number v-model="form.weight" :min="0" :precision="1" :step="0.5" style="width: 100%" />
        </el-form-item>
        <el-form-item label="头像">
          <div class="avatar-upload">
            <el-input v-model="form.avatar_url" placeholder="头像 URL 或点击上传" />
            <el-button :loading="uploading" @click="pickAvatar">上传</el-button>
            <input ref="avatarInput" type="file" accept="image/*" style="display: none" @change="onAvatarPicked" />
          </div>
        </el-form-item>
        <el-form-item label="健康说明">
          <el-input v-model="form.health_note" type="textarea" :rows="2" placeholder="疫苗、病史等" />
        </el-form-item>
        <el-form-item label="已绝育">
          <el-switch v-model="form.is_neutered" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="saving" @click="save">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { onMounted, reactive, ref } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import AppHeader from '../components/AppHeader.vue'
import { listPets, createPet, updatePet, deletePet } from '../api/pets'
import { uploadImage } from '../api/upload'
import { GENDER, SPECIES } from '../utils/dict'

const list = ref([])
const loading = ref(false)
const dialogVisible = ref(false)
const isEdit = ref(false)
const saving = ref(false)
const uploading = ref(false)
const editId = ref(null)
const avatarInput = ref(null)

const emptyForm = () => ({
  name: '',
  category: 'DOG',
  breed: '',
  gender: 'UNKNOWN',
  birthday: null,
  weight: null,
  avatar_url: '',
  health_note: '',
  is_neutered: false
})
const form = reactive(emptyForm())

async function load() {
  loading.value = true
  try {
    list.value = (await listPets()).data || []
  } finally {
    loading.value = false
  }
}

function openCreate() {
  isEdit.value = false
  editId.value = null
  Object.assign(form, emptyForm())
  dialogVisible.value = true
}

function openEdit(pet) {
  isEdit.value = true
  editId.value = pet.id
  Object.assign(form, {
    name: pet.name,
    category: pet.category,
    breed: pet.breed || '',
    gender: pet.gender,
    birthday: pet.birthday,
    weight: pet.weight,
    avatar_url: pet.avatar_url || '',
    health_note: pet.health_note || '',
    is_neutered: pet.is_neutered
  })
  dialogVisible.value = true
}

async function save() {
  if (!form.name) {
    ElMessage.warning('请填写宠物名字')
    return
  }
  saving.value = true
  try {
    const payload = { ...form }
    if (!payload.birthday) delete payload.birthday
    if (payload.weight == null) delete payload.weight
    if (isEdit.value) {
      await updatePet(editId.value, payload)
    } else {
      await createPet(payload)
    }
    ElMessage.success('保存成功')
    dialogVisible.value = false
    load()
  } finally {
    saving.value = false
  }
}

async function onDelete(pet) {
  await ElMessageBox.confirm(`确定删除「${pet.name}」吗？删除后将停用该档案。`, '提示', { type: 'warning' })
  await deletePet(pet.id)
  ElMessage.success('已删除')
  load()
}

function pickAvatar() {
  avatarInput.value?.click()
}

async function onAvatarPicked(e) {
  const file = e.target.files[0]
  if (!file) return
  uploading.value = true
  try {
    const res = await uploadImage(file, 'avatars')
    form.avatar_url = res.data.url
    ElMessage.success('头像上传成功')
  } finally {
    uploading.value = false
    e.target.value = ''
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
  max-width: 900px;
  margin: 0 auto;
  padding: 24px;
}
.head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 20px;
}
.head h2 {
  margin: 0;
}
.list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}
.pet-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
}
.pet-main {
  display: flex;
  gap: 16px;
  align-items: center;
}
.avatar {
  width: 64px;
  height: 64px;
  border-radius: 8px;
  background: #eef2f7;
  flex-shrink: 0;
}
.avatar.placeholder {
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 28px;
  color: #c0c4cc;
}
.name-row {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 6px;
}
.name {
  font-size: 16px;
  font-weight: 600;
}
.meta {
  font-size: 13px;
  color: #909399;
}
.note {
  font-size: 13px;
  color: #606266;
  margin-top: 4px;
}
.ops {
  flex-shrink: 0;
}
.avatar-upload {
  display: flex;
  gap: 8px;
  width: 100%;
}
.avatar-upload .el-input {
  flex: 1;
}
</style>
