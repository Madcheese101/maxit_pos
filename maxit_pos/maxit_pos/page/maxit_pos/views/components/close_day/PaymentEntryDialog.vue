<template>
	<v-dialog
		:model-value="modelValue"
		max-width="720"
		:fullscreen="xs"
		scrollable
		@update:model-value="emit('update:modelValue', $event)"
	>
		<v-card class="payment-entry-dialog" :rounded="xs ? 0 : 'xl'">
			<v-card-item class="pb-2">
				<div class="text-h6 font-weight-bold">{{ __('New Payment Entry') }}</div>
			</v-card-item>

			<v-divider />

			<v-card-text class="dialog-body">
				<v-form ref="paymentEntryFormRef" v-model="isPaymentEntryFormValid" class="pe-form" @submit.prevent="submitPaymentEntries">
					<DateField
						v-model="paymentEntryForm.posting_date"
						:label="__('Posting Date')"
						variant="outlined"
						density="compact"
						:rules="[requiredRule]"
						hide-details="auto"
						class="pe-form__date"
					/>

					<div class="section-title">
						{{ __('Mode of Payments') }}
						<v-chip v-if="noteCountEnabled" size="small" color="primary" variant="tonal">
							{{ __('Note Count Enabled') }}
						</v-chip>
					</div>

					<v-alert v-if="!paymentEntryForm.payments.length" type="info" variant="tonal" density="compact">
						{{ __('No mode of payments are configured for this POS Profile.') }}
					</v-alert>

					<div v-for="(item, index) in paymentEntryForm.payments" :key="item.mode_of_payment" class="pe-row">
						<div class="pe-row__mode">{{ item.mode_of_payment }}</div>
						<v-autocomplete
							v-if="noteCountEnabled"
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
							class="pe-row__note"
							@update:model-value="applyNoteCountSelection(index, $event)"
						/>
						<v-text-field
							:model-value="item.amount"
							type="number"
							variant="outlined"
							density="compact"
							hide-details="auto"
							:label="__('Amount')"
							:min="0"
							:readonly="noteCountEnabled"
							class="pe-row__amount"
							@update:model-value="updateAmount(index, $event)"
						/>
					</div>

					<div class="dialog-total">
						<span class="text-medium-emphasis">{{ __('Total') }}</span>
						<span class="dialog-total__value">{{ formatAmount(totalAmount) }}</span>
					</div>
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
					:loading="isSubmittingPaymentEntries"
					:disabled="!isPaymentEntryFormSubmittable"
					@click="submitPaymentEntries"
				>
					{{ __('Submit') }}
				</v-btn>
			</v-card-actions>
		</v-card>
	</v-dialog>
</template>

<script setup>
	import { computed, reactive, ref, watch } from 'vue';
	import { useDisplay } from 'vuetify';
	import DateField from '../ui/DateField.vue';

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
	const { xs } = useDisplay();

	const paymentEntryForm = reactive({
		posting_date: getToday(),
		payments: [],
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
		return format_number(value || 0);
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
		border: 1px solid var(--v-pos-panel-border);
		background: rgb(var(--v-theme-surface));
		box-shadow: var(--v-pos-panel-shadow);
		transition: var(--v-theme-transition);
	}

	.pe-form {
		display: flex;
		flex-direction: column;
		gap: var(--maxit-gap);
	}

	.pe-form__date {
		max-width: 220px;
	}

	.section-title {
		display: flex;
		align-items: center;
		flex-wrap: wrap;
		gap: 8px;
		font-size: 0.875rem;
		font-weight: 700;
	}

	.pe-row {
		display: flex;
		flex-wrap: wrap;
		align-items: center;
		gap: var(--maxit-gap-sm);
		padding: 10px;
		border: 1px solid var(--v-pos-panel-border-soft);
		border-radius: 10px;
		background: var(--v-pos-field-background);
	}

	.pe-row__mode {
		flex: 1 1 140px;
		min-width: 0;
		font-size: 0.875rem;
		font-weight: 600;
	}

	.pe-row__note {
		flex: 2 1 220px;
	}

	.pe-row__amount {
		flex: 0 1 130px;
	}

	.dialog-total {
		display: flex;
		align-items: baseline;
		justify-content: space-between;
		gap: 12px;
		padding: 10px 12px;
		border-radius: 10px;
		background: rgba(var(--v-theme-primary), 0.08);
	}

	.dialog-total__value {
		font-size: 1.125rem;
		font-weight: 800;
	}

	@media (max-width: 599px) {
		.pe-form__date {
			max-width: none;
		}

		.pe-row__amount {
			flex: 1 1 120px;
		}
	}
</style>
