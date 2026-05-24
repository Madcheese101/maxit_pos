<template>
	<v-dialog :model-value="modelValue" max-width="1100" @update:model-value="emit('update:modelValue', $event)">
		<v-card class="expense-view-dialog" rounded="xl">
			<v-card-item class="pb-2">
				<div class="d-flex align-center justify-space-between gap-2 flex-wrap">
					<div>
						<div class="text-overline text-medium-emphasis">{{ __('Expense Claim') }}</div>
						<div class="text-h6 font-weight-bold">{{ doc?.name || __('View Expense Claim') }}</div>
					</div>
					<v-chip v-if="doc" size="small" :color="statusChip.color" variant="tonal">
						{{ statusChip.label }}
					</v-chip>
				</div>
			</v-card-item>

			<v-divider />

			<v-card-text class="pt-4 dialog-body">
				<v-skeleton-loader v-if="isLoading" type="article, article, table" />

				<v-alert v-else-if="!doc" type="info" variant="tonal">
					{{ __('Select an expense claim to view its details.') }}
				</v-alert>

				<template v-else>
					<v-row dense class="mb-2">
						<v-col cols="12" sm="6" md="3">
							<v-card class="stat-card" rounded="lg" variant="tonal" color="primary">
								<v-card-text>
									<div class="text-caption text-medium-emphasis">{{ __('Posting Date') }}</div>
									<div class="text-body-1 font-weight-bold">{{ doc.posting_date || __('N/A') }}</div>
								</v-card-text>
							</v-card>
						</v-col>

						<v-col cols="12" sm="6" md="3">
							<v-card class="stat-card" rounded="lg" variant="tonal" color="success">
								<v-card-text>
									<div class="text-caption text-medium-emphasis">{{ __('Employee') }}</div>
									<div class="text-body-1 font-weight-bold">{{ doc.employee_name || doc.employee || __('N/A') }}</div>
								</v-card-text>
							</v-card>
						</v-col>

						<v-col cols="12" sm="6" md="3">
							<v-card class="stat-card" rounded="lg" variant="tonal" color="warning">
								<v-card-text>
									<div class="text-caption text-medium-emphasis">{{ __('Branch') }}</div>
									<div class="text-body-1 font-weight-bold">{{ doc.branch || __('N/A') }}</div>
								</v-card-text>
							</v-card>
						</v-col>

						<v-col cols="12" sm="6" md="3">
							<v-card class="stat-card" rounded="lg" variant="tonal" color="info">
								<v-card-text>
									<div class="text-caption text-medium-emphasis">{{ __('Total Claimed') }}</div>
									<div class="text-body-1 font-weight-bold">{{ formatCurrency(doc.total_claimed_amount, doc.currency) }}</div>
								</v-card-text>
							</v-card>
						</v-col>
					</v-row>

					<v-row dense class="mb-3">
						<v-col cols="12" md="6">
							<div class="meta-row"><strong>{{ __('Company') }}:</strong> {{ doc.company || __('N/A') }}</div>
							<div class="meta-row"><strong>{{ __('Approval Status') }}:</strong> {{ doc.approval_status || __('N/A') }}</div>
							<div class="meta-row"><strong>{{ __('Payable Account') }}:</strong> {{ doc.payable_account || __('N/A') }}</div>
						</v-col>
						<v-col cols="12" md="6">
							<div class="meta-row"><strong>{{ __('Total Sanctioned') }}:</strong> {{ formatCurrency(doc.total_sanctioned_amount, doc.currency) }}</div>
							<div class="meta-row"><strong>{{ __('Taxes and Charges') }}:</strong> {{ formatCurrency(doc.total_taxes_and_charges, doc.currency) }}</div>
							<div class="meta-row"><strong>{{ __('Notes') }}:</strong> {{ doc.remark || __('N/A') }}</div>
						</v-col>
					</v-row>

					<v-card class="section-card" rounded="lg" variant="outlined">
						<v-card-item class="pb-1">
							<div class="text-subtitle-1 font-weight-bold">{{ __('Expense Rows') }}</div>
						</v-card-item>
						<v-card-text>
							<div class="expenses-table-wrap">
								<v-data-table
									:headers="itemHeaders"
									:items="doc.expenses || []"
									item-value="name"
									density="compact"
									fixed-header
									height="260"
									class="expense-items-table"
								>
									<template #item.amount="{ item }">
										{{ formatCurrency(item.amount, doc.currency) }}
									</template>

									<template #item.sanctioned_amount="{ item }">
										{{ formatCurrency(item.sanctioned_amount || item.amount, doc.currency) }}
									</template>

									<template #no-data>
										<div class="pa-4 text-medium-emphasis text-center">
											{{ __('No expense rows were found for this claim.') }}
										</div>
									</template>
								</v-data-table>
							</div>
						</v-card-text>
					</v-card>
				</template>
			</v-card-text>

			<v-card-actions class="px-4 pb-4 pt-0 d-flex gap-2 flex-wrap">
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
	const doc = ref(null);
	const isLoading = ref(false);
	const isSubmitting = ref(false);

	const itemHeaders = computed(() => [
		{ title: __('No.'), key: 'idx', width: '72px' },
		{ title: __('Expense Date'), key: 'expense_date' },
		{ title: __('Expense Type'), key: 'expense_type' },
		{ title: __('Amount'), key: 'amount', align: 'end' },
		{ title: __('Sanctioned Amount'), key: 'sanctioned_amount', align: 'end' },
	]);

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
		return Number(value || 0).toFixed(2);
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

		const printUrl = `/printview?doctype=${encodeURIComponent('Expense Claim')}&name=${encodeURIComponent(doc.value.name)}&format=Standard&no_letterhead=1&letterhead=No%20Letterhead&settings=%7B%7D&_lang=en&pdf_generator=wkhtmltopdf&trigger_print=1`;
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
		border: 1px solid rgba(120, 144, 156, 0.24);
		background: linear-gradient(180deg, rgba(255, 255, 255, 0.95), rgba(248, 251, 255, 0.97));
		box-shadow: 0 8px 20px rgba(12, 28, 43, 0.08);
	}

	.dialog-body {
		max-height: 70vh;
		overflow-y: auto;
	}

	.stat-card {
		border: 1px solid rgba(120, 144, 156, 0.18);
	}

	.section-card {
		border-color: rgba(120, 144, 156, 0.28) !important;
	}

	.meta-row {
		padding: 4px 0;
	}

	.expenses-table-wrap {
		min-height: 170px;
	}

	.expense-items-table :deep(.v-table__wrapper) {
		overflow-y: auto;
	}
</style>