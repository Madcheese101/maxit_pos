<template>
	<v-dialog
		:model-value="modelValue"
		max-width="720"
		:fullscreen="xs"
		scrollable
		@update:model-value="emit('update:modelValue', $event)"
	>
		<v-card class="note-dialog" :rounded="xs ? 0 : 'xl'">
			<v-card-item class="pb-2">
				<div class="text-h6 font-weight-bold">{{ __('Create Note Count') }}</div>
			</v-card-item>

			<v-divider />

			<v-card-text ref="dialogBody" class="dialog-body">
				<v-form ref="noteCountFormRef" v-model="isNoteCountFormValid" class="note-form" @submit.prevent="submitNoteCount">
					<div class="note-form__fields">
						<v-text-field
							v-model="noteCountForm.posting_date"
							type="date"
							:label="__('Posting Date')"
							variant="outlined"
							density="compact"
							:rules="[requiredRule]"
							hide-details="auto"
						/>
						<v-select
							v-model="noteCountForm.mode_of_payment"
							:items="modeOfPayments"
							item-title="name"
							item-value="name"
							:label="__('Mode of Payment')"
							variant="outlined"
							density="compact"
							:rules="[requiredRule]"
							hide-details="auto"
						/>
						<v-text-field
							:model-value="noteCountForm.type"
							:label="__('Type')"
							variant="outlined"
							density="compact"
							:rules="[requiredRule]"
							hide-details="auto"
							readonly
						/>
					</div>

					<template v-if="noteCountForm.type === 'Cash'">
						<div class="section-title">{{ __('Cash Breakdown') }}</div>
						<div v-for="(row, index) in noteCountForm.cash" :key="row.note" class="cash-row">
							<div class="cash-row__note">{{ row.note }}</div>
							<span class="text-medium-emphasis">×</span>
							<v-number-input
								:model-value="row.count"
								control-variant="hidden"
								variant="outlined"
								density="compact"
								:label="__('Count')"
								:rules="[positiveIntegerRule]"
								hide-details="auto"
								:min="0"
								class="cash-row__count"
								@update:model-value="updateCashCount(index, $event)"
							/>
							<div class="cash-row__amount">{{ formatAmount(row.amount) }}</div>
						</div>
					</template>

					<template v-else-if="noteCountForm.type === 'Bank'">
						<div class="section-title">{{ __('Bank Breakdown') }}</div>
						<v-alert v-if="!noteCountForm.bank.length" type="info" variant="tonal" density="compact">
							{{ __('Add a bank row to enter reference and amount details.') }}
						</v-alert>
						<div v-for="(row, index) in noteCountForm.bank" :key="`bank-${index}`" class="bank-row-card">
							<div class="bank-row-card__head">
								<span class="text-medium-emphasis font-weight-bold">{{ index + 1 }}</span>
								<v-btn
									icon="mdi-delete-outline"
									variant="text"
									color="error"
									size="small"
									:aria-label="__('Delete')"
									@click="removeBankRow(index)"
								/>
							</div>
							<div class="bank-row-card__fields">
								<v-text-field
									v-model="row.reference_number"
									:label="__('Reference Number')"
									variant="outlined"
									density="compact"
									:rules="[requiredTrimmedRule]"
									hide-details="auto"
								/>
								<v-number-input
									v-model="row.amount"
									control-variant="hidden"
									:label="__('Amount')"
									variant="outlined"
									density="compact"
									:rules="[positiveNumberRule]"
									hide-details="auto"
									:min="0.01"
								/>
								<v-text-field v-model="row.bank" :label="__('Bank')" variant="outlined" density="compact" hide-details="auto" />
								<v-text-field
									v-model="row.bank_branch"
									:label="__('Bank Branch')"
									:readonly="!row.bank"
									variant="outlined"
									density="compact"
									:rules="[requiredWhenBankRule(row)]"
									hide-details="auto"
								/>
								<v-text-field
									v-model="row.account_number"
									:label="__('Account Number')"
									:readonly="!row.bank"
									variant="outlined"
									density="compact"
									:rules="[requiredWhenBankRule(row)]"
									hide-details="auto"
								/>
								<v-text-field
									v-model="row.mobile_no"
									:label="__('Mobile No')"
									:readonly="!row.bank"
									variant="outlined"
									density="compact"
									:rules="[requiredWhenBankRule(row)]"
									hide-details="auto"
								/>
							</div>
						</div>
						<v-btn color="primary" variant="tonal" prepend-icon="mdi-plus" class="align-self-start" @click="addBankRow">
							{{ __('Add Row') }}
						</v-btn>
					</template>

					<v-alert v-else type="info" variant="tonal" density="compact">
						{{ __('Select a mode of payment to continue.') }}
					</v-alert>

					<div class="dialog-total">
						<span class="text-medium-emphasis">{{ __('Total') }}</span>
						<span class="dialog-total__value">{{ formatAmount(createDialogTotal) }}</span>
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
					:loading="isSubmittingNoteCount"
					:disabled="!isNoteCountFormSubmittable"
					@click="submitNoteCount"
				>
					{{ __('Submit') }}
				</v-btn>
			</v-card-actions>
		</v-card>
	</v-dialog>
</template>

<script setup>
	import { computed, nextTick, reactive, ref, watch } from 'vue';
	import { useDisplay } from 'vuetify';

	const props = defineProps({
		modelValue: {
			type: Boolean,
			default: false,
		},
        modeOfPayments: {
            type: Array,
            default: () => [],
        },
		posProfile: {
			type: String,
			default: '',
		},
	});

	const emit = defineEmits(['update:modelValue', 'created']);

	const __ = window.__;
	const frappe_ = window.frappe;
	const cashNotes = ['5', '10', '20', '50'];

	// const isLoadingModes = ref(false);
	const isSubmittingNoteCount = ref(false);
	const noteCountFormRef = ref(null);
	const isNoteCountFormValid = ref(false);
	const dialogBody = ref(null);
	const { xs } = useDisplay();

	const noteCountForm = reactive({
		posting_date: getToday(),
		mode_of_payment: '',
		type: '',
		cash: [],
		bank: [],
	});

	const modeTypeMap = computed(() => {
		return Object.fromEntries(props.modeOfPayments.map((mode) => [mode.name, mode.type]));
	});

	const createDialogTotal = computed(() => {
		if (noteCountForm.type === 'Cash') {
			return noteCountForm.cash.reduce((total, row) => total + Number(row.amount || 0), 0);
		}

		if (noteCountForm.type === 'Bank') {
			return noteCountForm.bank.reduce((total, row) => total + Number(row.amount || 0), 0);
		}

		return 0;
	});

	const isNoteCountFormSubmittable = computed(() => {
		if (!noteCountForm.posting_date || !noteCountForm.mode_of_payment || !noteCountForm.type) {
			return false;
		}

		if (noteCountForm.type === 'Cash') {
			return noteCountForm.cash.length === cashNotes.length && createDialogTotal.value > 0;
		}

		if (noteCountForm.type === 'Bank') {
			return noteCountForm.bank.length > 0;
		}

		return false;
	});

	const requiredRule = (value) => !!value || __('Required');
	const requiredTrimmedRule = (value) => !!String(value || '').trim() || __('Required');
	const positiveIntegerRule = (value) => Number.isInteger(Number(value)) && Number(value) >= 0 || __('Must be greater than 0');
	const positiveNumberRule = (value) => Number(value) > 0 || __('Must be greater than 0');
	const requiredWhenBankRule = (row) => (value) => !String(row.bank || '').trim() || !!String(value || '').trim() || __('Required');

	watch(
		() => props.modelValue,
		(isOpen) => {
			if (!isOpen) {
				return;
			}

			resetForm();
		},
		{ immediate: true }
	);

	watch(
		() => noteCountForm.mode_of_payment,
		(modeOfPayment) => {
			noteCountForm.type = modeTypeMap.value[modeOfPayment] || '';
			resetModalTables();
		}
	);

	function getToday() {
		if (frappe_?.datetime?.get_today) {
			return frappe_.datetime.get_today();
		}

		return new Date().toISOString().slice(0, 10);
	}

	function formatAmount(value) {
		return format_number(value || 0);
	}

	function seedCashRows() {
		return cashNotes.map((note) => ({ note, count: 0, amount: 0 }));
	}

	function createEmptyBankRow() {
		return {
			reference_number: '',
			amount: 0,
			bank: '',
			bank_branch: '',
			account_number: '',
			mobile_no: '',
		};
	}

	function resetModalTables() {
		noteCountForm.cash = [];
		noteCountForm.bank = [];

		if (noteCountForm.type === 'Cash') {
			noteCountForm.cash = seedCashRows();
		}
	}

	function resetForm() {
		noteCountForm.posting_date = getToday();
		noteCountForm.mode_of_payment = '';
		noteCountForm.type = '';
		noteCountForm.cash = [];
		noteCountForm.bank = [];
		isNoteCountFormValid.value = false;
		noteCountFormRef.value?.resetValidation();
	}

	async function addBankRow() {
		noteCountForm.bank.push(createEmptyBankRow());
		// the dialog body is the scroll container; keep the new row in view
		await nextTick();
		const bodyEl = dialogBody.value?.$el;
		if (bodyEl) {
			bodyEl.scrollTop = bodyEl.scrollHeight;
		}
	}

	function removeBankRow(index) {
		noteCountForm.bank.splice(index, 1);
	}

	function updateCashCount(index, value) {
		const count = Math.max(Math.trunc(Number(value || 0)), 0);
		const note = Number(noteCountForm.cash[index]?.note || 0);
		noteCountForm.cash[index].count = count;
		noteCountForm.cash[index].amount = note * count;
	}

	async function submitNoteCount() {
		const validationResult = await noteCountFormRef.value?.validate();
		if (!validationResult?.valid) {
			frappe_.show_alert({ message: __('Please complete the required fields.'), indicator: 'red' }, 5);
			return;
		}

		if (noteCountForm.type === 'Bank' && !noteCountForm.bank.length) {
			frappe_.show_alert({ message: __('Add at least one bank row before submitting.'), indicator: 'red' }, 5);
			return;
		}

		isSubmittingNoteCount.value = true;
		try {
			const payload = {
				posting_date: noteCountForm.posting_date,
				mode_of_payment: noteCountForm.mode_of_payment,
				cash: noteCountForm.cash,
				bank: noteCountForm.bank,
				pos_profile: props.posProfile,
			};
			console.log('Submitting Note Count with payload:', payload);
			const response = await frappe.call({
				method: 'maxit_pos.maxit_pos.page.maxit_pos.api.close_day_vue.create_note_count',
				args: {
					doc: JSON.stringify(payload),
				},
			});

			const createdDoc = response.message;
			emit('update:modelValue', false);
			emit('created', createdDoc);
			frappe_.show_alert({ message: __('Note Count created successfully.'), indicator: 'green' }, 5);
		} finally {
			isSubmittingNoteCount.value = false;
		}
	}
</script>

<style scoped>
	.note-dialog {
		border: 1px solid var(--v-pos-panel-border);
		background: rgb(var(--v-theme-surface));
		box-shadow: var(--v-pos-panel-shadow);
		transition: var(--v-theme-transition);
	}

	.note-form {
		display: flex;
		flex-direction: column;
		gap: 10px;
	}

	.note-form__fields {
		display: grid;
		grid-template-columns: repeat(auto-fill, minmax(180px, 1fr));
		gap: 8px;
	}

	.section-title {
		font-size: 0.875rem;
		font-weight: 700;
	}

	.cash-row {
		display: flex;
		align-items: center;
		gap: 10px;
		padding: 6px 8px;
		border: 1px solid var(--v-pos-panel-border-soft);
		border-radius: 10px;
		background: var(--v-pos-field-background);
	}

	.cash-row__note {
		min-width: 40px;
		font-size: 1rem;
		font-weight: 700;
		text-align: center;
	}

	.cash-row__count {
		flex: 1 1 120px;
		max-width: 180px;
	}

	.cash-row__amount {
		flex: 1;
		text-align: end;
		font-weight: 700;
	}

	.bank-row-card {
		display: flex;
		flex-direction: column;
		gap: 4px;
		padding: 8px;
		border: 1px solid var(--v-pos-panel-border-soft);
		border-radius: 10px;
		background: var(--v-pos-field-background);
	}

	.bank-row-card__head {
		display: flex;
		align-items: center;
		justify-content: space-between;
		padding-inline-start: 4px;
	}

	.bank-row-card__fields {
		display: grid;
		grid-template-columns: repeat(auto-fill, minmax(130px, 1fr));
		gap: 8px;
	}

	/* six bank fields: 2 columns on phones, 3 + 3 elsewhere */
	@media (min-width: 600px) {
		.bank-row-card__fields {
			grid-template-columns: repeat(3, minmax(0, 1fr));
		}
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
</style>
