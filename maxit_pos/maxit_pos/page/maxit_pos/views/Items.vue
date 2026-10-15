<template>
	<PageSurface glow="info-success" class="items-view pa-3">
		<SurfaceCard class="items-pane">
			<div class="items-pane__body">
				<div class="pane-header">
					<div class="pane-header__title">{{ __('Items Browser') }}</div>
					<v-chip size="x-small" color="primary" variant="tonal">{{ rawItems.length }}</v-chip>
				</div>

				<div class="filters-row">
					<v-text-field
						v-model="searchTerm"
						:placeholder="__('Search by code or name')"
						prepend-inner-icon="mdi-magnify"
						variant="outlined"
						density="compact"
						hide-details
						single-line
						clearable
						class="filters-row__search"
						@keydown.enter="triggerImmediateSearch"
					/>
					<v-btn
						v-if="dynamicFilters.length"
						icon
						size="small"
						variant="tonal"
						:color="showFilters ? 'primary' : undefined"
						:title="__('Filter')"
						:aria-label="__('Filter')"
						@click="showFilters = !showFilters"
					>
						<v-badge v-if="activeFilterCount" :content="activeFilterCount" color="primary" floating>
							<v-icon icon="mdi-filter-variant" />
						</v-badge>
						<v-icon v-else icon="mdi-filter-variant" />
					</v-btn>
					<v-btn
						v-if="activeFilterCount"
						icon="mdi-filter-remove-outline"
						size="small"
						variant="text"
						:title="__('Reset Filters')"
						:aria-label="__('Reset Filters')"
						@click="resetLocalFilters"
					/>
				</div>

				<v-expand-transition>
					<div v-show="showFilters && dynamicFilters.length" class="filters-panel">
						<template v-for="filter in dynamicFilters" :key="filter.fieldname">
							<v-select
								v-if="filter.field_type === 'Select' || filter.field_type === 'Link'"
								v-model="filter.selected"
								:label="filter.label"
								:items="filter.options || []"
								variant="outlined"
								density="compact"
								hide-details
								clearable
							/>
							<v-checkbox
								v-else-if="filter.field_type === 'Check'"
								v-model="filter.selected"
								:label="filter.label"
								density="compact"
								hide-details
							/>
							<v-text-field
								v-else
								v-model="filter.selected"
								:label="filter.label"
								variant="outlined"
								density="compact"
								hide-details
								clearable
							/>
						</template>
					</div>
				</v-expand-transition>

				<v-alert v-if="errorMessage" type="error" variant="tonal" density="compact">
					{{ errorMessage }}
				</v-alert>

				<v-progress-linear v-if="isLoading" indeterminate color="primary" />

				<div v-if="!searchTerm?.trim()" class="items-empty text-medium-emphasis">
					<v-icon icon="mdi-magnify" size="32" />
					<div>{{ __('Type in search to load items from database.') }}</div>
				</div>

				<div v-else-if="!rawItems.length && !isLoading" class="items-empty text-medium-emphasis">
					{{ __('No items found for this search/filter combination.') }}
				</div>

				<!-- searches can return thousands of items, so only visible rows are rendered -->
				<v-virtual-scroll v-else :items="rawItems" item-key="item_code" class="items-list">
					<template #default="{ item }">
						<div class="item-row">
							<div class="item-row__main">
								<div class="item-row__line">
									<span class="item-row__name">{{ item.item_name }}</span>
									<v-chip
										size="small"
										variant="flat"
										:color="item.actual_qty > 0 ? 'success' : 'error'"
										prepend-icon="mdi-package-variant-closed"
										class="item-row__qty"
										:title="__('Qty')"
									>
										{{ item.actual_qty }}
									</v-chip>
								</div>
								<div class="item-row__line item-row__line--sub">
									<span class="item-row__meta">
										{{ item.item_code }}<template v-for="attribute in attributeFields" :key="attribute.fieldname"><template v-if="item[attribute.fieldname]"> · {{ attribute.label }}: {{ item[attribute.fieldname] }}</template></template>
									</span>
									<span class="item-row__rate">{{ item.rate }} {{ item.currency }}</span>
								</div>
							</div>
							<v-menu location="bottom end" offset="4">
								<template #activator="{ props }">
									<v-btn
										v-bind="props"
										icon="mdi-dots-vertical"
										variant="text"
										size="small"
										color="primary"
										:aria-label="__('Actions')"
									/>
								</template>
								<v-list density="compact">
									<v-list-item prepend-icon="mdi-package-variant" :title="__('Get Stock')" @click="getItemStock(item)" />
									<v-list-item prepend-icon="mdi-swap-horizontal" :title="__('Stock Entry')" @click="openStockEntry(item)" />
									<v-list-item prepend-icon="mdi-receipt-text-outline" :title="__('Orders')" @click="openOrders(item)" />
								</v-list>
							</v-menu>
						</div>
					</template>
				</v-virtual-scroll>
			</div>
		</SurfaceCard>
	</PageSurface>
</template>

<script>
export default {
	name: 'Items',
};
</script>

<script setup>
import { computed, ref, watch } from 'vue';
import { storeToRefs } from 'pinia';
import { useRouter } from 'vue-router';
import { useDisplay } from 'vuetify';
import { usePosStore } from '../store/posStore';
import PageSurface from './components/ui/PageSurface.vue';
import SurfaceCard from './components/ui/SurfaceCard.vue';

const frappe_ = window.frappe;
const __ = window.__;
const router = useRouter();

const posStore = usePosStore();
const { posProfileData } = storeToRefs(posStore);

const searchTerm = ref('');
const rawItems = ref([]);
const dynamicFilters = ref([]);
const isLoading = ref(false);
const errorMessage = ref('');
const searchRequestId = ref(0);
let searchTimer = null;
let filterTimer = null;
// filters start open on laptops, collapsed on phones and tablets
const { mdAndUp } = useDisplay();
const showFilters = ref(mdAndUp.value);
const activeFilterCount = computed(() => dynamicFilters.value.filter((filter) => filter.selected).length);

// attribute filters double as the attribute values shown on each item row
const attributeFields = computed(() => {
	const seenKeys = new Set();
	return dynamicFilters.value
		.filter((filter) => filter.doctype === 'Item Attribute Value' && filter.fieldname)
		.filter((filter) => !seenKeys.has(filter.fieldname) && seenKeys.add(filter.fieldname))
		.map((filter) => ({ fieldname: filter.fieldname, label: __(filter.label || filter.fieldname) }));
});

const getItemStock = async (item) => {
	const method = posProfileData.value?.allow_purchase ? 'get_item_stock_from_main_company' : 'get_item_stock_from_sister_branches';
	frappe.call({
		method: `maxit_pos.maxit_pos.page.maxit_pos.api.items_vue.${method}`,
		args: {
			item_code: item.item_code,
			item_name: item.item_name || '',
			warehouse: posProfileData.value?.warehouse || '',
		},
		freeze: true,
		freeze_message: __('Getting stock...'),
	});
};

const openStockEntry = (item) => router.push({
	name: 'StockEntry',
	query: { item_code: item.item_code || '' },
});

const openOrders = (item) => router.push({
	name: 'Orders',
	query: { item_code: item.item_code || '' },
});

const loadDynamicFilters = async () => {
	const customFilters = posProfileData.value?.custom_filters || [];
	if (!customFilters.length) {
		dynamicFilters.value = [];
		return;
	}

	try {
		const response = await frappe.call({
			method: 'maxit_pos.maxit_pos.page.maxit_pos.api.api.get_advanced_item_filters_dict',
			args: { custom_filters: customFilters },
		});

		dynamicFilters.value = (response.message || []).map((filter) => ({
			...filter,
			selected: '',
		}));
	} catch (error) {
		errorMessage.value = __('Failed to load dynamic filters.');
		dynamicFilters.value = [];
	}
};

const fetchItems = async () => {
	const term = (searchTerm.value || '').trim();
	errorMessage.value = '';

	if (!posProfileData.value?.warehouse || !posProfileData.value?.selling_price_list) {
		rawItems.value = [];
		errorMessage.value = __('POS profile data is not ready yet.');
		isLoading.value = false;
		return;
	}

	if (!term) {
		rawItems.value = [];
		isLoading.value = false;
		return;
	}

	const requestId = ++searchRequestId.value;
	isLoading.value = true;
	try {
		const response = await frappe.call({
			method: 'maxit_pos.maxit_pos.page.maxit_pos.api.api.get_items_browser',
			freeze: false,
			args: {
				pos_profile_data: posProfileData.value,
				search_term: term,
				custom_filters: dynamicFilters.value,
			},
		});

		if (requestId !== searchRequestId.value) {
			return;
		}

		rawItems.value = response.message?.items || [];
	} catch (error) {
		if (requestId !== searchRequestId.value) {
			return;
		}
		rawItems.value = [];
		errorMessage.value = __('Failed to load items.');
	}

	if (requestId === searchRequestId.value) {
		isLoading.value = false;
	}
};

const triggerImmediateSearch = () => {
	if (searchTimer) {
		clearTimeout(searchTimer);
		searchTimer = null;
	}
	fetchItems();
};

const resetLocalFilters = () => {
	dynamicFilters.value = dynamicFilters.value.map((filter) => ({
		...filter,
		selected: filter.field_type === 'Check' ? false : '',
	}));
};

const scheduleFilterFetch = () => {
	if (!(searchTerm.value || '').trim()) {
		return;
	}

	if (filterTimer) {
		clearTimeout(filterTimer);
	}

	filterTimer = setTimeout(() => {
		fetchItems();
	}, 150);
};

watch(
	searchTerm,
	() => {
		if (searchTimer) {
			clearTimeout(searchTimer);
		}
		searchTimer = setTimeout(() => {
			fetchItems();
		}, 350);
	},
	{ flush: 'post' }
);

watch(
	dynamicFilters,
	() => {
		scheduleFilterFetch();
	},
	{ deep: true }
);

watch(
	() => posProfileData.value?.name,
	async (profileName) => {
		if (!profileName) return;
		await loadDynamicFilters();
	},
	{ immediate: true }
);
</script>

<style scoped>
.items-pane {
	display: flex;
	flex-direction: column;
	flex: 1;
	min-height: 0;
	border: 1px solid var(--v-pos-panel-border);
	background: var(--v-pos-panel-background);
	box-shadow: var(--v-pos-panel-shadow);
	transition: var(--v-theme-transition);
}

.items-pane__body {
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

.filters-row {
	display: flex;
	align-items: center;
	gap: var(--maxit-gap-sm);
}

.filters-row__search {
	flex: 1;
	max-width: 480px;
}

.filters-panel {
	display: grid;
	grid-template-columns: repeat(auto-fill, minmax(160px, 1fr));
	gap: var(--maxit-gap);
}

@media (max-width: 599px) {
	.filters-row__search {
		max-width: none;
	}
}

.items-empty {
	display: flex;
	flex-direction: column;
	align-items: center;
	gap: 4px;
	padding: 32px 8px;
	text-align: center;
}

.items-list {
	flex: 1;
	min-height: 0;
}

.item-row {
	display: flex;
	align-items: center;
	gap: 4px;
	margin-block-end: var(--maxit-gap-xs);
	padding: 8px 6px 8px 12px;
	border: 1px solid var(--v-pos-panel-border-soft);
	border-radius: 10px;
	background: var(--v-pos-field-background);
}

.item-row__main {
	flex: 1;
	min-width: 0;
	display: flex;
	flex-direction: column;
	gap: 2px;
}

.item-row__line {
	display: flex;
	align-items: center;
	justify-content: space-between;
	gap: 8px;
}

.item-row__name {
	min-width: 0;
	font-size: 0.875rem;
	font-weight: 700;
	line-height: 1.35;
}

.item-row__qty {
	flex-shrink: 0;
	font-weight: 700;
}

.item-row__line--sub {
	font-size: 0.8125rem;
}

.item-row__meta {
	min-width: 0;
	color: rgba(var(--v-theme-on-surface), 0.72);
	font-weight: 500;
	overflow-wrap: anywhere;
}

.item-row__rate {
	flex-shrink: 0;
	font-weight: 700;
}
</style>
