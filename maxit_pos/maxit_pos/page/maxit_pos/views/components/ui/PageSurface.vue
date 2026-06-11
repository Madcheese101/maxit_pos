<template>
  <div :class="surfaceClasses">
    <slot />
  </div>
</template>

<script setup>
import { computed } from 'vue';

const props = defineProps({
  glow: {
    type: String,
    default: 'info-success',
  },
});

const surfaceClasses = computed(() => [
  'page-surface',
  `page-surface--${props.glow}`,
]);
</script>

<style scoped>
.page-surface {
  --maxit-page-glow-top: var(--v-pos-info-glow);
  --maxit-page-glow-bottom: var(--v-pos-success-glow);
  width: 100%;
  min-height: calc(100dvh - var(--v-layout-top, 0px) - var(--v-layout-bottom, 0px));
  height: calc(100dvh - var(--v-layout-top, 0px) - var(--v-layout-bottom, 0px));
  display: flex;
  flex-direction: column;
  overflow-y: auto;
  background:
    radial-gradient(circle at top right, var(--maxit-page-glow-top), transparent 42%),
    radial-gradient(circle at left bottom, var(--maxit-page-glow-bottom), transparent 38%);
  transition: var(--v-theme-transition);
}

.page-surface--info-success {
  --maxit-page-glow-top: var(--v-pos-info-glow);
  --maxit-page-glow-bottom: var(--v-pos-success-glow);
}

.page-surface--success-warning {
  --maxit-page-glow-top: var(--v-pos-success-glow);
  --maxit-page-glow-bottom: var(--v-pos-warning-glow);
}

.page-surface--info-warning {
  --maxit-page-glow-top: var(--v-pos-info-glow);
  --maxit-page-glow-bottom: var(--v-pos-warning-glow);
}

@media (max-width: 960px) {
  .page-surface {
    padding: var(--maxit-page-padding-mobile, 10px) !important;
  }
}

@media (max-height: 768px) and (min-width: 960px) {
  .page-surface {
    padding-block: var(--maxit-page-padding-short, 8px) !important;
  }
}
</style>