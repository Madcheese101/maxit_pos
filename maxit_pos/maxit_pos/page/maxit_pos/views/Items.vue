<template>
	<PageSurface glow="info-success" class="items-view pa-2 pa-md-4" :style="layoutVars">
		<SurfaceCard surface="filter" class="pa-3 pa-md-4 items-filters-card">
			<v-row dense>
				<v-col cols="12" md="4">
					<v-text-field
						v-model="searchTerm"
						:label="__('Search Items')"
						:placeholder="__('Search by code or name')"
						prepend-inner-icon="mdi-magnify"
						variant="solo-filled"
						density="comfortable"
						hide-details
						single-line
						clearable
						@keydown.enter="triggerImmediateSearch"
					/>
				</v-col>

				<v-col
					v-for="filter in dynamicFilters"
					:key="filter.fieldname"
					:sm="filter.field_type === 'Check' ? 1 : 2"
					:md="filter.field_type === 'Check' ? 1 : 2"
					:class="filter.field_type === 'Check' ? 'd-flex align-center' : ''"
				>
					<v-select
						v-if="filter.field_type === 'Select' || filter.field_type === 'Link'"
						v-model="filter.selected"
						:label="filter.label"
						:items="filter.options || []"
						variant="solo-filled"
						density="comfortable"
						hide-details
						clearable
					/>
					<v-checkbox
						v-else-if="filter.field_type === 'Check'"
						:label="filter.label"
						v-model="filter.selected"
						density="compact"
						hide-details
						class="mt-0 pt-0"
					/>
					<v-text-field
						v-else
						v-model="filter.selected"
						:label="filter.label"
						variant="solo-filled"
						density="comfortable"
						hide-details
						clearable
					/>
				</v-col>

				<v-col cols="12" md="2" class="d-flex align-center">
					<v-btn
						variant="tonal"
						color="primary"
						block
						@click="resetLocalFilters"
					>
						{{ __('Reset Filters') }}
					</v-btn>
				</v-col>
			</v-row>
		</SurfaceCard>

		<SurfaceCard surface="results" class="mt-4 items-results-card">
			<v-card-item>
				<div class="d-flex justify-space-between align-center flex-wrap ga-2">
					<div>
						<div class="text-overline text-medium-emphasis">{{ __('Items Browser') }}</div>
						<div class="text-h6 font-weight-bold">{{ __('Search Results') }}</div>
					</div>
					<v-chip size="small" color="primary" variant="tonal">
						{{ rawItems.length }}
					</v-chip>
				</div>
			</v-card-item>

			<v-card-text class="items-results-body">
				<v-alert
					v-if="errorMessage"
					type="error"
					variant="tonal"
					class="mb-3 items-state-message"
				>
					{{ errorMessage }}
				</v-alert>

				<v-skeleton-loader
					v-if="isLoading"
					type="table"
					class="items-state-loader"
				/>

				<v-alert
					v-else-if="!searchTerm.trim()"
					type="info"
					variant="tonal"
					class="items-state-message"
				>
					{{ __('Type in search to load items from database.') }}
				</v-alert>

				<v-alert
					v-else-if="!rawItems.length"
					type="warning"
					variant="tonal"
					class="items-state-message"
				>
					{{ __('No items found for this search/filter combination.') }}
				</v-alert>

				<div v-else class="items-table-wrap">
					<v-data-table-virtual
						:headers="headers"
						:items="rawItems"
						item-value="item_code"
						density="comfortable"
						class="items-table"
						height="100%"
						fixed-header
					>
						<template #item.item_name="{ item }">
							<div class="font-weight-bold">{{ item.item_name }}</div>
						</template>
						<template #item.rate="{ item }">
							<div class="font-weight-bold">{{ item.rate }} {{ item.currency }}</div>
						</template>
						<template #item.get_stock_btn="{ item }">
							<v-menu location="bottom end" offset="8">
								<template #activator="{ props }">
									<v-btn
										v-bind="props"
										icon="mdi-dots-vertical"
										variant="text"
										size="small"
										color="primary"
									/>
								</template>

								<SurfaceCard surface="menu" min-width="220">
									<v-card-text class="pa-2 d-flex flex-column ga-2">
										<v-btn
											color="primary"
											variant="text"
											prepend-icon="mdi-package-variant"
											justify="start"
											@click="getItemStock(item)"
										>
											{{ __('Get Stock') }}
										</v-btn>

										<v-btn
											color="secondary"
											variant="text"
											prepend-icon="mdi-swap-horizontal"
											justify="start"
											@click="openStockEntry(item)"
										>
											{{ __('Stock Entry') }}
										</v-btn>

										<v-btn
											color="secondary"
											variant="text"
											prepend-icon="mdi-receipt-text-outline"
											justify="start"
											@click="openOrders(item)"
										>
											{{ __('Orders') }}
										</v-btn>
									</v-card-text>
								</SurfaceCard>
							</v-menu>
						</template>
					</v-data-table-virtual>
				</div>

			</v-card-text>
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
const { smAndDown, height: viewportHeight } = useDisplay();
const isMobile = computed(() => smAndDown.value);

const viewportHeightPx = computed(() => viewportHeight.value || window.innerHeight || 800);
const itemsTableHeight = computed(() => {
	const reserved = isMobile.value ? 420 : 340;
	return Math.max(150, viewportHeightPx.value - reserved);
});

const layoutVars = computed(() => ({
	'--items-table-height': `${itemsTableHeight.value}px`,
}));

const baseHeaders = [
	{ title: __('Item Code'), key: 'item_code' },
	{ title: __('Item Name'), key: 'item_name' },
	// { title: __('Item Group'), key: 'item_group' },
	{ title: __('Rate'), key: 'rate' },
	{ title: __('Qty'), key: 'actual_qty' },
	{ title: __(''), key: 'get_stock_btn', width: '50px', sortable: false },
];

const headers = computed(() => {
	const attributeHeaders = [];
	const seenKeys = new Set();

	dynamicFilters.value.forEach((filter) => {
		if (filter.doctype !== 'Item Attribute Value' || !filter.fieldname) {
			return;
		}
		if (seenKeys.has(filter.fieldname)) {
			return;
		}
		seenKeys.add(filter.fieldname);
		attributeHeaders.push({
			title: __(filter.label || filter.fieldname),
			key: filter.fieldname,
		});
	});

	return [
		baseHeaders[0],
		baseHeaders[1],
		// baseHeaders[2],
		...attributeHeaders,
		baseHeaders[2],
		baseHeaders[3],
		baseHeaders[4],
	];
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
	const term = searchTerm.value.trim();
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
	if (!searchTerm.value.trim()) {
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
.items-view {
	min-height: calc(100dvh - var(--v-layout-top, 0px) - var(--v-layout-bottom, 0px));
	height: calc(100dvh - var(--v-layout-top, 0px) - var(--v-layout-bottom, 0px));
	display: flex;
	flex-direction: column;
	overflow-y: auto;
	overflow-x: hidden;
}

.items-filters-card {
	flex: 0 0 auto;
}

.items-results-card {
	flex: 1;
	min-height: 0;
	display: flex;
	flex-direction: column;
}

.items-results-body {
	flex: 1;
	min-height: 0;
	display: flex;
	flex-direction: column;
	overflow: hidden;
}

.items-state-message,
.items-state-loader {
	flex: 0 0 auto;
}

.items-table-wrap {
	flex: 1;
	min-height: 150px;
	height: min(var(--items-table-height), 100%);
	max-height: 100%;
	overflow: hidden;
}

.items-table {
	border-radius: 14px;
	height: 100%;
}

.items-table :deep(.v-table__wrapper) {
	height: 100%;
	max-height: 100%;
	overflow-y: auto;
}

@media (max-width: 960px) {
	.items-view {
		padding: 10px;
	}

	.items-table-wrap {
		min-height: 130px;
	}
}

@media (max-height: 720px) {
	.items-view {
		padding-top: 8px;
		padding-bottom: 8px;
	}
}
</style>