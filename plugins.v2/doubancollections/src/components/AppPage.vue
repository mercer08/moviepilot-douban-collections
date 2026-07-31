<script setup>
import { computed, inject, onMounted, ref } from 'vue'
import { unwrapResponse } from '../provider'

const props = defineProps({
  api: {
    type: Object,
    default: () => ({}),
  },
  nativeSubscribe: {
    type: Function,
    default: null,
  },
  pluginId: {
    type: String,
    default: 'DoubanCollections',
  },
  hideTitle: {
    type: Boolean,
    default: false,
  },
})

const hostToast = inject('moviepilot:toast', null)
const injectedSubscribe = inject('moviepilot:nativeSubscribe', null)
const loading = ref(false)
const loadingMore = ref(false)
const error = ref('')
const payload = ref({
  collection: {},
  categories: [],
  items: [],
  source: '',
  stale: false,
})

const pluginBase = computed(() => `plugin/${props.pluginId || 'DoubanCollections'}`)
const collection = computed(() => payload.value.collection || {})
const categories = computed(() => payload.value.categories || [])
const items = computed(() => payload.value.items || [])
const currentId = computed(() => collection.value.id || '')
const hasMore = computed(() => items.value.length < Number(collection.value.total || 0))
const activeCategory = computed(() => {
  return categories.value.find(category => category.items.some(item => item.current || item.id === currentId.value))
    || categories.value[0]
    || { name: '', items: [] }
})
const filters = computed(() => activeCategory.value.items || [])
const heroStyle = computed(() => {
  if (!collection.value.backdrop) return {}
  return { backgroundImage: `linear-gradient(90deg, rgba(18,18,24,.92), rgba(18,18,24,.54)), url("${collection.value.backdrop}")` }
})

// 读取指定榜单；翻页时只追加条目，不替换筛选矩阵。
async function loadCollection(collectionId = '', start = 0, refresh = false, append = false) {
  if (append) loadingMore.value = true
  else loading.value = true
  error.value = ''
  try {
    const params = new URLSearchParams({
      collection_id: collectionId,
      start: String(start),
      count: '20',
      refresh: String(refresh),
    })
    const response = await props.api.get(`${pluginBase.value}/collection?${params.toString()}`)
    const data = unwrapResponse(response)
    if (append) {
      const known = new Set(items.value.map(item => item.id))
      payload.value = {
        ...payload.value,
        ...data,
        items: [...items.value, ...(data.items || []).filter(item => !known.has(item.id))],
      }
    } else {
      payload.value = data || payload.value
    }
  } catch (err) {
    error.value = err?.message || '榜单加载失败'
    hostToast?.error?.(error.value)
  } finally {
    loading.value = false
    loadingMore.value = false
  }
}

// 切换左侧地区时，优先保持当前类型；不存在时选择该地区首个真实榜单。
function selectCategory(category) {
  const preferred = category.items.find(item => item.name === collection.value.filter_name)
    || category.items[0]
  if (preferred) loadCollection(preferred.id)
}

// 切换当前地区下的类型榜单。
function selectFilter(filter) {
  if (filter.id !== currentId.value) loadCollection(filter.id)
}

// 调用 MoviePilot 原生订阅；旧宿主没有该能力时打开豆瓣详情。
async function subscribe(item) {
  const subscribeHandler = props.nativeSubscribe || injectedSubscribe
  if (!subscribeHandler) {
    openDouban(item.url)
    hostToast?.info?.('当前 MoviePilot 版本不支持插件原生订阅，已打开豆瓣详情')
    return
  }
  const result = await subscribeHandler({
    title: item.title,
    type: item.type === 'movie' ? '电影' : '电视剧',
    year: item.year,
    douban_id: item.id,
    media_id: item.id,
    mediaid_prefix: 'douban',
  })
  if (result && !result.success && result.code === 'INVALID_MEDIA') openDouban(item.url)
}

// 在新标签页打开可信的豆瓣链接。
function openDouban(url) {
  if (/^https:\/\/(?:movie|m)\.douban\.com\//.test(url || '')) {
    window.open(url, '_blank', 'noopener,noreferrer')
  }
}

// 将关注人数格式化为紧凑中文。
function formatFollowers(value) {
  const number = Number(value || 0)
  if (number >= 10000) return `${(number / 10000).toFixed(number >= 100000 ? 0 : 1)} 万人关注`
  return number > 0 ? `${number.toLocaleString()} 人关注` : ''
}

// 将评分人数格式化为紧凑数字。
function formatCount(value) {
  const number = Number(value || 0)
  if (number >= 10000) return `${(number / 10000).toFixed(1)}万`
  return number.toLocaleString()
}

defineExpose({ loadCollection, loading })
onMounted(() => loadCollection())
</script>

<template>
  <div class="dc-page">
    <section class="dc-hero" :style="heroStyle">
      <div class="dc-hero__content">
        <div class="dc-eyebrow">DOUBAN COLLECTION</div>
        <h1 v-if="!hideTitle" class="dc-title">{{ collection.name || '豆瓣榜单' }}</h1>
        <h2 v-else class="dc-title dc-title--compact">{{ collection.name || '豆瓣榜单' }}</h2>
        <div class="dc-meta">
          <span v-if="formatFollowers(collection.followers)">{{ formatFollowers(collection.followers) }}</span>
          <span>{{ collection.total || 0 }} 个条目</span>
          <span v-if="collection.updated_at">更新于 {{ collection.updated_at }}</span>
          <span v-if="payload.source === 'cache'">缓存数据</span>
        </div>
      </div>
      <div class="dc-hero__actions">
        <VBtn icon="mdi-refresh" variant="tonal" :loading="loading" title="刷新" @click="loadCollection(currentId, 0, true)" />
        <VBtn icon="mdi-open-in-new" variant="tonal" title="打开豆瓣原榜单" @click="openDouban(collection.url)" />
      </div>
    </section>

    <VAlert v-if="payload.stale" type="warning" variant="tonal" density="compact" class="ma-4 mb-0">
      豆瓣暂时无法访问，当前显示最后一次成功缓存。
    </VAlert>
    <VAlert v-if="error" type="error" variant="tonal" density="compact" class="ma-4 mb-0">
      {{ error }}
    </VAlert>

    <div class="dc-layout">
      <aside class="dc-regions" aria-label="地区筛选">
        <button
          v-for="category in categories"
          :key="category.name"
          class="dc-region"
          :class="{ 'dc-region--active': category.name === activeCategory.name }"
          type="button"
          @click="selectCategory(category)"
        >
          {{ category.name }}
        </button>
      </aside>

      <main class="dc-main">
        <div class="dc-filters" aria-label="类型筛选">
          <button
            v-for="filter in filters"
            :key="filter.id"
            class="dc-filter"
            :class="{ 'dc-filter--active': filter.id === currentId }"
            type="button"
            @click="selectFilter(filter)"
          >
            {{ filter.name }}
          </button>
        </div>

        <div v-if="loading && !items.length" class="dc-grid">
          <VSkeletonLoader v-for="index in 10" :key="index" type="image, article" class="dc-skeleton" />
        </div>

        <div v-else-if="items.length" class="dc-grid">
          <article v-for="item in items" :key="item.id" class="dc-card">
            <button class="dc-poster-wrap" type="button" :aria-label="`打开 ${item.title} 的豆瓣详情`" @click="openDouban(item.url)">
              <img
                v-if="item.poster"
                class="dc-poster"
                :src="item.poster"
                :alt="`${item.title} 海报`"
                loading="lazy"
                referrerpolicy="no-referrer"
              >
              <div v-else class="dc-poster dc-poster--empty">暂无海报</div>
              <span class="dc-rank">{{ item.rank }}</span>
              <span v-if="item.rating" class="dc-rating">{{ item.rating }}</span>
            </button>
            <div class="dc-card__body">
              <button class="dc-card__title" type="button" @click="openDouban(item.url)">{{ item.title }}</button>
              <div class="dc-card__subtitle">{{ item.subtitle || item.year || '暂无简介' }}</div>
              <div class="dc-card__footer">
                <span v-if="item.rating_count" class="dc-votes">{{ formatCount(item.rating_count) }} 人评分</span>
                <span v-else />
                <VBtn size="small" variant="tonal" color="primary" prepend-icon="mdi-plus" @click="subscribe(item)">
                  订阅
                </VBtn>
              </div>
            </div>
          </article>
        </div>

        <div v-else-if="!loading" class="dc-empty">
          <VIcon icon="mdi-movie-open-off-outline" size="52" />
          <div>这个榜单暂时没有条目</div>
        </div>

        <div v-if="hasMore" class="dc-load-more">
          <VBtn variant="tonal" :loading="loadingMore" @click="loadCollection(currentId, items.length, false, true)">
            加载更多
          </VBtn>
        </div>
      </main>
    </div>
  </div>
</template>

<style scoped>
.dc-page {
  min-height: 100%;
  color: rgb(var(--v-theme-on-surface));
}

.dc-hero {
  min-height: 190px;
  padding: 28px clamp(20px, 4vw, 54px);
  display: flex;
  align-items: flex-end;
  justify-content: space-between;
  gap: 24px;
  color: #fff;
  background: linear-gradient(135deg, #2c2630, #514854);
  background-size: cover;
  background-position: center 28%;
}

.dc-eyebrow {
  margin-bottom: 8px;
  color: rgba(255, 255, 255, .68);
  font-size: 11px;
  font-weight: 700;
  letter-spacing: .18em;
}

.dc-title {
  margin: 0;
  font-size: clamp(30px, 4vw, 48px);
  line-height: 1.08;
  text-shadow: 0 2px 18px rgba(0, 0, 0, .38);
}

.dc-title--compact {
  font-size: clamp(24px, 3vw, 38px);
}

.dc-meta {
  margin-top: 12px;
  display: flex;
  flex-wrap: wrap;
  gap: 8px 18px;
  color: rgba(255, 255, 255, .78);
  font-size: 13px;
}

.dc-hero__actions {
  display: flex;
  flex: 0 0 auto;
  gap: 8px;
}

.dc-layout {
  display: grid;
  grid-template-columns: 136px minmax(0, 1fr);
  align-items: start;
}

.dc-regions {
  position: sticky;
  top: 0;
  min-height: calc(100vh - 190px);
  padding: 18px 12px;
  display: flex;
  flex-direction: column;
  gap: 5px;
  background: rgba(var(--v-theme-surface-variant), .45);
}

.dc-region,
.dc-filter,
.dc-card__title,
.dc-poster-wrap {
  font: inherit;
}

.dc-region,
.dc-filter {
  border: 0;
  cursor: pointer;
  color: inherit;
}

.dc-region {
  padding: 11px 12px;
  border-radius: 12px;
  background: transparent;
  text-align: left;
  font-size: 14px;
  transition: background-color .18s ease, color .18s ease;
}

.dc-region:hover {
  background: rgba(var(--v-theme-on-surface), .06);
}

.dc-region--active {
  color: rgb(var(--v-theme-primary));
  background: rgba(var(--v-theme-primary), .13);
  font-weight: 700;
}

.dc-main {
  min-width: 0;
  padding: 18px clamp(14px, 2.5vw, 34px) 42px;
}

.dc-filters {
  margin-bottom: 20px;
  padding-bottom: 2px;
  display: flex;
  gap: 8px;
  overflow-x: auto;
  scrollbar-width: none;
}

.dc-filters::-webkit-scrollbar {
  display: none;
}

.dc-filter {
  flex: 0 0 auto;
  padding: 8px 13px;
  border-radius: 999px;
  background: rgba(var(--v-theme-on-surface), .06);
  font-size: 13px;
  white-space: nowrap;
}

.dc-filter:hover {
  background: rgba(var(--v-theme-on-surface), .1);
}

.dc-filter--active {
  color: rgb(var(--v-theme-on-primary));
  background: rgb(var(--v-theme-primary));
  font-weight: 700;
}

.dc-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(180px, 1fr));
  gap: clamp(14px, 2vw, 24px);
}

.dc-card {
  min-width: 0;
  overflow: hidden;
  border: 1px solid rgba(var(--v-border-color), var(--v-border-opacity));
  border-radius: 16px;
  background: rgba(var(--v-theme-surface), .78);
  box-shadow: 0 10px 28px rgba(0, 0, 0, .07);
  transition: transform .2s ease, box-shadow .2s ease;
}

.dc-card:hover {
  transform: translateY(-3px);
  box-shadow: 0 16px 34px rgba(0, 0, 0, .13);
}

.dc-poster-wrap {
  position: relative;
  width: 100%;
  display: block;
  padding: 0;
  border: 0;
  cursor: pointer;
  background: rgba(var(--v-theme-on-surface), .06);
}

.dc-poster {
  width: 100%;
  aspect-ratio: 2 / 3;
  display: block;
  object-fit: cover;
}

.dc-poster--empty {
  display: grid;
  place-items: center;
  color: rgba(var(--v-theme-on-surface), .5);
  font-size: 13px;
}

.dc-rank,
.dc-rating {
  position: absolute;
  top: 10px;
  min-width: 30px;
  height: 30px;
  padding: 0 8px;
  display: grid;
  place-items: center;
  border-radius: 999px;
  color: #fff;
  font-size: 13px;
  font-weight: 800;
  box-shadow: 0 4px 14px rgba(0, 0, 0, .22);
}

.dc-rank {
  left: 10px;
  background: rgba(20, 20, 26, .76);
}

.dc-rating {
  right: 10px;
  background: #ff8a1f;
}

.dc-card__body {
  padding: 13px;
}

.dc-card__title {
  max-width: 100%;
  padding: 0;
  overflow: hidden;
  border: 0;
  cursor: pointer;
  color: inherit;
  background: transparent;
  font-weight: 700;
  text-align: left;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.dc-card__subtitle {
  height: 36px;
  margin-top: 7px;
  overflow: hidden;
  color: rgba(var(--v-theme-on-surface), .58);
  display: -webkit-box;
  font-size: 12px;
  line-height: 18px;
  -webkit-box-orient: vertical;
  -webkit-line-clamp: 2;
}

.dc-card__footer {
  min-height: 34px;
  margin-top: 12px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 6px;
}

.dc-votes {
  color: rgba(var(--v-theme-on-surface), .5);
  font-size: 11px;
}

.dc-empty,
.dc-load-more {
  min-height: 160px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.dc-empty {
  flex-direction: column;
  gap: 10px;
  color: rgba(var(--v-theme-on-surface), .48);
}

.dc-skeleton {
  overflow: hidden;
  border-radius: 16px;
}

@media (max-width: 760px) {
  .dc-hero {
    min-height: 164px;
    padding: 22px 18px;
    align-items: flex-end;
  }

  .dc-meta span:nth-child(3) {
    display: none;
  }

  .dc-layout {
    display: block;
  }

  .dc-regions {
    position: sticky;
    top: 0;
    z-index: 4;
    min-height: auto;
    padding: 10px 12px;
    flex-direction: row;
    overflow-x: auto;
    backdrop-filter: blur(14px);
    scrollbar-width: none;
  }

  .dc-regions::-webkit-scrollbar {
    display: none;
  }

  .dc-region {
    flex: 0 0 auto;
    padding: 8px 11px;
    white-space: nowrap;
  }

  .dc-main {
    padding: 14px 12px 32px;
  }

  .dc-grid {
    grid-template-columns: repeat(2, minmax(0, 1fr));
    gap: 12px;
  }

  .dc-card__body {
    padding: 10px;
  }

  .dc-votes {
    display: none;
  }
}

@media (max-width: 430px) {
  .dc-title {
    font-size: 27px;
  }

  .dc-hero__actions :deep(.v-btn):last-child {
    display: none;
  }
}
</style>
