<template>
	<v-dialog :model-value="modelValue" max-width="1100" @update:model-value="emit('update:modelValue', $event)">
		<v-card class="stock-entry-dialog" rounded="xl">
			<v-card-item class="pb-2">
				<div class="d-flex align-center justify-space-between gap-2 flex-wrap">
					<div>
						<div class="text-overline text-medium-emphasis">{{ __('Stock Entry') }}</div>
						<div class="text-h6 font-weight-bold">{{ doc?.name || __('View Transfer') }}</div>
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
					{{ __('Select a transfer to view its details.') }}
				</v-alert>

				<template v-else>
					<v-row dense class="mb-2">
						<v-col cols="12" sm="6" md="3">
							<StatMetricCard
								class="stat-card"
								color="primary"
								:label="__('Posting Date')"
								:value="doc.posting_date || __('N/A')"
							/>
						</v-col>

						<v-col cols="12" sm="6" md="3">
							<StatMetricCard
								class="stat-card"
								color="success"
								:label="__('From Branch')"
								:value="doc.from_branch || __('N/A')"
							/>
						</v-col>

						<v-col cols="12" sm="6" md="3">
							<StatMetricCard
								class="stat-card"
								color="warning"
								:label="__('To Branch')"
								:value="doc.to_branch || __('N/A')"
							/>
						</v-col>

						<v-col cols="12" sm="6" md="3">
							<StatMetricCard
								class="stat-card"
								color="info"
								:label="__('Transfer Type')"
								:value="Number(doc.add_to_transit) === 1 ? __('In Transit') : __('Received')"
							/>
						</v-col>
					</v-row>

					<v-row dense class="mb-3">
						<v-col cols="12" md="6">
							<div class="meta-row"><strong>{{ __('From Warehouse') }}:</strong> {{ doc.from_warehouse || __('N/A') }}</div>
							<div class="meta-row"><strong>{{ __('To Warehouse') }}:</strong> {{ doc.to_warehouse || __('N/A') }}</div>
						</v-col>
						<v-col cols="12" md="6">
							<div class="meta-row"><strong>{{ __('Transferred %') }}:</strong> {{ Number(doc.per_transferred || 0).toFixed(2) }}</div>
							<div class="meta-row"><strong>{{ __('Docstatus') }}:</strong> {{ docstatusLabel }}</div>
						</v-col>
					</v-row>

					<SurfaceCard surface="section" class="section-card">
						<v-card-item class="pb-1">
							<div class="text-subtitle-1 font-weight-bold">{{ __('Items') }}</div>
						</v-card-item>
						<v-card-text>
							<div class="items-table-wrap">
								<v-data-table-virtual
									:headers="itemHeaders"
									:items="doc.items || []"
									item-value="name"
									density="compact"
									height="260"
									fixed-header
									class="stock-entry-items-table"
								/>
							</div>
						</v-card-text>
					</SurfaceCard>
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
					v-if="canReceive"
					color="success"
					variant="tonal"
					prepend-icon="mdi-truck-check-outline"
					:loading="isSubmitting"
					@click="receiveTransfer"
				>
					{{ __('Receive') }}
				</v-btn>
				<v-btn
					v-if="canCancel"
					color="error"
					variant="tonal"
					prepend-icon="mdi-cancel"
					:loading="isSubmitting"
					@click="cancelTransfer"
				>
					{{ __('Cancel') }}
				</v-btn>
			</v-card-actions>
		</v-card>
	</v-dialog>
</template>

<script setup>
	import { computed, ref, watch } from 'vue';
	import { usePosStore } from '../../../store/posStore';
	import SurfaceCard from '../ui/SurfaceCard.vue';
	import StatMetricCard from '../ui/StatMetricCard.vue';
	
	const props = defineProps({
		modelValue: {
			type: Boolean,
			default: false,
		},
		docname: {
			type: String,
			default: '',
		},
		sourceTab: {
			type: String,
			default: 'outgoing',
		},
	});

	const emit = defineEmits(['update:modelValue', 'updated']);

	const __ = window.__;
	const frappe_ = window.frappe;
	const { buildPrintViewUrl } = usePosStore();
	const doc = ref(null);
	const isLoading = ref(false);
	const isSubmitting = ref(false);

	const itemHeaders = computed(() => [
		{ title: __('No.'), key: 'idx', width: '70px' },
		{ title: __('Item Code'), key: 'item_code' },
		{ title: __('Item Name'), key: 'item_name' },
		{ title: __('Qty'), key: 'qty' },
	]);

	const docstatusLabel = computed(() => {
		switch (Number(doc.value?.docstatus || 0)) {
			case 1:
				return __('Submitted');
			case 2:
				return __('Cancelled');
			default:
				return __('Draft');
		}
	});

	const statusChip = computed(() => {
		if (Number(doc.value?.docstatus || 0) === 2) {
			return { label: __('Cancelled'), color: 'error' };
		}

		if (Number(doc.value?.per_transferred || 0) > 0 || Number(doc.value?.add_to_transit || 0) === 0) {
			return { label: __('Received'), color: 'success' };
		}

		if (Number(doc.value?.add_to_transit || 0) === 1 && !doc.value?.outgoing_stock_entry) {
			return { label: __('In Transit'), color: 'warning' };
		}

		return { label: __('Submitted'), color: 'info' };
	});

	const canCancel = computed(() => {
		const isSubmitted = Number(doc.value?.docstatus || 0) === 1;
		const isInTransit = Number(doc.value?.add_to_transit || 0) === 1;
		const isTransferred = Number(doc.value?.per_transferred || 0) > 0;
		const isSourceBranch = doc.value?.from_branch === frappe.boot.user_branch;
		const isDestBranch = doc.value?.to_branch === frappe.boot.user_branch;
		const hasBranchPermission = isInTransit ? isSourceBranch : (isSourceBranch || isDestBranch);
		return isSubmitted && !(isInTransit && isTransferred) && hasBranchPermission;
	});
	const canReceive = computed(() => {
		return props.sourceTab === 'incoming'
			&& Number(doc.value?.docstatus || 0) === 1
			&& Number(doc.value?.add_to_transit || 0) === 1
			&& !doc.value?.outgoing_stock_entry;
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

	async function loadDoc() {
		isLoading.value = true;
		try {
			doc.value = await frappe.db.get_doc('Stock Entry', props.docname);
		} catch (error) {
			frappe_.msgprint({
				title: __('Stock Entry fetch failed'),
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
			doctype: 'Stock Entry',
			name: doc.value.name,
			format: 'Standard',
			no_letterhead: 1,
			letterhead: 'No Letterhead',
		});
		window.open(printUrl, '_blank');
	}

	function cancelTransfer() {
		if (doc.value?.add_to_transit && doc.value?.from_branch !== frappe.boot.user_branch) {
			frappe_.alert(__('Only the branch which initiated the transfer can cancel it.'), { indicator: 'red' });
			return;
		}
		frappe_.confirm(
			__('Are you sure you want to cancel this stock entry?'),
			async () => {
				isSubmitting.value = true;
				try {
					await frappe.call({
						method: 'maxit_pos.maxit_pos.page.maxit_pos.api.stock_entry_vue.cancel_transfer_stock_entry',
						args: {
							docname: props.docname,
						},
					});

					frappe_.show_alert({ message: __('Stock Entry cancelled successfully.'), indicator: 'green' }, 5);
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

	function receiveTransfer() {
		frappe_.confirm(
			__('Are you sure you want to receive this transfer?'),
			async () => {
				isSubmitting.value = true;
				try {
					await frappe.call({
						method: 'maxit_pos.maxit_pos.page.maxit_pos.api.stock_entry_vue.make_stock_in_entry',
						args: {
							source_name: props.docname,
						},
					});

					frappe_.show_alert({ message: __('Transfer received successfully.'), indicator: 'green' }, 5);
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
	.stock-entry-dialog {
		border: 1px solid var(--v-pos-panel-border);
		background: var(--v-pos-panel-background);
		box-shadow: var(--v-pos-panel-shadow);
		transition: var(--v-theme-transition);
	}

	.dialog-body {
		max-height: 70vh;
		overflow-y: auto;
	}

	.stat-card {
		border: 1px solid var(--v-pos-panel-border-soft);
		transition: var(--v-theme-transition);
	}

	.section-card {
		border-color: var(--v-pos-panel-border-strong) !important;
	}

	.meta-row {
		padding: 4px 0;
	}

	.items-table-wrap {
		min-height: 170px;
	}

	.stock-entry-items-table :deep(.v-table__wrapper) {
		overflow-y: auto;
	}
</style>