<template>
  <v-main class="orders-view pa-3 pa-md-6">
    <v-row class="orders-shell" align="stretch">
      <v-col v-show="!isMobile || !showDetailsOnMobile" cols="12" md="4" lg="3">
        <v-card class="orders-panel " max-height="100vh" rounded="xl" variant="flat">
          <v-card-item class="pb-2">
            <div class="d-flex align-center justify-space-between gap-2 mb-3">
              <div>
                <div class="text-overline text-medium-emphasis">{{ __('Orders') }}</div>
                <div class="text-h6 font-weight-bold">{{ __('Select Invoice') }}</div>
              </div>
              <v-chip size="small" color="primary" variant="tonal">
                {{ invoices.length }}
              </v-chip>
            </div>
            <v-text-field
              v-model="searchTerm"
              density="comfortable"
              :placeholder="__('Search invoice, customer, mobile')"
              prepend-inner-icon="mdi-magnify"
              variant="solo-filled"
              hide-details
              single-line
              rounded="lg"
              @keydown.enter="getInvoices()"
            />
          </v-card-item>

          <v-divider />

          <v-card-text class="pt-3 px-2">
            <div v-if="isLoadingList" class="px-2 py-5">
              <v-skeleton-loader type="list-item-two-line, list-item-two-line, list-item-two-line" />
            </div>

            <v-list
              v-else-if="invoices.length"
              lines="two"
              color="primary"
              max-height="50vh"
              nav
              rounded="lg"
              class="orders-list overflow-y-auto"
              v-model:selected="selected"
            >
              <v-list-item
                v-for="inv in invoices"
                :key="inv.name"
                :value="inv.name"
                :title="inv.name"
                :subtitle="invoiceSubtitle(inv)"
                rounded="lg"
                class="mb-1"
              >
                <template #append>
                  <v-chip
                    size="small"
                    :color="getStatusColor(inv.status, inv.docstatus)"
                    variant="tonal"
                  >
                    {{ inv.status || __('Draft') }}
                  </v-chip>
                </template>
              </v-list-item>
            </v-list>

            <v-alert
              v-else
              type="info"
              variant="tonal"
              density="compact"
              class="mt-2"
            >
              {{ __('No invoices found for this filter.') }}
            </v-alert>
          </v-card-text>
        </v-card>
      </v-col>

      <v-col v-show="!isMobile || showDetailsOnMobile" cols="12" md="8" lg="9">
        <v-card class="orders-panel " rounded="xl" variant="flat" max-height="100vh">
          <v-card-item class="pb-0">
            <div class="d-flex align-center justify-space-between flex-wrap gap-3">
              <div class="d-flex align-center gap-2">
                <v-btn
                  v-if="isMobile"
                  :icon="backIcon"
                  variant="text"
                  size="small"
                  @click="showDetailsOnMobile = false"
                />

                <div v-if="invoice">
                  <div class="text-overline text-medium-emphasis">{{ __('Invoice Details') }}</div>
                  <div class="text-h6 font-weight-bold d-flex align-center flex-wrap gap-2">
                    {{ invoice.name }}
                    <v-chip size="small" :color="statusChip.color" variant="tonal">
                      {{ invoice.status }}
                    </v-chip>
                  </div>
                </div>

                <div v-else>
                  <div class="text-overline text-medium-emphasis">{{ __('Invoice Details') }}</div>
                  <div class="text-h6 font-weight-bold">{{ __('No Invoice Selected') }}</div>
                </div>
              </div>

              <v-chip v-if="invoice" size="small" color="secondary" variant="outlined">
                {{ __('Date') }}: {{ invoice.posting_date }}
              </v-chip>
            </div>
          </v-card-item>

          <v-card-text class="pt-4">
            <v-skeleton-loader
              v-if="isLoadingInvoice"
              type="table, article, article"
            />

            <v-alert
              v-else-if="!invoice"
              type="info"
              variant="tonal"
            >
              {{ __('Select an invoice from the left panel to view full details.') }}
            </v-alert>

            <template v-else>
              <v-row dense class="mb-2">
                <v-col cols="12" sm="6" md="4">
                  <v-card class="stat-card" rounded="lg" variant="tonal" color="primary">
                    <v-card-text>
                      <div class="text-caption text-medium-emphasis">{{ __('Customer') }}</div>
                      <div class="text-body-1 font-weight-bold text-truncate">{{ invoice.customer || 'N/A' }}</div>
                    </v-card-text>
                  </v-card>
                </v-col>

                <v-col cols="12" sm="6" md="4">
                  <v-card class="stat-card" rounded="lg" variant="tonal" color="success">
                    <v-card-text>
                      <div class="text-caption text-medium-emphasis">{{ __('Grand Total') }}</div>
                      <div class="text-body-1 font-weight-bold">{{ invoice.grand_total }} {{ invoice.price_list_currency }}</div>
                    </v-card-text>
                  </v-card>
                </v-col>

                <v-col cols="12" sm="6" md="4">
                  <v-card class="stat-card" rounded="lg" variant="tonal" color="warning">
                    <v-card-text>
                      <div class="text-caption text-medium-emphasis">{{ __('Outstanding') }}</div>
                      <div class="text-body-1 font-weight-bold">{{ invoice.outstanding_amount }} {{ invoice.price_list_currency }}</div>
                    </v-card-text>
                  </v-card>
                </v-col>
              </v-row>

              <v-row class="mb-1" dense>
                <v-col cols="12" md="6">
                  <div class="meta-row"><strong>{{ __('Status') }}:</strong> {{ invoice.status || 'N/A' }}</div>
                  <div class="meta-row"><strong>{{ __('Date') }}:</strong> {{ invoice.posting_date || 'N/A' }}</div>
                </v-col>
                <v-col cols="12" md="6">
                  <div class="meta-row"><strong>{{ __('Paid Amount') }}:</strong> {{ invoice.paid_amount || '0' }} {{ invoice.price_list_currency }}</div>
                  <div class="meta-row"><strong>{{ __('Outstanding Amount') }}:</strong> {{ invoice.outstanding_amount || '0' }} {{ invoice.price_list_currency }}</div>
                </v-col>
              </v-row>

              <v-card class="section-card mt-4" rounded="lg" variant="outlined" v-if="invoice.items?.length">
                <v-card-item class="pb-1">
                  <div class="text-subtitle-1 font-weight-bold">{{ __('Items') }}</div>
                </v-card-item>
                <v-card-text>
                  <v-data-table-virtual
                    :headers="[
                      { title: __('Item Name'), key: 'item_name' },
                      { title: __('Qty'), key: 'qty' },
                      { title: __('Rate'), key: 'rate' },
                      { title: __('Amount'), key: 'amount' }
                    ]"
                    :items="invoice.items"
                    item-value="item_name"
                    density="compact"
                    max-height="30vh"
                    class="orders-table"
                  />
                </v-card-text>
              </v-card>

              <v-card class="section-card mt-4" rounded="lg" variant="outlined" v-if="invoice.payments?.length">
                <v-card-item class="pb-1">
                  <div class="text-subtitle-1 font-weight-bold">{{ __('Payments') }}</div>
                </v-card-item>
                <v-card-text>
                  <v-data-table-virtual
                    :headers="[
                      { title: __('Mode of Payment'), key: 'mode_of_payment' },
                      { title: __('Amount'), key: 'amount' }
                    ]"
                    :items="invoice.payments"
                    item-value="mode_of_payment"
                    density="compact"
                    max-height="15vh"
                    class="orders-table"
                  />
                </v-card-text>
              </v-card>

              <v-card class="section-card mt-4" rounded="lg" variant="outlined" v-if="paymentEntries?.length">
                <v-card-item class="pb-1">
                  <div class="text-subtitle-1 font-weight-bold">{{ __('Payment Entries') }}</div>
                </v-card-item>
                <v-card-text>
                  <v-data-table-virtual
                    :headers="[
                      { title: __('Date'), key: 'posting_date' },
                      { title: __('Name'), key: 'name' },
                      { title: __('Mode of Payment'), key: 'mode_of_payment' },
                      { title: __('Amount'), key: 'paid_amount' },
                      { title: __('Print'), key: 'print', sortable: false }
                    ]"
                    :items="paymentEntries"
                    item-value="name"
                    density="compact"
                    max-height="30vh"
                    class="orders-table"
                  >
                    <template #item.print="{ item }">
                      <v-btn
                        size="small"
                        color="primary"
                        variant="tonal"
                        @click="printPaymentEntry(item.name)"
                      >
                        {{ __('Print') }}
                      </v-btn>
                    </template>
                  </v-data-table-virtual>
                </v-card-text>
              </v-card>

              <div class="actions-wrap mt-5">
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

                <v-btn
                  v-if="invoice.outstanding_amount > 0 && invoice.is_return == 0"
                  color="success"
                  variant="elevated"
                  prepend-icon="mdi-cash-multiple"
                  @click="payClick()"
                >
                  {{ __('Pay') }}
                </v-btn>
              </div>
            </template>
          </v-card-text>
        </v-card>
      </v-col>
    </v-row>

    <payInvoiceDialog
      v-model="payInvoiceDialogToggle"
      :paymentModes="posProfileData.payments"
      :currency="currency"
      :outstandingAmount="outstandingAmount"
      @pay="payInvoice"
      @close="payInvoiceDialogToggle = false"
    />
  </v-main>
</template>

<script setup>
    import { ref, watch, computed } from "vue";
    import { usePosStore } from '../store/posStore';
    import {storeToRefs} from 'pinia';
    import { useRouter, useRoute } from 'vue-router';
    import { useDisplay } from 'vuetify';
    import payInvoiceDialog from './components/orders/payInvoiceDialog.vue';
    const frappe_ = frappe;
    const __ = window.__;
    const invoices = ref([]);
    const invoice = ref();
    const selected = ref([]);
    const payInvoiceDialogToggle = ref(false);
    const outstandingAmount = ref(0);
    const currency = ref('');
    const searchTerm = ref('');
    const paymentEntries = ref([]);
    const isLoadingList = ref(false);
    const isLoadingInvoice = ref(false);
    const router = useRouter();
    const route = useRoute();
    const { smAndDown } = useDisplay();
    const isMobile = computed(() => smAndDown.value);
    const showDetailsOnMobile = ref(false);
    const posStore = usePosStore();
    const {pos_profile, posProfileData} = storeToRefs(posStore);
    const {edit_invoice, process_return, buildPrintViewUrl, isAppRTL} = posStore;
    const backIcon = computed(() => isAppRTL() ? 'mdi-arrow-right' : 'mdi-arrow-left');

    const getStatusColor = (status, docstatus) => {
      const normalizedStatus = (status || '').toLowerCase();

      if (normalizedStatus == 'unpaid' || normalizedStatus == 'overdue') return 'error';
      if (normalizedStatus == 'paid' || normalizedStatus == 'completed') return 'success';
      if (normalizedStatus == 'partly paid') return 'warning';
      if (normalizedStatus == 'cancel') return 'error';
      if (docstatus === 0) return 'info';
      return 'secondary';
    };

    const statusChip = computed(() => ({
      color: getStatusColor(invoice.value?.status, invoice.value?.docstatus)
    }));

    const invoiceSubtitle = (inv) => `${inv.customer || __('Unknown Customer')} - ${inv.grand_total || 0}`;

    const selectedCustomerFilter = computed(() => (route.query.customer || '').toString());

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

    watch(selected, (val) => {
      if (!val.length) {
        invoice.value = null;
        paymentEntries.value = [];
        showDetailsOnMobile.value = false;
        return;
      }
      showDetailsOnMobile.value = true;
      GetInvoiceDoc(val[0]);
    });

    watch(() => route.query.customer, () => {
      selected.value = [];
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
.orders-view {
  background:
    radial-gradient(circle at top right, rgba(25, 118, 210, 0.09), transparent 42%),
    radial-gradient(circle at left bottom, rgba(76, 175, 80, 0.08), transparent 38%);
}

.orders-panel {
  border: 1px solid rgba(120, 144, 156, 0.24);
  background: linear-gradient(180deg, rgba(255, 255, 255, 0.94), rgba(248, 251, 255, 0.96));
  box-shadow: 0 10px 24px rgba(12, 28, 43, 0.08);
}

.orders-list :deep(.v-list-item--active) {
  background: rgba(25, 118, 210, 0.13);
}

.section-card {
  border-color: rgba(120, 144, 156, 0.28) !important;
}

.orders-table {
  border-radius: 10px;
  overflow: hidden;
}

.stat-card {
  border: 1px solid rgba(120, 144, 156, 0.18);
}

.meta-row {
  padding: 4px 0;
}

.actions-wrap {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
}

@media (max-width: 960px) {
  .orders-view {
    padding: 10px;
  }

  .actions-wrap {
    display: grid;
    grid-template-columns: 1fr;
  }
}
</style>