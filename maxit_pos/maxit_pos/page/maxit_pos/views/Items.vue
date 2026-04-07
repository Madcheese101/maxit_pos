<template>
	<v-main class="items-view pa-3 pa-md-6">
		<v-card rounded="xl" variant="flat" class="pa-3 pa-md-4">
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
		</v-card>

		<v-card rounded="xl" variant="flat" class="mt-4">
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

			<v-card-text>
				<v-alert
					v-if="errorMessage"
					type="error"
					variant="tonal"
					class="mb-3"
				>
					{{ errorMessage }}
				</v-alert>

				<v-skeleton-loader
					v-if="isLoading"
					type="table"
				/>

				<v-alert
					v-else-if="!searchTerm.trim()"
					type="info"
					variant="tonal"
				>
					{{ __('Type in search to load items from database.') }}
				</v-alert>

				<v-alert
					v-else-if="!rawItems.length"
					type="warning"
					variant="tonal"
				>
					{{ __('No items found for this search/filter combination.') }}
				</v-alert>

				<v-data-table-virtual
					v-else
					:headers="headers"
					:items="rawItems"
					item-value="item_code"
					density="comfortable"
					class="items-table"
                    height="75vh"
                    fixed-header
				>
					<template #item.item_name="{ item }">
						<div class="font-weight-bold">{{ item.item_name }}</div>
					</template>
					<template #item.rate="{ item }">
						<div class="font-weight-bold">{{ item.rate }} {{ item.currency }}</div>
					</template>
                </v-data-table-virtual>

			</v-card-text>
		</v-card>
	</v-main>
</template>

<script setup>
import { computed, ref, watch } from 'vue';
import { storeToRefs } from 'pinia';
import { usePosStore } from '../store/posStore';

const frappe_ = window.frappe;
const __ = window.__;

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

const baseHeaders = [
	{ title: __('Item Code'), key: 'item_code' },
	{ title: __('Item Name'), key: 'item_name' },
	// { title: __('Item Group'), key: 'item_group' },
	{ title: __('Rate'), key: 'rate' },
	{ title: __('Qty'), key: 'actual_qty' },
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
	];
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
.items-table {
	border-radius: 14px;
}
</style>