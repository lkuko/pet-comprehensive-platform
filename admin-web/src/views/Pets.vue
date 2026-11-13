<template>
  <div class="page">
    <AdminHeader />
    <main class="container">
      <div class="head">
        <h2>领养宠物管理</h2>
        <el-button type="primary" @click="openCreate">+ 新增宠物</el-button>
      </div>

      <div class="toolbar">
        <el-input v-model="keyword" placeholder="搜索名字或品种" clearable class="search" @keyup.enter="search" />
        <el-select v-model="statusFilter" placeholder="全部状态" clearable class="status" @change="search">
          <el-option v-for="(v, k) in ADOPT_STATUS" :key="k" :label="v" :value="k" />
        </el-select>
        <el-button type="primary" @click="search">查询</el-button>
      </div>

      <el-table :data="list" v-loading="loading" stripe>
        <el-table-column label="封面" width="90">
          <template #default="{ row }">
            <el-image v-if="row.cover_url" :src="row.cover_url" fit="cover" class="cover" />
            <div v-else class="cover placeholder">🐾</div>
          </template>
        </el-table-column>
        <el-table-column prop="name" label="名称" width="120" />
        <el-table-column label="分类" width="90">
          <template #default="{ row }">{{ row.category_name }}</template>
        </el-table-column>
        <el-table-column prop="breed" label="品种" width="120" />
        <el-table-column label="性别" width="70">
          <template #default="{ row }">{{ GENDER[row.gender] }}</template>
        </el-table-column>
        <el-table-column prop="region" label="地区" width="110" />
        <el-table-column label="状态" width="100">
          <template #default="{ row }">
            <el-tag :type="ADOPT_STATUS_TAG[row.status] || 'info'" size="small">
              {{ ADOPT_STATUS[row.status] || row.status }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="操作" min-width="220">
          <template #default="{ row }">
            <el-button size="small" @click="openEdit(row)">编辑</el-button>
            <el-button
              v-if="row.status === 'AVAILABLE'"
              size="small"
              type="warning"
              @click="setStatus(row, 'OFFLINE')"
            >下架</el-button>
            <el-button
              v-else-if="row.status !== 'ADOPTED'"
              size="small"
              type="success"
              @click="setStatus(row, 'AVAILABLE')"
            >上架</el-button>
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

    <el-dialog v-model="dialogVisible" :title="isEdit ? '编辑宠物' : '新增宠物'" width="720px">
      <el-form :model="form" label-width="100px">
        <el-row :gutter="12">
          <el-col :span="12">
            <el-form-item label="名称" required>
              <el-input v-model="form.name" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="分类" required>
              <el-select v-model="form.category_id" style="width: 100%">
                <el-option v-for="c in categories" :key="c.id" :label="c.name" :value="c.id" />
              </el-select>
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="品种">
              <el-input v-model="form.breed" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="性别">
              <el-radio-group v-model="form.gender">
                <el-radio v-for="(v, k) in GENDER" :key="k" :value="k">{{ v }}</el-radio>
              </el-radio-group>
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="年龄(月)">
              <el-input-number v-model="form.age_months" :min="0" style="width: 100%" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="体重(kg)">
              <el-input-number v-model="form.weight" :min="0" :precision="1" :step="0.5" style="width: 100%" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="健康状态">
              <el-input v-model="form.health_status" placeholder="如：健康、已驱虫" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="地区">
              <el-input v-model="form.region" placeholder="如：北京" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="疫苗/绝育">
              <el-checkbox v-model="form.vaccinated">已完成疫苗</el-checkbox>
              <el-checkbox v-model="form.neutered">已绝育</el-checkbox>
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="状态">
              <el-select v-model="form.status" style="width: 100%">
                <el-option v-for="(v, k) in ADOPT_STATUS" :key="k" :label="v" :value="k" />
              </el-select>
            </el-form-item>
          </el-col>
        </el-row>
        <el-form-item label="性格特点">
          <el-input v-model="form.personality" type="textarea" :rows="2" />
        </el-form-item>
        <el-form-item label="领养要求">
          <el-input v-model="form.adoption_requirements" type="textarea" :rows="2" />
        </el-form-item>
        <el-form-item label="详细介绍">
          <el-input v-model="form.description" type="textarea" :rows="3" />
        </el-form-item>
        <el-form-item label="图片">
          <div class="images">
            <div v-for="(img, i) in form.images" :key="i" class="img-item">
              <img :src="img" />
              <span class="img-del" @click="removeImage(i)">×</span>
            </div>
            <div class="img-add" @click="pickImage">
              <span v-if="uploading">上传中…</span>
              <span v-else>+ 上传</span>
            </div>
            <input ref="imageInput" type="file" accept="image/*" multiple style="display: none" @change="onImagesPicked" />
          </div>
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
import { ElMessage } from 'element-plus'
import AdminHeader from '../components/AdminHeader.vue'
import { listPets, getPet, createPet, updatePet, updateStatus, listCategories } from '../api/adoption'
import { uploadImage } from '../api/upload'
import { GENDER, ADOPT_STATUS, ADOPT_STATUS_TAG } from '../utils/dict'

const list = ref([])
const categories = ref([])
const total = ref(0)
const page = ref(1)
const pageSize = ref(10)
const keyword = ref('')
const statusFilter = ref('')
const loading = ref(false)

const dialogVisible = ref(false)
const isEdit = ref(false)
const saving = ref(false)
const uploading = ref(false)
const editId = ref(null)
const imageInput = ref(null)

const emptyForm = () => ({
  name: '',
  category_id: null,
  breed: '',
  gender: 'UNKNOWN',
  age_months: null,
  weight: null,
  health_status: '',
  vaccinated: false,
  neutered: false,
  personality: '',
  adoption_requirements: '',
  region: '',
  description: '',
  status: 'DRAFT',
  images: []
})
const form = reactive(emptyForm())

async function load() {
  loading.value = true
  try {
    const res = await listPets({
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

async function loadCategories() {
  try {
    categories.value = (await listCategories()).data || []
  } catch {}
}

function openCreate() {
  isEdit.value = false
  editId.value = null
  Object.assign(form, emptyForm())
  if (categories.value.length) form.category_id = categories.value[0].id
  dialogVisible.value = true
}

async function openEdit(row) {
  isEdit.value = true
  editId.value = row.id
  const detail = (await getPet(row.id)).data
  Object.assign(form, {
    name: detail.name,
    category_id: detail.category_id,
    breed: detail.breed || '',
    gender: detail.gender,
    age_months: detail.age_months,
    weight: detail.weight,
    health_status: detail.health_status || '',
    vaccinated: detail.vaccinated,
    neutered: detail.neutered,
    personality: detail.personality || '',
    adoption_requirements: detail.adoption_requirements || '',
    region: detail.region || '',
    description: detail.description || '',
    status: detail.status,
    images: [...detail.images]
  })
  dialogVisible.value = true
}

async function save() {
  if (!form.name || !form.category_id) {
    ElMessage.warning('请填写名称与分类')
    return
  }
  saving.value = true
  try {
    const payload = { ...form }
    if (payload.age_months == null) delete payload.age_months
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

async function setStatus(row, status) {
  await updateStatus(row.id, status)
  ElMessage.success('状态已更新')
  load()
}

function pickImage() {
  imageInput.value?.click()
}

async function onImagesPicked(e) {
  const files = Array.from(e.target.files || [])
  if (!files.length) return
  uploading.value = true
  try {
    for (const file of files) {
      const res = await uploadImage(file, 'pets')
      form.images.push(res.data.url)
    }
    ElMessage.success('图片上传成功')
  } finally {
    uploading.value = false
    e.target.value = ''
  }
}

function removeImage(i) {
  form.images.splice(i, 1)
}

onMounted(() => {
  loadCategories()
  load()
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
.cover {
  width: 56px;
  height: 56px;
  border-radius: 6px;
  background: #eef2f7;
}
.cover.placeholder {
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 24px;
  color: #c0c4cc;
}
.pager {
  display: flex;
  justify-content: center;
  margin-top: 16px;
}
.images {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
}
.img-item {
  position: relative;
  width: 80px;
  height: 80px;
}
.img-item img {
  width: 100%;
  height: 100%;
  object-fit: cover;
  border-radius: 6px;
}
.img-del {
  position: absolute;
  top: -6px;
  right: -6px;
  width: 18px;
  height: 18px;
  line-height: 18px;
  text-align: center;
  background: #f56c6c;
  color: #fff;
  border-radius: 50%;
  cursor: pointer;
  font-size: 12px;
}
.img-add {
  width: 80px;
  height: 80px;
  border: 1px dashed #c0c4cc;
  border-radius: 6px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #909399;
  cursor: pointer;
  font-size: 13px;
}
</style>
