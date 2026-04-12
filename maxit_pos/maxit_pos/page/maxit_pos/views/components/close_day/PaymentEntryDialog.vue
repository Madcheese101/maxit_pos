<template>
	<v-dialog :model-value="modelValue" max-width="920" @update:model-value="emit('update:modelValue', $event)">
		<v-form ref="paymentEntryFormRef" v-model="isPaymentEntryFormValid" @submit.prevent="submitPaymentEntries">
			<v-card class="payment-entry-dialog" rounded="xl">
				<v-card-item>
					<div class="d-flex align-center justify-space-between flex-wrap gap-2">
						<div>
							<div class="text-overline text-medium-emphasis">{{ __('Close Day') }}</div>
						</div>
					</div>
				</v-card-item>
				<v-divider />
				<v-card-text class="pt-1 pb-2">
					<v-row dense>
						<v-col cols="12" md="4">
							<v-text-field
								v-model="paymentEntryForm.posting_date"
								type="date"
								:label="__('Posting Date')"
								variant="outlined"
								density="compact"
								:rules="[requiredRule]"
								hide-details="auto"
							/>
						</v-col>
					</v-row>

					<v-card class="section-card mt-1" rounded="lg" variant="outlined">
						<v-card-item class="pb-1">
							<div class="d-flex align-center justify-space-between gap-2 flex-wrap">
								<div class="text-subtitle-1 font-weight-bold">{{ __('Mode of Payments') }}</div>
								<v-chip v-if="noteCountEnabled" size="small" color="primary" variant="tonal">
									{{ __('Note Count Enabled') }}
								</v-chip>
							</div>
						</v-card-item>
						<v-card-text class="pt-1">
							<div v-if="!paymentEntryForm.payments.length" class="pa-2">
								<v-alert type="info" variant="tonal" density="compact">
									{{ __('No mode of payments are configured for this POS Profile.') }}
								</v-alert>
							</div>
							<div v-else class="overflow-x-auto">
								<v-data-table
									:headers="paymentHeaders"
									:items="paymentEntryForm.payments"
									item-value="mode_of_payment"
									density="compact"
									hide-default-footer
									class="payment-entry-table"
								>
									<template #item.mode_of_payment="{ item }">
										<div class="text-body-2 font-weight-medium py-2">{{ item.mode_of_payment }}</div>
									</template>

									<template #item.note_count="{ item, index }">
										<v-autocomplete
											:model-value="item.note_count"
											:items="item.note_count_options"
											:item-title="getNoteCountOptionLabel"
											item-value="name"
											variant="outlined"
											density="compact"
											:loading="isLoadingNoteCounts"
											hide-details="auto"
											clearable
											:placeholder="__('Select Note Count')"
											class="compact-input py-1"
											@update:model-value="applyNoteCountSelection(index, $event)"
										/>
									</template>

									<template #item.amount="{ item, index }">
										<v-text-field
											:model-value="item.amount"
											type="number"
											variant="outlined"
											density="compact"
											hide-details="auto"
											:min="0"
											:readonly="noteCountEnabled"
											class="amount-input ml-auto py-1"
											@update:model-value="updateAmount(index, $event)"
										/>
									</template>
								</v-data-table>
							</div>
						</v-card-text>
					</v-card>

					<v-row dense class="mt-3">
						<v-col cols="12" sm="4">
							<v-sheet class="summary-card" color="warning" rounded="lg" variant="tonal">
								<div class="text-caption text-medium-emphasis">{{ __('Total') }}</div>
								<div class="text-body-1 font-weight-bold">{{ formatAmount(totalAmount) }}</div>
							</v-sheet>
						</v-col>
					</v-row>
				</v-card-text>

				<v-card-actions class="px-4 pb-4 pt-0 d-flex gap-2 flex-wrap">
					<v-spacer />
					<v-btn
						color="primary"
						variant="elevated"
						prepend-icon="mdi-content-save"
						:loading="isSubmittingPaymentEntries"
						:disabled="!isPaymentEntryFormSubmittable"
						type="submit"
					>
						{{ __('Submit') }}
					</v-btn>
					<v-btn variant="tonal" @click="emit('update:modelValue', false)">
						{{ __('Close') }}
					</v-btn>
				</v-card-actions>
			</v-card>
		</v-form>
	</v-dialog>
</template>

<script setup>
	import { computed, reactive, ref, watch } from 'vue';

	const props = defineProps({
		modelValue: {
			type: Boolean,
			default: false,
		},
		modeOfPayments: {
			type: Array,
			default: () => [],
		},
		noteCountEnabled: {
			type: Boolean,
			default: false,
		},
		company: {
			type: String,
			default: '',
		},
		posProfile: {
			type: String,
			default: '',
		},
        costCenter: {
            type: String,
            default: '',
        },
	});

	const emit = defineEmits(['update:modelValue', 'created']);

	const __ = window.__;
	const frappe_ = window.frappe;
	const paymentEntryFormRef = ref(null);
	const isPaymentEntryFormValid = ref(false);
	const isSubmittingPaymentEntries = ref(false);
	const isLoadingNoteCounts = ref(false);

	const paymentEntryForm = reactive({
		posting_date: getToday(),
		payments: [],
	});

	const paymentHeaders = computed(() => {
		const headers = [
			{ title: __('Mode of Payment'), key: 'mode_of_payment', sortable: false },
		];

		if (props.noteCountEnabled) {
			headers.push({ title: __('Note Count'), key: 'note_count', sortable: false, width: '260px' });
		}

		headers.push({ title: __('Amount'), key: 'amount', sortable: false, align: 'end', width: '140px' });
		return headers;
	});

	const totalAmount = computed(() => {
		return paymentEntryForm.payments.reduce((total, row) => total + Number(row.amount || 0), 0);
	});

	const isPaymentEntryFormSubmittable = computed(() => {
		if (!paymentEntryForm.posting_date) {
			return false;
		}

		const positiveRows = paymentEntryForm.payments.filter((row) => Number(row.amount || 0) > 0);
		if (!positiveRows.length) {
			return false;
		}

		if (!props.noteCountEnabled) {
			return true;
		}

		return positiveRows.every((row) => !!row.note_count);
	});

	const requiredRule = (value) => !!value || __('Required');

	watch(
		() => props.modelValue,
		async (isOpen) => {
			if (!isOpen) {
				return;
			}

			resetForm();
			if (props.noteCountEnabled) {
				await loadNoteCountOptions();
			}
		},
		{ immediate: true }
	);

	watch(
		() => paymentEntryForm.posting_date,
		async () => {
			if (!props.modelValue || !props.noteCountEnabled) {
				return;
			}

			await loadNoteCountOptions();
		}
	);

	watch(
		() => props.modeOfPayments,
		() => {
			if (!props.modelValue) {
				return;
			}

			resetPayments();
		},
		{ deep: true }
	);

	function getToday() {
		if (frappe_?.datetime?.get_today) {
			return frappe_.datetime.get_today();
		}

		return new Date().toISOString().slice(0, 10);
	}

	function createPaymentRow(mode) {
		return {
			mode_of_payment: mode.name,
			type: mode.type,
			note_count: '',
			note_count_options: [],
			amount: 0,
		};
	}

	function resetPayments() {
		paymentEntryForm.payments = props.modeOfPayments.map((mode) => createPaymentRow(mode));
	}

	function resetForm() {
		paymentEntryForm.posting_date = getToday();
		resetPayments();
		isPaymentEntryFormValid.value = false;
		paymentEntryFormRef.value?.resetValidation();
	}

	function groupNoteCountsByMode(rows) {
		return rows.reduce((grouped, row) => {
			const mode = row.mode_of_payment;
			if (!grouped[mode]) {
				grouped[mode] = [];
			}
			grouped[mode].push(row);
			return grouped;
		}, {});
	}

	function getNoteCountOptionLabel(option) {
		if (!option) {
			return '';
		}

		return [option.name, option.mode_of_payment, formatAmount(option.total)]
			.filter(Boolean)
			.join(' | ');
	}

	async function loadNoteCountOptions() {
		isLoadingNoteCounts.value = true;
		try {
			const response = await frappe.call({
				method: 'maxit_pos.maxit_pos.page.maxit_pos.api.close_day_vue.get_note_count_options',
				args: {
					posting_date: paymentEntryForm.posting_date,
					mode_of_payments: props.modeOfPayments,
				},
			});

			const groupedOptions = groupNoteCountsByMode(
				(response.message || []).map((row) => ({
					...row,
					label: getNoteCountOptionLabel(row),
				}))
			);
			paymentEntryForm.payments.forEach((row) => {
				row.note_count_options = groupedOptions[row.mode_of_payment] || [];
				autoSelectNoteCount(row);
			});
		} finally {
			isLoadingNoteCounts.value = false;
		}
	}

	function autoSelectNoteCount(row) {
		if (!props.noteCountEnabled) {
			return;
		}

		const existingOption = row.note_count_options.find((option) => option.name === row.note_count);
		const nextOption = existingOption || (row.note_count_options.length === 1 ? row.note_count_options[0] : null);
		if (!nextOption) {
			row.note_count = '';
			row.amount = 0;
			return;
		}

		row.note_count = nextOption.name;
		row.amount = Number(nextOption.total || 0);
	}

	function applyNoteCountSelection(index, value) {
		const row = paymentEntryForm.payments[index];
		const option = row.note_count_options.find((item) => item.name === value);
		row.note_count = option?.name || '';
		row.amount = Number(option?.total || 0);
	}

	function updateAmount(index, value) {
		paymentEntryForm.payments[index].amount = Number(value || 0);
	}

	function formatAmount(value) {
		return Number(value || 0).toFixed(2);
	}

	async function submitPaymentEntries() {
		const validationResult = await paymentEntryFormRef.value?.validate();
		if (!validationResult?.valid) {
			frappe_.show_alert({ message: __('Please complete the required fields.'), indicator: 'red' }, 5);
			return;
		}

		if (!isPaymentEntryFormSubmittable.value) {
			frappe_.show_alert({ message: __('Add at least one payment row with a positive amount.'), indicator: 'red' }, 5);
			return;
		}

		isSubmittingPaymentEntries.value = true;
		try {
			const response = await frappe.call({
				method: 'maxit_pos.maxit_pos.page.maxit_pos.api.close_day_vue.create_payment_entries',
				args: {
					doc: JSON.stringify({
						posting_date: paymentEntryForm.posting_date,
						company: props.company,
						pos_profile: props.posProfile,
                        cost_center: props.costCenter,
						note_count_enabled: props.noteCountEnabled ? 1 : 0,
						payments: paymentEntryForm.payments.map((row) => ({
							mode_of_payment: row.mode_of_payment,
							note_count: row.note_count,
							amount: Number(row.amount || 0),
						})),
					}),
				},
			});

			const createdDocs = response.message || [];
			emit('update:modelValue', false);
			emit('created', createdDocs);
			frappe_.show_alert({ message: __('Payment Entries created successfully.'), indicator: 'green' }, 5);
		} finally {
			isSubmittingPaymentEntries.value = false;
		}
	}
</script>

<style scoped>
	.payment-entry-dialog {
		border: 1px solid rgba(120, 144, 156, 0.24);
		background: linear-gradient(180deg, rgba(255, 255, 255, 0.95), rgba(248, 251, 255, 0.97));
		box-shadow: 0 8px 20px rgba(12, 28, 43, 0.08);
	}

	.section-card {
		border-color: rgba(120, 144, 156, 0.28) !important;
	}

	.payment-entry-table {
		border: 1px solid rgba(120, 144, 156, 0.2);
		border-radius: 12px;
		overflow: hidden;
	}

	.payment-entry-table :deep(table) {
		min-width: 700px;
	}

	.payment-entry-table :deep(th) {
		white-space: nowrap;
	}

	.compact-input {
		min-width: 220px;
	}

	.amount-input {
		max-width: 120px;
	}

	.summary-card {
		border: 1px solid rgba(120, 144, 156, 0.18);
		padding: 12px;
	}
</style>