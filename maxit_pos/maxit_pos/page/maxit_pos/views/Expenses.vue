<template>
	<PageSurface glow="success-warning" class="expenses-view pa-3">
		<v-alert v-if="!canViewExpenses" type="warning" variant="tonal">
			{{ __('You do not have permission to manage expenses.') }}
		</v-alert>

		<SurfaceCard v-else class="expenses-pane">
			<div class="expenses-pane__body">
				<div class="pane-header">
					<div class="pane-header__title">{{ __('Manage Expenses') }}</div>
					<v-chip size="x-small" color="primary" variant="tonal">{{ expenses.length }}</v-chip>
					<v-spacer />
					<v-btn
						icon="mdi-wallet-outline"
						size="small"
						variant="text"
						:title="__('Check Custody Balance')"
						:aria-label="__('Check Custody Balance')"
						@click="checkCustodyBalance"
					/>
					<v-btn
						v-if="xs"
						icon="mdi-plus"
						color="primary"
						variant="elevated"
						size="small"
						:aria-label="__('New Expense')"
						@click="expenseDialogOpen = true"
					/>
					<v-btn
						v-else
						color="primary"
						variant="elevated"
						prepend-icon="mdi-plus"
						@click="expenseDialogOpen = true"
					>
						{{ __('New Expense') }}
					</v-btn>
				</div>

				<div class="filters-row">
					<v-text-field
						v-model="searchTerm"
						:placeholder="__('Search claim or notes')"
						prepend-inner-icon="mdi-magnify"
						variant="outlined"
						density="compact"
						hide-details
						single-line
						class="filters-row__search"
						@keydown.enter="getExpenses"
					/>
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
						v-if="activeFilterCount || searchTerm"
						icon="mdi-filter-remove-outline"
						size="small"
						variant="text"
						:title="__('Clear Filters')"
						:aria-label="__('Clear Filters')"
						@click="resetFilters"
					/>
				</div>

				<v-expand-transition>
					<div v-show="showFilters" class="filters-panel">
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
							class="filters-panel__wide"
						/>
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
					</div>
				</v-expand-transition>

				<div class="expenses-list">
					<v-progress-linear v-if="isLoadingExpenses" indeterminate color="primary" class="mb-2" />

					<div v-if="!expenses.length && !isLoadingExpenses" class="expenses-empty text-medium-emphasis">
						{{ __('No expenses found for the selected filters.') }}
					</div>

					<v-list v-else nav density="compact" bg-color="transparent" class="pa-0">
						<v-list-item
							v-for="item in expenses"
							:key="item.row_id || item.name"
							rounded="lg"
							class="expense-row"
							@click="openExpenseDialog(item.name)"
						>
							<div class="expense-row__line">
								<span class="expense-row__title">{{ item.expense_type || item.name }}</span>
								<v-chip size="small" :color="getStatusColor(item.docstatus)" variant="flat" class="status-chip">
									{{ getStatusLabel(item.docstatus) }}
								</v-chip>
							</div>
							<div class="expense-row__line expense-row__line--sub">
								<span class="expense-row__meta">
									<template v-if="item.expense_type">{{ item.name }} · </template>{{ formatDate(item.posting_date) }}<template v-if="item.branch"> · {{ item.branch }}</template>
								</span>
								<span class="expense-row__amount">{{ formatAmount(item.amount) }}</span>
							</div>
						</v-list-item>
					</v-list>
				</div>
			</div>

			<ExpenseDialog v-model="expenseDialogOpen" @created="handleExpenseCreated" />
			<ExpenseViewDialog
				v-model="expenseViewDialogOpen"
				:docname="selectedExpenseName"
				@updated="handleExpenseUpdated"
			/>
		</SurfaceCard>
	</PageSurface>
</template>

<script setup>
	import { computed, onMounted, ref, watch } from 'vue';
	import { useDisplay } from 'vuetify';
	import ExpenseDialog from './components/expenses/ExpenseDialog.vue';
	import ExpenseViewDialog from './components/expenses/ExpenseViewDialog.vue';
	import PageSurface from './components/ui/PageSurface.vue';
	import SurfaceCard from './components/ui/SurfaceCard.vue';
	import DateField from './components/ui/DateField.vue';

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

	// filters start open on laptops, collapsed on phones and tablets
	const { mdAndUp, xs } = useDisplay();
	const showFilters = ref(mdAndUp.value);
	const activeFilterCount = computed(() => [
		selectedExpenseType.value,
		selectedStatus.value,
		selectedViewMode.value !== 'expanded',
		fromDate.value,
		toDate.value,
	].filter(Boolean).length);

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

	watch([selectedExpenseType, selectedStatus, selectedViewMode, fromDate, toDate], async () => {
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
		return format_number(value || 0);
	}

	function formatDate(value) {
		return value ? frappe_.datetime.str_to_user(value) : '';
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

	async function checkCustodyBalance() {
		await frappe.call({
			method: 'maxit_pos.maxit_pos.page.maxit_pos.api.expenses_vue.get_custody_account_balance',
		});
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
		// the filters watcher reloads the list when any of them changes
		const willReloadFromFilters = activeFilterCount.value > 0;

		searchTerm.value = '';
		selectedExpenseType.value = '';
		expenseTypeSearch.value = '';
		selectedStatus.value = '';
		selectedViewMode.value = 'expanded';
		fromDate.value = '';
		toDate.value = '';

		if (!willReloadFromFilters) {
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
	}

	.expenses-pane {
		display: flex;
		flex-direction: column;
		flex: 1;
		min-height: 0;
		border: 1px solid var(--v-pos-panel-border);
		background: var(--v-pos-panel-background);
		box-shadow: var(--v-pos-panel-shadow);
		transition: var(--v-theme-transition);
	}

	.expenses-pane__body {
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

	.pane-header .v-chip {
		flex-shrink: 0;
	}

	.filters-row {
		display: flex;
		align-items: center;
		gap: var(--maxit-gap-sm);
	}

	.filters-row__search {
		flex: 1;
		max-width: 480px;
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
		.filters-row__search {
			max-width: none;
		}

		.filters-panel__wide {
			grid-column: 1 / -1;
		}
	}

	.expenses-list {
		flex: 1;
		min-height: 0;
		overflow-y: auto;
	}

	.expenses-empty {
		padding: 24px 8px;
		text-align: center;
	}

	.expense-row {
		margin-block-end: var(--maxit-gap-xs);
		border: 1px solid var(--v-pos-panel-border-soft);
	}

	.expense-row :deep(.v-list-item__content) {
		display: flex;
		flex-direction: column;
		gap: 2px;
	}

	.expense-row__line {
		display: flex;
		align-items: center;
		justify-content: space-between;
		gap: 8px;
	}

	.expense-row__title {
		min-width: 0;
		font-size: 0.875rem;
		font-weight: 700;
		white-space: nowrap;
		overflow: hidden;
		text-overflow: ellipsis;
	}

	.expense-row__line--sub {
		font-size: 0.8125rem;
	}

	.expense-row__meta {
		min-width: 0;
		color: rgba(var(--v-theme-on-surface), 0.72);
		white-space: nowrap;
		overflow: hidden;
		text-overflow: ellipsis;
	}

	.expense-row__amount {
		flex-shrink: 0;
		font-weight: 700;
	}

	.status-chip {
		flex-shrink: 0;
		font-weight: 700;
	}
</style>
