<template>
	<v-dialog :model-value="modelValue" max-width="760" @update:model-value="emit('update:modelValue', $event)">
		<v-form ref="expenseFormRef" v-model="isExpenseFormValid" @submit.prevent="submitExpense">
			<v-card class="expense-dialog" rounded="xl">
				<v-card-item class="pb-2">
					<div class="d-flex align-center justify-space-between gap-2 flex-wrap">
						<div>
							<div class="text-overline text-medium-emphasis">{{ __('Expenses') }}</div>
							<div class="text-h6 font-weight-bold">{{ __('Create Expense') }}</div>
						</div>
					</div>
				</v-card-item>

				<v-divider />

				<v-card-text class="pt-4">
					<v-row dense>
						<v-col cols="12" md="6">
							<v-autocomplete
								v-model="expenseForm.expense_type"
								v-model:search="expenseTypeSearch"
								:items="expenseTypeOptions"
								item-title="label"
								item-value="value"
								:label="__('Expense Type')"
								variant="outlined"
								density="compact"
								:rules="[requiredRule]"
								:loading="isLoadingExpenseTypes"
								hide-details="auto"
								clearable
								no-filter
							/>
						</v-col>

						<v-col cols="12" md="3">
							<v-text-field
								v-model="expenseForm.posting_date"
								type="date"
								:label="__('Posting Date')"
								variant="outlined"
								density="compact"
								:rules="[requiredRule]"
								hide-details="auto"
							/>
						</v-col>

						<v-col cols="12" md="3">
							<v-text-field
								v-model="expenseForm.amount"
								type="number"
								min="0.01"
								step="0.01"
								:label="__('Amount')"
								variant="outlined"
								density="compact"
								:rules="[requiredRule, positiveAmountRule]"
								hide-details="auto"
							/>
						</v-col>
					</v-row>

					<v-textarea
						v-model="expenseForm.notes"
						:label="__('Notes')"
						variant="outlined"
						density="compact"
						auto-grow
						rows="3"
						hide-details="auto"
						class="mt-2"
					/>

					<v-alert type="info" variant="tonal" density="compact" class="mt-4">
						{{ __('Branch, custody account, and cost center are filled from your default branch during submit.') }}
					</v-alert>
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
						:loading="isSubmittingExpense"
						type="submit"
					>
						{{ __('Create') }}
					</v-btn>
				</v-card-actions>
			</v-card>
		</v-form>
	</v-dialog>
</template>

<script setup>
	import { reactive, ref, watch } from 'vue';

	const props = defineProps({
		modelValue: {
			type: Boolean,
			default: false,
		},
	});

	const emit = defineEmits(['update:modelValue', 'created']);

	const __ = window.__;
	const frappe_ = window.frappe;
	const expenseFormRef = ref(null);
	const isExpenseFormValid = ref(false);
	const isSubmittingExpense = ref(false);
	const isLoadingExpenseTypes = ref(false);
	const expenseTypeOptions = ref([]);
	const expenseTypeSearch = ref('');

	const expenseForm = reactive({
		expense_type: '',
		amount: '',
		posting_date: getToday(),
		notes: '',
	});

	const requiredRule = (value) => !!value || __('Required');
	const positiveAmountRule = (value) => Number(value || 0) > 0 || __('Amount must be greater than zero');

	watch(
		() => props.modelValue,
		async (isOpen) => {
			if (!isOpen) {
				return;
			}

			resetForm();
			await loadExpenseTypeOptions();
		},
		{ immediate: true }
	);

	watch(expenseTypeSearch, async (value) => {
		if (!props.modelValue) {
			return;
		}

		await loadExpenseTypeOptions(value);
	});

	function getToday() {
		if (frappe_?.datetime?.get_today) {
			return frappe_.datetime.get_today();
		}

		return new Date().toISOString().slice(0, 10);
	}

	function resetForm() {
		expenseForm.expense_type = '';
		expenseForm.amount = '';
		expenseForm.posting_date = getToday();
		expenseForm.notes = '';
		expenseTypeSearch.value = '';
		isExpenseFormValid.value = false;
		expenseFormRef.value?.resetValidation();
	}

	async function loadExpenseTypeOptions(searchTerm = '') {
		isLoadingExpenseTypes.value = true;
		try {
			const response = await frappe.call({
				method: 'frappe.desk.search.search_link',
				args: {
					doctype: 'Expense Type',
					txt: searchTerm || '',
					page_length: 20,
				},
			});

			expenseTypeOptions.value = (response.message || []).map((item) => ({
				value: item.value,
				label: item.label || item.value,
				description: item.description || '',
			}));
		} catch (error) {
			frappe_.msgprint({
				title: __('Expense type search failed'),
				indicator: 'red',
				message: error?.message || String(error),
			});
		} finally {
			isLoadingExpenseTypes.value = false;
		}
	}

	async function submitExpense() {
		const validationResult = await expenseFormRef.value?.validate();
		if (!validationResult?.valid) {
			frappe_.show_alert({ message: __('Please complete the required fields.'), indicator: 'red' }, 5);
			return;
		}

		isSubmittingExpense.value = true;
		try {
			const response = await frappe.call({
				method: 'maxit_pos.maxit_pos.page.maxit_pos.api.expenses_vue.create_expense',
				args: {
					doc: JSON.stringify({
						expense_type: expenseForm.expense_type,
						amount: Number(expenseForm.amount || 0),
						posting_date: expenseForm.posting_date,
						notes: expenseForm.notes,
					}),
				},
			});

			emit('update:modelValue', false);
			emit('created', response.message);
			frappe_.show_alert({ message: __('Expense created successfully.'), indicator: 'green' }, 5);
		} finally {
			isSubmittingExpense.value = false;
		}
	}
</script>

<style scoped>
	.expense-dialog {
		border: 1px solid rgba(120, 144, 156, 0.24);
		background: linear-gradient(180deg, rgba(255, 255, 255, 0.95), rgba(248, 251, 255, 0.97));
		box-shadow: 0 8px 20px rgba(12, 28, 43, 0.08);
	}
</style>