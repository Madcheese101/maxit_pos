<template>
    <div class="items-list">
        <div v-if="!props.items.length" class="items-empty text-medium-emphasis">
          {{ __('No items found for this search/filter combination.') }}
        </div>

        <div
          v-else-if="props.viewMode === 'grid'"
          class="items-grid items-scroll"
        >
          <Item
            v-for="(item, idx) in props.items"
            :key="item.item_code || idx"
            :item="item"
            @click="item_clicked(item)"
          />
        </div>

        <v-list
          v-else
          class="item-rows items-scroll"
          bg-color="transparent"
          density="compact"
          lines="one"
        >
          <template v-for="(item, idx) in props.items" :key="item.item_code || idx">
          <v-tooltip :text="item.item_code" location="top" open-delay="400">
            <template #activator="{ props: tipProps }">
          <v-list-item
            class="item-row"
            rounded="0"
            v-bind="tipProps"
            @click="item_clicked(item)"
          >
            <template #title>
              <div class="item-row-grid">
                <span class="item-row-name">{{ item.item_name }}</span>
                <span class="item-row-value">{{ item.actual_qty ?? 0 }}</span>
                <span class="item-row-value item-row-rate">{{ item.price_list_rate ?? 0 }} {{item.currency || ''}}</span>
              </div>
            </template>
          </v-list-item>
            </template>
          </v-tooltip>
          </template>
        </v-list>
    </div>
</template>

<script setup>
    import Item from "./Item.vue";
    import { usePosStore } from '../../../store/posStore';
    const __ = window.__;
    const posStore = usePosStore();
    const props = defineProps({
      items: {
        type: Array,
        default: () => [],
      },
      viewMode: {
        type: String,
        default: 'grid',
      },
    });
    const {update_cart} = posStore;

    const item_clicked = (item) => {
      update_cart({
        field: "qty",
        value: "+1",
        item: item
      });
    }
</script>

<style scoped>
.items-list {
  display: flex;
  flex-direction: column;
  flex: 1;
  min-height: 0;
}

.items-scroll {
  flex: 1;
  min-height: 0;
  overflow-y: auto;
}

.items-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(130px, 1fr));
  /* cards clip overflow, so auto rows would shrink to 0 inside the scroll area */
  grid-auto-rows: max-content;
  align-content: start;
  gap: 8px;
  padding: 2px;
}

.items-empty {
  padding: 24px 8px;
  text-align: center;
}

.item-rows {
  padding: 0;
}

.item-row-grid {
  display: grid;
  grid-template-columns: minmax(0, 1fr) minmax(48px, auto) minmax(88px, auto);
  align-items: center;
  column-gap: 12px;
}

.item-row {
  border-radius: 0 !important;
  border-bottom: 1px solid var(--v-pos-panel-border-soft);
  min-height: 0;
  transition: background-color 0.15s ease;
}

.item-row:hover,
.item-row:focus-visible {
  background: var(--v-pos-nav-hover);
}

.item-row :deep(.v-list-item__content) {
  padding: 8px 4px;
}

.item-row-name {
  color: rgb(var(--v-theme-on-surface));
  font-size: 0.875rem;
  font-weight: 600;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.item-row-value {
  color: rgb(var(--v-pos-text-muted));
  font-size: 0.8125rem;
  font-weight: 500;
}

.item-row-rate {
  justify-self: end;
}
</style>
