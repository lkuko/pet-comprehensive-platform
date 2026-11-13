<template>
  <div class="page">
    <AppHeader />
    <main class="container">
      <div class="hero">
        <h1>给它们一个温暖的家</h1>
        <p>浏览待领养的毛孩子，找到你的那个它</p>
      </div>

      <div class="toolbar">
        <el-input
          v-model="keyword"
          placeholder="搜索名字或品种"
          clearable
          class="search-input"
          @keyup.enter="search"
        >
          <template #prefix>🔍</template>
        </el-input>
        <el-select v-model="categoryId" placeholder="全部分类" clearable class="cat-select" @change="search">
          <el-option v-for="c in categories" :key="c.id" :label="c.name" :value="c.id" />
        </el-select>
        <el-button type="primary" @click="search">搜索</el-button>
      </div>

      <div v-loading="loading" class="grid">
        <div v-for="pet in list" :key="pet.id" class="pet-card" @click="$router.push(`/adoption/${pet.id}`)">
          <div class="cover">
            <el-image v-if="pet.cover_url" :src="pet.cover_url" fit="cover" class="cover-img" />
            <div v-else class="cover-placeholder">🐾</div>
            <span class="badge">{{ ADOPT_STATUS[pet.status] || pet.status }}</span>
          </div>
          <div class="info">
            <div class="name-row">
              <span class="name">{{ pet.name }}</span>
              <el-tag size="small" type="info">{{ pet.category_name }}</el-tag>
            </div>
            <div class="meta">
              <span>{{ GENDER[pet.gender] }}</span>
              <span v-if="pet.breed">· {{ pet.breed }}</span>
              <span v-if="pet.age_months != null">· {{ pet.age_months }} 个月</span>
            </div>
            <div class="region">📍 {{ pet.region }}</div>
          </div>
        </div>
        <el-empty v-if="!loading && list.length === 0" description="暂无待领养的宠物" class="empty" />
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
    </main>
  </div>
</template>

<script setup>
import { onMounted, ref } from 'vue'
import AppHeader from '../components/AppHeader.vue'
import { listPets, listCategories } from '../api/adoption'
import { GENDER, ADOPT_STATUS } from '../utils/dict'

const list = ref([])
const categories = ref([])
const total = ref(0)
const page = ref(1)
const pageSize = ref(12)
const keyword = ref('')
const categoryId = ref(null)
const loading = ref(false)

async function loadCategories() {
  try {
    categories.value = (await listCategories()).data || []
  } catch {}
}

async function load() {
  loading.value = true
  try {
    const res = await listPets({
      page: page.value,
      page_size: pageSize.value,
      category_id: categoryId.value || undefined,
      keyword: keyword.value || undefined
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
.hero {
  text-align: center;
  margin: 16px 0 24px;
}
.hero h1 {
  margin: 0 0 8px;
  font-size: 28px;
  color: #303133;
}
.hero p {
  margin: 0;
  color: #909399;
}
.toolbar {
  display: flex;
  gap: 12px;
  margin-bottom: 20px;
}
.search-input {
  flex: 1;
}
.cat-select {
  width: 160px;
}
.grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(240px, 1fr));
  gap: 16px;
  min-height: 200px;
}
.pet-card {
  background: #fff;
  border-radius: 8px;
  overflow: hidden;
  cursor: pointer;
  box-shadow: 0 1px 4px rgba(0, 0, 0, 0.06);
  transition: transform 0.15s, box-shadow 0.15s;
}
.pet-card:hover {
  transform: translateY(-3px);
  box-shadow: 0 6px 16px rgba(0, 0, 0, 0.1);
}
.cover {
  position: relative;
  height: 180px;
  background: #eef2f7;
}
.cover-img {
  width: 100%;
  height: 100%;
}
.cover-placeholder {
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 48px;
  color: #c0c4cc;
}
.badge {
  position: absolute;
  top: 8px;
  right: 8px;
  padding: 2px 8px;
  font-size: 12px;
  color: #fff;
  background: #67c23a;
  border-radius: 10px;
}
.info {
  padding: 12px 14px;
}
.name-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 6px;
}
.name {
  font-size: 16px;
  font-weight: 600;
  color: #303133;
}
.meta {
  font-size: 13px;
  color: #909399;
  margin-bottom: 6px;
}
.region {
  font-size: 13px;
  color: #606266;
}
.empty {
  grid-column: 1 / -1;
}
.pager {
  display: flex;
  justify-content: center;
  margin-top: 24px;
}
</style>
