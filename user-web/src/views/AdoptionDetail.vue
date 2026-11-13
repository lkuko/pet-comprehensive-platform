<template>
  <div class="page">
    <AppHeader />
    <main class="container" v-loading="loading">
      <el-page-header content="宠物详情" @back="$router.back()" class="back" />

      <template v-if="pet">
        <div class="detail-card">
          <div class="gallery">
            <el-image v-if="pet.images.length" :src="activeImage" fit="cover" class="main-img" />
            <div v-else class="main-img placeholder">🐾</div>
            <div v-if="pet.images.length > 1" class="thumbs">
              <img
                v-for="(img, i) in pet.images"
                :key="i"
                :src="img"
                :class="{ active: activeImage === img }"
                @click="activeImage = img"
              />
            </div>
          </div>

          <div class="side">
            <div class="title-row">
              <h2>{{ pet.name }}</h2>
              <el-tag>{{ ADOPT_STATUS[pet.status] || pet.status }}</el-tag>
            </div>
            <el-descriptions :column="1" border>
              <el-descriptions-item label="分类">{{ pet.category_name }}</el-descriptions-item>
              <el-descriptions-item label="品种">{{ pet.breed || '—' }}</el-descriptions-item>
              <el-descriptions-item label="性别">{{ GENDER[pet.gender] }}</el-descriptions-item>
              <el-descriptions-item label="年龄">{{ pet.age_months != null ? pet.age_months + ' 个月' : '—' }}</el-descriptions-item>
              <el-descriptions-item label="体重">{{ pet.weight != null ? pet.weight + ' kg' : '—' }}</el-descriptions-item>
              <el-descriptions-item label="健康状态">{{ pet.health_status || '—' }}</el-descriptions-item>
              <el-descriptions-item label="疫苗">{{ pet.vaccinated ? '已完成' : '未完成' }}</el-descriptions-item>
              <el-descriptions-item label="绝育">{{ pet.neutered ? '已绝育' : '未绝育' }}</el-descriptions-item>
              <el-descriptions-item label="地区">{{ pet.region || '—' }}</el-descriptions-item>
            </el-descriptions>
          </div>
        </div>

        <div class="section">
          <h3>性格特点</h3>
          <p>{{ pet.personality || '暂无描述' }}</p>
        </div>
        <div class="section">
          <h3>领养要求</h3>
          <p>{{ pet.adoption_requirements || '暂无要求' }}</p>
        </div>
        <div class="section">
          <h3>详细介绍</h3>
          <p>{{ pet.description || '暂无介绍' }}</p>
        </div>
      </template>
    </main>
  </div>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue'
import { useRoute } from 'vue-router'
import AppHeader from '../components/AppHeader.vue'
import { getPet } from '../api/adoption'
import { GENDER, ADOPT_STATUS } from '../utils/dict'

const route = useRoute()
const pet = ref(null)
const loading = ref(false)

const activeImage = computed(() => (pet.value && pet.value.images.length ? pet.value.images[0] : ''))

async function load() {
  loading.value = true
  try {
    pet.value = (await getPet(route.params.id)).data
  } finally {
    loading.value = false
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
  max-width: 1000px;
  margin: 0 auto;
  padding: 24px;
}
.back {
  margin-bottom: 16px;
}
.detail-card {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 24px;
  background: #fff;
  padding: 24px;
  border-radius: 8px;
  box-shadow: 0 1px 4px rgba(0, 0, 0, 0.06);
}
.gallery {
  display: flex;
  flex-direction: column;
  gap: 12px;
}
.main-img {
  width: 100%;
  height: 360px;
  border-radius: 8px;
  background: #eef2f7;
}
.main-img.placeholder {
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 80px;
  color: #c0c4cc;
}
.thumbs {
  display: flex;
  gap: 8px;
}
.thumbs img {
  width: 64px;
  height: 64px;
  object-fit: cover;
  border-radius: 6px;
  cursor: pointer;
  border: 2px solid transparent;
}
.thumbs img.active {
  border-color: #409eff;
}
.title-row {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 16px;
}
.title-row h2 {
  margin: 0;
}
.section {
  background: #fff;
  padding: 20px 24px;
  border-radius: 8px;
  margin-top: 16px;
}
.section h3 {
  margin: 0 0 12px;
  color: #303133;
}
.section p {
  margin: 0;
  color: #606266;
  line-height: 1.7;
  white-space: pre-wrap;
}
</style>
