<template>
	<v-main class="close-day-view pa-2 pa-md-4" v-if="closeDayEnabled" :style="layoutVars">
		<v-row class="close-day-shell" align="stretch" dense>
			<v-col cols="12" class="close-day-tabs-col">
				<v-card class="close-day-panel close-day-tabs-panel" rounded="xl" variant="flat">
					<v-card-item class="py-2 px-3 px-md-4">
						<v-tabs v-model="activeTab" color="primary" fixed-tabs class="close-day-tabs">
							<v-tab value="note-count" v-if="noteCountEnabled">{{ __('Note Count') }}</v-tab>
							<v-tab value="payment-entry">{{ __('Payment Entry') }}</v-tab>
						</v-tabs>
					</v-card-item>
				</v-card>
			</v-col>

			<v-col cols="12" class="close-day-main-col">
				<v-window v-model="activeTab" class="close-day-window">
					<v-window-item value="note-count" v-if="noteCountEnabled">
						<v-row class="close-day-content" align="stretch" dense>
							<v-col v-show="!smAndDown || !showDetailsOnMobile" cols="12" md="5" lg="4" class="close-day-column">
								<v-card class="close-day-panel" rounded="xl" variant="flat">
									<v-card-item class="pb-2">
										<div class="d-flex align-center justify-space-between gap-2 mb-2">
											<div>
												<div class="text-overline text-medium-emphasis">{{ __('Close Day') }}</div>
												<div class="text-h6 font-weight-bold">{{ __('Select Note Count') }}</div>
											</div>

											<v-menu location="bottom end" offset="8">
												<template #activator="{ props }">
													<v-btn
														v-bind="props"
														icon="mdi-dots-vertical"
														variant="text"
														size="small"
														color="secondary"
													/>
												</template>

												<v-card class="close-day-menu" rounded="lg" variant="flat" min-width="180">
													<v-card-text class="pa-2 d-flex flex-column ga-2">
														<v-btn
															color="primary"
															variant="text"
															prepend-icon="mdi-plus-box"
															size="small"
															@click="openNoteCountDialog"
														>
															{{ __('New Note Count') }}
														</v-btn>
														<v-btn
															color="secondary"
															variant="text"
															prepend-icon="mdi-refresh"
															size="small"
															@click="loadNoteCounts()"
														>
															{{ __('Refresh') }}
														</v-btn>
													</v-card-text>
												</v-card>
											</v-menu>
										</div>

										<v-text-field
											v-model="noteSearchTerm"
											density="compact"
											:placeholder="__('Search note count')"
											prepend-inner-icon="mdi-magnify"
											variant="solo-filled"
											hide-details
											single-line
											clearable
											rounded="lg"
											@click:prepend-inner="loadNoteCounts()"
											@keydown.enter="loadNoteCounts()"
										/>
									</v-card-item>

									<v-divider />

									<v-card-text class="pt-2 px-2 close-day-list-body">
										<div v-if="isLoadingNoteList" class="px-2 py-5 close-day-state-loader">
											<v-skeleton-loader type="list-item-two-line, list-item-two-line, list-item-two-line" />
										</div>

										<v-list
											v-else-if="noteEntries.length"
											lines="two"
											color="primary"
											nav
											rounded="lg"
											class="close-day-list"
											density="compact"
											:style="entryListStyle"
										>
											<v-list-item
												v-for="entry in noteEntries"
												:key="entry.name"
												:title="entry.mode_of_payment"
												:subtitle="entry.posting_date"
												rounded="lg"
												class="mb-1"
												:active="selectedNoteEntryName === entry.name"
												@click="selectNoteEntry(entry.name)"
											>
												<template #append>
													<div class="d-flex align-center ga-2">
														<v-chip size="small" color="secondary" variant="outlined">
															{{ formatAmount(entry.total) }}
														</v-chip>
														<v-chip size="small" :color="entry.statusColor" variant="tonal">
															{{ entry.status }}
														</v-chip>
													</div>
												</template>
											</v-list-item>
										</v-list>

										<v-alert v-else type="info" variant="tonal" density="compact" class="mt-2 close-day-state-message">
											{{ __('No note counts found for this filter.') }}
										</v-alert>
									</v-card-text>
								</v-card>
							</v-col>

							<v-col v-show="!smAndDown || showDetailsOnMobile" cols="12" md="7" lg="8" class="close-day-column">
								<v-card class="close-day-panel h-100" rounded="xl" variant="flat">
									<v-card-item class="pb-0">
										<div class="d-flex align-center justify-space-between flex-wrap gap-2">
											<div class="d-flex align-center gap-2">
												<v-btn
													v-if="smAndDown"
													icon="mdi-arrow-left"
													variant="text"
													size="small"
													@click="showDetailsOnMobile = false"
												/>

												<div>
													<div class="text-overline text-medium-emphasis">{{ __('Note Count Details') }}</div>
													<div class="text-h6 font-weight-bold d-flex align-center flex-wrap gap-2">
														{{ selectedNoteEntry?.name || __('No Note Count Selected') }}
														<v-chip
															v-if="selectedNoteEntry"
															size="small"
															:color="selectedNoteEntry.statusColor"
															variant="tonal"
														>
															{{ selectedNoteEntry.status }}
														</v-chip>
													</div>
												</div>
											</div>

											<v-chip v-if="selectedNoteEntry" size="small" color="secondary" variant="outlined">
												{{ __('Date') }}: {{ selectedNoteEntry.posting_date }}
											</v-chip>
										</div>
									</v-card-item>

									<v-card-text class="pt-3 close-day-details-body">
										<v-skeleton-loader v-if="isLoadingNoteDetail" type="table, article" />

										<v-alert v-else-if="!selectedNoteEntry" type="info" variant="tonal" density="compact">
											{{ __('Select a note count from the left panel to view full details.') }}
										</v-alert>

										<template v-else>
											<v-row dense class="mb-1">
												<v-col cols="12" sm="6" md="4">
													<v-card class="stat-card" rounded="lg" variant="tonal" color="primary">
														<v-card-text class="py-2">
															<div class="text-caption text-medium-emphasis">{{ __('Mode of Payment') }}</div>
															<div class="text-body-2 font-weight-bold text-truncate">{{ selectedNoteEntry.mode_of_payment }}</div>
														</v-card-text>
													</v-card>
												</v-col>

												<v-col cols="12" sm="6" md="4">
													<v-card class="stat-card" rounded="lg" variant="tonal" color="success">
														<v-card-text class="py-2">
															<div class="text-caption text-medium-emphasis">{{ __('Type') }}</div>
															<div class="text-body-2 font-weight-bold">{{ selectedNoteEntry.type }}</div>
														</v-card-text>
													</v-card>
												</v-col>

												<v-col cols="12" sm="6" md="4">
													<v-card class="stat-card" rounded="lg" variant="tonal" color="warning">
														<v-card-text class="py-2">
															<div class="text-caption text-medium-emphasis">{{ __('Total') }}</div>
															<div class="text-body-2 font-weight-bold">{{ formatAmount(selectedNoteEntry.total) }}</div>
														</v-card-text>
													</v-card>
												</v-col>
											</v-row>

											<v-row class="mb-1" dense>
												<v-col cols="12" md="7">
													<div class="meta-row"><strong>{{ __('Status') }}:</strong> {{ selectedNoteEntry.status }}</div>
													<div class="meta-row"><strong>{{ __('Posting Date') }}:</strong> {{ selectedNoteEntry.posting_date }}</div>
												</v-col>
											</v-row>

											<v-card class="section-card mt-3" rounded="lg" variant="outlined">
												<v-card-item class="pb-1">
													<div class="text-subtitle-1 font-weight-bold">
														{{ selectedNoteEntry.type === 'Cash' ? __('Cash Breakdown') : __('Bank Breakdown') }}
													</div>
												</v-card-item>
												<v-card-text>
													<div v-if="selectedNoteEntry.type === 'Cash'" class="close-day-table-wrap close-day-table-wrap--lg" :style="detailsTableWrapStyle">
														<v-data-table-virtual
															:headers="noteHeaders"
															:items="selectedNoteEntry.cash || []"
															item-value="note"
															density="compact"
															:height="detailsTableHeight"
															fixed-header
															class="close-day-table"
														/>
													</div>

													<div v-else class="close-day-table-wrap close-day-table-wrap--lg" :style="detailsTableWrapStyle">
														<v-data-table-virtual
															:headers="bankHeaders"
															:items="selectedNoteEntry.bank || []"
															item-value="reference_number"
															density="compact"
															:height="detailsTableHeight"
															fixed-header
															class="close-day-table"
														/>
													</div>
												</v-card-text>
											</v-card>

											<div class="actions-wrap mt-4">
												<v-btn color="primary" variant="elevated" prepend-icon="mdi-printer" size="small" :disabled="!selectedNoteEntry?.name" @click="print_note_count()">
													{{ __('Print') }}
												</v-btn>
												<v-btn color="error" variant="elevated" prepend-icon="mdi-cancel" size="small" :disabled="!canCancelSelectedNoteEntry" :loading="isCancellingNoteEntry" @click="cancel_note_count()">
													{{ __('Cancel') }}
												</v-btn>
											</div>
										</template>
									</v-card-text>
								</v-card>
							</v-col>
						</v-row>
					</v-window-item>

					<v-window-item value="payment-entry">
						<v-row class="close-day-content" align="stretch" dense>
							<v-col v-show="!smAndDown || !showDetailsOnMobile" cols="12" md="5" lg="4" class="close-day-column">
								<v-card class="close-day-panel" rounded="xl" variant="flat">
									<v-card-item class="pb-2">
										<div class="d-flex align-center justify-space-between gap-2 mb-2">
											<div>
												<div class="text-overline text-medium-emphasis">{{ __('Close Day') }}</div>
												<div class="text-h6 font-weight-bold">{{ __('Select Payment Entry') }}</div>
											</div>

											<v-menu location="bottom end" offset="8">
												<template #activator="{ props }">
													<v-btn
														v-bind="props"
														icon="mdi-dots-vertical"
														variant="text"
														size="small"
														color="secondary"
													/>
												</template>

												<v-card class="close-day-menu" rounded="lg" variant="flat" min-width="180">
													<v-card-text class="pa-2 d-flex flex-column ga-2">
														<v-btn
															color="primary"
															variant="text"
															prepend-icon="mdi-plus-box"
															size="small"
															@click="openPaymentEntryDialog"
														>
															{{ __('New Payment Entry') }}
														</v-btn>
														<v-btn
															color="secondary"
															variant="text"
															prepend-icon="mdi-printer"
															size="small"
															@click="openPaymentEntryPrintDialog"
														>
															{{ __('Print Report') }}
														</v-btn>
														<v-btn
															color="secondary"
															variant="text"
															prepend-icon="mdi-refresh"
															size="small"
															@click="loadPaymentEntries()"
														>
															{{ __('Refresh') }}
														</v-btn>
													</v-card-text>
												</v-card>
											</v-menu>
										</div>

										<v-text-field
											v-model="paymentSearchTerm"
											density="compact"
											:placeholder="__('Search payment entry')"
											prepend-inner-icon="mdi-magnify"
											variant="solo-filled"
											hide-details
											single-line
											clearable
											rounded="lg"
											@click:prepend-inner="loadPaymentEntries()"
											@keydown.enter="loadPaymentEntries()"
										/>
									</v-card-item>

									<v-divider />

									<v-card-text class="pt-2 px-2 close-day-list-body">
										<div v-if="isLoadingPaymentList" class="px-2 py-5 close-day-state-loader">
											<v-skeleton-loader type="list-item-two-line, list-item-two-line, list-item-two-line" />
										</div>

										<v-list
											v-else-if="paymentEntries.length"
											lines="two"
											color="primary"
											nav
											rounded="lg"
											class="close-day-list"
											density="compact"
											:style="entryListStyle"
										>
											<v-list-item
												v-for="entry in paymentEntries"
												:key="entry.name"
												:title="entry.mode_of_payment"
												:subtitle="entry.posting_date"
												rounded="lg"
												class="mb-1"
												:active="selectedPaymentEntryName === entry.name"
												@click="selectPaymentEntry(entry.name)"
											>
												<template #append>
													<div class="d-flex align-center ga-2">
														<v-chip size="small" color="secondary" variant="outlined">
															{{ formatAmount(entry.amount) }}
														</v-chip>
														<v-chip size="x-small" :color="entry.statusColor" variant="tonal">
															{{ entry.status }}
														</v-chip>
													</div>
												</template>
											</v-list-item>
										</v-list>

										<v-alert v-else type="info" variant="tonal" density="compact" class="mt-2 close-day-state-message">
											{{ __('No payment entries found for this filter.') }}
										</v-alert>
									</v-card-text>
								</v-card>
							</v-col>

							<v-col v-show="!smAndDown || showDetailsOnMobile" cols="12" md="7" lg="8" class="close-day-column">
								<v-card class="close-day-panel" rounded="xl" variant="flat">
									<v-card-item class="pb-0">
										<div class="d-flex align-center justify-space-between flex-wrap gap-2">
											<div class="d-flex align-center gap-2">
												<v-btn
													v-if="smAndDown"
													icon="mdi-arrow-left"
													variant="text"
													size="small"
													@click="showDetailsOnMobile = false"
												/>

												<div>
													<div class="text-overline text-medium-emphasis">{{ __('Payment Entry Details') }}</div>
													<div class="text-h6 font-weight-bold d-flex align-center flex-wrap gap-2">
														{{ selectedPaymentEntry?.name || __('No Payment Entry Selected') }}
														<v-chip
															v-if="selectedPaymentEntry"
															size="x-small"
															:color="selectedPaymentEntry.statusColor"
															variant="tonal"
														>
															{{ selectedPaymentEntry.status }}
														</v-chip>
													</div>
												</div>
											</div>

											<v-chip v-if="selectedPaymentEntry" size="x-small" color="secondary" variant="outlined">
												{{ __('Date') }}: {{ selectedPaymentEntry.posting_date }}
											</v-chip>
										</div>
									</v-card-item>

									<v-card-text class="pt-3 close-day-details-body">
										<v-skeleton-loader v-if="isLoadingPaymentDetail" type="table, article" />

										<v-alert v-else-if="!selectedPaymentEntry" type="info" variant="tonal" density="compact">
											{{ __('Select a payment entry from the left panel to view full details.') }}
										</v-alert>

										<template v-else>
											<v-row dense class="mb-1">
												<v-col cols="12" sm="6" md="4">
													<v-card class="stat-card" rounded="lg" variant="tonal" color="primary">
														<v-card-text class="py-2">
															<div class="text-caption text-medium-emphasis">{{ __('Mode of Payment') }}</div>
															<div class="text-body-2 font-weight-bold text-truncate">{{ selectedPaymentEntry.mode_of_payment }}</div>
														</v-card-text>
													</v-card>
												</v-col>

												<v-col cols="12" sm="6" md="4">
													<v-card class="stat-card" rounded="lg" variant="tonal" color="success">
														<v-card-text class="py-2">
															<div class="text-caption text-medium-emphasis">{{ __('Amount') }}</div>
															<div class="text-body-2 font-weight-bold">{{ formatAmount(selectedPaymentEntry.amount) }}</div>
														</v-card-text>
													</v-card>
												</v-col>

												<v-col cols="12" sm="6" md="4">
													<v-card class="stat-card" rounded="lg" variant="tonal" color="warning">
														<v-card-text class="py-2">
															<div class="text-caption text-medium-emphasis">{{ __('Note Count') }}</div>
															<div class="text-body-2 font-weight-bold">{{ selectedPaymentEntry.note_count || __('Not linked') }}</div>
														</v-card-text>
													</v-card>
												</v-col>
											</v-row>

											<v-row class="mb-1" dense>
												<v-col cols="12" md="6">
													<div class="meta-row"><strong>{{ __('Status') }}:</strong> {{ selectedPaymentEntry.status }}</div>
													<div class="meta-row"><strong>{{ __('Posting Date') }}:</strong> {{ selectedPaymentEntry.posting_date }}</div>
												</v-col>
												<v-col cols="12" md="6">
													<div class="meta-row"><strong>{{ __('From Account') }}:</strong> {{ selectedPaymentEntry.paid_from }}</div>
													<div class="meta-row"><strong>{{ __('To Account') }}:</strong> {{ selectedPaymentEntry.paid_to }}</div>
												</v-col>
											</v-row>

											<div class="actions-wrap mt-4">
												<v-btn
													color="error"
													variant="elevated"
													prepend-icon="mdi-cancel"
													size="small"
													:disabled="!canCancelSelectedPaymentEntry"
													:loading="isCancellingPaymentEntry"
													@click="cancel_payment_entry()"
												>
													{{ __('Cancel Payment Entry') }}
												</v-btn>
											</div>
										</template>
									</v-card-text>
								</v-card>
							</v-col>
						</v-row>
					</v-window-item>
				</v-window>
			</v-col>
		</v-row>

		<NoteCountDialog v-model="noteCountDialogOpen" @created="handleNoteCountCreated" :modeOfPayments="modeOfPayments" :posProfile="posProfileData?.name || ''"/>
		<PaymentEntryDialog
			v-model="paymentEntryDialogOpen"
			@created="handlePaymentEntriesCreated"
			:modeOfPayments="modeOfPayments"
			:noteCountEnabled="noteCountEnabled"
			:company="posProfileData?.company || ''"
			:posProfile="posProfileData?.name || ''"
			:costCenter="posProfileData?.cost_center || ''"
		/>
	</v-main>
</template>

<script setup>
	import { onMounted, ref, watch, computed } from 'vue';
    import {storeToRefs} from 'pinia';
	import { useDisplay } from 'vuetify';
	import NoteCountDialog from './components/close_day/NoteCountDialog.vue';
	import PaymentEntryDialog from './components/close_day/PaymentEntryDialog.vue';
    import { usePosStore } from '../store/posStore';
	const __ = window.__;
	const frappe_ = window.frappe;
	const { smAndDown, height: viewportHeight } = useDisplay();
    const posStore = usePosStore();
    const { posProfileData } = storeToRefs(posStore);
	const noteSearchTerm = ref('');
	const paymentSearchTerm = ref('');
	const showDetailsOnMobile = ref(false);
	const isLoadingNoteList = ref(false);
	const isLoadingNoteDetail = ref(false);
	const isLoadingPaymentList = ref(false);
	const isLoadingPaymentDetail = ref(false);
	const isCancellingNoteEntry = ref(false);
	const isCancellingPaymentEntry = ref(false);
	const noteEntries = ref([]);
	const selectedNoteEntry = ref(null);
	const selectedNoteEntryName = ref('');
	const noteCountDialogOpen = ref(false);
	const paymentEntryDialogOpen = ref(false);
    const modeOfPayments = ref([]);
	const paymentEntries = ref([]);
	const selectedPaymentEntry = ref(null);
	const selectedPaymentEntryName = ref('');
	const hasInitializedTab = ref(false);
	const isMobile = computed(() => smAndDown.value);
	const canCancelSelectedNoteEntry = computed(() => Number(selectedNoteEntry.value?.docstatus) === 1 && !isCancellingNoteEntry.value);
	const canCancelSelectedPaymentEntry = computed(() => Number(selectedPaymentEntry.value?.docstatus) === 1 && !isCancellingPaymentEntry.value);
	const profileContextKey = computed(() => JSON.stringify({
		profileName: posProfileData.value?.name || '',
		company: posProfileData.value?.company || '',
		costCenter: posProfileData.value?.cost_center || '',
		noteCountEnabled: !!posProfileData.value?.enable_note_count,
		payments: (posProfileData.value?.payments || []).map((row) => row?.mode_of_payment || row?.name || ''),
	}));
	let suppressNoteSearchReload = false;
	let suppressPaymentSearchReload = false;

	const viewportHeightPx = computed(() => viewportHeight.value || window.innerHeight || 800);
	const listScrollHeight = computed(() => {
		const reserved = isMobile.value ? 320 : 300;
		return Math.max(220, viewportHeightPx.value - reserved);
	});

	const detailsTableHeight = computed(() => {
		const reserved = isMobile.value ? 600 : 540;
		return Math.max(150, viewportHeightPx.value - reserved);
	});

	const layoutVars = computed(() => ({
		'--close-day-list-scroll-height': `${listScrollHeight.value}px`,
		'--close-day-table-height': `${detailsTableHeight.value}px`,
	}));

	const entryListStyle = computed(() => ({
		height: 'var(--close-day-list-scroll-height)',
		maxHeight: 'var(--close-day-list-scroll-height)',
	}));

	const detailsTableWrapStyle = computed(() => ({
		height: 'var(--close-day-table-height)',
		maxHeight: 'var(--close-day-table-height)',
	}));

	const noteHeaders = [
		{ title: __('Note'), key: 'note' },
		{ title: __('Count'), key: 'count' },
		{ title: __('Amount'), key: 'amount' },
	];

	const bankHeaders = [
		{ title: __('Reference Number'), key: 'reference_number' },
		{ title: __('Amount'), key: 'amount' },
		{ title: __('Bank'), key: 'bank' },
		{ title: __('Bank Branch'), key: 'bank_branch' },
		{ title: __('Account Number'), key: 'account_number' },
		{ title: __('Mobile No'), key: 'mobile_no' },
	];

	const closeDayEnabled = computed(() => {
	const roles = ['Accounts User', 'Accounts Manager', 'Administrator', 'System Manager'];
	return roles.some(role => frappe.user.has_role(role));
	});
	const noteCountEnabled = computed(() => {
	return closeDayEnabled.value && posProfileData.value?.enable_note_count;
	});
	const activeTab = ref(noteCountEnabled.value ? 'note-count' : 'payment-entry');
	
	watch(activeTab, () => {
		showDetailsOnMobile.value = false;
	});
	watch(noteSearchTerm, (value) => {
		if (!value && !suppressNoteSearchReload) {
			loadNoteCounts();
		}
	});
	watch(paymentSearchTerm, (value) => {
		if (!value && !suppressPaymentSearchReload) {
			loadPaymentEntries();
		}
	});
	watch(profileContextKey, async () => {
		if (!hasInitializedTab.value) {
			activeTab.value = noteCountEnabled.value ? 'note-count' : 'payment-entry';
			hasInitializedTab.value = true;
		} else if (!noteCountEnabled.value && activeTab.value === 'note-count') {
			activeTab.value = 'payment-entry';
		}

		if (!posProfileData.value?.name || !posProfileData.value?.cost_center) {
			modeOfPayments.value = [];
			paymentEntries.value = [];
			selectedPaymentEntryName.value = '';
			selectedPaymentEntry.value = null;
			return;
		}

		await loadModeOfPayments();
		await loadPaymentEntries();
	}, { immediate: true });
	onMounted(async () => {
		await loadNoteCounts();
	});

	function getToday() {
		if (frappe.datetime?.get_today) {
			return frappe.datetime.get_today();
		}

		return new Date().toISOString().slice(0, 10);
	}

	function formatAmount(value) {
		return Number(value || 0).toFixed(2);
	}

	function getDocstatusLabel(docstatus) {
		switch (Number(docstatus)) {
			case 1:
				return __('Submitted');
			case 2:
				return __('Cancelled');
			default:
				return __('Draft');
		}
	}

	function getDocstatusColor(docstatus) {
		switch (Number(docstatus)) {
			case 1:
				return 'success';
			case 2:
				return 'error';
			default:
				return 'info';
		}
	}

	function buildNoteSubtitle(entry) {
		return [entry?.mode_of_payment, entry?.type].filter(Boolean).join(' - ');
	}

	function getPaymentEntryAmount(entry) {
		return Number(entry?.paid_amount || entry?.received_amount || entry?.amount || 0);
	}

	function mapNoteEntry(entry) {
		if (!entry) {
			return null;
		}

		return {
			...entry,
			total: Number(entry.total || 0),
			status: getDocstatusLabel(entry.docstatus),
			statusColor: getDocstatusColor(entry.docstatus),
			subtitle: buildNoteSubtitle(entry),
		};
	}

	function mapPaymentEntry(entry) {
		if (!entry) {
			return null;
		}

		const modeOfPayment = entry.mode_of_payment || '';
		const noteCount = entry.note_count || '';
		const amount = getPaymentEntryAmount(entry);

		return {
			...entry,
			mode_of_payment: modeOfPayment,
			note_count: noteCount,
			amount,
			status: getDocstatusLabel(entry.docstatus),
			statusColor: getDocstatusColor(entry.docstatus),
			subtitle: [modeOfPayment, noteCount].filter(Boolean).join(' - '),
		};
	}

	function confirmDialog(message) {
		return new Promise((resolve) => {
			frappe_.confirm(message, () => resolve(true), () => resolve(false));
		});
	}

	function openNoteCountDialog() {
		noteCountDialogOpen.value = true;
	}

	function openPaymentEntryDialog() {
		paymentEntryDialogOpen.value = true;
	}

	function openPaymentEntryPrintDialog() {
		if (!posProfileData.value?.name) {
			frappe_.msgprint(__('POS Profile is required to print the Close Day report.'));
			return;
		}

		const dialog = new frappe.ui.Dialog({
			title: __('Print Close Day Report'),
			fields: [
				{
					label: __('Posting Date'),
					fieldname: 'posting_date',
					fieldtype: 'Date',
					reqd: true,
					default: getToday(),
				},
			],
			primary_action_label: __('Print'),
			primary_action: async (values) => {
				const postingDate = values?.posting_date;
				if (!postingDate) {
					frappe_.show_alert({ message: __('Posting Date is required.'), indicator: 'red' }, 5);
					return;
				}

				const printWindow = window.open('', '_blank');
				if (!printWindow) {
					frappe_.show_alert({ message: __('Allow pop-ups to print the Close Day report.'), indicator: 'red' }, 5);
					return;
				}

				printWindow.document.write(`
					<html>
						<head><title>${__('Preparing Close Day Report')}</title></head>
						<body style="font-family: Arial, sans-serif; padding: 24px;">${__('Preparing report...')}</body>
					</html>
				`);
				printWindow.document.close();

				const primaryButton = dialog.get_primary_btn();
				primaryButton.prop('disabled', true);

				try {
					const response = await frappe_.call({
						method: 'maxit_pos.maxit_pos.page.maxit_pos.api.close_day_vue.get_close_day_payment_report_html',
						args: {
							posting_date: postingDate,
							pos_profile: posProfileData.value?.name || '',
							company: posProfileData.value?.company || '',
							cost_center: posProfileData.value?.cost_center || '',
							letter_head: posProfileData.value?.letter_head || '',
							mode_of_payments: JSON.stringify(posProfileData.value?.payments || []),
						},
					});

					const html = response.message?.html;
					if (!html) {
						throw new Error(__('Unable to generate the Close Day report.'));
					}

					printWindow.document.open();
					printWindow.document.write(html);
					printWindow.document.close();
					dialog.hide();
				} catch (error) {
					printWindow.close();
					frappe_.msgprint(error?.message || __('Unable to generate the Close Day report.'));
				} finally {
					primaryButton.prop('disabled', false);
				}
			},
		});

		dialog.show();
	}

	async function loadNoteCounts() {
		isLoadingNoteList.value = true;
		try {
			const response = await frappe_.call({
				method: 'maxit_pos.maxit_pos.page.maxit_pos.api.close_day_vue.get_note_count_list',
				args: {
					search_term: noteSearchTerm.value || '',
					pos_profile: posProfileData.value?.name || '',
				},
			});

			noteEntries.value = (response.message || []).map(mapNoteEntry);

			if (!noteEntries.value.length) {
				selectedNoteEntryName.value = '';
				selectedNoteEntry.value = null;
				return;
			}

			const existingSelection = noteEntries.value.some((entry) => entry.name === selectedNoteEntryName.value);
			const nameToLoad = existingSelection ? selectedNoteEntryName.value : noteEntries.value[0].name;
			await loadNoteDetail(nameToLoad);
		} finally {
			isLoadingNoteList.value = false;
		}
	}

    async function loadModeOfPayments() {
		if (!posProfileData.value?.name) {
			modeOfPayments.value = [];
			return;
		}

		try {
			const response = await frappe_.call({
				method: 'maxit_pos.maxit_pos.page.maxit_pos.api.close_day_vue.get_mode_of_payments',
				args: {
					mode_of_payments: posProfileData.value?.payments || [],
					company: posProfileData.value?.company,
				},
			});
			modeOfPayments.value = response.message || [];
		} finally {}
	}

	async function loadPaymentEntries() {
		if (!posProfileData.value?.name || !posProfileData.value?.cost_center) {
			paymentEntries.value = [];
			selectedPaymentEntryName.value = '';
			selectedPaymentEntry.value = null;
			return;
		}

		isLoadingPaymentList.value = true;
		try {
			const response = await frappe_.call({
				method: 'maxit_pos.maxit_pos.page.maxit_pos.api.close_day_vue.get_payment_entry_list',
				args: {
					search_term: paymentSearchTerm.value || '',
					cost_center: posProfileData.value?.cost_center || '',
					pos_profile: posProfileData.value?.name || '',
				},
			});

			paymentEntries.value = (response.message || []).map(mapPaymentEntry);

			if (!paymentEntries.value.length) {
				selectedPaymentEntryName.value = '';
				selectedPaymentEntry.value = null;
				return;
			}

			const existingSelection = paymentEntries.value.some((entry) => entry.name === selectedPaymentEntryName.value);
			const nameToLoad = existingSelection ? selectedPaymentEntryName.value : paymentEntries.value[0].name;
			await loadPaymentEntryDetail(nameToLoad);
		} finally {
			isLoadingPaymentList.value = false;
		}
	}

	async function loadPaymentEntryDetail(name) {
		if (!name) {
			selectedPaymentEntryName.value = '';
			selectedPaymentEntry.value = null;
			return;
		}

		isLoadingPaymentDetail.value = true;
		selectedPaymentEntryName.value = name;
		try {
			const response = await frappe_.call({
				method: 'maxit_pos.maxit_pos.page.maxit_pos.api.close_day_vue.get_payment_entry_detail',
				args: { name },
			});
			selectedPaymentEntry.value = mapPaymentEntry(response.message);
		} finally {
			isLoadingPaymentDetail.value = false;
		}
	}

	async function selectPaymentEntry(name) {
		showDetailsOnMobile.value = true;
		await loadPaymentEntryDetail(name);
	}

	async function loadNoteDetail(name) {
		if (!name) {
			selectedNoteEntryName.value = '';
			selectedNoteEntry.value = null;
			return;
		}

		isLoadingNoteDetail.value = true;
		selectedNoteEntryName.value = name;
		try {
			const response = await frappe_.call({
				method: 'maxit_pos.maxit_pos.page.maxit_pos.api.close_day_vue.get_note_count_detail',
				args: { name },
			});
			selectedNoteEntry.value = mapNoteEntry(response.message);
		} finally {
			isLoadingNoteDetail.value = false;
		}
	}

	async function selectNoteEntry(name) {
		showDetailsOnMobile.value = true;
		await loadNoteDetail(name);
	}

	async function handleNoteCountCreated(createdDoc) {
		noteCountDialogOpen.value = false;
		suppressNoteSearchReload = true;
		noteSearchTerm.value = '';
		suppressNoteSearchReload = false;
		await loadNoteCounts();
		if (createdDoc?.name) {
			await loadNoteDetail(createdDoc.name);
			showDetailsOnMobile.value = true;
		}
	}

	async function handlePaymentEntriesCreated(createdDocs) {
		paymentEntryDialogOpen.value = false;
		suppressPaymentSearchReload = true;
		paymentSearchTerm.value = '';
		suppressPaymentSearchReload = false;
		await loadPaymentEntries();
		const firstCreatedDoc = createdDocs?.[0];
		if (firstCreatedDoc?.name) {
			await loadPaymentEntryDetail(firstCreatedDoc.name);
			showDetailsOnMobile.value = true;
		}
	}

	function print_note_count(){
		const invoice = selectedNoteEntry.value?.name;
		if (!invoice) {
			frappe_.msgprint(__('Select a note count to print.'));
			return;
		}

		const doctype = "Note Count";
		const printFormat = posProfileData.value?.note_count_print_format || 'Standard';
		const letterHead = posProfileData.value?.letter_head || 'No Letterhead';
		const no_letterhead = letterHead === 'No Letterhead' ? '1' : '0';
		const printUrl = `/printview?${new URLSearchParams({
			doctype,
			name: invoice,
			format: printFormat,
			no_letterhead,
			letterhead: letterHead,
			settings: '{}',
			_lang: frappe_.boot?.lang || 'en',
			pdf_generator: 'wkhtmltopdf',
			trigger_print: '1',
		}).toString()}`;
		window.open(printUrl, '_blank');
	}
	async function cancel_note_count(){
		if (!selectedNoteEntry.value?.name) {
			frappe_.msgprint(__('Select a note count to cancel.'));
			return;
		}

		if (!canCancelSelectedNoteEntry.value) {
			frappe_.msgprint(__('Only submitted note counts can be cancelled.'));
			return;
		}

		const confirmed = await confirmDialog(__('Cancel note count {0}?').replace('{0}', selectedNoteEntry.value.name));
		if (!confirmed) {
			return;
		}

		isCancellingNoteEntry.value = true;
		try {
			await frappe_.call({
				method: 'maxit_pos.maxit_pos.page.maxit_pos.api.close_day_vue.cancel_note_count',
				args: { name: selectedNoteEntry.value.name },
			});
			frappe_.show_alert({ message: __('Note count cancelled successfully.'), indicator: 'green' }, 5);
			await loadNoteCounts();
			showDetailsOnMobile.value = true;
		} catch (error) {
			frappe_.msgprint(error?.message || __('Unable to cancel note count.'));
		} finally {
			isCancellingNoteEntry.value = false;
		}
	}

	async function cancel_payment_entry(){
		if (!selectedPaymentEntry.value?.name) {
			frappe_.msgprint(__('Select a payment entry to cancel.'));
			return;
		}

		if (!canCancelSelectedPaymentEntry.value) {
			frappe_.msgprint(__('Only submitted payment entries can be cancelled.'));
			return;
		}

		const confirmed = await confirmDialog(__('Cancel payment entry {0}?').replace('{0}', selectedPaymentEntry.value.name));
		if (!confirmed) {
			return;
		}

		isCancellingPaymentEntry.value = true;
		try {
			await frappe_.call({
				method: 'maxit_pos.maxit_pos.page.maxit_pos.api.close_day_vue.cancel_payment_entry',
				args: { name: selectedPaymentEntry.value.name },
			});
			frappe_.show_alert({ message: __('Payment entry cancelled successfully.'), indicator: 'green' }, 5);
			await loadPaymentEntries();
			showDetailsOnMobile.value = true;
		} catch (error) {
			frappe_.msgprint(error?.message || __('Unable to cancel payment entry.'));
		} finally {
			isCancellingPaymentEntry.value = false;
		}
	}
</script>

<style scoped>
	.close-day-view {
		min-height: calc(100dvh - var(--v-layout-top, 0px) - var(--v-layout-bottom, 0px));
		height: calc(100dvh - var(--v-layout-top, 0px) - var(--v-layout-bottom, 0px));
		overflow: hidden;
		background:
			radial-gradient(circle at top right, rgba(25, 118, 210, 0.08), transparent 40%),
			radial-gradient(circle at left bottom, rgba(76, 175, 80, 0.07), transparent 35%);
	}

	.close-day-shell {
		display: flex;
		flex-direction: column;
		flex-wrap: nowrap;
		height: 100%;
		min-height: 0;
	}

	.close-day-main-col {
		flex: 1 1 auto;
		display: flex;
		min-height: 0;
	}

	.close-day-tabs-col {
		flex: 0 0 auto;
	}

	.close-day-window {
		flex: 1;
		min-height: 0;
	}

	.close-day-window :deep(.v-window__container),
	.close-day-window :deep(.v-window-item),
	.close-day-window :deep(.v-window-item--active) {
		height: 100%;
		min-height: 0;
	}

	.close-day-content {
		height: 100%;
		min-height: 0;
	}

	.close-day-column {
		display: flex;
		min-height: 0;
	}

	.close-day-panel,
	.close-day-menu {
		border: 1px solid rgba(120, 144, 156, 0.24);
		background: linear-gradient(180deg, rgba(255, 255, 255, 0.95), rgba(248, 251, 255, 0.97));
		box-shadow: 0 8px 20px rgba(12, 28, 43, 0.08);
	}

	.close-day-panel {
		width: 100%;
		height: 100%;
		min-height: 0;
		display: flex;
		flex-direction: column;
	}

	.close-day-tabs-panel {
		height: auto;
		min-height: auto;
		display: block;
	}

	.close-day-list-body {
		flex: 1;
		min-height: 0;
		display: flex;
		flex-direction: column;
		overflow: hidden;
	}

	.close-day-list {
		flex: 1;
		min-height: 0;
		overflow-y: auto;
	}

	.close-day-state-message,
	.close-day-state-loader {
		flex: 0 0 auto;
	}

	.close-day-details-body {
		flex: 1;
		min-height: 0;
		overflow-y: auto;
		overflow-x: hidden;
	}

	.close-day-table-wrap {
		min-height: 150px;
		overflow: hidden;
	}

	.close-day-tabs :deep(.v-tab--selected) {
		font-weight: 700;
	}

	.close-day-list :deep(.v-list-item--active) {
		background: rgba(25, 118, 210, 0.13);
	}

	.section-card {
		border-color: rgba(120, 144, 156, 0.28) !important;
	}

	.close-day-table {
		border-radius: 10px;
		height: 100%;
	}

	.close-day-table :deep(.v-table__wrapper) {
		height: 100%;
		max-height: 100%;
		overflow-y: auto;
	}

	.stat-card,
	.summary-card {
		border: 1px solid rgba(120, 144, 156, 0.18);
	}

	.meta-row {
		padding: 3px 0;
	}

	.actions-wrap {
		display: flex;
		flex-wrap: wrap;
		gap: 8px;
	}

	@media (max-width: 960px) {
		.close-day-view {
			min-height: calc(100dvh - var(--v-layout-top, 0px) - var(--v-layout-bottom, 0px));
			height: calc(100dvh - var(--v-layout-top, 0px) - var(--v-layout-bottom, 0px));
			padding: 10px;
		}

		.actions-wrap {
			display: grid;
			grid-template-columns: 1fr;
		}
	}

	@media (max-height: 720px) {
		.close-day-view {
			padding-top: 8px;
			padding-bottom: 8px;
		}
	}
</style>
