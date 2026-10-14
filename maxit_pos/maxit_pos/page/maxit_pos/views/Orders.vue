<template>
  <PageSurface glow="info-success" class="orders-view pa-2">
    <div class="orders-layout">
      <SurfaceCard v-show="!isMobile || !showDetailsOnMobile" class="orders-pane orders-pane--list">
        <div class="orders-pane__body">
          <div class="pane-header">
            <div class="pane-header__title">{{ __('Orders') }}</div>
            <v-chip size="x-small" color="primary" variant="tonal">{{ invoices.length }}</v-chip>
            <v-spacer />
            <v-btn
              icon="mdi-refresh"
              size="small"
              variant="text"
              :title="__('Refresh')"
              :aria-label="__('Refresh')"
              @click="getInvoices()"
            />
          </div>

          <v-text-field
            v-model="searchTerm"
            density="compact"
            :placeholder="__('Search invoice, customer, mobile')"
            prepend-inner-icon="mdi-magnify"
            variant="outlined"
            hide-details
            single-line
            class="flex-grow-0"
            @keydown.enter="getInvoices()"
          />

          <div v-if="selectedItemCodeFilter">
            <v-chip
              closable
              color="secondary"
              variant="tonal"
              prepend-icon="mdi-barcode"
              @click:close="clearItemFilter"
            >
              {{ __('Item') }}: {{ selectedItemCodeFilter }}
            </v-chip>
          </div>

          <div class="orders-list">
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
                class="order-row"
                @click="openInvoice(inv.name)"
              >
                <div class="order-row__line">
                  <span class="order-row__name">{{ inv.name }}</span>
                  <v-chip size="small" :color="getStatusColor(inv.status, inv.docstatus)" variant="flat" class="status-chip">
                    {{ __(inv.status || 'Draft') }}
                  </v-chip>
                </div>
                <div class="order-row__line order-row__line--sub">
                  <span class="order-row__customer">
                    {{ inv.customer || __('Unknown Customer') }}
                    <span v-if="inv.posting_date" class="text-medium-emphasis"> · {{ formatDate(inv.posting_date) }}</span>
                  </span>
                  <span class="order-row__total">{{ formatNumber(inv.grand_total) }}</span>
                </div>
              </v-list-item>
            </v-list>

            <v-alert
              v-else
              type="info"
              variant="tonal"
              density="compact"
            >
              {{ __('No invoices found for this filter.') }}
            </v-alert>
          </div>
        </div>
      </SurfaceCard>

      <SurfaceCard v-show="!isMobile || showDetailsOnMobile" class="orders-pane orders-pane--details">
        <div class="orders-pane__body">
          <div class="pane-header">
            <v-btn
              v-if="isMobile"
              :icon="backIcon"
              size="small"
              variant="text"
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
                <span class="font-weight-medium">{{ invoice.customer || 'N/A' }}</span>
                <span class="text-medium-emphasis"> · {{ formatDate(invoice.posting_date) }}</span>
              </div>
            </div>
            <div v-else class="pane-header__title">{{ __('Invoice Details') }}</div>
          </div>

          <div class="details-scroll">
            <v-skeleton-loader
              v-if="isLoadingInvoice"
              type="article, list-item-two-line, list-item-two-line"
            />

            <v-alert
              v-else-if="!invoice"
              type="info"
              variant="tonal"
              density="compact"
            >
              {{ __('Select an invoice from the left panel to view full details.') }}
            </v-alert>

            <template v-else>
              <div class="totals-strip">
                <div class="totals-strip__item">
                  <span class="totals-strip__label">{{ __('Grand Total') }}</span>
                  <span class="totals-strip__value">{{ formatNumber(invoice.grand_total) }}</span>
                </div>
                <div class="totals-strip__item">
                  <span class="totals-strip__label">{{ __('Paid Amount') }}</span>
                  <span class="totals-strip__value text-success">{{ formatNumber(invoice.paid_amount) }}</span>
                </div>
                <div class="totals-strip__item">
                  <span class="totals-strip__label">{{ __('Outstanding') }}</span>
                  <span class="totals-strip__value" :class="invoice.outstanding_amount > 0 ? 'text-warning' : ''">
                    {{ formatNumber(invoice.outstanding_amount) }}
                  </span>
                </div>
              </div>

              <div v-if="invoice.sales_person" class="text-body-2">
                <span class="text-medium-emphasis">{{ __('Sales Person') }}:</span>
                <span class="font-weight-bold"> {{ salesPersonName || invoice.sales_person }}</span>
              </div>

              <section v-if="invoice.items?.length" class="details-section">
                <div class="details-section__title">
                  {{ __('Items') }}
                  <span class="text-medium-emphasis">({{ invoice.items.length }})</span>
                </div>
                <div v-for="item in invoice.items" :key="item.name" class="detail-line">
                  <div class="detail-line__main">
                    <div class="detail-line__name">{{ item.item_name }}</div>
                    <div class="detail-line__sub">
                      {{ item.item_code }} · {{ item.qty }} × {{ formatNumber(item.rate) }}
                    </div>
                  </div>
                  <div class="detail-line__amount">{{ formatNumber(item.amount) }}</div>
                </div>
              </section>

              <section v-if="invoice.payments?.length" class="details-section">
                <div class="details-section__title">{{ __('Payments') }}</div>
                <div v-for="payment in invoice.payments" :key="payment.name || payment.mode_of_payment" class="detail-line">
                  <div class="detail-line__main">
                    <div class="detail-line__name">{{ payment.mode_of_payment }}</div>
                  </div>
                  <div class="detail-line__amount">{{ formatNumber(payment.amount) }}</div>
                </div>
              </section>

              <section v-if="paymentEntries?.length" class="details-section">
                <div class="details-section__title">{{ __('Payment Entries') }}</div>
                <div v-for="entry in paymentEntries" :key="entry.name" class="detail-line">
                  <div class="detail-line__main">
                    <div class="detail-line__name">{{ entry.mode_of_payment }}</div>
                    <div class="detail-line__sub">{{ entry.name }} · {{ formatDate(entry.posting_date) }}</div>
                  </div>
                  <div class="detail-line__amount">{{ formatNumber(entry.paid_amount) }}</div>
                  <v-btn
                    icon="mdi-printer"
                    size="small"
                    variant="text"
                    color="primary"
                    :title="__('Print')"
                    :aria-label="__('Print')"
                    @click="printPaymentEntry(entry.name)"
                  />
                </div>
              </section>
            </template>
          </div>

          <div v-if="invoice && !isLoadingInvoice" class="details-actions">
            <v-btn
              v-if="invoice.outstanding_amount > 0 && invoice.is_return == 0"
              color="success"
              variant="elevated"
              prepend-icon="mdi-cash-multiple"
              @click="payClick()"
            >
              {{ __('Pay') }}
            </v-btn>

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
              v-if="invoice.docstatus == 0"
              color="primary"
              variant="elevated"
              prepend-icon="mdi-pencil"
              @click="editInvoice()"
            >
              {{ __('Edit') }}
            </v-btn>

            <v-btn
              v-if="!invoice.is_return && !invoice.is_consolidated"
              color="warning"
              variant="tonal"
              prepend-icon="mdi-backup-restore"
              @click="returnInvoice()"
            >
              {{ __('Return') }}
            </v-btn>

            <v-btn
              v-if="!invoice.is_consolidated && invoice.docstatus == 1"
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

    <payInvoiceDialog
      v-model="payInvoiceDialogToggle"
      :paymentModes="posProfileData.payments"
      :currency="currency"
      :outstandingAmount="outstandingAmount"
      @pay="payInvoice"
      @close="payInvoiceDialogToggle = false"
    />
  </PageSurface>
</template>

<script setup>
    import { ref, watch, computed } from "vue";
    import { usePosStore } from '../store/posStore';
    import {storeToRefs} from 'pinia';
    import { useRouter, useRoute } from 'vue-router';
    import { useDisplay } from 'vuetify';
    import payInvoiceDialog from './components/orders/payInvoiceDialog.vue';
    import PageSurface from './components/ui/PageSurface.vue';
    import SurfaceCard from './components/ui/SurfaceCard.vue';
    const frappe_ = frappe;
    const __ = window.__;
    const invoices = ref([]);
    const invoice = ref();
    const payInvoiceDialogToggle = ref(false);
    const outstandingAmount = ref(0);
    const currency = ref('');
    const searchTerm = ref('');
    const paymentEntries = ref([]);
    const isLoadingList = ref(false);
    const isLoadingInvoice = ref(false);
    const salesPersonName = ref('');
    const router = useRouter();
    const route = useRoute();
    const { smAndDown } = useDisplay();
    const isMobile = computed(() => smAndDown.value);
    const showDetailsOnMobile = ref(false);
    const formatNumber = (value) => format_number(value || 0);
    const formatDate = (value) => value ? frappe.datetime.str_to_user(value) : '';
    const posStore = usePosStore();
    const {pos_profile, posProfileData} = storeToRefs(posStore);
    const {edit_invoice, process_return, buildPrintViewUrl, isAppRTL} = posStore;
    const backIcon = computed(() => isAppRTL() ? 'mdi-arrow-right' : 'mdi-arrow-left');

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

    const normalizeQueryValue = (value) => {
      if (Array.isArray(value)) {
        return (value[0] || '').toString();
      }

      return (value || '').toString();
    };

    const selectedCustomerFilter = computed(() => normalizeQueryValue(route.query.customer));
    const selectedItemCodeFilter = computed(() => normalizeQueryValue(route.query.item_code));

    const clearInvoiceSelection = () => {
      if (invoice.value) {
        invoice.value = null;
      }
      if (paymentEntries.value.length) {
        paymentEntries.value = [];
      }
      if (showDetailsOnMobile.value) {
        showDetailsOnMobile.value = false;
      }
    };

    const clearItemFilter = async () => {
      const nextQuery = { ...route.query };
      delete nextQuery.item_code;
      await router.replace({ query: nextQuery });
    };

    const returnInvoice = async () =>{
      await process_return('Sales Invoice', invoice.value.name);
      await router.push({ name: 'POS' });
    };

    const editInvoice = async () => {
      await edit_invoice(invoice.value.name);
      await router.push({ name: 'POS' });
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
    const deleteInvoice = async () => {
      frappe.confirm(__('Are you sure you want to delete this invoice? This action cannot be undone.'),
        () => {
            // action to perform if Yes is selected
        }, () => {
            // action to perform if No is selected
        });
    };
    const payInvoice = async (payments) => {
      frappe.call("maxit_pos.maxit_pos.page.maxit_pos.api.api.pay_invoice", {
        doc: invoice.value,
        payments: payments
      }).then((res) => {        
        // invoice.value = res.message;
        frappe.show_alert({
          message:__('Payment Successful'),
          indicator:'green'
        }, 5);
        GetInvoiceDoc(invoice.value.name);
      });
    };
    
    const GetInvoiceDoc = async (invoice_id) => {
      isLoadingInvoice.value = true;
      frappe.db.get_doc('Sales Invoice', invoice_id).then((doc) => {
          invoice.value = doc;
          salesPersonName.value = '';
          if (doc.sales_person) {
            frappe.db.get_value('Employee', doc.sales_person, 'employee_name')
              .then((r) => { salesPersonName.value = r?.message?.employee_name || doc.sales_person; });
          }
          frappe.call("maxit_pos.maxit_pos.page.maxit_pos.api.api.get_invoice_payment_entries", {
            sales_invoice: invoice_id
          }).then((res) => {
            paymentEntries.value = res.message;
            isLoadingInvoice.value = false;
          });
      }).catch(() => {
        isLoadingInvoice.value = false;
      });
    };
    
    const payClick = () => {
      outstandingAmount.value = invoice.value.outstanding_amount;
      currency.value = invoice.value.price_list_currency;
      payInvoiceDialogToggle.value = true;
    };

    const printPaymentEntry = (paymentEntryId) => {
      const printFormat = posProfileData.value?.payment_entry_print_format || 'Standard';
      const letterHead = posProfileData.value?.letter_head || 'No Letterhead';
      const no_letterhead = letterHead === 'No Letterhead' ? 1 : 0;
      const printUrl = buildPrintViewUrl({
        doctype: 'Payment Entry',
        name: paymentEntryId,
        format: printFormat,
        no_letterhead,
        letterhead: letterHead,
      });
      window.open(printUrl, '_blank');
    };

    const printInvoice = () => {
      const doctype = "Sales Invoice";
      const printFormat = posProfileData.value?.print_format || 'Standard';
      const letterHead = posProfileData.value?.letter_head || 'No Letterhead';
      const no_letterhead = letterHead === 'No Letterhead' ? 1 : 0;
      const printUrl = buildPrintViewUrl({
        doctype,
        name: invoice.value.name,
        format: printFormat,
        no_letterhead,
        letterhead: letterHead,
      });
      window.open(printUrl, '_blank');
    };

    const openInvoice = (invoice_id) => {
      showDetailsOnMobile.value = true;
      if (invoice.value?.name !== invoice_id) GetInvoiceDoc(invoice_id);
    };

    watch([selectedCustomerFilter, selectedItemCodeFilter], () => {
      clearInvoiceSelection();
      getInvoices();
    });

    const getInvoices = () => {
      isLoadingList.value = true;
      frappe.call({
        method: "maxit_pos.maxit_pos.page.maxit_pos.api.api.get_sales_invoice_list",
        freeze: true,
        args: { 
          pos_profile: pos_profile.value,
          search_term: searchTerm.value || '',
          customer: selectedCustomerFilter.value,
          item_code: selectedItemCodeFilter.value,
        },
      }).then((response) => {
        invoices.value = response.message || [];
        clearInvoiceSelection();
        isLoadingList.value = false;
      }).catch(() => {
        isLoadingList.value = false;
      });
    };

    getInvoices();
</script>

<style scoped>
.orders-view {
  background:
    radial-gradient(circle at top right, var(--v-pos-info-glow), transparent 42%),
    radial-gradient(circle at left bottom, var(--v-pos-success-glow), transparent 38%);
}

.orders-layout {
  display: flex;
  gap: 8px;
  flex: 1;
  min-height: 0;
}

.orders-pane {
  display: flex;
  flex-direction: column;
  min-height: 0;
  border: 1px solid var(--v-pos-panel-border);
  background: var(--v-pos-panel-background);
  box-shadow: var(--v-pos-panel-shadow);
  transition: var(--v-theme-transition);
}

.orders-pane--list {
  flex: 0 0 clamp(340px, 38%, 480px);
}

.orders-pane--details {
  flex: 1;
  min-width: 0;
}

@media (max-width: 959px) {
  .orders-pane--list {
    flex: 1;
  }
}

.orders-pane__body {
  display: flex;
  flex-direction: column;
  gap: 8px;
  flex: 1;
  min-height: 0;
  padding: 10px;
}

.pane-header {
  display: flex;
  align-items: center;
  gap: 6px;
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
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.orders-list {
  flex: 1;
  min-height: 0;
  overflow-y: auto;
}

.order-row {
  margin-block-end: 2px;
  border: 1px solid var(--v-pos-panel-border-soft);
}

.order-row :deep(.v-list-item__content) {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.order-row__line {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
}

.order-row__name {
  font-size: 0.875rem;
  font-weight: 700;
}

.order-row__line--sub {
  font-size: 0.8125rem;
}

.order-row__customer {
  min-width: 0;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.order-row__total {
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
  grid-template-columns: repeat(3, minmax(0, 1fr));
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
  font-size: clamp(0.8125rem, 3.4vw, 0.9375rem);
  font-weight: 700;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.details-section {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.details-section__title {
  font-size: 0.875rem;
  font-weight: 700;
}

.detail-line {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 6px 8px;
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

.status-chip {
  flex-shrink: 0;
  font-weight: 700;
}

/* yellow needs dark text to stay readable */
.status-chip.bg-amber-darken-1 {
  color: rgba(0, 0, 0, 0.87) !important;
}

.detail-line__amount {
  flex-shrink: 0;
  font-size: 0.875rem;
  font-weight: 700;
}

.details-actions {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  padding-block-start: 8px;
  border-top: 1px solid var(--v-pos-panel-border-soft);
}

.details-actions .v-btn {
  flex: 1 1 auto;
}
</style>
