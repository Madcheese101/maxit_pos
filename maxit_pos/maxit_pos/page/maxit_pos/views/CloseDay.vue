<template>
	<v-main class="close-day-view pa-2 pa-md-4" v-if="closeDayEnabled">
		<v-row class="close-day-shell" align="stretch" dense>
			<v-col cols="12">
				<v-card class="close-day-panel" rounded="xl" variant="flat">
					<v-card-item class="py-2 px-3 px-md-4">
						<v-tabs v-model="activeTab" color="primary" fixed-tabs class="close-day-tabs">
							<v-tab value="note-count" v-if="noteCountEnabled">{{ __('Note Count') }}</v-tab>
							<v-tab value="payment-entry">{{ __('Payment Entry') }}</v-tab>
						</v-tabs>
					</v-card-item>
				</v-card>
			</v-col>

			<v-col cols="12">
				<v-window v-model="activeTab">
					<v-window-item value="note-count" v-if="noteCountEnabled">
						<v-row class="close-day-content" align="stretch" dense>
							<v-col v-show="!smAndDown || !showDetailsOnMobile" cols="12" md="4" lg="3">
								<v-card class="close-day-panel" rounded="xl" variant="flat" max-height="100vh">
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
											@click:clear="loadNoteCounts()"
											@keydown.enter="loadNoteCounts()"
										/>
									</v-card-item>

									<v-divider />

									<v-card-text class="pt-2 px-2">
										<div v-if="isLoadingNoteList" class="px-2 py-5">
											<v-skeleton-loader type="list-item-two-line, list-item-two-line, list-item-two-line" />
										</div>

										<v-list
											v-else-if="noteEntries.length"
											lines="two"
											color="primary"
											nav
											rounded="lg"
											class="close-day-list overflow-y-auto"
											density="compact"
											max-height="50vh"
										>
											<v-list-item
												v-for="entry in noteEntries"
												:key="entry.name"
												:title="entry.name"
												:subtitle="entry.subtitle"
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

										<v-alert v-else type="info" variant="tonal" density="compact" class="mt-2">
											{{ __('No note counts found for this filter.') }}
										</v-alert>
									</v-card-text>
								</v-card>
							</v-col>

							<v-col v-show="!smAndDown || showDetailsOnMobile" cols="12" md="8" lg="9">
								<v-card class="close-day-panel h-100" rounded="xl" variant="flat" max-height="100vh">
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

									<v-card-text class="pt-3">
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
													<v-data-table-virtual
														v-if="selectedNoteEntry.type === 'Cash'"
														:headers="noteHeaders"
														:items="selectedNoteEntry.cash || []"
														item-value="note"
														density="compact"
														max-height="50vh"
														fixed-header
														class="close-day-table overflow-y-auto"
													/>

													<v-data-table-virtual
														v-else
														:headers="bankHeaders"
														:items="selectedNoteEntry.bank || []"
														item-value="reference_number"
														density="compact"
														height="36vh"
														fixed-header
														class="close-day-table overflow-y-auto"
													/>
												</v-card-text>
											</v-card>

											<div class="actions-wrap mt-4">
												<v-btn color="primary" variant="elevated" prepend-icon="mdi-printer" size="small" @click="print_note_count()">
													{{ __('Print') }}
												</v-btn>
												<v-btn color="error" variant="elevated" prepend-icon="mdi-cancel" size="small" @click="cancel_note_count()">
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
							<v-col v-show="!smAndDown || !showDetailsOnMobile" cols="12" md="4" lg="3">
								<v-card class="close-day-panel" rounded="xl" variant="flat" max-height="100vh">
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
											@click:clear="loadPaymentEntries()"
											@keydown.enter="loadPaymentEntries()"
										/>
									</v-card-item>

									<v-divider />

									<v-card-text class="pt-2 px-2">
										<div v-if="isLoadingPaymentList" class="px-2 py-5">
											<v-skeleton-loader type="list-item-two-line, list-item-two-line, list-item-two-line" />
										</div>

										<v-list
											v-else-if="paymentEntries.length"
											lines="two"
											color="primary"
											nav
											rounded="lg"
											class="close-day-list overflow-y-auto"
											density="compact"
											max-height="50vh"
										>
											<v-list-item
												v-for="entry in paymentEntries"
												:key="entry.name"
												:title="entry.name"
												:subtitle="entry.subtitle"
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

										<v-alert v-else type="info" variant="tonal" density="compact" class="mt-2">
											{{ __('No payment entries found for this filter.') }}
										</v-alert>
									</v-card-text>
								</v-card>
							</v-col>

							<v-col v-show="!smAndDown || showDetailsOnMobile" cols="12" md="8" lg="9">
								<v-card class="close-day-panel" rounded="xl" variant="flat" max-height="100vh">
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

									<v-card-text class="pt-3">
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
													<div class="meta-row"><strong>{{ __('POS Profile') }}:</strong> {{ selectedPaymentEntry.pos_profile || __('Not set') }}</div>
												</v-col>
												<v-col cols="12" md="6">
													<div class="meta-row"><strong>{{ __('From Account') }}:</strong> {{ selectedPaymentEntry.paid_from }}</div>
													<div class="meta-row"><strong>{{ __('To Account') }}:</strong> {{ selectedPaymentEntry.paid_to }}</div>
												</v-col>
											</v-row>

											<v-card class="section-card mt-3" rounded="lg" variant="outlined">
												<v-card-item class="pb-1">
													<div class="text-subtitle-1 font-weight-bold">{{ __('Transfer Details') }}</div>
												</v-card-item>
												<v-card-text>
													<v-data-table-virtual
														:headers="paymentHeaders"
														:items="selectedPaymentEntry.transfers || []"
														item-value="mode_of_payment"
														density="compact"
														max-height="50vh"
														fixed-header
														class="close-day-table overflow-y-auto"
													/>
												</v-card-text>
											</v-card>
										</template>
									</v-card-text>
								</v-card>
							</v-col>
						</v-row>
					</v-window-item>
				</v-window>
			</v-col>
		</v-row>

		<NoteCountDialog v-model="noteCountDialogOpen" @created="handleNoteCountCreated" :modeOfPayments="modeOfPayments" />
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
	const { smAndDown } = useDisplay();
    const posStore = usePosStore();
    const { posProfileData } = storeToRefs(posStore);
	const noteSearchTerm = ref('');
	const paymentSearchTerm = ref('');
	const showDetailsOnMobile = ref(false);
	const isLoadingNoteList = ref(false);
	const isLoadingNoteDetail = ref(false);
	const isLoadingPaymentList = ref(false);
	const isLoadingPaymentDetail = ref(false);
	const noteEntries = ref([]);
	const selectedNoteEntry = ref(null);
	const selectedNoteEntryName = ref('');
	const noteCountDialogOpen = ref(false);
	const paymentEntryDialogOpen = ref(false);
    const modeOfPayments = ref([]);
	const paymentEntries = ref([]);
	const selectedPaymentEntry = ref(null);
	const selectedPaymentEntryName = ref('');

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

	const paymentHeaders = [
		{ title: __('Mode of Payment'), key: 'mode_of_payment' },
		{ title: __('Amount'), key: 'amount' },
		{ title: __('Note Count'), key: 'note_count' },
		{ title: __('From Account'), key: 'paid_from' },
		{ title: __('To Account'), key: 'paid_to' },
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
		if (!value) {
			loadNoteCounts();
		}
	});
	watch(paymentSearchTerm, (value) => {
		if (!value) {
			loadPaymentEntries();
		}
	});
	onMounted(async () => {
		await loadNoteCounts();
        await loadModeOfPayments();
		await loadPaymentEntries();
	});

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

	function parsePaymentEntryRemarks(remarks) {
		const metadata = {};
		for (const part of String(remarks || '').split('|').slice(1)) {
			if (!part.includes(':')) {
				continue;
			}

			const [key, ...rest] = part.split(':');
			metadata[key.trim().toLowerCase().replace(/\s+/g, '_')] = rest.join(':').trim();
		}
		return metadata;
	}

	function normalizeMetadataValue(value) {
		return value && value !== '-' ? value : '';
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

		const metadata = parsePaymentEntryRemarks(entry.remarks);
		const modeOfPayment = entry.mode_of_payment || normalizeMetadataValue(metadata.mode_of_payment);
		const noteCount = normalizeMetadataValue(entry.reference_no || entry.note_count || metadata.note_count);
		const amount = getPaymentEntryAmount(entry);

		return {
			...entry,
			mode_of_payment: modeOfPayment,
			note_count: noteCount,
			amount,
			pos_profile: normalizeMetadataValue(entry.pos_profile || metadata.pos_profile),
			status: getDocstatusLabel(entry.docstatus),
			statusColor: getDocstatusColor(entry.docstatus),
			subtitle: [modeOfPayment, noteCount].filter(Boolean).join(' - '),
			transfers: [
				{
					mode_of_payment: modeOfPayment,
					amount,
					note_count: noteCount,
					paid_from: entry.paid_from,
					paid_to: entry.paid_to,
				},
			],
		};
	}

	function openNoteCountDialog() {
		noteCountDialogOpen.value = true;
	}

	function openPaymentEntryDialog() {
		paymentEntryDialogOpen.value = true;
	}

	async function loadNoteCounts() {
		isLoadingNoteList.value = true;
		try {
			const response = await frappe_.call({
				method: 'maxit_pos.maxit_pos.page.maxit_pos.api.close_day_vue.get_note_count_list',
				args: {
					search_term: noteSearchTerm.value || '',
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
		try {
			const response = await frappe.call({
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
		isLoadingPaymentList.value = true;
		try {
			const response = await frappe_.call({
				method: 'maxit_pos.maxit_pos.page.maxit_pos.api.close_day_vue.get_payment_entry_list',
				args: {
					search_term: paymentSearchTerm.value || '',
					cost_center: posProfileData.value?.cost_center || '',
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
			const response = await frappe.db.get_doc('Payment Entry', name);
			selectedPaymentEntry.value = mapPaymentEntry(response);
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
			const response = await frappe.db.get_doc('Note Count', name);
			selectedNoteEntry.value = mapNoteEntry(response);
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
			noteSearchTerm.value = '';
			await loadNoteCounts();
			if (createdDoc?.name) {
				await loadNoteDetail(createdDoc.name);
				showDetailsOnMobile.value = true;
			}
	}

	async function handlePaymentEntriesCreated(createdDocs) {
		paymentEntryDialogOpen.value = false;
		paymentSearchTerm.value = '';
		await loadPaymentEntries();
		const firstCreatedDoc = createdDocs?.[0];
		if (firstCreatedDoc?.name) {
			await loadPaymentEntryDetail(firstCreatedDoc.name);
			showDetailsOnMobile.value = true;
		}
	}

	function print_note_count(){
		const invoice = selectedNoteEntry.value?.name;
		const doctype = "Note Count";
		const printFormat = posProfileData.value?.note_count_print_format || 'Standard';
		const letterHead = posProfileData.value?.letter_head || 'No Letterhead';
		// const no_letterhead = letterHead === 'No Letterhead' ? 1 : 0;
		const no_letterhead = 1;
		const printUrl = `/printview?doctype=${doctype}&name=${invoice}&
format=${printFormat}&no_letterhead=${no_letterhead}&letterhead=${letterHead}&settings=%7B%7D&_lang=en&
pdf_generator=wkhtmltopdf&trigger_print=1`;
		window.open(printUrl, '_blank');
	}
	function cancel_note_count(){
		frappe_.call({
			method: 'maxit_pos.maxit_pos.page.maxit_pos.api.close_day_vue.cancel_note_count',
			args: { name: selectedNoteEntry.value?.name },
			callback: async (response) => {
				frappe_.msgprint(__('Note count cancelled successfully.'));
				await loadNoteCounts();
			},
		});
	}
</script>

<style scoped>
	.close-day-view {
		background:
			radial-gradient(circle at top right, rgba(25, 118, 210, 0.08), transparent 40%),
			radial-gradient(circle at left bottom, rgba(76, 175, 80, 0.07), transparent 35%);
	}

	.close-day-panel,
	.close-day-menu {
		border: 1px solid rgba(120, 144, 156, 0.24);
		background: linear-gradient(180deg, rgba(255, 255, 255, 0.95), rgba(248, 251, 255, 0.97));
		box-shadow: 0 8px 20px rgba(12, 28, 43, 0.08);
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
			padding: 10px;
		}

		.actions-wrap {
			display: grid;
			grid-template-columns: 1fr;
		}
	}
</style>
