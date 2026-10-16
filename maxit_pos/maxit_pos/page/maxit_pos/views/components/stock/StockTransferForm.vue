<template>
	<ItemPickerForm
		:title="__('Create Outgoing Transfer')"
		:lines-title="__('Items')"
		:submit-label="__('Create')"
		submit-icon="mdi-content-save"
		:submitting="isSubmitting"
		:ready="!!toBranch"
		@cancel="emit('cancel')"
		@submit="onSubmit"
	>
		<template #fields>
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
				class="flex-grow-0"
				@update:search="(search) => loadBranchOptions(search)"
			/>
		</template>
	</ItemPickerForm>
</template>

<script setup>
	import { onMounted, ref } from 'vue';
	import ItemPickerForm from '../ui/ItemPickerForm.vue';

	const emit = defineEmits(['cancel', 'created']);

	const __ = window.__;
	const frappe_ = window.frappe;
	const branchOptions = ref([]);
	const isLoadingBranches = ref(false);
	const isSubmitting = ref(false);
	const toBranch = ref('');

	onMounted(() => loadBranchOptions());

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

	function onSubmit(items) {
		const totalQty = items.reduce((sum, item) => sum + item.qty, 0);
		frappe_.confirm(
			__('Create a transfer of {0} items (total qty {1}) to {2}?', [items.length, totalQty, toBranch.value]),
			() => submitTransfer(items)
		);
	}

	async function submitTransfer(items) {
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
