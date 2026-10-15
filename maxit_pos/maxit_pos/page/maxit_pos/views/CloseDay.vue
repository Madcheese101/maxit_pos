<template>
	<PageSurface glow="info-success" class="close-day-view pa-3" v-if="closeDayEnabled">
		<div class="close-day-layout">
			<SurfaceCard v-show="!smAndDown || !showDetailsOnMobile" class="cd-pane cd-pane--list">
				<div class="cd-pane__body">
					<div class="pane-header">
						<v-btn-toggle
							v-if="noteCountEnabled"
							v-model="activeTab"
							mandatory
							divided
							density="compact"
							color="primary"
							variant="outlined"
							class="cd-tabs"
						>
							<v-btn value="note-count">{{ __('Note Count') }}</v-btn>
							<v-btn value="payment-entry">{{ __('Payment Entry') }}</v-btn>
						</v-btn-toggle>
						<div v-else class="pane-header__title">{{ __('Payment Entry') }}</div>
						<v-spacer v-if="!noteCountEnabled" />
						<v-btn
							color="primary"
							variant="elevated"
							prepend-icon="mdi-plus"
							:title="isNoteTab ? __('New Note Count') : __('New Payment Entry')"
							@click="isNoteTab ? openNoteCountDialog() : openPaymentEntryDialog()"
						>
							{{ __('New') }}
						</v-btn>
					</div>

					<div class="search-row">
						<v-text-field
							v-if="isNoteTab"
							v-model="noteSearchTerm"
							density="compact"
							:placeholder="__('Search note count')"
							prepend-inner-icon="mdi-magnify"
							variant="outlined"
							hide-details
							single-line
							clearable
							@keydown.enter="loadNoteCounts()"
						/>
						<v-text-field
							v-else
							v-model="paymentSearchTerm"
							density="compact"
							:placeholder="__('Search payment entry')"
							prepend-inner-icon="mdi-magnify"
							variant="outlined"
							hide-details
							single-line
							clearable
							@keydown.enter="loadPaymentEntries()"
						/>
						<v-btn
							icon="mdi-wallet-outline"
							size="small"
							variant="text"
							:title="__('Check Balance')"
							:aria-label="__('Check Balance')"
							@click="checkBalance"
						/>
						<v-btn
							v-if="!isNoteTab"
							icon="mdi-printer-outline"
							size="small"
							variant="text"
							:title="__('Print Report')"
							:aria-label="__('Print Report')"
							@click="openPaymentEntryPrintDialog"
						/>
						<v-btn
							icon="mdi-refresh"
							size="small"
							variant="text"
							:title="__('Refresh')"
							:aria-label="__('Refresh')"
							@click="isNoteTab ? loadNoteCounts() : loadPaymentEntries()"
						/>
					</div>

					<div class="cd-list">
						<v-skeleton-loader
							v-if="isNoteTab ? isLoadingNoteList : isLoadingPaymentList"
							type="list-item-two-line, list-item-two-line, list-item-two-line"
						/>

						<v-list
							v-else-if="listEntries.length"
							nav
							density="compact"
							bg-color="transparent"
							class="pa-0"
						>
							<v-list-item
								v-for="entry in listEntries"
								:key="entry.name"
								:active="(isNoteTab ? selectedNoteEntryName : selectedPaymentEntryName) === entry.name"
								color="primary"
								rounded="lg"
								class="cd-row"
								@click="isNoteTab ? selectNoteEntry(entry.name) : selectPaymentEntry(entry.name)"
							>
								<div class="cd-row__line">
									<span class="cd-row__title">{{ entry.mode_of_payment }}</span>
									<v-chip size="small" :color="entry.statusColor" variant="flat" class="status-chip">
										{{ entry.status }}
									</v-chip>
								</div>
								<div class="cd-row__line cd-row__line--sub">
									<span class="cd-row__meta">{{ formatDate(entry.posting_date) }} · {{ entry.name }}</span>
									<span class="cd-row__amount">{{ formatAmount(isNoteTab ? entry.total : entry.amount) }}</span>
								</div>
							</v-list-item>
						</v-list>

						<v-alert v-else type="info" variant="tonal" density="compact">
							{{ isNoteTab ? __('No note counts found for this filter.') : __('No payment entries found for this filter.') }}
						</v-alert>
					</div>
				</div>
			</SurfaceCard>

			<SurfaceCard v-show="!smAndDown || showDetailsOnMobile" class="cd-pane cd-pane--details">
				<div class="cd-pane__body">
					<div class="pane-header">
						<v-btn
							v-if="smAndDown"
							:icon="backIcon"
							variant="text"
							size="small"
							:aria-label="__('Back')"
							@click="showDetailsOnMobile = false"
						/>
						<div v-if="detailEntry" class="pane-header__info">
							<div class="pane-header__title">
								{{ detailEntry.name }}
								<v-chip size="small" :color="detailEntry.statusColor" variant="flat" class="status-chip">
									{{ detailEntry.status }}
								</v-chip>
							</div>
							<div class="pane-header__sub">
								{{ detailEntry.mode_of_payment }} · {{ formatDate(detailEntry.posting_date) }}
							</div>
						</div>
						<div v-else class="pane-header__title">
							{{ isNoteTab ? __('Note Count Details') : __('Payment Entry Details') }}
						</div>
					</div>

					<div class="details-scroll">
						<v-skeleton-loader
							v-if="isNoteTab ? isLoadingNoteDetail : isLoadingPaymentDetail"
							type="article, list-item-two-line, list-item-two-line"
						/>

						<v-alert v-else-if="!detailEntry" type="info" variant="tonal" density="compact">
							{{ isNoteTab
								? __('Select a note count from the left panel to view full details.')
								: __('Select a payment entry from the left panel to view full details.') }}
						</v-alert>

						<template v-else-if="isNoteTab">
							<div class="totals-strip">
								<div class="totals-strip__item">
									<span class="totals-strip__label">{{ __('Type') }}</span>
									<span class="totals-strip__value">{{ __(detailEntry.type) }}</span>
								</div>
								<div class="totals-strip__item">
									<span class="totals-strip__label">{{ __('Total') }}</span>
									<span class="totals-strip__value">{{ formatAmount(detailEntry.total) }}</span>
								</div>
							</div>

							<section class="details-section">
								<div class="details-section__title">
									{{ detailEntry.type === 'Cash' ? __('Cash Breakdown') : __('Bank Breakdown') }}
								</div>
								<template v-if="detailEntry.type === 'Cash'">
									<div v-for="row in detailEntry.cash || []" :key="row.note" class="detail-line">
										<div class="detail-line__main">
											<div class="detail-line__name">{{ row.note }} × {{ row.count }}</div>
										</div>
										<div class="detail-line__amount">{{ formatAmount(row.amount) }}</div>
									</div>
								</template>
								<template v-else>
									<div v-for="(row, index) in detailEntry.bank || []" :key="row.reference_number || index" class="detail-line">
										<div class="detail-line__main">
											<div class="detail-line__name">{{ row.reference_number }}</div>
											<div class="detail-line__sub">
												{{ [row.bank, row.bank_branch, row.account_number, row.mobile_no].filter(Boolean).join(' · ') }}
											</div>
										</div>
										<div class="detail-line__amount">{{ formatAmount(row.amount) }}</div>
									</div>
								</template>
							</section>
						</template>

						<template v-else>
							<div class="totals-strip">
								<div class="totals-strip__item">
									<span class="totals-strip__label">{{ __('Amount') }}</span>
									<span class="totals-strip__value">{{ formatAmount(detailEntry.amount) }}</span>
								</div>
								<div class="totals-strip__item">
									<span class="totals-strip__label">{{ __('Note Count') }}</span>
									<span class="totals-strip__value">{{ detailEntry.note_count || __('Not linked') }}</span>
								</div>
							</div>

							<section class="details-section">
								<div class="detail-line">
									<div class="detail-line__main">
										<div class="detail-line__sub">{{ __('From Account') }}</div>
										<div class="detail-line__name">{{ detailEntry.paid_from }}</div>
									</div>
								</div>
								<div class="detail-line">
									<div class="detail-line__main">
										<div class="detail-line__sub">{{ __('To Account') }}</div>
										<div class="detail-line__name">{{ detailEntry.paid_to }}</div>
									</div>
								</div>
							</section>
						</template>
					</div>

					<div v-if="detailEntry && !(isNoteTab ? isLoadingNoteDetail : isLoadingPaymentDetail)" class="details-actions">
						<template v-if="isNoteTab">
							<v-btn color="primary" variant="elevated" prepend-icon="mdi-printer" @click="print_note_count()">
								{{ __('Print') }}
							</v-btn>
							<v-btn
								color="error"
								variant="tonal"
								prepend-icon="mdi-cancel"
								:disabled="!canCancelSelectedNoteEntry"
								:loading="isCancellingNoteEntry"
								@click="cancel_note_count()"
							>
								{{ __('Cancel') }}
							</v-btn>
						</template>
						<v-btn
							v-else
							color="error"
							variant="tonal"
							prepend-icon="mdi-cancel"
							:disabled="!canCancelSelectedPaymentEntry"
							:loading="isCancellingPaymentEntry"
							@click="cancel_payment_entry()"
						>
							{{ __('Cancel Payment Entry') }}
						</v-btn>
					</div>
				</div>
			</SurfaceCard>
		</div>

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
	</PageSurface>
</template>

<script setup>
	import { onMounted, ref, watch, computed } from 'vue';
    import {storeToRefs} from 'pinia';
	import { useDisplay } from 'vuetify';
	import NoteCountDialog from './components/close_day/NoteCountDialog.vue';
	import PaymentEntryDialog from './components/close_day/PaymentEntryDialog.vue';
    import { usePosStore } from '../store/posStore';
	import PageSurface from './components/ui/PageSurface.vue';
	import SurfaceCard from './components/ui/SurfaceCard.vue';
	const __ = window.__;
	const frappe_ = window.frappe;
	const { smAndDown } = useDisplay();
    const posStore = usePosStore();
    const { posProfileData } = storeToRefs(posStore);
    const { isAppRTL } = posStore;
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
	const backIcon = computed(() => isAppRTL() ? 'mdi-arrow-right' : 'mdi-arrow-left');
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

	const closeDayEnabled = computed(() => {
	const roles = ['Accounts User', 'Accounts Manager', 'Administrator', 'System Manager'];
	return roles.some(role => frappe.user.has_role(role));
	});
	const noteCountEnabled = computed(() => {
	return Boolean(closeDayEnabled.value && posProfileData.value?.enable_note_count);
	});
	const activeTab = ref(noteCountEnabled.value ? 'note-count' : 'payment-entry');
	const isNoteTab = computed(() => activeTab.value === 'note-count');
	const listEntries = computed(() => isNoteTab.value ? noteEntries.value : paymentEntries.value);
	const detailEntry = computed(() => isNoteTab.value ? selectedNoteEntry.value : selectedPaymentEntry.value);
	
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
		return format_number(value || 0);
	}

	function formatDate(value) {
		return value ? frappe_.datetime.str_to_user(value) : '';
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
	async function checkBalance() {
		frappe.prompt({
			label: __('Select Date'),
			fieldname: 'date',
			fieldtype: 'Date',
			reqd: true,
		}, (values) => {
			frappe.call({
				method: 'maxit_pos.maxit_pos.page.maxit_pos.api.close_day_vue.get_current_balance_msg',
				args: {
					date: values.date,
					mode_of_payments: modeOfPayments.value || [],
				},
			});
		});
	}
</script>

<style scoped>
	.close-day-view {
		background:
			radial-gradient(circle at top right, var(--v-pos-info-glow), transparent 40%),
			radial-gradient(circle at left bottom, var(--v-pos-success-glow), transparent 35%);
	}

	.close-day-layout {
		display: flex;
		gap: var(--maxit-gap);
		flex: 1;
		min-height: 0;
	}

	.cd-pane {
		display: flex;
		flex-direction: column;
		min-height: 0;
		border: 1px solid var(--v-pos-panel-border);
		background: var(--v-pos-panel-background);
		box-shadow: var(--v-pos-panel-shadow);
		transition: var(--v-theme-transition);
	}

	.cd-pane--list {
		flex: 0 0 clamp(340px, 38%, 480px);
	}

	.cd-pane--details {
		flex: 1;
		min-width: 0;
	}

	@media (max-width: 959px) {
		.cd-pane--list {
			flex: 1;
		}
	}

	.cd-pane__body {
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

	.pane-header__info {
		min-width: 0;
	}

	.pane-header__title {
		display: flex;
		align-items: center;
		flex-wrap: wrap;
		gap: 6px;
		font-size: 1rem;
		font-weight: 700;
		padding-inline: 4px;
	}

	.pane-header__sub {
		font-size: 0.8125rem;
		padding-inline: 4px;
		color: rgba(var(--v-theme-on-surface), 0.72);
		white-space: nowrap;
		overflow: hidden;
		text-overflow: ellipsis;
	}

	.cd-tabs {
		flex: 1;
		min-width: 0;
	}

	.cd-tabs .v-btn {
		flex: 1;
		font-weight: 700;
	}

	.search-row {
		display: flex;
		align-items: center;
		gap: var(--maxit-gap-xs);
	}

	.search-row .v-text-field {
		flex: 1;
		margin-inline-end: 4px;
	}

	.cd-list {
		flex: 1;
		min-height: 0;
		overflow-y: auto;
	}

	.cd-row {
		margin-block-end: var(--maxit-gap-xs);
		border: 1px solid var(--v-pos-panel-border-soft);
	}

	.cd-row :deep(.v-list-item__content) {
		display: flex;
		flex-direction: column;
		gap: 2px;
	}

	.cd-row__line {
		display: flex;
		align-items: center;
		justify-content: space-between;
		gap: 8px;
	}

	.cd-row__title {
		min-width: 0;
		font-size: 0.875rem;
		font-weight: 700;
		white-space: nowrap;
		overflow: hidden;
		text-overflow: ellipsis;
	}

	.cd-row__line--sub {
		font-size: 0.8125rem;
	}

	.cd-row__meta {
		min-width: 0;
		color: rgba(var(--v-theme-on-surface), 0.72);
		white-space: nowrap;
		overflow: hidden;
		text-overflow: ellipsis;
	}

	.cd-row__amount {
		flex-shrink: 0;
		font-weight: 700;
	}

	.status-chip {
		flex-shrink: 0;
		font-weight: 700;
	}

	.details-scroll {
		display: flex;
		flex-direction: column;
		gap: 12px;
		flex: 1;
		min-height: 0;
		overflow-y: auto;
	}

	.totals-strip {
		display: grid;
		grid-template-columns: repeat(2, minmax(0, 1fr));
		border: 1px solid var(--v-pos-panel-border-soft);
		border-radius: 10px;
		background: var(--v-pos-field-background);
	}

	.totals-strip__item {
		display: flex;
		flex-direction: column;
		gap: 2px;
		min-width: 0;
		padding: 8px;
	}

	.totals-strip__item + .totals-strip__item {
		border-inline-start: 1px solid var(--v-pos-panel-border-soft);
	}

	.totals-strip__label {
		font-size: 0.75rem;
		color: rgb(var(--v-pos-text-muted));
	}

	.totals-strip__value {
		font-size: 0.9375rem;
		font-weight: 700;
		overflow-wrap: anywhere;
	}

	.details-section {
		display: flex;
		flex-direction: column;
		gap: var(--maxit-gap-xs);
	}

	.details-section__title {
		font-size: 0.875rem;
		font-weight: 700;
	}

	.detail-line {
		display: flex;
		align-items: center;
		gap: 8px;
		padding: 8px 10px;
		border: 1px solid var(--v-pos-panel-border-soft);
		border-radius: 8px;
		background: var(--v-pos-field-background);
	}

	.detail-line__main {
		flex: 1;
		min-width: 0;
	}

	.detail-line__name {
		font-size: 0.875rem;
		font-weight: 600;
		line-height: 1.35;
		overflow-wrap: anywhere;
	}

	.detail-line__sub {
		font-size: 0.8125rem;
		font-weight: 500;
		color: rgba(var(--v-theme-on-surface), 0.72);
	}

	.detail-line__amount {
		flex-shrink: 0;
		font-size: 0.875rem;
		font-weight: 700;
	}

	.details-actions {
		display: flex;
		flex-wrap: wrap;
		gap: var(--maxit-gap-sm);
		padding-block-start: var(--maxit-gap);
		border-top: 1px solid var(--v-pos-panel-border-soft);
	}

	.details-actions .v-btn {
		flex: 1 1 auto;
	}
</style>
