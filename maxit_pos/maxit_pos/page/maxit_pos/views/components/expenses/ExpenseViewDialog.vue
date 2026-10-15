<template>
	<v-dialog
		:model-value="modelValue"
		max-width="680"
		:fullscreen="xs"
		scrollable
		@update:model-value="emit('update:modelValue', $event)"
	>
		<v-card class="expense-view-dialog" :rounded="xs ? 0 : 'xl'">
			<v-card-item class="pb-2">
				<div class="d-flex align-center flex-wrap ga-2">
					<div class="text-h6 font-weight-bold">{{ doc?.name || __('View Expense Claim') }}</div>
					<v-chip v-if="doc" size="small" :color="statusChip.color" variant="flat" class="font-weight-bold">
						{{ statusChip.label }}
					</v-chip>
				</div>
				<div v-if="doc" class="dialog-subtitle">
					{{ formatDate(doc.posting_date) }} · {{ doc.employee_name || doc.employee || __('N/A') }}<template v-if="doc.branch"> · {{ doc.branch }}</template>
				</div>
			</v-card-item>

			<v-divider />

			<v-card-text class="dialog-body">
				<v-skeleton-loader v-if="isLoading" type="article, list-item-two-line, list-item-two-line" />

				<v-alert v-else-if="!doc" type="info" variant="tonal" density="compact">
					{{ __('Select an expense claim to view its details.') }}
				</v-alert>

				<template v-else>
					<div class="claim-total">
						<span class="text-medium-emphasis">{{ __('Total Claimed') }}</span>
						<span class="claim-total__value">{{ formatCurrency(doc.total_claimed_amount, doc.currency) }}</span>
					</div>

					<div class="meta-grid">
						<div class="meta-item">
							<span class="meta-item__label">{{ __('Total Sanctioned') }}</span>
							<span class="meta-item__value">{{ formatCurrency(doc.total_sanctioned_amount, doc.currency) }}</span>
						</div>
						<div class="meta-item">
							<span class="meta-item__label">{{ __('Taxes and Charges') }}</span>
							<span class="meta-item__value">{{ formatCurrency(doc.total_taxes_and_charges, doc.currency) }}</span>
						</div>
						<div class="meta-item">
							<span class="meta-item__label">{{ __('Approval Status') }}</span>
							<span class="meta-item__value">{{ doc.approval_status || __('N/A') }}</span>
						</div>
						<div class="meta-item">
							<span class="meta-item__label">{{ __('Company') }}</span>
							<span class="meta-item__value">{{ doc.company || __('N/A') }}</span>
						</div>
						<div class="meta-item meta-item--wide">
							<span class="meta-item__label">{{ __('Payable Account') }}</span>
							<span class="meta-item__value">{{ doc.payable_account || __('N/A') }}</span>
						</div>
						<div v-if="doc.remark" class="meta-item meta-item--wide">
							<span class="meta-item__label">{{ __('Notes') }}</span>
							<span class="meta-item__value meta-item__value--notes">{{ doc.remark }}</span>
						</div>
					</div>

					<section class="expense-lines">
						<div class="expense-lines__title">
							{{ __('Expense Rows') }}
							<span class="text-medium-emphasis">({{ (doc.expenses || []).length }})</span>
						</div>
						<div v-if="!(doc.expenses || []).length" class="text-medium-emphasis">
							{{ __('No expense rows were found for this claim.') }}
						</div>
						<div v-for="item in doc.expenses || []" :key="item.name" class="expense-line">
							<div class="expense-line__main">
								<div class="expense-line__name">{{ item.idx }}. {{ item.expense_type }}</div>
								<div class="expense-line__sub">
									{{ formatDate(item.expense_date) }} · {{ __('Sanctioned Amount') }}: {{ formatAmount(item.sanctioned_amount || item.amount) }}
								</div>
							</div>
							<div class="expense-line__amount">{{ formatAmount(item.amount) }}</div>
						</div>
					</section>
				</template>
			</v-card-text>

			<v-card-actions class="px-4 pb-4 pt-2 ga-2 flex-wrap">
				<v-spacer />
				<v-btn variant="tonal" @click="emit('update:modelValue', false)">
					{{ __('Close') }}
				</v-btn>
				<v-btn
					v-if="doc"
					color="primary"
					variant="elevated"
					prepend-icon="mdi-printer"
					@click="printDoc"
				>
					{{ __('Print') }}
				</v-btn>
				<v-btn
					v-if="doc"
					color="error"
					variant="tonal"
					prepend-icon="mdi-cancel"
					:loading="isSubmitting"
					:disabled="!canCancel"
					@click="cancelExpense"
				>
					{{ __('Cancel') }}
				</v-btn>
			</v-card-actions>
		</v-card>
	</v-dialog>
</template>

<script setup>
	import { computed, ref, watch } from 'vue';
	import { useDisplay } from 'vuetify';
	import { usePosStore } from '../../../store/posStore';

	const props = defineProps({
		modelValue: {
			type: Boolean,
			default: false,
		},
		docname: {
			type: String,
			default: '',
		},
	});

	const emit = defineEmits(['update:modelValue', 'updated']);

	const __ = window.__;
	const frappe_ = window.frappe;
	const { buildPrintViewUrl } = usePosStore();
	const doc = ref(null);
	const isLoading = ref(false);
	const isSubmitting = ref(false);
	const { xs } = useDisplay();

	const canCancel = computed(() => Number(doc.value?.docstatus || 0) === 1);

	const statusChip = computed(() => {
		switch (Number(doc.value?.docstatus || 0)) {
			case 1:
				return { label: __('Submitted'), color: 'success' };
			case 2:
				return { label: __('Cancelled'), color: 'error' };
			default:
				return { label: __('Draft'), color: 'info' };
		}
	});

	watch(
		() => [props.modelValue, props.docname],
		async ([isOpen, docname]) => {
			if (!isOpen || !docname) {
				if (!isOpen) {
					doc.value = null;
				}
				return;
			}

			await loadDoc();
		},
		{ immediate: true }
	);

	function formatAmount(value) {
		return format_number(value || 0);
	}

	function formatDate(value) {
		return value ? frappe_.datetime.str_to_user(value) : '';
	}

	function formatCurrency(value, currency = '') {
		const amount = formatAmount(value);
		return currency ? `${amount} ${currency}` : amount;
	}

	async function loadDoc() {
		isLoading.value = true;
		try {
			const response = await frappe.call({
				method: 'maxit_pos.maxit_pos.page.maxit_pos.api.expenses_vue.get_expense_details',
				args: {
					name: props.docname,
				},
			});

			doc.value = response.message || null;
		} catch (error) {
			frappe_.msgprint({
				title: __('Expense Claim fetch failed'),
				indicator: 'red',
				message: error?.message || String(error),
			});
			doc.value = null;
		} finally {
			isLoading.value = false;
		}
	}

	function printDoc() {
		if (!doc.value?.name) {
			return;
		}

		const printUrl = buildPrintViewUrl({
			doctype: 'Expense Claim',
			name: doc.value.name,
			format: 'Standard',
			no_letterhead: 1,
			letterhead: 'No Letterhead',
		});
		window.open(printUrl, '_blank');
	}

	function cancelExpense() {
		if (!doc.value?.name || !canCancel.value) {
			return;
		}

		frappe_.confirm(
			__('Are you sure you want to cancel this expense claim?'),
			async () => {
				isSubmitting.value = true;
				try {
					await frappe.call({
						method: 'maxit_pos.maxit_pos.page.maxit_pos.api.expenses_vue.cancel_expense',
						args: {
							name: doc.value.name,
						},
					});

					frappe_.show_alert({ message: __('Expense Claim cancelled successfully.'), indicator: 'green' }, 5);
					emit('update:modelValue', false);
					emit('updated');
				} catch (error) {
					// Frappe request cleanup surfaces the server error dialog.
				} finally {
					isSubmitting.value = false;
				}
			},
			() => {}
		);
	}
</script>

<style scoped>
	.expense-view-dialog {
		border: 1px solid var(--v-pos-panel-border);
		background: rgb(var(--v-theme-surface));
		box-shadow: var(--v-pos-panel-shadow);
		transition: var(--v-theme-transition);
	}

	.dialog-subtitle {
		font-size: 0.875rem;
		color: rgba(var(--v-theme-on-surface), 0.72);
	}

	.dialog-body {
		display: flex;
		flex-direction: column;
		gap: var(--maxit-gap);
	}

	.claim-total {
		display: flex;
		align-items: baseline;
		justify-content: space-between;
		gap: 12px;
		padding: 10px 12px;
		border-radius: 10px;
		background: rgba(var(--v-theme-primary), 0.08);
	}

	.claim-total__value {
		font-size: 1.25rem;
		font-weight: 800;
	}

	.meta-grid {
		display: grid;
		grid-template-columns: repeat(auto-fill, minmax(180px, 1fr));
		gap: var(--maxit-gap) 16px;
	}

	.meta-item {
		display: flex;
		flex-direction: column;
		min-width: 0;
	}

	.meta-item--wide {
		grid-column: 1 / -1;
	}

	.meta-item__label {
		font-size: 0.75rem;
		color: rgba(var(--v-theme-on-surface), 0.65);
	}

	.meta-item__value {
		font-size: 0.875rem;
		font-weight: 600;
		overflow-wrap: anywhere;
	}

	.meta-item__value--notes {
		white-space: pre-line;
		font-weight: 500;
	}

	.expense-lines {
		display: flex;
		flex-direction: column;
		gap: var(--maxit-gap-xs);
	}

	.expense-lines__title {
		font-size: 0.875rem;
		font-weight: 700;
	}

	.expense-line {
		display: flex;
		align-items: center;
		gap: 8px;
		padding: 8px 10px;
		border: 1px solid var(--v-pos-panel-border-soft);
		border-radius: 8px;
		background: var(--v-pos-field-background);
	}

	.expense-line__main {
		flex: 1;
		min-width: 0;
	}

	.expense-line__name {
		font-size: 0.875rem;
		font-weight: 600;
	}

	.expense-line__sub {
		font-size: 0.8125rem;
		font-weight: 500;
		color: rgba(var(--v-theme-on-surface), 0.72);
	}

	.expense-line__amount {
		flex-shrink: 0;
		font-size: 0.875rem;
		font-weight: 700;
	}
</style>
