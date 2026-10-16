<template>
  <PageSurface glow="info-warning" class="purchase-view pa-3" v-if="purchaseEnabled">
    <PurchaseReturnForm
      v-if="showReturnForm"
      @cancel="showReturnForm = false"
      @created="onReturnCreated"
    />

    <div v-else class="purchase-layout">
      <SurfaceCard v-show="!isMobile || !showDetailsOnMobile" class="purchase-pane purchase-pane--list">
        <div class="purchase-pane__body">
          <div class="pane-header">
            <div class="pane-header__title">{{ __('Purchase') }}</div>
            <v-chip size="x-small" color="primary" variant="tonal">{{ invoices.length }}</v-chip>
            <v-spacer />
            <v-btn
              icon="mdi-sync"
              size="small"
              variant="text"
              :title="__('Sync')"
              :aria-label="__('Sync')"
              @click="onSyncAction"
            />
            <v-btn
              color="primary"
              variant="tonal"
              prepend-icon="mdi-file-undo-outline"
              @click="showReturnForm = true"
            >
              {{ __('Return') }}
            </v-btn>
          </div>

          <v-text-field
            v-model="searchTerm"
            density="compact"
            :placeholder="__('Search invoice, supplier invoice')"
            prepend-inner-icon="mdi-magnify"
            variant="outlined"
            hide-details
            single-line
            class="flex-grow-0"
            @keydown.enter="getInvoices()"
          />

          <div class="purchase-list">
            <v-skeleton-loader
              v-if="isLoadingList"
              type="list-item-two-line, list-item-two-line, list-item-two-line"
            />

            <v-list
              v-else-if="invoices.length"
              nav
              density="compact"
              bg-color="transparent"
              class="pa-0"
            >
              <v-list-item
                v-for="inv in invoices"
                :key="inv.name"
                :active="invoice?.name === inv.name"
                color="primary"
                rounded="lg"
                class="purchase-row"
                @click="openInvoice(inv.name)"
              >
                <div class="purchase-row__line">
                  <span class="purchase-row__name">{{ inv.name }}</span>
                  <v-chip size="small" :color="getStatusColor(inv.status, inv.docstatus)" variant="flat" class="status-chip">
                    {{ __(inv.status || 'Draft') }}
                  </v-chip>
                </div>
                <div class="purchase-row__meta">
                  {{ inv.supplier_branch || __('Unknown Supplier') }} · {{ inv.bill_no || __('Unknown Bill') }}<template v-if="inv.posting_date"> · {{ formatDate(inv.posting_date) }}</template>
                </div>
              </v-list-item>
            </v-list>

            <v-alert v-else type="info" variant="tonal" density="compact">
              {{ __('No invoices found for this filter.') }}
            </v-alert>
          </div>
        </div>
      </SurfaceCard>

      <SurfaceCard v-show="!isMobile || showDetailsOnMobile" class="purchase-pane purchase-pane--details">
        <div class="purchase-pane__body">
          <div class="pane-header">
            <v-btn
              v-if="isMobile"
              :icon="backIcon"
              variant="text"
              size="small"
              :aria-label="__('Back')"
              @click="showDetailsOnMobile = false"
            />
            <div v-if="invoice" class="pane-header__info">
              <div class="pane-header__title">
                {{ invoice.name }}
                <v-chip size="small" :color="statusChip.color" variant="flat" class="status-chip">
                  {{ __(invoice.status) }}
                </v-chip>
              </div>
              <div class="pane-header__sub">
                {{ invoice.supplier_branch || 'N/A' }} · {{ formatDate(invoice.posting_date) }}
              </div>
            </div>
            <div v-else class="pane-header__title">{{ __('Invoice Details') }}</div>
          </div>

          <div class="details-scroll">
            <v-skeleton-loader
              v-if="isLoadingInvoice"
              type="article, list-item-two-line, list-item-two-line"
            />

            <v-alert v-else-if="!invoice" type="info" variant="tonal" density="compact">
              {{ __('Select an invoice from the left panel to view full details.') }}
            </v-alert>

            <template v-else>
              <div class="info-strip">
                <div class="info-strip__item">
                  <span class="info-strip__label">{{ __('Supplier Branch') }}</span>
                  <span class="info-strip__value">{{ invoice.supplier_branch || 'N/A' }}</span>
                </div>
                <div class="info-strip__item">
                  <span class="info-strip__label">{{ __('Supplier Invoice') }}</span>
                  <span class="info-strip__value">{{ invoice.bill_no || 'N/A' }}</span>
                </div>
                <div class="info-strip__item">
                  <span class="info-strip__label">{{ __('Supplier Invoice Date') }}</span>
                  <span class="info-strip__value">{{ formatDate(invoice.bill_date || invoice.posting_date) || 'N/A' }}</span>
                </div>
              </div>

              <section v-if="invoice.items?.length" class="details-section">
                <div class="details-section__title">
                  {{ __('Items') }}
                  <span class="text-medium-emphasis">({{ invoice.items.length }})</span>
                </div>
                <div v-for="item in invoice.items" :key="item.name" class="detail-line">
                  <div class="detail-line__main">
                    <div class="detail-line__name">{{ item.idx }}. {{ item.item_name }}</div>
                    <div class="detail-line__sub">{{ item.item_code }}</div>
                  </div>
                  <div class="detail-line__qty">{{ item.qty }} <span class="detail-line__uom">{{ item.uom }}</span></div>
                </div>
              </section>
            </template>
          </div>

          <div
            v-if="invoice && !isLoadingInvoice && (invoice.docstatus !== 0 || frappe_.user.has_role('Purchase Manager'))"
            class="details-actions"
          >
            <v-btn
              v-if="invoice.docstatus !== 0"
              color="primary"
              variant="elevated"
              prepend-icon="mdi-printer"
              @click="printInvoice()"
            >
              {{ __('Print') }}
            </v-btn>
            <v-btn
              v-if="invoice.docstatus == 1 && frappe_.user.has_role('Purchase Manager')"
              color="error"
              variant="tonal"
              prepend-icon="mdi-cancel"
              @click="cancelInvoice()"
            >
              {{ __('Cancel') }}
            </v-btn>
          </div>
        </div>
      </SurfaceCard>
    </div>
  </PageSurface>
</template>

<script setup>
  import {storeToRefs} from 'pinia';
  import { useDisplay } from 'vuetify';
  import { ref, computed } from "vue";
  import { usePosStore } from '../store/posStore';
  import PageSurface from './components/ui/PageSurface.vue';
  import SurfaceCard from './components/ui/SurfaceCard.vue';
  import PurchaseReturnForm from './components/purchase/PurchaseReturnForm.vue';

  const __ = window.__;
  const frappe_ = window.frappe;
  const invoices = ref([]);
  const invoice = ref();

  const searchTerm = ref('');
  const isLoadingInvoice = ref(false);
  const { smAndDown } = useDisplay();
  const isMobile = computed(() => smAndDown.value);
  const showDetailsOnMobile = ref(false);
  const showReturnForm = ref(false);
  const isLoadingList = ref(false);
  const syncJobId = ref(null);
  let isSyncRealtimeBound = false;
  const posStore = usePosStore();
  const {pos_profile, posProfileData} = storeToRefs(posStore);
  const { buildPrintViewUrl, isAppRTL } = posStore;
  const backIcon = computed(() => isAppRTL() ? 'mdi-arrow-right' : 'mdi-arrow-left');

  const syncRealtimeHandler = (data) => {
    if (!data || !syncJobId.value || data.job_id !== syncJobId.value) return;

    syncJobId.value = null;
    searchTerm.value = '';

    if (data.status === 'success') {
      getInvoices();
      frappe.msgprint({
        title: __('Sync Completed'),
        indicator: 'green',
        message: __('Invoices Synced: {0}', [data.synced_count || 0]),
      });
      return;
    }

    frappe.msgprint({
      title: __('Sync Failed'),
      indicator: 'red',
      message: data.message || __('Purchase invoice sync failed.'),
    });
  };

  frappe.realtime.on('maxit_pos_purchase_sync_done', function(data) {syncRealtimeHandler(data)});
  
  const getStatusColor = (status, docstatus) => {
    const normalizedStatus = (status || '').toLowerCase();

    if (normalizedStatus == 'unpaid' || normalizedStatus == 'overdue') return 'error';
    if (normalizedStatus == 'paid' || normalizedStatus == 'completed') return 'success';
    if (normalizedStatus == 'partly paid') return 'warning';
    if (normalizedStatus == 'return') return 'amber-darken-1';
    if (normalizedStatus == 'cancel') return 'error';
    if (docstatus === 0) return 'info';
    return 'secondary';
  };

  const statusChip = computed(() => ({
    color: getStatusColor(invoice.value?.status, invoice.value?.docstatus)
  }));

  const formatDate = (value) => value ? frappe_.datetime.str_to_user(value) : '';
  const purchaseEnabled = computed(() => {
      const roles = ['Purchase User', 'Purchase Manager', 'Administrator', 'System Manager'];
      return roles.some(role => frappe.user.has_role(role)) && posProfileData.value?.allow_purchase;
  });

  const sync = () => {
    frappe.show_alert({
        message: __('Syncing Invoices...'),
        indicator: 'blue'
      }, 5);
    isLoadingList.value = true;
    invoice.value = null;
    frappe.call({
      method: "maxit_pos.maxit_pos.page.maxit_pos.api.purchase_vue.sync_invoices",
      args: {
        pos_profile: posProfileData.value
      },
    }).then((response) => {
      const payload = response.message || {};
      isLoadingList.value = false;

      if (payload.status === 'queued' && payload.job_id) {
        syncJobId.value = payload.job_id;
        frappe.show_alert({
          message: payload.message || __('Sync started in background'),
          indicator: 'blue'
        }, 5);
        return;
      }

      frappe.show_alert({
        message: __('Unable to queue sync job'),
        indicator: 'red'
      }, 5);
    }).catch(() => {
      isLoadingList.value = false;
      frappe.show_alert({
        message: __('Sync Failed'),
        indicator: 'red'
      }, 5);
    });
  };

  const onSyncAction = () => {
    frappe.confirm(__('This sync invoices from the parent ERPNext site. Do you want to continue?'),
      () => {
          // action to perform if Yes is selected
          sync();
      }, () => {
          // action to perform if No is selected
      });
    
  };

  const onReturnCreated = () => {
    showReturnForm.value = false;
    searchTerm.value = '';
    getInvoices();
  };

  const cancelInvoice = async () => {
    frappe.confirm(__('Are you sure you want to cancel this invoice?'),
      () => {
          // action to perform if Yes is selected
          frappe.call("maxit_pos.maxit_pos.page.maxit_pos.api.api.cancel_invoice", {
            name: invoice.value.name
          }).then((res) => {
            invoice.value = res.message;
            frappe.show_alert({
              message:__('Invoice Cancelled'),
              indicator:'green'
            }, 5);
          });

      }, () => {
          // action to perform if No is selected
      });
  };
  
  const GetInvoiceDoc = async (invoice_id) => {
    isLoadingInvoice.value = true;
    const purchaseDoctype = posProfileData.value?.purchase_doctype || 'Purchase Receipt';
    frappe.db.get_doc(purchaseDoctype, invoice_id).then((doc) => {
        invoice.value = doc;
        isLoadingInvoice.value = false;
    }).catch(() => {
      isLoadingInvoice.value = false;
    });
  };

  const printInvoice = () => {
    const doctype = posProfileData.value?.purchase_doctype || 'Purchase Receipt';
    const printFormat = posProfileData.value?.purchase_receipt_print_format || 'Standard';
    const printUrl = buildPrintViewUrl({
      doctype,
      name: invoice.value.name,
      format: printFormat,
      no_letterhead: 1,
      letterhead: 'No Letterhead',
    });
    window.open(printUrl, '_blank');
  };

  const openInvoice = (invoice_id) => {
    showDetailsOnMobile.value = true;
    if (invoice.value?.name !== invoice_id) GetInvoiceDoc(invoice_id);
  };

  const getInvoices = () => {
    if (!purchaseEnabled.value) return;
    isLoadingList.value = true;
    frappe.call({
      method: "maxit_pos.maxit_pos.page.maxit_pos.api.purchase_vue.get_purchase_receipt_list",
      freeze: true,
      args: { 
        pos_profile: posProfileData.value,
        search_term: searchTerm.value || '',
      },
    }).then((response) => {
      invoices.value = response.message || [];
      invoice.value = null;
      isLoadingList.value = false;
    }).catch(() => {
      isLoadingList.value = false;
    });
  };

  getInvoices();
</script>

<style scoped>
.purchase-view {
  background:
    radial-gradient(circle at top right, var(--v-pos-info-glow), transparent 42%),
    radial-gradient(circle at left bottom, var(--v-pos-warning-glow), transparent 38%);
}

.purchase-layout {
  display: flex;
  gap: var(--maxit-gap);
  flex: 1;
  min-height: 0;
}

.purchase-pane {
  display: flex;
  flex-direction: column;
  min-height: 0;
  border: 1px solid var(--v-pos-panel-border);
  background: var(--v-pos-panel-background);
  box-shadow: var(--v-pos-panel-shadow);
  transition: var(--v-theme-transition);
}

.purchase-pane--list {
  flex: 0 0 clamp(340px, 38%, 480px);
}

.purchase-pane--details {
  flex: 1;
  min-width: 0;
}

@media (max-width: 959px) {
  .purchase-pane--list {
    flex: 1;
  }
}

.purchase-pane__body {
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

.purchase-list {
  flex: 1;
  min-height: 0;
  overflow-y: auto;
}

.purchase-row {
  margin-block-end: var(--maxit-gap-xs);
  border: 1px solid var(--v-pos-panel-border-soft);
}

.purchase-row :deep(.v-list-item__content) {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.purchase-row__line {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
}

.purchase-row__name {
  font-size: 0.875rem;
  font-weight: 700;
}

.purchase-row__meta {
  font-size: 0.8125rem;
  font-weight: 500;
  color: rgba(var(--v-theme-on-surface), 0.72);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.status-chip {
  flex-shrink: 0;
  font-weight: 700;
}

/* yellow needs dark text to stay readable */
.status-chip.bg-amber-darken-1 {
  color: rgba(0, 0, 0, 0.87) !important;
}

.details-scroll {
  display: flex;
  flex-direction: column;
  gap: var(--maxit-gap);
  flex: 1;
  min-height: 0;
  overflow-y: auto;
}

.info-strip {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(140px, 1fr));
  border: 1px solid var(--v-pos-panel-border-soft);
  border-radius: 10px;
  background: var(--v-pos-field-background);
}

.info-strip__item {
  display: flex;
  flex-direction: column;
  gap: 2px;
  min-width: 0;
  padding: 8px 10px;
}

.info-strip__label {
  font-size: 0.75rem;
  color: rgb(var(--v-pos-text-muted));
}

.info-strip__value {
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
}

.detail-line__sub {
  font-size: 0.8125rem;
  font-weight: 500;
  color: rgba(var(--v-theme-on-surface), 0.72);
}

.detail-line__qty {
  flex-shrink: 0;
  font-size: 0.9375rem;
  font-weight: 700;
}

.detail-line__uom {
  font-size: 0.75rem;
  font-weight: 500;
  color: rgba(var(--v-theme-on-surface), 0.65);
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
