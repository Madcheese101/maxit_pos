<template>
	<PageSurface glow="info-warning" class="stock-entry-view pa-3">
		<div v-if="!stockEntryEnabled" class="stock-entry-disabled-state">
			<v-alert type="warning" variant="tonal">
				{{ __('You do not have permission to manage stock transfers.') }}
			</v-alert>
		</div>

		<template v-else>
			<StockTransferForm
				v-if="showCreateForm"
				@cancel="showCreateForm = false"
				@created="handleTransferCreated"
			/>

			<SurfaceCard v-else class="se-pane">
				<div class="se-pane__body">
					<div class="pane-header">
						<div class="pane-header__title">{{ __('Manage Stock Entry') }}</div>
						<v-spacer />
						<v-btn
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
							:title="__('Clear Filters')"
							:aria-label="__('Clear Filters')"
							@click="resetFilters"
						/>
						<v-btn
							v-if="xs"
							icon="mdi-plus"
							color="primary"
							variant="elevated"
							size="small"
							:aria-label="__('New Outgoing Entry')"
							@click="showCreateForm = true"
						/>
						<v-btn
							v-else
							color="primary"
							variant="elevated"
							prepend-icon="mdi-plus"
							@click="showCreateForm = true"
						>
							{{ __('New Outgoing Entry') }}
						</v-btn>
					</div>

					<v-btn-toggle
						v-model="activeTab"
						mandatory
						divided
						density="compact"
						color="primary"
						variant="outlined"
						class="se-tabs"
					>
						<v-btn value="outgoing" prepend-icon="mdi-upload">
							{{ xs ? __('Outgoing') : __('Outgoing Transfers') }} ({{ outgoingTransfers.length }})
						</v-btn>
						<v-btn value="incoming" prepend-icon="mdi-download">
							{{ xs ? __('Incoming') : __('Incoming Transfers') }} ({{ incomingTransfers.length }})
						</v-btn>
					</v-btn-toggle>

					<v-expand-transition>
						<div v-show="showFilters" class="filters-panel">
							<DateField
								v-model="fromDate"
								:label="__('From Date')"
								variant="outlined"
								density="compact"
								clearable
								hide-details
							/>
							<DateField
								v-model="toDate"
								:label="__('To Date')"
								variant="outlined"
								density="compact"
								clearable
								hide-details
							/>
							<!-- outgoing transfers always leave this branch, incoming ones always arrive here -->
							<v-autocomplete
								v-if="activeTab === 'incoming'"
								v-model="selectedFromBranch"
								:items="branchOptions"
								item-title="label"
								item-value="value"
								:label="__('From Branch')"
								variant="outlined"
								density="compact"
								:loading="isLoadingBranches"
								hide-details
								clearable
								no-filter
								@update:search="(search) => loadBranchOptions(search, 'from_branch')"
							/>
							<v-autocomplete
								v-else
								v-model="selectedToBranch"
								:items="branchOptions"
								item-title="label"
								item-value="value"
								:label="__('To Branch')"
								variant="outlined"
								density="compact"
								:loading="isLoadingBranches"
								hide-details
								clearable
								no-filter
								@update:search="(search) => loadBranchOptions(search, 'to_branch')"
							/>
							<v-autocomplete
								v-model="selectedItemCode"
								:items="itemCodeOptions"
								item-title="label"
								item-value="value"
								:label="__('Item Code')"
								variant="outlined"
								density="compact"
								:loading="isLoadingItems"
								hide-details
								clearable
								no-filter
								class="filters-panel__wide"
								@update:search="loadItemCodeOptions"
							>
								<template #item="{ props, item }">
									<v-list-item
										v-bind="props"
										:title="item.raw.label"
										:subtitle="item.raw.description || undefined"
									/>
								</template>
							</v-autocomplete>
						</div>
					</v-expand-transition>

					<div class="se-list">
						<v-progress-linear
							v-if="activeTab === 'outgoing' ? isLoadingOutgoing : isLoadingIncoming"
							indeterminate
							color="primary"
							class="mb-2"
						/>

						<div v-if="!currentTransfers.length" class="se-empty text-medium-emphasis">
							{{ activeTab === 'outgoing'
								? __('No outgoing transfers found for the selected filters.')
								: __('No incoming transfers found for the selected filters.') }}
						</div>

						<v-list v-else nav density="compact" bg-color="transparent" class="pa-0">
							<v-list-item
								v-for="item in currentTransfers"
								:key="item.name"
								rounded="lg"
								class="se-row"
								@click="openViewDialog(activeTab, item)"
							>
								<div class="se-row__line">
									<span class="se-row__title">{{ item.name }}</span>
									<v-chip size="small" :color="getStatusColor(item)" variant="flat" class="status-chip">
										{{ getStatusLabel(item) }}
									</v-chip>
								</div>
								<div class="se-row__meta">
									{{ formatDate(item.posting_date) }} ·
									<template v-if="activeTab === 'outgoing'">{{ __('To Branch') }}: {{ item.to_branch }}</template>
									<template v-else>{{ __('From Branch') }}: {{ item.from_branch }}</template>
								</div>
							</v-list-item>
						</v-list>
					</div>
				</div>

				<StockEntryViewDialog
					v-model="viewDialogOpen"
					:docname="selectedDocname"
					:source-tab="viewSourceTab"
					@updated="handleTransferUpdated"
				/>
			</SurfaceCard>
		</template>
	</PageSurface>
</template>

<script setup>
	import { computed, onMounted, ref, watch } from 'vue';
	import { storeToRefs } from 'pinia';
	import { useRoute, useRouter } from 'vue-router';
	import { useDisplay } from 'vuetify';
	import { usePosStore } from '../store/posStore';
	import StockTransferForm from './components/stock/StockTransferForm.vue';
	import StockEntryViewDialog from './components/stock/StockEntryViewDialog.vue';
	import PageSurface from './components/ui/PageSurface.vue';
	import SurfaceCard from './components/ui/SurfaceCard.vue';
	import DateField from './components/ui/DateField.vue';

	const __ = window.__;
	const frappe_ = window.frappe;
	const route = useRoute();
	const router = useRouter();
	const posStore = usePosStore();
	const { posProfileData } = storeToRefs(posStore);

	const showCreateForm = ref(false);
	const viewDialogOpen = ref(false);
	const selectedDocname = ref('');
	const viewSourceTab = ref('outgoing');
	const activeTab = ref('outgoing');
	const outgoingTransfers = ref([]);
	const incomingTransfers = ref([]);
	const isLoadingOutgoing = ref(false);
	const isLoadingIncoming = ref(false);
	const isLoadingBranches = ref(false);
	const isLoadingItems = ref(false);
	const branchOptions = ref([]);
	const itemCodeOptions = ref([]);
	const fromDate = ref('');
	const toDate = ref('');
	const selectedFromBranch = ref('');
	const selectedToBranch = ref('');
	const selectedItemCode = ref('');
	const routeItemCode = computed(() => {
		const itemCode = route.query.item_code;
		if (Array.isArray(itemCode)) {
			return (itemCode[0] || '').toString();
		}
		return (itemCode || '').toString();
	});

	// filters start open on laptops, collapsed on phones and tablets
	const { mdAndUp, xs } = useDisplay();
	const showFilters = ref(mdAndUp.value);
	const currentTransfers = computed(() => activeTab.value === 'outgoing' ? outgoingTransfers.value : incomingTransfers.value);
	// only the branch filter shown for the active tab counts
	const activeFilterCount = computed(() => [
		fromDate.value,
		toDate.value,
		activeTab.value === 'incoming' ? selectedFromBranch.value : selectedToBranch.value,
		selectedItemCode.value,
	].filter(Boolean).length);

	const stockEntryEnabled = computed(() => {
		const roles = ['Stock User', 'Stock Manager', 'Administrator', 'System Manager'];
		return roles.some((role) => frappe_.user.has_role(role));
	});

	onMounted(async () => {
		if (!stockEntryEnabled.value) {
			return;
		}

		await Promise.all([loadBranchOptions(), loadItemCodeOptions(routeItemCode.value)]);
	});

	watch(
		routeItemCode,
		async (itemCode) => {
			if (!stockEntryEnabled.value) {
				return;
			}

			selectedItemCode.value = itemCode;
			ensureItemCodeOption(itemCode);

			if (itemCode) {
				await loadItemCodeOptions(itemCode);
			}

			await loadTransfers();
		},
		{ immediate: true }
	);

	// filters apply on change; the item code goes through the route query
	watch([fromDate, toDate, selectedFromBranch, selectedToBranch], () => {
		loadTransfers();
	});

	watch(selectedItemCode, (itemCode) => {
		// the route watcher already reloads when the item code came from the route
		if ((itemCode || '') === routeItemCode.value) {
			return;
		}
		applyFilters();
	});

	function formatDate(value) {
		return value ? frappe_.datetime.str_to_user(value) : '';
	}

	function buildFilters() {
		return {
			from_date: fromDate.value || '',
			to_date: toDate.value || '',
			from_branch: selectedFromBranch.value || '',
			to_branch: selectedToBranch.value || '',
			item_code: selectedItemCode.value || '',
		};
	}

	function getStatusLabel(item) {
		const docstatus = Number(item.docstatus);
		const add_to_transit = Number(item.add_to_transit);
		if (docstatus === 0) {
			return __('Draft');
		}
		if (docstatus === 2) {
			return __('Cancelled');
		}
		if (Number(item.per_transferred || 0) > 0) {
			return __('Received');
		}
		if (add_to_transit === 1 && !item.outgoing_stock_entry) {
			return __('In Transit');
		}
		if(add_to_transit === 0) {
			return __('Received');
		}
		return __('Submitted');
	}

	function getStatusColor(item) {
		const docstatus = Number(item.docstatus);
		const add_to_transit = Number(item.add_to_transit);
		if (docstatus === 0) {
			return 'grey';
		}
		if (docstatus === 2) {
			return 'error';
		}
		if (Number(item.per_transferred || 0) > 0) {
			return 'success';
		}

		if (add_to_transit === 1 && !item.outgoing_stock_entry) {
			return 'warning';
		}
		if(add_to_transit === 0 && item.outgoing_stock_entry) {
			return 'success';
		}
		return 'info';
	}

	function openViewDialog(sourceTab, item) {
		selectedDocname.value = item.name;
		viewSourceTab.value = sourceTab;
		viewDialogOpen.value = true;
	}

	async function loadBranchOptions(search = '', linkFieldname = 'from_branch') {
		isLoadingBranches.value = true;
		try {
			const response = await frappe.call({
				method: 'frappe.desk.search.search_link',
				args: {
					doctype: 'Branch',
					txt: search || '',
					page_length: 20,
					ignore_user_permissions: 1,
					reference_doctype: 'Stock Entry',
					link_fieldname: linkFieldname,
				},
			});

			branchOptions.value = (response.message || []).map((item) => ({
				value: item.value,
				label: item.label || item.value,
				description: item.description || '',
			}));
		} catch (error) {
			frappe_.msgprint({
				title: __('Branch search failed'),
				indicator: 'red',
				message: error?.message || String(error),
			});
		} finally {
			isLoadingBranches.value = false;
		}
	}

	async function loadItemCodeOptions(search = '') {
		isLoadingItems.value = true;
		try {
			const response = await frappe.call({
				method: 'frappe.desk.search.search_link',
				args: {
					doctype: 'Item',
					txt: search || '',
					page_length: 20,
				},
			});

			itemCodeOptions.value = (response.message || []).map((item) => ({
				value: item.value,
				label: item.label || item.value,
				description: item.description || '',
			}));
		} catch (error) {
			frappe_.msgprint({
				title: __('Item search failed'),
				indicator: 'red',
				message: error?.message || String(error),
			});
		} finally {
			isLoadingItems.value = false;
		}
	}

	function ensureItemCodeOption(itemCode) {
		if (!itemCode || itemCodeOptions.value.some((option) => option.value === itemCode)) {
			return;
		}

		itemCodeOptions.value = [
			{ value: itemCode, label: itemCode, description: '' },
			...itemCodeOptions.value,
		];
	}

	async function loadOutgoingTransfers() {
		isLoadingOutgoing.value = true;
		try {
			const response = await frappe.call({
				method: 'maxit_pos.maxit_pos.page.maxit_pos.api.stock_entry_vue.get_outgoing_transfers',
				args: {
					filters: JSON.stringify(buildFilters()),
				},
			});

			outgoingTransfers.value = response.message || [];
		} finally {
			isLoadingOutgoing.value = false;
		}
	}

	async function loadIncomingTransfers() {
		isLoadingIncoming.value = true;
		try {
			const response = await frappe.call({
				method: 'maxit_pos.maxit_pos.page.maxit_pos.api.stock_entry_vue.get_incoming_transfers',
				args: {
					filters: JSON.stringify(buildFilters()),
				},
			});

			incomingTransfers.value = response.message || [];
		} finally {
			isLoadingIncoming.value = false;
		}
	}

	async function loadTransfers() {
		await Promise.all([loadOutgoingTransfers(), loadIncomingTransfers()]);
	}

	async function applyFilters() {
		const nextItemCode = selectedItemCode.value || '';
		if (nextItemCode === routeItemCode.value) {
			await loadTransfers();
			return;
		}

		const nextQuery = { ...route.query };
		if (nextItemCode) {
			nextQuery.item_code = nextItemCode;
		} else {
			delete nextQuery.item_code;
		}

		await router.replace({ query: nextQuery });
	}

	// the filter watchers reload the lists
	function resetFilters() {
		fromDate.value = '';
		toDate.value = '';
		selectedFromBranch.value = '';
		selectedToBranch.value = '';
		selectedItemCode.value = '';
	}

	function handleTransferCreated() {
		showCreateForm.value = false;
		loadTransfers();
	}

	function handleTransferUpdated() {
		loadTransfers();
	}
</script>

<style scoped>
	.stock-entry-view {
		background:
			radial-gradient(circle at top right, var(--v-pos-info-glow), transparent 42%),
			radial-gradient(circle at left bottom, var(--v-pos-warning-glow), transparent 36%);
	}

	.stock-entry-disabled-state {
		align-self: flex-start;
		width: min(100%, 520px);
	}

	.se-pane {
		display: flex;
		flex-direction: column;
		flex: 1;
		min-height: 0;
		border: 1px solid var(--v-pos-panel-border);
		background: var(--v-pos-panel-background);
		box-shadow: var(--v-pos-panel-shadow);
		transition: var(--v-theme-transition);
	}

	.se-pane__body {
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
		min-width: 0;
		font-size: 1rem;
		font-weight: 700;
		padding-inline: 4px;
		white-space: nowrap;
		overflow: hidden;
		text-overflow: ellipsis;
	}

	.se-tabs {
		flex-shrink: 0;
		max-width: 520px;
	}

	.se-tabs .v-btn {
		flex: 1;
		font-weight: 700;
	}

	.filters-panel {
		display: grid;
		grid-template-columns: repeat(auto-fill, minmax(170px, 1fr));
		gap: var(--maxit-gap);
	}

	.filters-panel__wide {
		grid-column: span 2;
	}

	@media (max-width: 599px) {
		.se-tabs {
			max-width: none;
		}

		.filters-panel__wide {
			grid-column: 1 / -1;
		}
	}

	.se-list {
		flex: 1;
		min-height: 0;
		overflow-y: auto;
	}

	.se-empty {
		padding: 24px 8px;
		text-align: center;
	}

	.se-row {
		margin-block-end: var(--maxit-gap-xs);
		border: 1px solid var(--v-pos-panel-border-soft);
	}

	.se-row :deep(.v-list-item__content) {
		display: flex;
		flex-direction: column;
		gap: 2px;
	}

	.se-row__line {
		display: flex;
		align-items: center;
		justify-content: space-between;
		gap: 8px;
	}

	.se-row__title {
		min-width: 0;
		font-size: 0.875rem;
		font-weight: 700;
	}

	.se-row__meta {
		font-size: 0.8125rem;
		font-weight: 500;
		color: rgba(var(--v-theme-on-surface), 0.72);
	}

	.status-chip {
		flex-shrink: 0;
		font-weight: 700;
	}
</style>
