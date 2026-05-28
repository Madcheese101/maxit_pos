<template>
  <v-card
    :class="surfaceClasses"
    :rounded="roundedValue"
    :variant="variantValue"
  >
    <slot />
  </v-card>
</template>

<script setup>
import { computed } from 'vue';

const props = defineProps({
  surface: {
    type: String,
    default: 'panel',
  },
  rounded: {
    type: [String, Number, Boolean],
    default: undefined,
  },
  variant: {
    type: String,
    default: undefined,
  },
});

const roundedValue = computed(() => {
  if (props.rounded !== undefined) {
    return props.rounded;
  }

  return ['section', 'menu', 'stat'].includes(props.surface) ? 'lg' : 'xl';
});

const variantValue = computed(() => {
  if (props.variant) {
    return props.variant;
  }

  if (props.surface === 'section') {
    return 'outlined';
  }

  if (props.surface === 'stat') {
    return 'tonal';
  }

  return 'flat';
});

const surfaceClasses = computed(() => [
  'surface-card',
  `surface-card--${props.surface}`,
]);
</script>

<style scoped>
.surface-card {
  color: rgb(var(--v-theme-on-surface));
  transition: var(--v-theme-transition);
}

.surface-card--panel,
.surface-card--filter,
.surface-card--results,
.surface-card--menu {
  border: 1px solid var(--v-pos-panel-border);
  background: var(--v-pos-panel-background);
  box-shadow: var(--v-pos-panel-shadow);
}

.surface-card--menu {
  border-color: var(--v-pos-panel-border-strong);
  box-shadow: var(--v-pos-panel-shadow-strong);
}

.surface-card--section,
.surface-card--stat {
  border: 1px solid var(--v-pos-panel-border-strong);
}

.surface-card--section {
  background: rgba(var(--v-theme-surface), 0.38);
}

.surface-card--stat {
  box-shadow: none;
}
</style>