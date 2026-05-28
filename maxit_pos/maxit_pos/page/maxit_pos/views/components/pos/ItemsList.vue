<template>
    <VCard rounded="lg" class="ma-auto" max-height="100vh" flat>
      <VCardText class="items-list-shell">
        <v-row
          v-if="props.viewMode === 'grid'"
          class="overflow-y-auto"
          style="max-height: 55vh"
        >
          <v-col
            v-for="(item, idx) in props.items"
            :key="item.item_code || idx"
            xl="2"
            lg="3"
            md="6"
            sm="6"
            cols="6"
            min-height="50"
          >
            <Item :item="item" @click="item_clicked(item)"/>
          </v-col>
        </v-row>

        <v-list
          v-else
          class="item-rows"
          bg-color="transparent"
          density="compact"
          lines="one"
          max-height="55vh"
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
                <span class="item-row-value item-row-rate">{{ __('Rate:') }} {{ item.price_list_rate ?? 0 }} {{item.currency || ''}}</span>
              </div>
            </template>
          </v-list-item>
            </template>
          </v-tooltip>
          </template>
        </v-list>
      </VCardText>
    </VCard>
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
.items-list-shell {
  padding: 0;
}

.item-rows {
  padding: 0;
  overflow-y: auto;
}

.item-rows-header-grid,
.item-row-grid {
  display: grid;
  grid-template-columns: minmax(0, 1.8fr) minmax(72px, 0.6fr) minmax(88px, 0.7fr);
  align-items: center;
  column-gap: 12px;
}

.item-rows-header {
  position: sticky;
  top: 0;
  z-index: 1;
  padding: 12px 16px !important;
  min-height: auto;
  background: var(--v-pos-field-background);
  border-bottom: 1px solid var(--v-pos-panel-border-strong);
  color: rgba(var(--v-theme-on-surface), 0.78);
  font-size: 0.78rem;
  font-weight: 700;
  letter-spacing: 0.03em;
  text-transform: uppercase;
}

.item-rows-header-grid {
  width: 100%;
}

.item-col-qty {
  justify-self: center;
}

.item-col-rate {
  justify-self: end;
}

.item-row {
  border-radius: 0 !important;
  border-bottom: 1px solid var(--v-pos-panel-border-soft);
  transition: background-color 0.15s ease;
}

.item-row:hover,
.item-row:focus-visible {
  background: var(--v-pos-nav-hover);
}

.item-row :deep(.v-list-item__content) {
  padding: 14px 16px;
}

.item-row-name {
  color: rgb(var(--v-theme-on-surface));
  font-weight: 600;
}

.item-row-value {
  color: rgb(69, 90, 100);
  font-weight: 500;
}

.item-row-rate {
  justify-self: end;
}

@media (max-width: 600px) {
  .item-rows-header-grid,
  .item-row-grid {
    grid-template-columns: minmax(0, 1.4fr) minmax(56px, 0.5fr) minmax(72px, 0.6fr);
    column-gap: 8px;
  }

  .item-rows-header,
  .item-row :deep(.v-list-item__content) {
    padding-inline: 12px;
  }

  .item-row-name,
  .item-row-value {
    font-size: 0.9rem;
  }
}
</style>