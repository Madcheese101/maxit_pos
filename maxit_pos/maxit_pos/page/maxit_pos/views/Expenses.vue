<template>
	<v-main class="expenses-view pa-3 pa-md-6">
		<v-alert v-if="!canViewExpenses" type="warning" variant="tonal">
			{{ __('You do not have permission to manage expenses.') }}
		</v-alert>

		<template v-else>
			<v-card class="expenses-panel mb-2" rounded="xl" variant="flat">
				<v-card-item>
					<div class="d-flex align-center justify-space-between flex-wrap gap-3">
						<div>
							<div class="text-h6 font-weight-bold">{{ __('Manage Expenses') }}</div>
						</div>
						<div class="d-flex align-center flex-wrap ga-1">
							<v-btn
								color="primary"
								variant="elevated"
								prepend-icon="mdi-plus"
								@click="expenseDialogOpen = true"
							>
								{{ __('New Expense') }}
							</v-btn>
						</div>
					</div>
				</v-card-item>

				<v-divider />

				<v-card-text class="pt-1">
					<v-row dense>
						<v-col cols="12" md="3">
							<v-text-field
								v-model="searchTerm"
								:placeholder="__('Search claim or notes')"
								prepend-inner-icon="mdi-magnify"
								variant="outlined"
								density="compact"
								hide-details
								@keydown.enter="getExpenses"
							/>
						</v-col>

						<v-col cols="12" md="3">
							<v-autocomplete
								v-model="selectedExpenseType"
								v-model:search="expenseTypeSearch"
								:items="expenseTypeOptions"
								item-title="label"
								item-value="value"
								:label="__('Expense Type')"
								variant="outlined"
								density="compact"
								:loading="isLoadingExpenseTypes"
								hide-details
								clearable
								no-filter
							/>
						</v-col>

						<v-col cols="12" md="2">
							<v-select
								v-model="selectedStatus"
								:items="statusOptions"
								item-title="title"
								item-value="value"
								:label="__('Status')"
								variant="outlined"
								density="compact"
								hide-details
							/>
						</v-col>

						<v-col cols="12" md="2">
							<v-select
								v-model="selectedViewMode"
								:items="viewModeOptions"
								item-title="title"
								item-value="value"
								:label="__('View Mode')"
								variant="outlined"
								density="compact"
								hide-details
							/>
						</v-col>

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
					</v-row>

					<div class="d-flex justify-end flex-wrap ga-2 mt-3">
						<v-btn color="primary" variant="tonal" prepend-icon="mdi-filter-check" @click="getExpenses">
							{{ __('Apply Filters') }}
						</v-btn>
						<v-btn variant="text" prepend-icon="mdi-filter-remove-outline" @click="resetFilters">
							{{ __('Clear Filters') }}
						</v-btn>
					</div>
				</v-card-text>
			</v-card>

			<v-card class="expenses-panel expenses-table-panel" rounded="xl" variant="flat">
				<v-card-text class="pa-0 expenses-table-body">
					<div class="expenses-table-wrap">
						<v-data-table
							:headers="headers"
							:items="expenses"
							item-value="row_id"
							:loading="isLoadingExpenses"
							fixed-header
							height="100%"
							class="expenses-table"
						>
						<template #item.name="{ item }">
							<v-btn variant="text" color="primary" class="px-0 text-none" @click="openExpenseDialog(item.name)">
								{{ item.name }}
							</v-btn>
						</template>

						<template #item.expense_type="{ item }">
							<span>{{ item.expense_type }}</span>
						</template>

						<template #item.amount="{ item }">
							{{ formatAmount(item.amount) }}
						</template>

						<template #item.status="{ item }">
							<v-chip size="small" :color="getStatusColor(item.docstatus)" variant="tonal">
								{{ getStatusLabel(item.docstatus) }}
							</v-chip>
						</template>

						<template #no-data>
							<div class="pa-6 text-medium-emphasis text-center">
								{{ __('No expenses found for the selected filters.') }}
							</div>
						</template>
						</v-data-table>
					</div>
				</v-card-text>
			</v-card>

			<ExpenseDialog v-model="expenseDialogOpen" @created="handleExpenseCreated" />
			<ExpenseViewDialog
				v-model="expenseViewDialogOpen"
				:docname="selectedExpenseName"
				@updated="handleExpenseUpdated"
			/>
		</template>
	</v-main>
</template>

<script setup>
	import { computed, onMounted, ref, watch } from 'vue';
	import ExpenseDialog from './components/expenses/ExpenseDialog.vue';
	import ExpenseViewDialog from './components/expenses/ExpenseViewDialog.vue';

	const __ = window.__;
	const frappe_ = window.frappe;
	const expenses = ref([]);
	const expenseDialogOpen = ref(false);
	const expenseViewDialogOpen = ref(false);
	const isLoadingExpenses = ref(false);
	const isLoadingExpenseTypes = ref(false);
	const searchTerm = ref('');
	const selectedExpenseType = ref('');
	const selectedStatus = ref('');
	const selectedViewMode = ref('expanded');
	const selectedExpenseName = ref('');
	const fromDate = ref('');
	const toDate = ref('');
	const expenseTypeOptions = ref([]);
	const expenseTypeSearch = ref('');

	const headers = computed(() => {
		const result = [
			{ title: __('Expense Claim'), key: 'name' },
		];

		if (selectedViewMode.value !== 'grouped') {
			result.push({ title: __('Expense Type'), key: 'expense_type' });
		}

		result.push(
			{ title: __('Posting Date'), key: 'posting_date' },
			{ title: __('Branch'), key: 'branch' },
			{ title: selectedViewMode.value === 'grouped' ? __('Total Amount') : __('Amount'), key: 'amount', align: 'end' },
			{ title: __('Status'), key: 'status' },
		);

		return result;
	});

	const statusOptions = computed(() => [
		{ title: __('All Statuses'), value: '' },
		{ title: __('Draft'), value: 'draft' },
		{ title: __('Submitted'), value: 'submitted' },
		{ title: __('Cancelled'), value: 'cancelled' },
	]);

	const viewModeOptions = computed(() => [
		{ title: __('Grouped'), value: 'grouped' },
		{ title: __('Expanded'), value: 'expanded' },
	]);

	const canViewExpenses = computed(() => {
		const roles = ['Expense User', 'Expense Manager', 'Accounts User', 'Accounts Manager', 'Administrator', 'System Manager'];
		return roles.some((role) => frappe_.user.has_role(role));
	});

	watch(expenseTypeSearch, async (value) => {
		await loadExpenseTypeOptions(value);
	});

	watch(selectedViewMode, async () => {
		if (!canViewExpenses.value) {
			return;
		}

		await getExpenses();
	});

	watch(expenseViewDialogOpen, (isOpen) => {
		if (!isOpen) {
			selectedExpenseName.value = '';
		}
	});

	onMounted(async () => {
		if (!canViewExpenses.value) {
			return;
		}

		await Promise.all([loadExpenseTypeOptions(), getExpenses()]);
	});

	function formatAmount(value) {
		return Number(value || 0).toFixed(2);
	}

	function getStatusLabel(docstatus) {
		switch (Number(docstatus)) {
			case 1:
				return __('Submitted');
			case 2:
				return __('Cancelled');
			default:
				return __('Draft');
		}
	}

	function getStatusColor(docstatus) {
		switch (Number(docstatus)) {
			case 1:
				return 'success';
			case 2:
				return 'error';
			default:
				return 'info';
		}
	}

	function openExpenseDialog(name) {
		if (!name) {
			return;
		}

		selectedExpenseName.value = name;
		expenseViewDialogOpen.value = true;
	}

	async function loadExpenseTypeOptions(search = '') {
		if (!canViewExpenses.value) {
			return;
		}

		isLoadingExpenseTypes.value = true;
		try {
			const response = await frappe.call({
				method: 'frappe.desk.search.search_link',
				args: {
					doctype: 'Expense Claim Type',
					txt: search || '',
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

	async function getExpenses() {
		if (!canViewExpenses.value) {
			return;
		}

		isLoadingExpenses.value = true;
		try {
			const response = await frappe.call({
				method: 'maxit_pos.maxit_pos.page.maxit_pos.api.expenses_vue.get_expense_list',
				args: {
					search_term: searchTerm.value || '',
					expense_type: selectedExpenseType.value || '',
					from_date: fromDate.value || '',
					to_date: toDate.value || '',
					status: selectedStatus.value || '',
					view_mode: selectedViewMode.value,
				},
			});

			expenses.value = response.message || [];
		} finally {
			isLoadingExpenses.value = false;
		}
	}

	function resetFilters() {
		const willReloadFromViewMode = selectedViewMode.value !== 'expanded';

		searchTerm.value = '';
		selectedExpenseType.value = '';
		expenseTypeSearch.value = '';
		selectedStatus.value = '';
		selectedViewMode.value = 'expanded';
		fromDate.value = '';
		toDate.value = '';

		if (!willReloadFromViewMode) {
			getExpenses();
		}
	}

	function handleExpenseCreated() {
		getExpenses();
	}

	function handleExpenseUpdated() {
		getExpenses();
	}
</script>

<style scoped>
	.expenses-view {
		background:
			radial-gradient(circle at top right, var(--v-pos-success-glow), transparent 40%),
			radial-gradient(circle at left bottom, var(--v-pos-warning-glow), transparent 38%);
		height: calc(100dvh - var(--v-layout-top, 0px) - var(--v-layout-bottom, 0px));
		min-height: calc(100dvh - var(--v-layout-top, 0px) - var(--v-layout-bottom, 0px));
		display: flex;
		flex-direction: column;
		overflow: hidden;
	}

	.expenses-panel {
		border: 1px solid var(--v-pos-panel-border);
		background: var(--v-pos-panel-background);
		box-shadow: var(--v-pos-panel-shadow);
		transition: var(--v-theme-transition);
	}

	.expenses-table-panel {
		flex: 1;
		min-height: 0;
		display: flex;
		flex-direction: column;
	}

	.expenses-table-body {
		flex: 1;
		min-height: 0;
		display: flex;
		flex-direction: column;
	}

	.expenses-table :deep(th) {
		white-space: nowrap;
	}

	.expenses-table-wrap {
		flex: 1;
		min-height: 0;
	}

	.expenses-table {
		height: 100%;
	}
</style>