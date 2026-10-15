<template>
	<v-card class="stock-transfer-form">
		<div class="form-header">
			<v-btn :icon="backIcon" variant="text" size="small" :aria-label="__('Back')" @click="emit('cancel')" />
			<div class="form-header__title">{{ __('Create Outgoing Transfer') }}</div>
		</div>

		<v-divider />

		<div ref="itemsTableWrap" class="stock-transfer-form-body">
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
				class="transfer-branch"
				@update:search="(search) => loadBranchOptions(search)"
			/>

			<div class="section-title">{{ __('Items') }}</div>

			<div v-for="(row, index) in itemRows" :key="row.id" class="item-row-card">
				<div class="item-row-card__index text-medium-emphasis">{{ index + 1 }}</div>
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
					class="item-row-card__item"
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
				<v-text-field
					v-model="row.qty"
					type="number"
					min="0.01"
					step="0.01"
					:label="__('Qty')"
					variant="outlined"
					density="compact"
					hide-details="auto"
					class="item-row-card__qty"
				/>
				<v-btn
					icon="mdi-delete-outline"
					variant="text"
					color="error"
					size="small"
					:aria-label="__('Delete')"
					:disabled="itemRows.length === 1"
					@click="removeItemRow(index)"
				/>
			</div>

			<v-btn
				variant="tonal"
				color="primary"
				prepend-icon="mdi-plus"
				class="align-self-start"
				@click="addItemRow"
			>
				{{ __('Add Row') }}
			</v-btn>
		</div>

		<v-card-actions class="px-4 pb-4 pt-2 ga-2">
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

	.form-header {
		display: flex;
		align-items: center;
		gap: var(--maxit-gap-sm);
		padding: 10px var(--maxit-pane-padding);
	}

	.form-header__title {
		font-size: 1rem;
		font-weight: 700;
	}

	.stock-transfer-form-body {
		flex: 1;
		min-height: 0;
		display: flex;
		flex-direction: column;
		gap: var(--maxit-gap);
		padding: var(--maxit-pane-padding);
		overflow-y: auto;
	}

	.transfer-branch {
		flex-grow: 0;
		max-width: 420px;
	}

	.section-title {
		font-size: 0.875rem;
		font-weight: 700;
	}

	.item-row-card {
		display: flex;
		flex-wrap: wrap;
		align-items: flex-start;
		gap: var(--maxit-gap-sm);
		padding: 10px;
		border: 1px solid var(--v-pos-panel-border-soft);
		border-radius: 10px;
		background: var(--v-pos-field-background);
	}

	.item-row-card__index {
		width: 20px;
		padding-block-start: 10px;
		text-align: center;
		font-weight: 700;
	}

	.item-row-card__item {
		flex: 1 1 240px;
	}

	.item-row-card__qty {
		flex: 0 1 130px;
	}

	@media (max-width: 599px) {
		.transfer-branch {
			max-width: none;
		}

		.item-row-card__qty {
			flex: 1 1 120px;
		}
	}
</style>
