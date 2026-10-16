<template>
  <div class="picker-form">
    <SurfaceCard class="picker-pane picker-pane--search">
      <div class="picker-pane__body">
        <div class="pane-header">
          <v-btn
            :icon="backIcon"
            variant="text"
            size="small"
            :aria-label="__('Back')"
            @click="onBack"
          />
          <div class="pane-header__title">{{ title }}</div>
        </div>

        <slot name="fields" />

        <v-text-field
          ref="searchInput"
          v-model="searchText"
          density="compact"
          :placeholder="__('Scan barcode or search item')"
          prepend-inner-icon="mdi-barcode-scan"
          variant="outlined"
          hide-details
          single-line
          clearable
          :autofocus="!isMobile"
          :loading="isSearching"
          class="flex-grow-0"
          @update:model-value="onSearchInput"
          @keydown.enter.prevent="onSearchEnter"
        />

        <div v-if="!isMobile || searchText" class="picker-results">
          <v-list
            v-if="results.length"
            nav
            density="compact"
            bg-color="transparent"
            class="pa-0"
          >
            <v-list-item
              v-for="item in results"
              :key="item.value"
              rounded="lg"
              class="result-row"
              :disabled="item.actual_qty <= 0"
              @click="onResultClick(item)"
            >
              <div class="result-row__name">{{ item.label }}</div>
              <div class="result-row__sub">{{ item.value }} · {{ __('Available') }}: {{ item.actual_qty }}</div>
              <template #append>
                <v-chip
                  v-if="lineQtyByCode[item.value]"
                  size="x-small"
                  color="primary"
                  variant="flat"
                  class="me-2"
                >
                  {{ lineQtyByCode[item.value] }}
                </v-chip>
                <v-icon icon="mdi-plus-circle-outline" color="primary" />
              </template>
            </v-list-item>
          </v-list>

          <v-alert v-else-if="!isSearching" type="info" variant="tonal" density="compact">
            {{ __('No items found.') }}
          </v-alert>
        </div>
      </div>
    </SurfaceCard>

    <SurfaceCard class="picker-pane picker-pane--lines">
      <div class="picker-pane__body">
        <div class="pane-header">
          <div class="pane-header__title">{{ linesTitle }}</div>
          <v-chip size="x-small" color="primary" variant="tonal">{{ lines.length }}</v-chip>
          <v-spacer />
          <span class="pane-header__sub">{{ __('Total Qty') }}: {{ totalQty }}</span>
        </div>

        <div ref="linesWrap" class="picker-lines">
          <v-alert v-if="!lines.length" type="info" variant="tonal" density="compact">
            {{ __('Search or scan items to add them.') }}
          </v-alert>

          <div
            v-for="(line, index) in lines"
            :key="line.item_code"
            :data-code="line.item_code"
            class="picker-line"
            :class="{
              'picker-line--flash': flashCode === line.item_code,
              'picker-line--over': Number(line.qty) > line.actual_qty,
            }"
          >
            <div class="picker-line__main">
              <div class="picker-line__name">{{ index + 1 }}. {{ line.item_name }}</div>
              <div class="picker-line__sub">{{ line.item_code }} · {{ __('Available') }}: {{ line.actual_qty }}</div>
            </div>
            <div class="picker-line__qty">
              <v-btn
                icon="mdi-minus"
                size="x-small"
                variant="tonal"
                :disabled="Number(line.qty) <= 1"
                :aria-label="__('Decrease')"
                @click="stepQty(line, -1)"
              />
              <v-text-field
                v-model="line.qty"
                type="number"
                min="0.01"
                step="any"
                density="compact"
                variant="outlined"
                hide-details
                single-line
                class="picker-line__qty-input"
              />
              <v-btn
                icon="mdi-plus"
                size="x-small"
                variant="tonal"
                :disabled="Number(line.qty) + 1 > line.actual_qty"
                :aria-label="__('Increase')"
                @click="stepQty(line, 1)"
              />
            </div>
            <v-btn
              icon="mdi-delete-outline"
              variant="text"
              color="error"
              size="small"
              :aria-label="__('Delete')"
              @click="lines.splice(index, 1)"
            />
          </div>
        </div>

        <div class="picker-actions">
          <v-btn variant="tonal" @click="onBack">{{ __('Cancel') }}</v-btn>
          <v-btn
            color="primary"
            variant="elevated"
            :prepend-icon="submitIcon"
            :disabled="!canSubmit"
            :loading="submitting"
            @click="emit('submit', lines.map((line) => ({ item_code: line.item_code, qty: Number(line.qty) })))"
          >
            {{ submitLabel }}
          </v-btn>
        </div>
      </div>
    </SurfaceCard>
  </div>
</template>

<script setup>
  import { useDisplay } from 'vuetify';
  import { computed, nextTick, onMounted, ref } from 'vue';
  import SurfaceCard from './SurfaceCard.vue';

  // search-and-add item lines editor; the parent owns the header fields (slot) and the submit call
  const props = defineProps({
    title: { type: String, required: true },
    linesTitle: { type: String, required: true },
    submitLabel: { type: String, required: true },
    submitIcon: { type: String, default: 'mdi-content-save' },
    submitting: { type: Boolean, default: false },
    // whether the parent's header fields are valid
    ready: { type: Boolean, default: false },
    // warehouse to check stock in; the server falls back to the user's branch warehouse
    warehouse: { type: String, default: '' },
  });
  const emit = defineEmits(['cancel', 'submit']);

  const __ = window.__;
  const frappe_ = window.frappe;
  const { smAndDown } = useDisplay();
  const isMobile = computed(() => smAndDown.value);
  const backIcon = computed(() => frappe_.utils.is_rtl() ? 'mdi-arrow-right' : 'mdi-arrow-left');

  const searchInput = ref(null);
  const searchText = ref('');
  const results = ref([]);
  const isSearching = ref(false);
  const linesWrap = ref(null);
  const lines = ref([]);
  const flashCode = ref('');
  let searchTimer = null;
  let searchSeq = 0;
  let flashTimer = null;

  const totalQty = computed(() => lines.value.reduce((sum, line) => sum + Number(line.qty || 0), 0));
  const lineQtyByCode = computed(() => Object.fromEntries(lines.value.map((line) => [line.item_code, line.qty])));
  const canSubmit = computed(() =>
    props.ready && lines.value.length > 0
      && lines.value.every((line) => Number(line.qty) > 0 && Number(line.qty) <= line.actual_qty)
  );

  onMounted(() => fetchItems(''));

  // returns the results, or null when a newer search superseded this one or it failed
  async function fetchItems(txt) {
    const seq = ++searchSeq;
    isSearching.value = true;
    try {
      const response = await frappe_.call({
        method: 'maxit_pos.maxit_pos.api.search_items_with_stock',
        args: {
          txt: txt || '',
          warehouse: props.warehouse || null,
          page_length: 20,
        },
      });
      if (seq !== searchSeq) return null;
      results.value = (response.message || []).map((item) => ({
        value: item.item_code,
        label: item.item_name || item.item_code,
        actual_qty: Number(item.actual_qty) || 0,
        exact: !!item.exact,
      }));
      return results.value;
    } catch (error) {
      if (seq === searchSeq) {
        frappe_.msgprint({
          title: __('Item search failed'),
          indicator: 'red',
          message: error?.message || String(error),
        });
      }
      return null;
    } finally {
      if (seq === searchSeq) isSearching.value = false;
    }
  }

  function onSearchInput() {
    clearTimeout(searchTimer);
    searchTimer = setTimeout(() => fetchItems((searchText.value || '').trim()), 250);
  }

  // scanners type the code then press Enter, so search right away and add a single match
  async function onSearchEnter() {
    clearTimeout(searchTimer);
    const txt = (searchText.value || '').trim();
    if (!txt) return;

    const found = await fetchItems(txt);
    if (!found) return;

    const match = found.find((item) => item.exact) || (found.length === 1 ? found[0] : null);
    if (!match || !addItem(match)) return;

    searchText.value = '';
    fetchItems('');
  }

  function onResultClick(item) {
    addItem(item);
    if (!isMobile.value) searchInput.value?.focus();
  }

  // returns false when the item has no more stock to add
  function addItem(item) {
    const existing = lines.value.find((line) => line.item_code === item.value);
    const qty = Number(existing?.qty || 0) + 1;
    if (qty > item.actual_qty) {
      frappe_.show_alert({
        message: __('Only {0} available for {1}', [item.actual_qty, item.label]),
        indicator: 'orange'
      }, 5);
      return false;
    }

    if (existing) {
      existing.qty = qty;
      existing.actual_qty = item.actual_qty;
    } else {
      lines.value.push({ item_code: item.value, item_name: item.label, qty, actual_qty: item.actual_qty });
    }

    clearTimeout(flashTimer);
    flashCode.value = item.value;
    flashTimer = setTimeout(() => { flashCode.value = ''; }, 900);
    scrollToLine(item.value, !existing);
    return true;
  }

  async function scrollToLine(code, isNew) {
    await nextTick();
    if (!linesWrap.value) return;
    if (isNew) {
      linesWrap.value.scrollTop = linesWrap.value.scrollHeight;
    } else {
      linesWrap.value
        .querySelector(`[data-code="${CSS.escape(code)}"]`)
        ?.scrollIntoView({ block: 'nearest' });
    }
  }

  function stepQty(line, delta) {
    line.qty = Math.max(1, Number(line.qty || 0) + delta);
  }

  function onBack() {
    if (!lines.value.length) {
      emit('cancel');
      return;
    }
    frappe_.confirm(__('Discard the added items?'), () => emit('cancel'));
  }
</script>

<style scoped>
.picker-form {
  display: flex;
  gap: var(--maxit-gap);
  flex: 1;
  min-height: 0;
}

.picker-pane {
  display: flex;
  flex-direction: column;
  min-height: 0;
  border: 1px solid var(--v-pos-panel-border);
  background: var(--v-pos-panel-background);
  box-shadow: var(--v-pos-panel-shadow);
  transition: var(--v-theme-transition);
}

.picker-pane--search {
  flex: 0 0 clamp(340px, 42%, 520px);
}

.picker-pane--lines {
  flex: 1;
  min-width: 0;
}

.picker-pane__body {
  display: flex;
  flex-direction: column;
  gap: var(--maxit-gap);
  flex: 1;
  min-height: 0;
  padding: var(--maxit-pane-padding);
}

.pane-header {
  display: flex;
  align-items: center;
  gap: var(--maxit-gap-sm);
  min-height: 36px;
}

.pane-header__title {
  font-size: 1rem;
  font-weight: 700;
  padding-inline: 4px;
}

.pane-header__sub {
  font-size: 0.8125rem;
  font-weight: 600;
  color: rgba(var(--v-theme-on-surface), 0.72);
}

.picker-results,
.picker-lines {
  display: flex;
  flex-direction: column;
  gap: var(--maxit-gap-xs);
  flex: 1;
  min-height: 0;
  overflow-y: auto;
}

.result-row {
  margin-block-end: var(--maxit-gap-xs);
  border: 1px solid var(--v-pos-panel-border-soft);
}

.result-row__name,
.picker-line__name {
  font-size: 0.875rem;
  font-weight: 600;
  line-height: 1.35;
}

.result-row__sub,
.picker-line__sub {
  font-size: 0.8125rem;
  font-weight: 500;
  color: rgba(var(--v-theme-on-surface), 0.72);
}

.picker-line {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 8px;
  padding: 8px 10px;
  border: 1px solid var(--v-pos-panel-border-soft);
  border-radius: 8px;
  background: var(--v-pos-field-background);
  transition: background-color 0.4s ease;
}

.picker-line--flash {
  background: rgba(var(--v-theme-primary), 0.16);
}

.picker-line--over {
  border-color: rgb(var(--v-theme-error));
}

.picker-line--over .picker-line__sub {
  color: rgb(var(--v-theme-error));
  font-weight: 700;
}

.picker-line__main {
  flex: 1 1 200px;
  min-width: 0;
}

.picker-line__qty {
  display: flex;
  align-items: center;
  gap: 6px;
}

.picker-line__qty-input {
  width: 84px;
  flex: 0 0 84px;
}

.picker-line__qty-input :deep(input) {
  text-align: center;
}

.picker-actions {
  display: flex;
  flex-wrap: wrap;
  gap: var(--maxit-gap-sm);
  padding-block-start: var(--maxit-gap);
  border-top: 1px solid var(--v-pos-panel-border-soft);
}

.picker-actions .v-btn {
  flex: 1 1 auto;
}

@media (max-width: 959px) {
  .picker-form {
    flex-direction: column;
  }

  .picker-pane--search {
    flex: 0 0 auto;
  }

  .picker-pane--search .picker-results {
    max-height: 40vh;
  }
}
</style>
