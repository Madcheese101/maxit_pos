<template>
	<v-main class="stock-entry-view pa-3 pa-md-6">
		<v-alert v-if="!stockEntryEnabled" type="warning" variant="tonal">
			{{ __('You do not have permission to manage stock transfers.') }}
		</v-alert>

		<template v-else>
			<v-card class="stock-entry-panel mb-2" rounded="xl" variant="flat">
				<v-card-item>
					<div class="d-flex align-center justify-space-between flex-wrap gap-3">
						<div>
							<div class="text-h6 font-weight-bold">{{ __('Manage Stock Entry') }}</div>
						</div>
						<v-btn
							color="primary"
							variant="elevated"
							prepend-icon="mdi-plus"
							@click="transferDialogOpen = true"
						>
							{{ __('New Outgoing Entry') }}
						</v-btn>
					</div>
				</v-card-item>

				<v-divider />

				<v-card-text class="pt-1">
					<v-row dense>
						<v-col cols="12" md="2">
							<v-text-field
								v-model="fromDate"
								type="date"
								:label="__('From Date')"
								variant="outlined"
								density="compact"
								hide-details
							/>
						</v-col>

						<v-col cols="12" md="2">
							<v-text-field
								v-model="toDate"
								type="date"
								:label="__('To Date')"
								variant="outlined"
								density="compact"
								hide-details
							/>
						</v-col>

						<v-col cols="12" md="2">
							<v-autocomplete
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
						</v-col>

						<v-col cols="12" md="2">
							<v-autocomplete
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
						</v-col>

						<v-col cols="12" md="4">
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
						</v-col>
					</v-row>

					<div class="d-flex justify-end flex-wrap ga-2 mt-3">
						<v-btn color="primary" variant="tonal" prepend-icon="mdi-filter-check" @click="loadTransfers">
							{{ __('Apply Filters') }}
						</v-btn>
						<v-btn variant="text" prepend-icon="mdi-filter-remove-outline" @click="resetFilters">
							{{ __('Clear Filters') }}
						</v-btn>
					</div>
				</v-card-text>
			</v-card>

			<v-card class="stock-entry-panel stock-entry-table-panel" rounded="xl" variant="flat">
				<v-tabs v-model="activeTab" color="primary" class="px-2 pt-2">
					<v-tab value="outgoing">
						<v-icon size="18" class="me-2">mdi-upload</v-icon>
						{{ __('Outgoing Transfers') }}
					</v-tab>
					<v-tab value="incoming">
						<v-icon size="18" class="me-2">mdi-download</v-icon>
						{{ __('Incoming Transfers') }}
					</v-tab>
				</v-tabs>

				<v-divider />

				<v-window v-model="activeTab" class="stock-entry-window">
					<v-window-item value="outgoing" class="stock-entry-window-item">
						<div class="stock-entry-table-wrap">
							<v-data-table
								:headers="headers"
								:items="outgoingTransfers"
								item-value="name"
								:loading="isLoadingOutgoing"
								fixed-header
								height="100%"
								class="stock-entry-table"
							>
								<template #item.status="{ item }">
									<v-chip size="small" :color="getStatusColor(item)" variant="tonal">
										{{ getStatusLabel(item) }}
									</v-chip>
								</template>

								<template #item.actions="{ item }">
									<v-btn size="small" color="primary" variant="tonal" @click="openViewDialog('outgoing', item)">
										{{ __('View') }}
									</v-btn>
								</template>

								<template #no-data>
									<div class="pa-6 text-medium-emphasis text-center">
										{{ __('No outgoing transfers found for the selected filters.') }}
									</div>
								</template>
							</v-data-table>
						</div>
					</v-window-item>

					<v-window-item value="incoming" class="stock-entry-window-item">
						<div class="stock-entry-table-wrap">
							<v-data-table
								:headers="headers"
								:items="incomingTransfers"
								item-value="name"
								:loading="isLoadingIncoming"
								fixed-header
								height="100%"
								class="stock-entry-table"
							>
								<template #item.status="{ item }">
									<v-chip size="small" :color="getStatusColor(item)" variant="tonal">
										{{ getStatusLabel(item) }}
									</v-chip>
								</template>

								<template #item.actions="{ item }">
									<v-btn size="small" color="primary" variant="tonal" @click="openViewDialog('incoming', item)">
										{{ __('View') }}
									</v-btn>
								</template>

								<template #no-data>
									<div class="pa-6 text-medium-emphasis text-center">
										{{ __('No incoming transfers found for the selected filters.') }}
									</div>
								</template>
							</v-data-table>
						</div>
					</v-window-item>
				</v-window>
			</v-card>

			<StockTransferDialog v-model="transferDialogOpen" @created="handleTransferCreated" />
			<StockEntryViewDialog
				v-model="viewDialogOpen"
				:docname="selectedDocname"
				:source-tab="viewSourceTab"
				@updated="handleTransferUpdated"
			/>
		</template>
	</v-main>
</template>

<script setup>
	import { computed, onMounted, ref } from 'vue';
	import { storeToRefs } from 'pinia';
	import { usePosStore } from '../store/posStore';
	import StockTransferDialog from './components/stock/StockTransferDialog.vue';
	import StockEntryViewDialog from './components/stock/StockEntryViewDialog.vue';

	const __ = window.__;
	const frappe_ = window.frappe;
	const posStore = usePosStore();
	const { posProfileData } = storeToRefs(posStore);

	const transferDialogOpen = ref(false);
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

	const headers = computed(() => [
		{ title: __('Stock Entry'), key: 'name' },
		{ title: __('Posting Date'), key: 'posting_date' },
		{ title: __('From Branch'), key: 'from_branch' },
		{ title: __('To Branch'), key: 'to_branch' },
		{ title: __('Status'), key: 'status', sortable: false },
		{ title: __('Actions'), key: 'actions', sortable: false },
	]);

	const stockEntryEnabled = computed(() => {
		const roles = ['Purchase User', 'Purchase Manager', 'Administrator', 'System Manager'];
		return roles.some((role) => frappe_.user.has_role(role)) && posProfileData.value?.allow_purchase;
	});

	onMounted(async () => {
		if (!stockEntryEnabled.value) {
			return;
		}

		await Promise.all([loadBranchOptions(), loadItemCodeOptions(), loadTransfers()]);
	});

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
		if (add_to_transit === 1) {
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

		if (add_to_transit === 1) {
			return 'warning';
		}
		if(add_to_transit === 0) {
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

	function resetFilters() {
		fromDate.value = '';
		toDate.value = '';
		selectedFromBranch.value = '';
		selectedToBranch.value = '';
		selectedItemCode.value = '';
		loadTransfers();
	}

	function handleTransferCreated() {
		loadTransfers();
	}

	function handleTransferUpdated() {
		loadTransfers();
	}
</script>

<style scoped>
	.stock-entry-view {
		background:
			radial-gradient(circle at top right, rgba(25, 118, 210, 0.09), transparent 42%),
			radial-gradient(circle at left bottom, rgba(255, 167, 38, 0.08), transparent 36%);
		height: calc(100dvh - var(--v-layout-top, 0px) - var(--v-layout-bottom, 0px));
		min-height: calc(100dvh - var(--v-layout-top, 0px) - var(--v-layout-bottom, 0px));
		display: flex;
		flex-direction: column;
		overflow: hidden;
	}

	.stock-entry-panel {
		border: 1px solid rgba(120, 144, 156, 0.24);
		background: linear-gradient(180deg, rgba(255, 255, 255, 0.94), rgba(248, 251, 255, 0.97));
		box-shadow: 0 10px 24px rgba(12, 28, 43, 0.08);
	}

	.stock-entry-table-panel {
		flex: 1;
		min-height: 0;
		display: flex;
		flex-direction: column;
	}

	.stock-entry-window {
		flex: 1;
		min-height: 0;
		display: flex;
		flex-direction: column;
	}

	.stock-entry-window-item,
		.stock-entry-window :deep(.v-window__container),
		.stock-entry-window :deep(.v-window-item) {
			height: 100%;
			min-height: 0;
		}

	.stock-entry-table-wrap {
		padding: 0 16px 16px;
		height: 100%;
		min-height: 0;
	}

	.stock-entry-table {
		height: 100%;
	}

	.stock-entry-table :deep(th) {
		white-space: nowrap;
	}

	.stock-entry-table :deep(.v-table__wrapper) {
		height: 100%;
		max-height: 100%;
		overflow-y: auto;
	}
</style>