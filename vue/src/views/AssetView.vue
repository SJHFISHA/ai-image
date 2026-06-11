<script setup lang="ts">
import { computed, onMounted, reactive, ref } from 'vue'
import { DownOutlined, FileImageOutlined, VideoCameraOutlined, AudioOutlined } from '@ant-design/icons-vue'
import { getAssets, type AssetItem, type AssetType } from '@/api/asset'

const loading = ref(false)
const activeType = ref<AssetType>('image')
const assets = ref<AssetItem[]>([])

const tabs: { key: AssetType; label: string }[] = [
  { key: 'image', label: '图片' },
  { key: 'video', label: '视频' },
  { key: 'audio', label: '音频' },
]

const pagination = reactive({
  page: 1,
  pageSize: 80,
  total: 0,
})

const groupedAssets = computed(() => {
  const groups: Record<string, AssetItem[]> = {}

  assets.value.forEach((item) => {
    const label = formatDateGroup(item.created_at)
    if (!groups[label]) groups[label] = []
    groups[label].push(item)
  })

  return Object.entries(groups).map(([label, items]) => ({
    label,
    items,
  }))
})

function formatDateGroup(value: string) {
  const date = new Date(value)
  const now = new Date()

  const startOfToday = new Date(now.getFullYear(), now.getMonth(), now.getDate())
  const startOfTarget = new Date(date.getFullYear(), date.getMonth(), date.getDate())
  const diffDays = Math.floor((startOfToday.getTime() - startOfTarget.getTime()) / 86400000)

  if (diffDays === 0) return '今天'
  if (diffDays === 1) return '1天前'
  if (diffDays === 2) return '2天前'

  return `${date.getMonth() + 1}月${date.getDate()}日`
}

async function loadAssets() {
  loading.value = true
  try {
    const res = await getAssets({
      type: activeType.value,
      page: pagination.page,
      page_size: pagination.pageSize,
    })
    assets.value = res.items || []
    pagination.total = res.total || 0
  } finally {
    loading.value = false
  }
}

function handleTabClick(type: AssetType) {
  activeType.value = type
  pagination.page = 1
  loadAssets()
}

function getMediaIcon(type: AssetType) {
  if (type === 'video') return VideoCameraOutlined
  if (type === 'audio') return AudioOutlined
  return FileImageOutlined
}

onMounted(() => {
  loadAssets()
})
</script>

<template>
  <div class="asset-page">
    <div class="asset-toolbar">
      <button
        v-for="tab in tabs"
        :key="tab.key"
        class="asset-tab"
        :class="{ active: activeType === tab.key }"
        type="button"
        @click="handleTabClick(tab.key)"
      >
        {{ tab.label }}
      </button>

      <button class="asset-filter-btn" type="button">
        筛选
        <DownOutlined />
      </button>
    </div>

    <div v-if="loading" class="asset-state">加载中...</div>
    <div v-else-if="assets.length === 0" class="asset-state">暂无资产</div>

    <section
      v-for="group in groupedAssets"
      v-else
      :key="group.label"
      class="asset-group"
    >
      <h2 class="asset-date-title">{{ group.label }}</h2>

      <div class="asset-grid">
        <article
          v-for="item in group.items"
          :key="`${item.task_id}-${item.url}`"
          class="asset-card"
        >
          <img
            v-if="item.type === 'image'"
            :src="item.url"
            class="asset-media"
            :alt="item.prompt || '生成图片'"
          />

          <video
            v-else-if="item.type === 'video'"
            :src="item.url"
            :poster="item.cover_url"
            class="asset-media"
            muted
            controls
          ></video>

          <div v-else class="asset-audio-card">
            <component :is="getMediaIcon(item.type)" class="asset-audio-icon" />
            <audio :src="item.url" controls class="asset-audio-player"></audio>
          </div>

          <div class="asset-card-mask">
            <span class="asset-type-badge">{{ item.type }}</span>
          </div>
        </article>
      </div>
    </section>
  </div>
</template>

<style scoped>
.asset-page {
  width: 100%;
  min-height: 100%;
  padding: 18px 44px 48px;
  box-sizing: border-box;
  background: #f5f6f7;
}

.asset-toolbar {
  height: 42px;
  display: flex;
  align-items: center;
  gap: 28px;
  margin-bottom: 28px;
}

.asset-tab,
.asset-filter-btn {
  border: none;
  background: transparent;
  color: #172033;
  font-size: 14px;
  cursor: pointer;
  padding: 0;
  display: inline-flex;
  align-items: center;
  gap: 4px;
}

.asset-tab.active {
  font-weight: 600;
}

.asset-tab:hover,
.asset-filter-btn:hover {
  color: #1677ff;
}

.asset-state {
  padding-top: 80px;
  color: rgba(0, 0, 0, 0.45);
  text-align: center;
}

.asset-group {
  margin-bottom: 34px;
}

.asset-date-title {
  margin: 0 0 14px;
  font-size: 28px;
  line-height: 1.2;
  font-weight: 700;
  color: #000;
}

.asset-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(172px, 1fr));
  gap: 2px;
  max-width: 920px;
}

.asset-card {
  position: relative;
  aspect-ratio: 1 / 1;
  overflow: hidden;
  background: #e9ecef;
  border-radius: 2px;
}

.asset-media {
  width: 100%;
  height: 100%;
  object-fit: cover;
  display: block;
  background: #e9ecef;
}

.asset-audio-card {
  width: 100%;
  height: 100%;
  padding: 18px;
  box-sizing: border-box;
  background: linear-gradient(135deg, #edf5ff, #f5f7fb);
  display: flex;
  flex-direction: column;
  justify-content: space-between;
}

.asset-audio-icon {
  font-size: 34px;
  color: #1677ff;
}

.asset-audio-player {
  width: 100%;
}

.asset-card-mask {
  position: absolute;
  inset: 0;
  pointer-events: none;
  background: linear-gradient(to bottom, rgba(0, 0, 0, 0.22), transparent 34%);
  opacity: 0;
  transition: opacity 0.2s;
}

.asset-card:hover .asset-card-mask {
  opacity: 1;
}

.asset-type-badge {
  position: absolute;
  top: 6px;
  left: 6px;
  height: 18px;
  padding: 0 6px;
  border-radius: 4px;
  background: rgba(0, 0, 0, 0.38);
  color: #fff;
  font-size: 11px;
  line-height: 18px;
}

[data-theme='dark'] .asset-page {
  background: #141414;
}

[data-theme='dark'] .asset-tab,
[data-theme='dark'] .asset-filter-btn,
[data-theme='dark'] .asset-date-title {
  color: rgba(255, 255, 255, 0.88);
}

[data-theme='dark'] .asset-state {
  color: rgba(255, 255, 255, 0.45);
}

[data-theme='dark'] .asset-card {
  background: #262626;
}
</style>
