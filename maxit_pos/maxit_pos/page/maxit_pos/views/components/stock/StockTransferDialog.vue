<template>
	<v-dialog :model-value="modelValue" max-width="960" @update:model-value="emit('update:modelValue', $event)">
		<v-card class="stock-transfer-dialog" rounded="xl">
			<v-card-item class="pb-2">
				<div class="d-flex align-center justify-space-between gap-2 flex-wrap">
					<div>
						<div class="text-overline text-medium-emphasis">{{ __('Stock Entry') }}</div>
						<div class="text-h6 font-weight-bold">{{ __('Create Outgoing Transfer') }}</div>
					</div>
				</div>
			</v-card-item>

			<v-divider />

			<v-card-text class="pt-4">
				<v-row dense>
					<v-col cols="12" md="6">
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
							@update:search="(search) => loadBranchOptions(search, 'to_branch')"
						/>
					</v-col>
				</v-row>

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
				<v-btn variant="tonal" @click="emit('update:modelValue', false)">
					{{ __('Close') }}
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
	</v-dialog>
</template>

<script setup>
	import { nextTick, ref, watch } from 'vue';

	const props = defineProps({
		modelValue: {
			type: Boolean,
			default: false,
		},
	});

	const emit = defineEmits(['update:modelValue', 'created']);

	const __ = window.__;
	const frappe_ = window.frappe;
	const branchOptions = ref([]);
	const defaultItemCodeOptions = ref([]);
	const isLoadingBranches = ref(false);
	const isSubmitting = ref(false);
	const itemsTableWrap = ref(null);
	const toBranch = ref('');
	const itemRows = ref([createEmptyRow()]);

	watch(
		() => props.modelValue,
		async (isOpen) => {
			if (!isOpen) {
				return;
			}

			await Promise.all([loadBranchOptions(), loadItemCodeOptions()]);
			resetForm();
		},
		{ immediate: true }
	);

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

	function resetForm() {
		toBranch.value = '';
		itemRows.value = [createEmptyRow()];
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

	async function loadBranchOptions(search = '', linkFieldname = 'to_branch') {
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

	async function loadItemCodeOptions(search = '', row = null) {
		if (row) {
			row.isLoading = true;
		}
		try {
			const response = await frappe.call({
				method: 'frappe.desk.search.search_link',
				args: {
					doctype: 'Item',
					txt: search || '',
					page_length: 20,
				},
			});

			const options = (response.message || []).map((item) => ({
				value: item.value,
				label: item.label || item.value,
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

			emit('update:modelValue', false);
			emit('created');
			frappe_.show_alert({ message: __('Outgoing transfer created successfully.'), indicator: 'green' }, 5);
		} finally {
			isSubmitting.value = false;
		}
	}
</script>

<style scoped>
	.stock-transfer-dialog {
		border: 1px solid rgba(120, 144, 156, 0.24);
		background: linear-gradient(180deg, rgba(255, 255, 255, 0.95), rgba(248, 251, 255, 0.97));
		box-shadow: 0 8px 20px rgba(12, 28, 43, 0.08);
	}

	.transfer-items-table-wrap {
		max-height: 48vh;
		overflow-x: auto;
		overflow-y: auto;
		border: 1px solid rgba(120, 144, 156, 0.18);
		border-radius: 16px;
		background: rgba(255, 255, 255, 0.78);
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
		text-align: right;
	}

	.transfer-add-row-cell {
		border-top: 1px dashed rgba(120, 144, 156, 0.28);
		text-align: left;
	}

	.transfer-add-row-btn {
		margin-left: -8px;
	}
</style>