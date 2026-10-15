<template>
	<v-dialog
		:model-value="modelValue"
		max-width="720"
		:fullscreen="xs"
		scrollable
		@update:model-value="emit('update:modelValue', $event)"
	>
		<v-card class="expense-dialog" :rounded="xs ? 0 : 'xl'">
			<v-card-item class="pb-2">
				<div class="text-h6 font-weight-bold">{{ __('Create Expense Claim') }}</div>
			</v-card-item>

			<v-divider />

			<v-card-text ref="dialogBody" class="dialog-body">
				<v-form ref="expenseFormRef" v-model="isExpenseFormValid" class="expense-form" @submit.prevent="submitExpense">
					<DateField
						v-model="expenseForm.posting_date"
						:label="__('Posting Date')"
						variant="outlined"
						density="compact"
						:rules="[requiredRule]"
						hide-details="auto"
						class="expense-form__date"
					/>

					<v-textarea
						v-model="expenseForm.notes"
						:label="__('Notes')"
						variant="outlined"
						density="compact"
						auto-grow
						rows="2"
						hide-details="auto"
					/>

					<div class="text-subtitle-2 font-weight-bold">{{ __('Expense Rows') }}</div>

					<div class="expense-rows">
						<div v-for="(row, index) in expenseRows" :key="row.id" class="expense-row-card">
							<div class="expense-row-card__index text-medium-emphasis">{{ index + 1 }}</div>
							<v-autocomplete
								v-model="row.expense_type"
								v-model:search="row.search"
								:items="row.expenseTypeOptions"
								item-title="label"
								item-value="value"
								:label="__('Expense Claim Type')"
								variant="outlined"
								density="compact"
								:loading="row.isLoading || isLoadingExpenseTypes"
								hide-details="auto"
								clearable
								no-filter
								class="expense-row-card__type"
								@update:search="(search) => updateRowExpenseTypeSearch(row, search)"
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
								v-model="row.amount"
								type="number"
								min="0.01"
								step="0.01"
								:label="__('Amount')"
								variant="outlined"
								density="compact"
								hide-details="auto"
								class="expense-row-card__amount"
							/>
							<v-btn
								icon="mdi-delete-outline"
								variant="text"
								color="error"
								size="small"
								:aria-label="__('Delete')"
								:disabled="expenseRows.length === 1"
								@click="removeExpenseRow(index)"
							/>
						</div>

						<v-btn
							variant="tonal"
							color="primary"
							prepend-icon="mdi-plus"
							class="align-self-start"
							@click="addExpenseRow"
						>
							{{ __('Add Row') }}
						</v-btn>
					</div>

					<v-alert type="info" variant="tonal" density="compact">
						{{ __('Branch, expense approver, and advances are filled from your employee and branch defaults during submit.') }}
					</v-alert>
				</v-form>
			</v-card-text>

			<v-card-actions class="px-4 pb-4 pt-2 ga-2">
				<v-spacer />
				<v-btn variant="tonal" @click="emit('update:modelValue', false)">
					{{ __('Close') }}
				</v-btn>
				<v-btn
					color="primary"
					variant="elevated"
					prepend-icon="mdi-content-save"
					:loading="isSubmittingExpense"
					@click="submitExpense"
				>
					{{ __('Create') }}
				</v-btn>
			</v-card-actions>
		</v-card>
	</v-dialog>
</template>

<script setup>
	import { nextTick, reactive, ref, watch } from 'vue';
	import { useDisplay } from 'vuetify';
	import DateField from '../ui/DateField.vue';

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
	const defaultExpenseTypeOptions = ref([]);
	const dialogBody = ref(null);
	const { xs } = useDisplay();
	const expenseRows = ref([createEmptyRow()]);

	const expenseForm = reactive({
		posting_date: getToday(),
		notes: '',
	});

	const requiredRule = (value) => !!value || __('Required');

	watch(
		() => props.modelValue,
		async (isOpen) => {
			if (!isOpen) {
				return;
			}

			await loadExpenseTypeOptions();
			resetForm();
		},
		{ immediate: true }
	);

	function getToday() {
		if (frappe_?.datetime?.get_today) {
			return frappe_.datetime.get_today();
		}

		return new Date().toISOString().slice(0, 10);
	}

	function createEmptyRow() {
		return {
			id: `${Date.now()}-${Math.random()}`,
			expense_type: '',
			amount: '',
			search: '',
			isLoading: false,
			expenseTypeOptions: [...defaultExpenseTypeOptions.value],
		};
	}

	function resetForm() {
		expenseForm.posting_date = getToday();
		expenseForm.notes = '';
		expenseRows.value = [createEmptyRow()];
		isExpenseFormValid.value = false;
		expenseFormRef.value?.resetValidation();
	}

	async function addExpenseRow() {
		expenseRows.value.push(createEmptyRow());
		await nextTick();

		// the dialog body is the scroll container; keep the new row in view
		const bodyEl = dialogBody.value?.$el;
		if (bodyEl) {
			bodyEl.scrollTop = bodyEl.scrollHeight;
		}
	}

	function removeExpenseRow(index) {
		if (expenseRows.value.length === 1) {
			return;
		}

		expenseRows.value.splice(index, 1);
	}

	function updateRowExpenseTypeSearch(row, search = '') {
		row.search = search || '';
		row.isLoading = false;

		if (!row.search) {
			row.expenseTypeOptions = [...defaultExpenseTypeOptions.value];
			return;
		}

		loadExpenseTypeOptions(row.search, row);
	}

	async function loadExpenseTypeOptions(searchTerm = '', row = null) {
		if (row) {
			row.isLoading = true;
		} else {
			isLoadingExpenseTypes.value = true;
		}

		try {
			const response = await frappe.call({
				method: 'frappe.desk.search.search_link',
				args: {
					doctype: 'Expense Claim Type',
					txt: searchTerm || '',
					page_length: 20,
				},
			});

			const options = (response.message || []).map((item) => ({
				value: item.value,
				label: item.label || item.value,
				description: item.description || '',
			}));

			if (row) {
				row.expenseTypeOptions = options;
				return;
			}

			defaultExpenseTypeOptions.value = options;
		} catch (error) {
			frappe_.msgprint({
				title: __('Expense claim type search failed'),
				indicator: 'red',
				message: error?.message || String(error),
			});
		} finally {
			if (row) {
				row.isLoading = false;
			} else {
				isLoadingExpenseTypes.value = false;
			}
		}
	}

	async function submitExpense() {
		const validationResult = await expenseFormRef.value?.validate();
		if (!validationResult?.valid) {
			frappe_.show_alert({ message: __('Please complete the required fields.'), indicator: 'red' }, 5);
			return;
		}

		const expenses = expenseRows.value
			.map((row) => ({
				expense_type: row.expense_type,
				amount: Number(row.amount || 0),
			}))
			.filter((row) => row.expense_type || row.amount > 0);

		if (!expenses.length || expenses.length !== expenseRows.value.length) {
			frappe_.show_alert({ message: __('Please complete every expense row with a claim type and amount.'), indicator: 'red' }, 5);
			return;
		}

		if (expenses.some((row) => row.amount <= 0)) {
			frappe_.show_alert({ message: __('Every expense amount must be greater than zero.'), indicator: 'red' }, 5);
			return;
		}

		isSubmittingExpense.value = true;
		try {
			const response = await frappe.call({
				method: 'maxit_pos.maxit_pos.page.maxit_pos.api.expenses_vue.create_expense',
				args: {
					doc: JSON.stringify({
						posting_date: expenseForm.posting_date,
						notes: expenseForm.notes,
						expenses,
					}),
				},
			});

			emit('update:modelValue', false);
			emit('created', response.message);
			frappe_.show_alert({ message: __('Expense Claim created successfully.'), indicator: 'green' }, 5);
		} finally {
			isSubmittingExpense.value = false;
		}
	}
</script>

<style scoped>
	.expense-dialog {
		border: 1px solid var(--v-pos-panel-border);
		background: rgb(var(--v-theme-surface));
		box-shadow: var(--v-pos-panel-shadow);
		transition: var(--v-theme-transition);
	}

	.expense-form {
		display: flex;
		flex-direction: column;
		gap: var(--maxit-gap);
	}

	.expense-form__date {
		max-width: 220px;
	}

	.expense-rows {
		display: flex;
		flex-direction: column;
		gap: var(--maxit-gap-sm);
	}

	.expense-row-card {
		display: flex;
		flex-wrap: wrap;
		align-items: flex-start;
		gap: var(--maxit-gap-sm);
		padding: 10px;
		border: 1px solid var(--v-pos-panel-border-soft);
		border-radius: 10px;
		background: var(--v-pos-field-background);
	}

	.expense-row-card__index {
		width: 20px;
		padding-block-start: 10px;
		text-align: center;
		font-weight: 700;
	}

	.expense-row-card__type {
		flex: 1 1 220px;
	}

	.expense-row-card__amount {
		flex: 0 1 140px;
	}

	@media (max-width: 599px) {
		.expense-form__date {
			max-width: none;
		}

		.expense-row-card__amount {
			flex: 1 1 120px;
		}
	}
</style>
