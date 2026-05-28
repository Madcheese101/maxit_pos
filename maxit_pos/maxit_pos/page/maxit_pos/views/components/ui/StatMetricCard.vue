<template>
  <SurfaceCard
    surface="stat"
    :class="cardClasses"
    :color="color"
  >
    <v-card-text :class="textClasses">
      <div :class="labelClasses">{{ label }}</div>
      <div :class="valueClasses">{{ value }}</div>
      <slot />
    </v-card-text>
  </SurfaceCard>
</template>

<script setup>
import { computed } from 'vue';
import SurfaceCard from './SurfaceCard.vue';

const props = defineProps({
  label: {
    type: String,
    required: true,
  },
  value: {
    type: [String, Number],
    default: '',
  },
  color: {
    type: String,
    default: 'primary',
  },
  compact: {
    type: Boolean,
    default: false,
  },
  truncate: {
    type: Boolean,
    default: false,
  },
  interactive: {
    type: Boolean,
    default: false,
  },
  valueClass: {
    type: [String, Array, Object],
    default: '',
  },
});

const cardClasses = computed(() => [
  'stat-metric-card',
  {
    'stat-metric-card--compact': props.compact,
    'stat-metric-card--interactive': props.interactive,
  },
]);

const textClasses = computed(() => [
  props.compact ? 'stat-metric-card__text--compact' : 'stat-metric-card__text',
]);

const labelClasses = computed(() => [
  'text-caption',
  'text-medium-emphasis',
  'stat-metric-card__label',
]);

const valueClasses = computed(() => [
  props.compact ? 'text-body-2' : 'text-body-1',
  'font-weight-bold',
  'stat-metric-card__value',
  props.truncate ? 'text-truncate' : null,
  props.valueClass,
]);
</script>

<style scoped>
.stat-metric-card {
  min-height: 100%;
}

.stat-metric-card--interactive {
  cursor: pointer;
}

.stat-metric-card--interactive:hover {
  transform: translateY(-1px);
}

.stat-metric-card__text,
.stat-metric-card__text--compact {
  padding: var(--maxit-stat-padding, 16px);
}

.stat-metric-card__text--compact {
  padding: var(--maxit-stat-padding-compact, 12px);
}

.stat-metric-card__label {
  margin-block-end: 4px;
}

.stat-metric-card__value {
  line-height: 1.3;
}
</style>