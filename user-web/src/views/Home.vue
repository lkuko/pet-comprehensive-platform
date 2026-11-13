<template>
  <div class="page">
    <AppHeader />

    <!-- 首屏：暖色 hero -->
    <section class="hero">
      <div class="hero-inner">
        <div class="hero-copy">
          <h1 class="hero-title">给每一个毛孩子<br />一个温暖的家</h1>
          <p class="hero-sub">领养代替购买，为等待中的它，找到属于彼此的那份陪伴。</p>
          <div class="hero-actions">
            <button class="btn-accent hero-cta" @click="scrollToList">去看看待领养的它们</button>
            <router-link to="/shop" class="hero-link">逛逛宠物用品 →</router-link>
          </div>
        </div>
        <div class="hero-media">
          <img :src="heroImg" alt="等待领养的狗狗" class="hero-img" />
          <div class="hero-badge">
            <span class="badge-num">{{ total }}</span>
            <span class="badge-label">只毛孩子正在等待</span>
          </div>
        </div>
      </div>
    </section>

    <!-- 领养列表 -->
    <main class="container">
      <div class="section-head">
        <h2 class="section-title">待领养</h2>
        <p class="section-sub">每一只都值得被温柔以待</p>
      </div>

      <div class="toolbar">
        <el-input
          v-model="keyword"
          placeholder="搜索名字或品种"
          clearable
          class="search-input"
          @keyup.enter="search"
        >
          <template #prefix>
            <svg class="search-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="11" cy="11" r="7" /><path d="M21 21l-4.3-4.3" /></svg>
          </template>
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
            <div v-else class="cover-placeholder">
              <svg viewBox="0 0 40 40" xmlns="http://www.w3.org/2000/svg"><ellipse cx="20" cy="27" rx="9.5" ry="8" /><ellipse cx="8.5" cy="15" rx="4.2" ry="5.2" /><ellipse cx="16.5" cy="10.5" rx="4.2" ry="5.2" /><ellipse cx="23.5" cy="10.5" rx="4.2" ry="5.2" /><ellipse cx="31.5" cy="15" rx="4.2" ry="5.2" /></svg>
            </div>
            <span class="badge" :class="pet.status === 'AVAILABLE' ? 'is-ok' : ''">{{ ADOPT_STATUS[pet.status] || pet.status }}</span>
          </div>
          <div class="info">
            <div class="name-row">
              <span class="name">{{ pet.name }}</span>
              <span class="cat">{{ pet.category_name }}</span>
            </div>
            <div class="meta">
              <span>{{ GENDER[pet.gender] }}</span>
              <span v-if="pet.breed">· {{ pet.breed }}</span>
              <span v-if="pet.age_months != null">· {{ pet.age_months }} 个月</span>
            </div>
            <div class="region">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 21s-7-5.1-7-11a7 7 0 0 1 14 0c0 5.9-7 11-7 11z" /><circle cx="12" cy="10" r="2.5" /></svg>
              {{ pet.region }}
            </div>
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
import heroImg from '../assets/hero.jpg'

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

function scrollToList() {
  document.querySelector('.container')?.scrollIntoView({ behavior: 'smooth' })
}

onMounted(() => {
  loadCategories()
  load()
})
</script>

<style scoped>
.page {
  min-height: 100vh;
  background: var(--brand-paper);
}

/* ---------- hero ---------- */
.hero {
  background: linear-gradient(180deg, var(--brand-cream) 0%, var(--brand-paper) 100%);
  border-bottom: 1px solid var(--brand-line);
}
.hero-inner {
  max-width: 1100px;
  margin: 0 auto;
  padding: 56px 24px 48px;
  display: grid;
  grid-template-columns: 1.05fr 0.95fr;
  gap: 48px;
  align-items: center;
}
.hero-title {
  font-family: var(--font-display);
  font-size: 44px;
  line-height: 1.25;
  font-weight: 700;
  letter-spacing: 1px;
  margin: 0 0 16px;
}
.hero-sub {
  font-size: 16px;
  color: var(--el-text-color-regular);
  line-height: 1.7;
  margin: 0 0 28px;
  max-width: 420px;
}
.hero-actions {
  display: flex;
  align-items: center;
  gap: 20px;
}
.hero-cta {
  padding: 12px 26px;
  border-radius: 999px;
  font-size: 15px;
  cursor: pointer;
}
.hero-link {
  font-size: 15px;
  font-weight: 500;
  color: var(--brand-forest);
}
.hero-link:hover {
  text-decoration: underline;
}
.hero-media {
  position: relative;
}
.hero-img {
  width: 100%;
  aspect-ratio: 4 / 3;
  object-fit: cover;
  border-radius: 20px;
  box-shadow: 0 20px 40px rgba(35, 48, 42, 0.16);
}
.hero-badge {
  position: absolute;
  left: -18px;
  bottom: 22px;
  background: #fff;
  border-radius: 14px;
  padding: 12px 18px;
  box-shadow: 0 10px 24px rgba(35, 48, 42, 0.14);
  display: flex;
  align-items: baseline;
  gap: 8px;
}
.badge-num {
  font-family: var(--font-display);
  font-size: 26px;
  font-weight: 700;
  color: var(--brand-apricot);
}
.badge-label {
  font-size: 13px;
  color: var(--el-text-color-regular);
}

/* ---------- list ---------- */
.container {
  max-width: 1100px;
  margin: 0 auto;
  padding: 40px 24px 56px;
}
.section-head {
  margin-bottom: 20px;
}
.section-title {
  font-size: 26px;
}
.section-sub {
  margin: 6px 0 0;
  color: var(--el-text-color-secondary);
  font-size: 14px;
}
.toolbar {
  display: flex;
  gap: 12px;
  margin-bottom: 22px;
}
.search-input {
  flex: 1;
  max-width: 360px;
}
.search-icon {
  width: 15px;
  height: 15px;
}
.cat-select {
  width: 160px;
}
.grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(248px, 1fr));
  gap: 20px;
  min-height: 200px;
}
.pet-card {
  background: #fff;
  border: 1px solid var(--brand-line);
  border-radius: 16px;
  overflow: hidden;
  cursor: pointer;
  transition: transform 0.2s, box-shadow 0.2s, border-color 0.2s;
}
.pet-card:hover {
  transform: translateY(-4px);
  border-color: var(--brand-sage-strong);
  box-shadow: 0 14px 30px rgba(35, 48, 42, 0.12);
}
.cover {
  position: relative;
  height: 190px;
  background: var(--brand-sage);
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
}
.cover-placeholder svg {
  width: 56px;
  height: 56px;
  fill: var(--brand-sage-strong);
}
.badge {
  position: absolute;
  top: 10px;
  right: 10px;
  padding: 4px 12px;
  font-size: 12px;
  color: #fff;
  background: rgba(35, 48, 42, 0.6);
  border-radius: 999px;
  backdrop-filter: blur(4px);
}
.badge.is-ok {
  background: var(--brand-forest);
}
.info {
  padding: 14px 16px 16px;
}
.name-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 6px;
}
.name {
  font-family: var(--font-display);
  font-size: 18px;
  font-weight: 700;
  color: var(--brand-ink);
}
.cat {
  font-size: 12px;
  color: var(--brand-forest);
  background: var(--brand-sage);
  padding: 2px 10px;
  border-radius: 999px;
}
.meta {
  font-size: 13px;
  color: var(--el-text-color-secondary);
  margin-bottom: 8px;
}
.region {
  display: flex;
  align-items: center;
  gap: 5px;
  font-size: 13px;
  color: var(--el-text-color-regular);
}
.region svg {
  width: 14px;
  height: 14px;
  color: var(--brand-apricot);
}
.empty {
  grid-column: 1 / -1;
}
.pager {
  display: flex;
  justify-content: center;
  margin-top: 28px;
}

@media (max-width: 800px) {
  .hero-inner {
    grid-template-columns: 1fr;
    gap: 28px;
    padding: 36px 20px;
  }
  .hero-title {
    font-size: 34px;
  }
  .hero-badge {
    left: 10px;
    bottom: -14px;
  }
}
</style>
