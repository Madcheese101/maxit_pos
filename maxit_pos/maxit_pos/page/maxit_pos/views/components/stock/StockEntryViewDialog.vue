<template>
	<v-dialog
		:model-value="modelValue"
		max-width="680"
		:fullscreen="xs"
		scrollable
		@update:model-value="emit('update:modelValue', $event)"
	>
		<v-card class="stock-entry-dialog" :rounded="xs ? 0 : 'xl'">
			<v-card-item class="pb-2">
				<div class="d-flex align-center flex-wrap ga-2">
					<div class="text-h6 font-weight-bold">{{ doc?.name || __('View Transfer') }}</div>
					<v-chip v-if="doc" size="small" :color="statusChip.color" variant="flat" class="font-weight-bold">
						{{ statusChip.label }}
					</v-chip>
				</div>
				<div v-if="doc" class="dialog-subtitle">
					{{ formatDate(doc.posting_date) }} · {{ doc.from_branch || __('N/A') }}
					<v-icon :icon="isAppRTL() ? 'mdi-arrow-left' : 'mdi-arrow-right'" size="14" />
					{{ doc.to_branch || __('N/A') }}
				</div>
			</v-card-item>

			<v-divider />

			<v-card-text class="dialog-body">
				<v-skeleton-loader v-if="isLoading" type="article, list-item-two-line, list-item-two-line" />

				<v-alert v-else-if="!doc" type="info" variant="tonal" density="compact">
					{{ __('Select a transfer to view its details.') }}
				</v-alert>

				<template v-else>
					<div class="meta-grid">
						<div class="meta-item">
							<span class="meta-item__label">{{ __('Transfer Type') }}</span>
							<span class="meta-item__value">{{ Number(doc.add_to_transit) === 1 ? __('In Transit') : __('Received') }}</span>
						</div>
						<div class="meta-item">
							<span class="meta-item__label">{{ __('Transferred %') }}</span>
							<span class="meta-item__value">{{ Number(doc.per_transferred || 0).toFixed(2) }}</span>
						</div>
						<div class="meta-item">
							<span class="meta-item__label">{{ __('From Warehouse') }}</span>
							<span class="meta-item__value">{{ doc.from_warehouse || __('N/A') }}</span>
						</div>
						<div class="meta-item">
							<span class="meta-item__label">{{ __('To Warehouse') }}</span>
							<span class="meta-item__value">{{ doc.to_warehouse || __('N/A') }}</span>
						</div>
					</div>

					<section class="entry-lines">
						<div class="entry-lines__title">
							{{ __('Items') }}
							<span class="text-medium-emphasis">({{ (doc.items || []).length }})</span>
						</div>
						<div v-for="item in doc.items || []" :key="item.name" class="entry-line">
							<div class="entry-line__main">
								<div class="entry-line__name">{{ item.idx }}. {{ item.item_name }}</div>
								<div class="entry-line__sub">{{ item.item_code }}</div>
							</div>
							<div class="entry-line__qty">{{ item.qty }} <span class="entry-line__uom">{{ item.uom }}</span></div>
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
					v-if="canReceive"
					color="success"
					variant="elevated"
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
		sourceTab: {
			type: String,
			default: 'outgoing',
		},
	});

	const emit = defineEmits(['update:modelValue', 'updated']);

	const __ = window.__;
	const frappe_ = window.frappe;
	const { buildPrintViewUrl, isAppRTL } = usePosStore();
	const { xs } = useDisplay();
	const doc = ref(null);
	const isLoading = ref(false);
	const isSubmitting = ref(false);

	function formatDate(value) {
		return value ? frappe_.datetime.str_to_user(value) : '';
	}

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
		gap: 12px;
	}

	.meta-grid {
		display: grid;
		grid-template-columns: repeat(auto-fill, minmax(180px, 1fr));
		gap: 8px 16px;
		padding: 10px 12px;
		border-radius: 10px;
		background: rgba(var(--v-theme-primary), 0.06);
	}

	.meta-item {
		display: flex;
		flex-direction: column;
		min-width: 0;
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

	.entry-lines {
		display: flex;
		flex-direction: column;
		gap: 4px;
	}

	.entry-lines__title {
		font-size: 0.875rem;
		font-weight: 700;
	}

	.entry-line {
		display: flex;
		align-items: center;
		gap: 8px;
		padding: 6px 8px;
		border: 1px solid var(--v-pos-panel-border-soft);
		border-radius: 8px;
		background: var(--v-pos-field-background);
	}

	.entry-line__main {
		flex: 1;
		min-width: 0;
	}

	.entry-line__name {
		font-size: 0.875rem;
		font-weight: 600;
	}

	.entry-line__sub {
		font-size: 0.8125rem;
		font-weight: 500;
		color: rgba(var(--v-theme-on-surface), 0.72);
	}

	.entry-line__qty {
		flex-shrink: 0;
		font-size: 0.9375rem;
		font-weight: 700;
	}

	.entry-line__uom {
		font-size: 0.75rem;
		font-weight: 500;
		color: rgba(var(--v-theme-on-surface), 0.65);
	}
</style>
