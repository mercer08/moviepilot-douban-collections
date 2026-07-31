<script setup>
import { onMounted, ref } from 'vue'
import { cloneConfig } from '../provider'

const props = defineProps({
  initialConfig: {
    type: Object,
    default: () => ({}),
  },
})

const emit = defineEmits(['save', 'close'])
const localConfig = ref({
  enabled: false,
  show_sidebar_nav: true,
  use_proxy: false,
  collection: 'ECFA5DI7Q',
  cache_hours: 6,
})

// 交给 MoviePilot 宿主保存插件配置。
function saveConfig() {
  emit('save', {
    ...cloneConfig(localConfig.value),
    cache_hours: Math.max(0, Math.min(168, Number(localConfig.value.cache_hours || 0))),
  })
}

onMounted(() => {
  localConfig.value = {
    ...localConfig.value,
    ...cloneConfig(props.initialConfig),
  }
})
</script>

<template>
  <div class="dc-config pa-4">
    <div class="d-flex align-center mb-4">
      <div>
        <div class="text-h6">豆瓣合集榜单</div>
        <div class="text-body-2 text-medium-emphasis">使用豆瓣公开榜单数据，不需要 Cookie 或 API Key。</div>
      </div>
      <VSpacer />
      <VBtn icon="mdi-close" variant="text" @click="emit('close')" />
    </div>

    <VAlert type="info" variant="tonal" density="compact" class="mb-4">
      可以填写榜单 ID，也可以直接粘贴 https://m.douban.com/subject_collection/... 地址。
    </VAlert>

    <VSwitch v-model="localConfig.enabled" label="启用插件" color="primary" />
    <VSwitch v-model="localConfig.show_sidebar_nav" label="在发现分组显示“豆瓣榜单”" color="primary" />
    <VSwitch v-model="localConfig.use_proxy" label="访问豆瓣时使用 MoviePilot 代理" color="primary" />
    <VTextField
      v-model="localConfig.collection"
      label="默认豆瓣榜单 ID 或 URL"
      placeholder="ECFA5DI7Q"
      prepend-inner-icon="mdi-link-variant"
      clearable
    />
    <VTextField
      v-model.number="localConfig.cache_hours"
      type="number"
      min="0"
      max="168"
      label="缓存时长（小时）"
      hint="填 0 表示每次都请求豆瓣；远端失败时仍会回退到最后一次成功数据。"
      persistent-hint
    />

    <div class="d-flex justify-end mt-6">
      <VBtn color="primary" prepend-icon="mdi-content-save" @click="saveConfig">保存</VBtn>
    </div>
  </div>
</template>

<style scoped>
.dc-config {
  max-width: 760px;
  margin: 0 auto;
}
</style>
