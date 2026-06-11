<template>
	<v-card class="stock-transfer-form">
		<v-card-item class="pb-2">
			<template #prepend>
				<v-btn :icon="backIcon" variant="text" class="me-1" @click="emit('cancel')" />
			</template>
			<div>
				<div class="text-h6 font-weight-bold">{{ __('Create Outgoing Transfer') }}</div>
			</div>
		</v-card-item>

		<v-divider />

		<v-card-text class="stock-transfer-form-body pt-4">
			<div class="transfer-branch-row">
				<v-autocomplete
					v-model="toBranch"
					:items="branchOptions"
					item-title="label"
					item-value="value"
					:label="__('To Branch')"
					variant="outlined"
					density="compact"
					:loading="isLoadingBranches"
					hide-details="auto"
					clearable
					no-filter
					@update:search="(search) => loadBranchOptions(search)"
				/>
			</div>

			<div class="d-flex align-center justify-space-between flex-wrap gap-2 mt-3 mb-2">
				<div class="text-subtitle-1 font-weight-bold">{{ __('Items') }}</div>
			</div>

			<div ref="itemsTableWrap" class="transfer-items-table-wrap">
				<v-table density="comfortable" class="transfer-items-table">
					<thead>
						<tr>
							<th class="transfer-col-index">{{ __('No.') }}</th>
							<th>{{ __('Item Code') }}</th>
							<th class="transfer-col-qty">{{ __('Qty') }}</th>
							<th class="transfer-col-actions">{{ __('Actions') }}</th>
						</tr>
					</thead>
					<tbody>
						<tr v-for="(row, index) in itemRows" :key="row.id">
							<td class="transfer-col-index text-medium-emphasis">{{ index + 1 }}</td>
							<td>
								<v-autocomplete
									v-model="row.item_code"
									v-model:search="row.search"
									:items="row.itemOptions"
									item-title="label"
									item-value="value"
									:label="__('Item Code')"
									variant="outlined"
									density="compact"
									:loading="row.isLoading"
									hide-details="auto"
									clearable
									no-filter
									@update:search="(search) => updateRowItemSearch(row, search)"
								>
									<template #item="{ props, item }">

										<v-list-item
											v-bind="props"
											:title="item.raw.label"
											:subtitle="item.raw.description || undefined"
										/>
									</template>
								</v-autocomplete>
							</td>
							<td class="transfer-col-qty">
								<v-text-field
									v-model="row.qty"
									type="number"
									min="0.01"
									step="0.01"
									:label="__('Qty')"
									variant="outlined"
									density="compact"
									hide-details="auto"
								/>
							</td>
							<td class="transfer-col-actions">
								<v-btn
									icon="mdi-delete-outline"
									variant="text"
									color="error"
									:disabled="itemRows.length === 1"
									@click="removeItemRow(index)"
								/>
							</td>
						</tr>
					</tbody>
					<tfoot>
						<tr>
							<td colspan="4" class="transfer-add-row-cell">
								<v-btn
									variant="text"
									color="primary"
									prepend-icon="mdi-plus"
									class="transfer-add-row-btn"
									@click="addItemRow"
								>
									{{ __('Add Row') }}
								</v-btn>
							</td>
						</tr>
					</tfoot>
				</v-table>
			</div>
		</v-card-text>

		<v-card-actions class="px-4 pb-4 pt-0 d-flex gap-2 flex-wrap">
			<v-spacer />
			<v-btn variant="tonal" @click="emit('cancel')">
				{{ __('Cancel') }}
			</v-btn>
			<v-btn
				color="primary"
				variant="elevated"
				prepend-icon="mdi-content-save"
				:loading="isSubmitting"
				@click="submitTransfer"
			>
				{{ __('Create') }}
			</v-btn>
		</v-card-actions>
	</v-card>
</template>

<script setup>
	import { nextTick, onMounted, ref } from 'vue';
	import SurfaceCard from '../ui/SurfaceCard.vue';

	const emit = defineEmits(['cancel', 'created']);

	const __ = window.__;
	const frappe_ = window.frappe;
	const backIcon = frappe_.utils?.is_rtl?.() ? 'mdi-arrow-right-thick' : 'mdi-arrow-left-thick';
	const branchOptions = ref([]);
	const defaultItemCodeOptions = ref([]);
	const isLoadingBranches = ref(false);
	const isSubmitting = ref(false);
	const itemsTableWrap = ref(null);
	const toBranch = ref('');
	const itemRows = ref([createEmptyRow()]);

	onMounted(async () => {
		await Promise.all([loadBranchOptions(), loadItemCodeOptions()]);
		itemRows.value = [createEmptyRow()];
	});

	function createEmptyRow() {
		return {
			id: `${Date.now()}-${Math.random()}`,
			item_code: '',
			qty: '',
			search: '',
			isLoading: false,
			itemOptions: [...defaultItemCodeOptions.value],
		};
	}

	async function addItemRow() {
		itemRows.value.push(createEmptyRow());
		await nextTick();

		if (itemsTableWrap.value) {
			itemsTableWrap.value.scrollTop = itemsTableWrap.value.scrollHeight;
		}
	}

	function removeItemRow(index) {
		if (itemRows.value.length === 1) {
			return;
		}

		itemRows.value.splice(index, 1);
	}

	function updateRowItemSearch(row, search = '') {
		row.search = search || '';
		row.isLoading = false;

		if (!row.search) {
			row.itemOptions = [...defaultItemCodeOptions.value];
			return;
		}

		loadItemCodeOptions(row.search, row);
	}

	async function loadBranchOptions(search = '') {
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
					link_fieldname: 'to_branch',
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

	async function loadItemCodeOptions(search = '', row = null) {
		if (row) {
			row.isLoading = true;
		}
		try {
			const response = await frappe.call({
				method: 'maxit_pos.maxit_pos.api.custom_search_link',
				args: {
					doctype: 'Item',
					txt: search || '',
					page_length: 20,
					label_fieldname: 'item_name',
				},
			});
			const options = (response.message || []).map((item) => ({
				value: item.value,
				label: `${item.label}: ${item.value}` || item.value,
				description: item.description || '',
			}));

			if (row) {
				row.itemOptions = options;
				return;
			}

			defaultItemCodeOptions.value = options;
		} catch (error) {
			frappe_.msgprint({
				title: __('Item search failed'),
				indicator: 'red',
				message: error?.message || String(error),
			});
		} finally {
			if (row) {
				row.isLoading = false;
			}
		}
	}

	async function submitTransfer() {
		const items = itemRows.value
			.map((row) => ({
				item_code: row.item_code,
				qty: Number(row.qty || 0),
			}))
			.filter((row) => row.item_code && row.qty > 0);

		if (!toBranch.value) {
			frappe_.show_alert({ message: __('Please select a destination branch.'), indicator: 'red' }, 5);
			return;
		}

		if (!items.length || items.length !== itemRows.value.length) {
			frappe_.show_alert({ message: __('Please complete all item rows with a valid quantity.'), indicator: 'red' }, 5);
			return;
		}

		isSubmitting.value = true;
		try {
			await frappe.call({
				method: 'maxit_pos.maxit_pos.page.maxit_pos.api.stock_entry_vue.create_transfer_stock_entry',
				args: {
					to_branch: toBranch.value,
					items: JSON.stringify(items),
				},
			});

			emit('created');
			frappe_.show_alert({ message: __('Outgoing transfer created successfully.'), indicator: 'green' }, 5);
		} finally {
			isSubmitting.value = false;
		}
	}
</script>

<style scoped>
	.stock-transfer-form {
		flex: 1;
		min-height: 0;
		display: flex;
		flex-direction: column;
		border: 1px solid var(--v-pos-panel-border);
		background: var(--v-pos-panel-background);
		box-shadow: var(--v-pos-panel-shadow);
		transition: var(--v-theme-transition);
	}

	.transfer-branch-row {
		max-width: 50%;
		flex-shrink: 0;
	}

	.stock-transfer-form-body {
		flex: 1;
		min-height: 0;
		display: flex;
		flex-direction: column;
		overflow: hidden;
	}

	.transfer-items-table-wrap {
		flex: 1;
		min-height: 0;
		overflow-x: auto;
		overflow-y: auto;
		border: 1px solid var(--v-pos-panel-border-soft);
		border-radius: 16px;
		background: var(--v-pos-field-background);
	}

	.transfer-items-table {
		background: transparent;
	}

	.transfer-items-table :deep(table) {
		min-width: 760px;
	}

	.transfer-items-table :deep(th) {
		white-space: nowrap;
		font-weight: 700;
	}

	.transfer-items-table :deep(td) {
		vertical-align: top;
		padding-top: 12px;
		padding-bottom: 12px;
	}

	.transfer-items-table :deep(tfoot td) {
		padding-top: 8px;
		padding-bottom: 8px;
	}

	.transfer-col-index {
		width: 72px;
		white-space: nowrap;
	}

	.transfer-col-qty {
		width: 180px;
	}

	.transfer-col-actions {
		width: 88px;
		text-align: end;
	}

	.transfer-add-row-cell {
		border-top: 1px dashed var(--v-pos-panel-border-strong);
		text-align: start;
	}

	.transfer-add-row-btn {
		margin-inline-start: -8px;
	}
</style>
