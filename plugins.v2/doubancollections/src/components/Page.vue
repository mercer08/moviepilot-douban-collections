<script setup>
import { ref } from 'vue'
import AppPage from './AppPage.vue'

defineProps({
  api: {
    type: Object,
    default: () => ({}),
  },
  nativeSubscribe: {
    type: Function,
    default: null,
  },
})

const emit = defineEmits(['close'])
const pageRef = ref(null)
</script>

<template>
  <div class="dc-dialog-page">
    <VToolbar density="comfortable" class="dc-toolbar">
      <div class="text-h6 ms-3">豆瓣合集榜单</div>
      <VSpacer />
      <VBtn icon="mdi-refresh" variant="text" :loading="pageRef?.loading" @click="pageRef?.loadCollection()" />
      <VBtn icon="mdi-close" variant="text" @click="emit('close')" />
    </VToolbar>
    <VDivider />
    <AppPage ref="pageRef" :api="api" :native-subscribe="nativeSubscribe" plugin-id="DoubanCollections" hide-title />
  </div>
</template>

<style scoped>
.dc-toolbar {
  position: sticky;
  top: 0;
  z-index: 10;
  background: rgb(var(--v-theme-surface));
}
</style>
