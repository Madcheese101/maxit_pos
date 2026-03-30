<template>
  <v-main class="ma-10">
    <v-row>
      <v-col cols="3">
        <v-card>
          <v-card-title class="text-h6">
            Select Invoice
            <v-text-field
              density="compact"
              :placeholder="__('Search using invoice number, customer or customer mobile')"
              prepend-inner-icon="mdi-magnify"
              variant="solo"
              flat
              hide-details
              single-line
              v-model="searchTerm"
              @keydown.enter="getInvoices()"
            ></v-text-field>
          </v-card-title>
          <v-card-text>
            <v-list lines="one" color="primary" v-model:selected="selected">
                <v-list-item
                    v-for="inv in invoices"
                    :key="inv.name"
                    :value="inv.name"
                    :title="inv.name"
                    :subtitle="inv.customer + ' - ' + inv.grand_total"
                    
                ></v-list-item>
            </v-list>
          </v-card-text>

          <!-- <v-card-actions>
            <v-spacer />
            <v-btn text @click="closeDialog">Close</v-btn>
          </v-card-actions> -->
        </v-card>
      </v-col>
      <v-col cols="9">
        <v-card>
          <v-card-title class="text-h6" v-if="invoice">
            {{invoice.name}} <span :class="'indicator-pill whitespace-nowrap ' + pillColor">{{ invoice.status }}</span>
          </v-card-title>
          <v-card-text>
            <div v-if="!invoice">
              <!-- Invoice details will be displayed here -->
              Select an invoice to view details.
            </div>
            <v-row v-if="invoice">
              <v-col cols="6">
                <div><strong>{{ __('Customer') }}:</strong> {{ invoice ? invoice.customer : 'N/A' }}</div>
                <div><strong>{{ __('Date') }}:</strong> {{ invoice ? invoice.posting_date : 'N/A' }}</div>
                <div><strong>{{ __('Status') }}:</strong> {{ invoice ? invoice.status : 'N/A' }}</div>
              </v-col>
              <v-col cols="6">
                <div><strong>{{ __('Grand Total') }}:</strong> {{ invoice ? invoice.grand_total : 'N/A' }}</div>
                <div><strong>{{ __('Paid Amount') }}:</strong> {{ invoice ? invoice.paid_amount : 'N/A' }}</div>
                <div><strong>{{ __('Outstanding Amount') }}:</strong> {{ invoice ? invoice.outstanding_amount : 'N/A' }}</div>
              </v-col>
            </v-row>
            <v-row v-if="invoice && invoice.items && invoice.items.length" class="mt-4">
              <v-col cols="12">
                <div class="text-h6 mt-4">{{ __('Items') }}</div>
                <v-data-table-virtual
                  :headers="[
                    { title: __('Item Name'), key: 'item_name' },
                    { title: __('Qty'), key: 'qty' },
                    { title: __('Rate'), key: 'rate' },
                    { title: __('Amount'), key: 'amount' }
                  ]"
                  :items="invoice.items"
                  max-height="300"
                  item-value="item_name"
                  class="elevation-1"
                />
              </v-col>
            </v-row>
            <!-- Payments -->
            <v-row v-if="invoice && invoice.payments && invoice.payments.length" class="mt-4">
              <v-col cols="12">
                <div class="text-h6 mt-4">{{ __('Payments') }}</div>
                <v-data-table-virtual
                  :headers="[
                    { title: __('Mode of Payment'), key: 'mode_of_payment' },
                    { title: __('Amount'), key: 'amount' }
                  ]"
                  :items="invoice.payments"
                  max-height="200"
                  item-value="mode_of_payment"
                  class="elevation-1"
                />
              </v-col>
            </v-row>
            <v-row v-if="paymentEntries && paymentEntries.length" class="mt-4">
              <v-col cols="12">
                <div class="text-h6 mt-4">{{ __('Payment Entries') }}</div>
                <v-data-table-virtual 
                  :headers="[
                    { title: __('Date'), key: 'posting_date' },
                    { title: __('Name'), key: 'name' },
                    { title: __('Mode of Payment'), key: 'mode_of_payment' },
                    { title: __('Amount'), key: 'amount' },
                    { title: __('Print'), key: 'print' }
                  ]"
                  :items="paymentEntries"
                  max-height="200"
                  item-value="mode_of_payment"
                  class="elevation-1"
                >
                  <template #item.print="{ item }">
                    <v-btn 
                      size="small" 
                      color="primary" 
                      @click="printPaymentEntry(item.name)"
                    >
                      {{ __('Print') }}
                    </v-btn>
                  </template>
                </v-data-table-virtual>
              </v-col>
            </v-row>
            <v-row v-if="invoice" class="mt-4" dense>
              <v-col cols="3" v-if="invoice.docstatus!==0">
                <v-btn color="primary" block @click="printInvoice()">
                  Print
                </v-btn>
              </v-col>
              <v-col cols="3" v-if="invoice.docstatus==0">
                <v-btn color="primary" block @click="editInvoice()">
                  Edit
                </v-btn>
              </v-col>
              <v-col v-if="!invoice.is_return && !invoice.is_consolidated" cols="3">
                <v-btn color="warning" block @click="returnInvoice()">
                  Return
                </v-btn>
              </v-col>
              <v-col cols="3" v-if="!invoice.is_consolidated && invoice.docstatus==1">
                <v-btn color="error" block @click="cancelInvoice()">
                  Cancel
                </v-btn>
              </v-col>
              <v-col cols="3" v-if="invoice.outstanding_amount>0 && invoice.is_return==0">
                <v-btn color="success" block @click="payClick()">
                  Pay
                </v-btn>
              </v-col>
              <!-- <v-col cols="3" class="mt-2">
                <v-btn color="red-darken-2" block @click="deleteInvoice()">
                  Delete
                </v-btn>
              </v-col> -->
            </v-row>
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
    import { ref, watch } from "vue";
    import { usePosStore } from '../store/posStore';
    import {storeToRefs} from 'pinia';
    import { useRouter } from 'vue-router'
    import payInvoiceDialog from './components/orders/payInvoiceDialog.vue';
    const frappe_ = frappe;
    const __ = window.__;
    const invoices = ref([]);
    const invoice = ref();
    const pillColor = ref('red');
    const selected = ref([]);
    const payInvoiceDialogToggle = ref(false);
    const outstandingAmount = ref(0);
    const currency = ref('');
    const searchTerm = ref('');
    const paymentEntries = ref([]);
    const router = useRouter()
    const posStore = usePosStore();
    const {pos_profile, posProfileData} = storeToRefs(posStore);
    const {edit_invoice, process_return} = posStore;
    const returnInvoice = async () =>{
      await process_return('Sales Invoice', invoice.value.name);
      await router.push({ name: 'POS' });
    }

    const editInvoice = async () => {
      await edit_invoice(invoice.value.name);
      await router.push({ name: 'POS' });
    }

    const cancelInvoice = async () => {
      frappe.confirm(__('Are you sure you want to cancel this invoice?'),
        () => {
            // action to perform if Yes is selected
            console.log('Invoice cancelled', invoice.value.name);
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
        })
    }
    const deleteInvoice = async () => {
      frappe.confirm(__('Are you sure you want to delete this invoice? This action cannot be undone.'),
        () => {
            // action to perform if Yes is selected
            console.log('Invoice deleted', invoice.value.name);
        }, () => {
            // action to perform if No is selected
        })
    }
    const payInvoice = async (payments) => {
      console.log("Payments to be made:", payments);
      frappe.call("maxit_pos.maxit_pos.page.maxit_pos.api.api.pay_invoice", {
        doc: invoice.value,
        payments: payments
      }).then((res) => {        
        // invoice.value = res.message;
        console.log("Payment response:", res);
        frappe.show_alert({
          message:__('Payment Successful'),
          indicator:'green'
        }, 5);
      });
    }
    
    const GetInvoiceDoc = async (invoice_id) => {
      // await edit_invoice(invoice_id);
      // await router.push({ name: 'POS' });
      frappe.db.get_doc('Sales Invoice', invoice_id).then((doc) => {
          invoice.value = doc;
          frappe.call("maxit_pos.maxit_pos.page.maxit_pos.api.api.get_invoice_payment_entries", {
            sales_invoice: invoice_id
          }).then((res) => {
            paymentEntries.value = res.message;
          });
      });
    }
    
    const payClick = () => {
      outstandingAmount.value = invoice.value.outstanding_amount;
      currency.value = invoice.value.price_list_currency;
      payInvoiceDialogToggle.value = true;
    }

    const printPaymentEntry = (paymentEntryId) => {
      const printFormat = 'Standard';
      const printUrl = `/printview?doctype=Payment%20Entry&name=${paymentEntryId}&
format=${printFormat}&no_letterhead=1&letterhead=No%20Letterhead&settings=%7B%7D&_lang=en&
pdf_generator=wkhtmltopdf&trigger_print=1`;
      window.open(printUrl, '_blank');
    }

    const printInvoice = () => {
      const doctype = "Sales Invoice";
      const printFormat = 'Standard';
      const printUrl = `/printview?doctype=${doctype}&name=${invoice.value.name}&
format=${printFormat}&no_letterhead=1&letterhead=No%20Letterhead&settings=%7B%7D&_lang=en&
pdf_generator=wkhtmltopdf&trigger_print=1`;
      window.open(printUrl, '_blank');
    }

    watch(selected, (val) => {
      if (!val.length) {
        // nothing selected
        invoice.value = null
        return
      }
      GetInvoiceDoc(val[0]);
    })

    const getInvoices = () => {
      // Implement search functionality here, possibly by calling an API with the search term
      frappe.call({
        method: "maxit_pos.maxit_pos.page.maxit_pos.api.api.get_sales_invoice_list",
        freeze: true,
        args: { 
          pos_profile: pos_profile.value,
          search_term: searchTerm.value || ''
        },
      }).then((response) => {
        invoices.value = response.message;
      });
    }
    // Fetch orders for the selected POS profile
    getInvoices();
</script>