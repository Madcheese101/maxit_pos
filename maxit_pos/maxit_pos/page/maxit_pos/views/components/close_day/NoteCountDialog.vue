<template>
	<v-dialog :model-value="modelValue" max-width="980" @update:model-value="emit('update:modelValue', $event)">
		<v-form ref="noteCountFormRef" v-model="isNoteCountFormValid" @submit.prevent="submitNoteCount">
			<v-card class="note-dialog" rounded="xl">
				<v-card-item class="pb-2">
					<div class="d-flex align-center justify-space-between flex-wrap gap-2">
						<div>
							<div class="text-overline text-medium-emphasis">{{ __('Close Day') }}</div>
							<div class="text-h6 font-weight-bold">{{ __('Create Note Count') }}</div>
						</div>
					</div>
				</v-card-item>

				<v-divider />

				<v-card-text class="pt-4">
					<v-row dense>
						<v-col cols="12" md="4">
							<v-text-field
								v-model="noteCountForm.posting_date"
								type="date"
								:label="__('Posting Date')"
								variant="outlined"
								density="compact"
								:rules="[requiredRule]"
								hide-details="auto"
							/>
						</v-col>

						<v-col cols="12" md="4">
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
						</v-col>

						<v-col cols="12" md="4">
							<v-text-field
								:model-value="noteCountForm.type"
								:label="__('Type')"
								variant="outlined"
								density="compact"
								:rules="[requiredRule]"
								hide-details="auto"
								readonly
							/>
						</v-col>
					</v-row>

					<v-card v-if="noteCountForm.type === 'Cash'" class="section-card mt-4" rounded="lg" variant="outlined">
						<v-card-item class="pb-1">
							<div class="text-subtitle-1 font-weight-bold">{{ __('Cash Breakdown') }}</div>
						</v-card-item>
						<v-card-text>
							<v-table density="compact" class="note-create-table">
								<thead>
									<tr>
										<th>{{ __('Note') }}</th>
										<th class="text-right">{{ __('Count') }}</th>
										<th class="text-right">{{ __('Amount') }}</th>
									</tr>
								</thead>
								<tbody>
									<tr v-for="(row, index) in noteCountForm.cash" :key="row.note">
										<td class="font-weight-medium">{{ row.note }}</td>
										<td>
											<v-number-input
												:model-value="row.count"
												control-variant="hidden"
												variant="outlined"
												density="compact"
												:rules="[positiveIntegerRule]"
												hide-details="auto"
												:min="0"
												@update:model-value="updateCashCount(index, $event)"
											/>
										</td>
										<td class="text-right font-weight-medium">{{ formatAmount(row.amount) }}</td>
									</tr>
								</tbody>
							</v-table>
						</v-card-text>
					</v-card>

					<v-card v-else-if="noteCountForm.type === 'Bank'" class="section-card mt-4" rounded="lg" variant="outlined">
						<v-card-item class="pb-1">
							<div class="d-flex align-center justify-space-between gap-2 flex-wrap">
								<div class="text-subtitle-1 font-weight-bold">{{ __('Bank Breakdown') }}</div>
								<v-btn color="primary" variant="tonal" size="small" prepend-icon="mdi-plus" @click="addBankRow">
									{{ __('Add Row') }}
								</v-btn>
							</div>
						</v-card-item>
						<v-card-text>
							<div v-if="!noteCountForm.bank.length" class="pa-2">
								<v-alert type="info" variant="tonal" density="compact">
									{{ __('Add a bank row to enter reference and amount details.') }}
								</v-alert>
							</div>
							<div v-else class="overflow-x-auto">
								<v-table density="compact" class="note-create-table bank-create-table">
									<thead>
										<tr>
											<th>{{ __('Reference Number') }}</th>
											<th>{{ __('Amount') }}</th>
											<th>{{ __('Bank') }}</th>
											<th>{{ __('Bank Branch') }}</th>
											<th>{{ __('Account Number') }}</th>
											<th>{{ __('Mobile No') }}</th>
											<th></th>
										</tr>
									</thead>
									<tbody>
										<tr v-for="(row, index) in noteCountForm.bank" :key="`bank-${index}`">
											<td>
												<v-text-field
													v-model="row.reference_number"
													variant="outlined"
													density="compact"
													:rules="[requiredTrimmedRule]"
													hide-details="auto"
												/>
											</td>
											<td>
												<v-number-input
													v-model="row.amount"
													control-variant="hidden"
													variant="outlined"
													density="compact"
													:rules="[positiveNumberRule]"
													hide-details="auto"
													:min="0.01"
												/>
											</td>
											<td>
												<v-text-field v-model="row.bank" variant="outlined" density="compact" hide-details="auto" />
											</td>
											<td>
												<v-text-field
													v-model="row.bank_branch"
													:readonly="!row.bank"
													variant="outlined"
													density="compact"
													:rules="[requiredWhenBankRule(row)]"
													hide-details="auto"
												/>
											</td>
											<td>
												<v-text-field
													v-model="row.account_number"
													:readonly="!row.bank"
													variant="outlined"
													density="compact"
													:rules="[requiredWhenBankRule(row)]"
													hide-details="auto"
												/>
											</td>
											<td>
												<v-text-field
													v-model="row.mobile_no"
													:readonly="!row.bank"
													variant="outlined"
													density="compact"
													:rules="[requiredWhenBankRule(row)]"
													hide-details="auto"
												/>
											</td>
											<td class="text-right">
												<v-btn icon="mdi-delete-outline" variant="text" color="error" size="small" @click="removeBankRow(index)" />
											</td>
										</tr>
									</tbody>
								</v-table>
							</div>
						</v-card-text>
					</v-card>

					<v-alert v-else type="info" variant="tonal" density="compact" class="mt-4">
						{{ __('Select a mode of payment to continue.') }}
					</v-alert>

					<v-row dense class="mt-3">
						<v-col cols="12" sm="4">
							<v-sheet class="summary-card" color="warning" rounded="lg" variant="tonal">
								<div class="text-caption text-medium-emphasis">{{ __('Total') }}</div>
								<div class="text-body-1 font-weight-bold">{{ formatAmount(createDialogTotal) }}</div>
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
						:loading="isSubmittingNoteCount"
						:disabled="!isNoteCountFormSubmittable"
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
		return Number(value || 0).toFixed(2);
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

	function addBankRow() {
		noteCountForm.bank.push(createEmptyBankRow());
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
		border: 1px solid rgba(120, 144, 156, 0.24);
		background: linear-gradient(180deg, rgba(255, 255, 255, 0.95), rgba(248, 251, 255, 0.97));
		box-shadow: 0 8px 20px rgba(12, 28, 43, 0.08);
	}

	.section-card {
		border-color: rgba(120, 144, 156, 0.28) !important;
	}

	.note-create-table {
		border: 1px solid rgba(120, 144, 156, 0.2);
		border-radius: 12px;
	}

	.bank-create-table {
		min-width: 980px;
	}

	.summary-card {
		border: 1px solid rgba(120, 144, 156, 0.18);
		padding: 12px;
	}
</style>