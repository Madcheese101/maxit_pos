<template>
	<v-dialog :model-value="modelValue" max-width="960" @update:model-value="emit('update:modelValue', $event)">
		<v-form ref="expenseFormRef" v-model="isExpenseFormValid" @submit.prevent="submitExpense">
			<v-card class="expense-dialog" rounded="xl">
				<v-card-item class="pb-2">
					<div class="d-flex align-center justify-space-between gap-2 flex-wrap">
						<div>
							<div class="text-overline text-medium-emphasis">{{ __('Expenses') }}</div>
							<div class="text-h6 font-weight-bold">{{ __('Create Expense Claim') }}</div>
						</div>
					</div>
				</v-card-item>

				<v-divider />

				<v-card-text class="pt-4">
					<v-row dense>
						<v-col cols="12" md="4">
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

					<div class="d-flex align-center justify-space-between flex-wrap gap-2 mt-3 mb-2">
						<div class="text-subtitle-1 font-weight-bold">{{ __('Expense Rows') }}</div>
					</div>

					<div ref="expenseRowsTableWrap" class="expense-rows-table-wrap">
						<v-table density="comfortable" class="expense-rows-table">
							<thead>
								<tr>
									<th class="expense-col-index">{{ __('No.') }}</th>
									<th>{{ __('Expense Claim Type') }}</th>
									<th class="expense-col-amount">{{ __('Amount') }}</th>
									<th class="expense-col-actions">{{ __('Actions') }}</th>
								</tr>
							</thead>
							<tbody>
								<tr v-for="(row, index) in expenseRows" :key="row.id">
									<td class="expense-col-index text-medium-emphasis">{{ index + 1 }}</td>
									<td>
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
									</td>
									<td class="expense-col-amount">
										<v-text-field
											v-model="row.amount"
											type="number"
											min="0.01"
											step="0.01"
											:label="__('Amount')"
											variant="outlined"
											density="compact"
											hide-details="auto"
										/>
									</td>
									<td class="expense-col-actions">
										<v-btn
											icon="mdi-delete-outline"
											variant="text"
											color="error"
											:disabled="expenseRows.length === 1"
											@click="removeExpenseRow(index)"
										/>
									</td>
								</tr>
							</tbody>
							<tfoot>
								<tr>
									<td colspan="4" class="expense-add-row-cell">
										<v-btn
											variant="text"
											color="primary"
											prepend-icon="mdi-plus"
											class="expense-add-row-btn"
											@click="addExpenseRow"
										>
											{{ __('Add Row') }}
										</v-btn>
									</td>
								</tr>
							</tfoot>
						</v-table>
					</div>

					<v-alert type="info" variant="tonal" density="compact" class="mt-4">
						{{ __('Branch, expense approver, and advances are filled from your employee and branch defaults during submit.') }}
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
	import { nextTick, reactive, ref, watch } from 'vue';

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
	const expenseRowsTableWrap = ref(null);
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

		if (expenseRowsTableWrap.value) {
			expenseRowsTableWrap.value.scrollTop = expenseRowsTableWrap.value.scrollHeight;
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
		border: 1px solid rgba(120, 144, 156, 0.24);
		background: linear-gradient(180deg, rgba(255, 255, 255, 0.95), rgba(248, 251, 255, 0.97));
		box-shadow: 0 8px 20px rgba(12, 28, 43, 0.08);
	}

	.expense-rows-table-wrap {
		max-height: 48vh;
		overflow-x: auto;
		overflow-y: auto;
		border: 1px solid rgba(120, 144, 156, 0.18);
		border-radius: 16px;
		background: rgba(255, 255, 255, 0.78);
	}

	.expense-rows-table {
		background: transparent;
	}

	.expense-rows-table :deep(table) {
		min-width: 760px;
	}

	.expense-rows-table :deep(th) {
		white-space: nowrap;
		font-weight: 700;
	}

	.expense-rows-table :deep(td) {
		vertical-align: top;
		padding-top: 12px;
		padding-bottom: 12px;
	}

	.expense-rows-table :deep(tfoot td) {
		padding-top: 0;
	}

	.expense-col-index {
		width: 72px;
	}

	.expense-col-amount {
		width: 180px;
	}

	.expense-col-actions {
		width: 88px;
		text-align: center;
	}

	.expense-add-row-cell {
		text-align: left;
	}

	.expense-add-row-btn {
		text-transform: none;
	}
</style>