<template>
  <v-main class="orders-view pa-3 pa-md-6" v-if="purchaseEnabled">
    <v-row class="orders-shell" align="stretch">
      <v-col v-show="!isMobile || !showDetailsOnMobile" cols="12" md="4" lg="3">
        <v-card class="orders-panel h-100" max-height="100vh" rounded="xl" variant="flat">
          <v-card-item class="pb-2">
            <div class="d-flex align-center justify-space-between gap-2 mb-3">
              <div>
                <div class="text-overline text-medium-emphasis">{{ __('Purchase') }}</div>
                <div class="text-h6 font-weight-bold">{{ __('Select Invoice') }}</div>
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

                <v-card class="purchase-actions-menu" min-width="80px" rounded="lg" variant="flat">
                  <v-card-text class="pa-2 d-flex flex-column ga-2">
                    <v-btn
                      color="primary"
                      variant="text"
                      prepend-icon="mdi-sync"
                      size="small"
                      @click="onSyncAction"
                    >
                      {{ __('Sync') }}
                    </v-btn>

                    <v-btn
                      color="secondary"
                      variant="text"
                      prepend-icon="mdi-file-undo-outline"
                      size="small"
                      @click="returnInvoice"
                    >
                      {{ __('Return') }}
                    </v-btn>
                  </v-card-text>
                </v-card>
              </v-menu>
            </div>
            <v-text-field
              v-model="searchTerm"
              density="comfortable"
              :placeholder="__('Search invoice, supplier invoice')"
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
              max-height="70vh"
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
      <!-- Right Section -->
      <v-col v-show="!isMobile || showDetailsOnMobile" cols="12" md="8" lg="9">
        <v-card class="orders-panel h-100" max-height="90vh" rounded="xl" variant="flat">
          <v-card-item class="pb-0">
            <div class="d-flex align-center justify-space-between flex-wrap gap-3">
              <div class="d-flex align-center gap-2">
                <v-btn
                  v-if="isMobile"
                  icon="mdi-arrow-left"
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
                      <div class="text-caption text-medium-emphasis">{{ __('Supplier Branch') }}</div>
                      <div class="text-body-1 font-weight-bold text-truncate">{{ invoice.supplier_branch || 'N/A' }}</div>
                    </v-card-text>
                  </v-card>
                </v-col>

                <v-col cols="12" sm="6" md="4">
                  <v-card class="stat-card" rounded="lg" variant="tonal" color="success">
                    <v-card-text>
                      <div class="text-caption text-medium-emphasis">{{ __('Supplier Invoice') }}</div>
                      <div class="text-body-1 font-weight-bold">{{ invoice.bill_no || 'N/A' }}</div>
                    </v-card-text>
                  </v-card>
                </v-col>

                <v-col cols="12" sm="6" md="4">
                  <v-card class="stat-card" rounded="lg" variant="tonal" color="warning">
                    <v-card-text>
                      <div class="text-caption text-medium-emphasis">{{ __('Supplier Invoice Date') }}</div>
                      <div class="text-body-1 font-weight-bold">{{ invoice.posting_date || 'N/A' }}</div>
                    </v-card-text>
                  </v-card>
                </v-col>
              </v-row>

              <v-row class="mb-1" dense>
                <v-col cols="12" md="6">
                  <div class="meta-row"><strong>{{ __('Status') }}:</strong> {{ invoice.status || 'N/A' }}</div>
                  <div class="meta-row"><strong>{{ __('Date') }}:</strong> {{ invoice.posting_date || 'N/A' }}</div>
                </v-col>
              </v-row>

              <v-card class="section-card mt-4" rounded="lg" variant="outlined" v-if="invoice.items?.length">
                <v-card-item class="pb-1">
                  <div class="text-subtitle-1 font-weight-bold">{{ __('Items') }}</div>
                </v-card-item>
                <v-card-text>
                  <v-data-table-virtual
                    :headers="[
                      { title: __('No.'), key: 'idx', width: '70px' },
                      { title: __('Item Code'), key: 'item_code' },
                      { title: __('Item Name'), key: 'item_name' },
                      { title: __('Qty'), key: 'qty' },
                    ]"
                    :items="invoice.items"
                    item-value="item_name"
                    density="compact"
                    height="50vh"
                    max-height="60vh"
                    fixed-header
                    class="orders-table overflow-y-auto"
                  />
                </v-card-text>
              </v-card>

              <div class="actions-wrap mt-5">
                <!-- <v-btn
                  v-if="invoice.status === 'Draft'"
                  color="success"
                  variant="elevated"
                  prepend-icon="mdi-floppy-disk"
                  @click="console.log('Submit Invoice')"
                >
                  {{ __('Submit') }}
                </v-btn> -->
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
            </template>
          </v-card-text>
        </v-card>
      </v-col>
    </v-row>
  </v-main>
</template>

<script setup>
  import {storeToRefs} from 'pinia';
  import { useDisplay } from 'vuetify';
  import { ref, watch, computed } from "vue";
  import { usePosStore } from '../store/posStore';
    
  const __ = window.__;
  const frappe_ = window.frappe;
  const invoices = ref([]);
  const invoice = ref();
  const selected = ref([]);

  const searchTerm = ref('');
  const paymentEntries = ref([]);
  const isLoadingInvoice = ref(false);
  const { smAndDown } = useDisplay();
  const isMobile = computed(() => smAndDown.value);
  const showDetailsOnMobile = ref(false);
  const isLoadingList = ref(false);
  const posStore = usePosStore();
  const {pos_profile, posProfileData} = storeToRefs(posStore);
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

  const invoiceSubtitle = (inv) => `${inv.supplier_branch || __('Unknown Supplier')} - ${inv.bill_no || __('Unknown Bill')}`;
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
      searchTerm.value = '';
      getInvoices();
      frappe.show_alert({
        message: __('Sync Completed'),
        indicator: 'green'
      }, 5);
      if(response.message){
        frappe.show_alert({
          message: __('Invoices Synced: {0}', [response.message.join(', ')]),
          indicator: 'green'
        }, 10);
      }
      else      {
        frappe.show_alert({
          message: __('No new invoices to sync'),
          indicator: 'blue'
        }, 5);
      }
    }).catch(() => {
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

  const returnInvoice = async () =>{
    // await process_return('Sales Invoice', invoice.value.name);
    const dialog = new frappe.ui.Dialog({
        title: 'Enter details',
        fields: [
            {
                label: __('Supplier Branch'),
                fieldname: 'supplier_branch',
                fieldtype: 'Link',
                options: 'Supplier Branch',
                reqd: true
            },
            {
                label: __('Items'),
                fieldname: 'items',
                fieldtype: 'Table',
                fields: [
                  {
                    label: __('Item Code'),
                    fieldname: 'item_code',
                    fieldtype: 'Link',
                    options: 'Item',
                    onchange: function () {
                      const item_code = this.value;
                      if (!item_code) {
                        this.grid_row.on_grid_fields_dict.item_name.set_value('');
                      };
                      if (item_code) {
                        frappe.db.get_value('Item', item_code, ['item_name']).then(res => {
                          const msg = res.message;
                          this.grid_row.on_grid_fields_dict.item_name.set_value(msg.item_name);
                        });
                      }
                    },
                    reqd: true,
                    in_list_view: true,
                  },
                  {
                    label: __('Item Name'),
                    fieldname: 'item_name',
                    fieldtype: 'Data',
                    read_only: 1,
                    in_list_view: true,
                    columns: '6'
                  },
                  {
                    label: __('Qty'),
                    fieldname: 'qty',
                    fieldtype: 'Float',
                    reqd: true,
                    in_list_view: true,
                    columns: '2'
                  }
                ]
            }
        ],
        size: 'extra-large', // small, large, extra-large 
        primary_action_label: __('Submit'),
        primary_action(values) {
            frappe.call({
              method: "maxit_pos.maxit_pos.page.maxit_pos.api.purchase_vue.create_return_invoice",
              args: {
                supplier_branch: values.supplier_branch,
                items: values.items,
                cost_center: posProfileData.value?.cost_center || '',
                warehouse: posProfileData.value?.warehouse || '',
              },
            }).then((res) => {
              frappe.show_alert({
                message: __('Return Invoice Created'),
                indicator: 'green'
              }, 5);
              dialog.hide();
              searchTerm.value = '';
              getInvoices();
            });
            
        }});   

    dialog.show();
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
    frappe.db.get_doc('Purchase Receipt', invoice_id).then((doc) => {
        invoice.value = doc;
        isLoadingInvoice.value = false;
    }).catch(() => {
      isLoadingInvoice.value = false;
    });
  };

  const printInvoice = () => {
    const doctype = "Purchase Receipt";
    const printFormat = posProfileData.value?.purchase_receipt_print_format || 'Standard';
    const printUrl = `/printview?doctype=${doctype}&name=${invoice.value.name}&format=${printFormat}&no_letterhead=1&letterhead=No%20Letterhead&settings=%7B%7D&_lang=en&pdf_generator=wkhtmltopdf&trigger_print=1`;
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
}

.stat-card {
  border: 1px solid rgba(120, 144, 156, 0.18);
}

.purchase-actions-menu {
  border: 1px solid rgba(120, 144, 156, 0.26);
  background: linear-gradient(180deg, rgba(255, 255, 255, 0.98), rgba(248, 251, 255, 0.98));
  box-shadow: 0 8px 20px rgba(12, 28, 43, 0.12);
  /* min-width: 260px; */
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