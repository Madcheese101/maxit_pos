<script setup>
  $('.body-sidebar-container').removeClass('expanded');
  const frappe_ = frappe;
  const __ = window.__;
  
  import {storeToRefs} from 'pinia';
  import { ref, computed, watch } from 'vue'
  import { usePosStore } from '../store/posStore';
  import Cart from './components/pos/Cart.vue';
  import ItemsList from './components/pos/ItemsList.vue';
  import FiltersSection from './components/pos/FiltersSection.vue';
  import LoadInvoiceDialog from './components/pos/LoadInvoiceDialog.vue';
  
  const posStore = usePosStore();
  const {posProfileData, pos_profile, pos_opening, posFrm} = storeToRefs(posStore);
  const {make_new_invoice, update_cart, edit_invoice, setPosOpening, sales_order_to_invoice} = posStore;
  // Local State
  const activeTab = ref('pos')
  const customerSearch = ref('')
  const items = ref([]);
  const customers = ref([])
  const items_uoms = ref([]);
  const heldInvoices = ref([]);
  const loading = ref(false)
  const LoadInvoiceDialogToggle = ref(false);
  const customer = ref(posProfileData.value.customer);
  const posPayments = computed(() => posFrm.value?.doc?.payments || [])
  const priceListCurrency = computed(() => posFrm.value?.doc?.price_list_currency || "")
  const hasCartItems = computed(() => (posFrm.value?.doc?.items || []).length > 0)
  const isReturnInvoice = computed(() => {
    return posFrm.value?.doc?.is_return || false;
  });
  
  const searchItems = async (filters) => {
    search_term = filters ? filters.search_term : "";
    item_group = filters ? filters.item_group : null;
    custom_filters = filters ? filters.filters : [];

    const response = await frappe.call({
			method: "maxit_pos.maxit_pos.page.maxit_pos.api.api.get_items",
			freeze: true,
			args: {pos_profile_data: posProfileData.value,
        search_term: search_term,
        item_group: item_group,
        custom_filters: custom_filters},
      });
    // items.value = response.message.items;
    items.value = response.message[0];
    items_uoms.value = response.message[1];
  };

  const fetchCustomers = async (query = '') => {
    const filters = query ? { customer_name: ['like', `%${query}%`] } : {}
    loading.value = true
    try {
        const res = await frappe.db.get_list('Customer', {
            fields: ['name', 'customer_name'],
            // limit: 2,
            filters: filters
        })
        customers.value = res;
    } finally {
        loading.value = false
    }
  }
  // Debounced search
  let timeout
  watch(customerSearch, (val) => {
      clearTimeout(timeout)
      timeout = setTimeout(() => {
          if (!val || val == posProfileData.value.customer) fetchCustomers()
          else fetchCustomers(val)
      }, 300)
  })

  const openAddCustomerDialog = () => {
  //   frappe.new_doc('Customer')
    console.log("Create new customer")
    if (frappe.ui?.form?.make_quick_entry) {
      frappe.ui.form.make_quick_entry(
        "Customer",
        async (doc) => {
          const newCustomer = {
            name: doc.name,
            customer_name: doc.customer_name || doc.name,
          };

          customers.value = [
            newCustomer,
            ...customers.value.filter((c) => c.name !== newCustomer.name),
          ];
          customer.value = newCustomer;
          customerSearch.value = newCustomer.customer_name;

          await updateSelection();

          frappe.show_alert({
            indicator: "green",
            message: __("Customer {0} created successfully", [doc.name]),
          });
        },
        null,
        null,
        true
      );
    }
  }

  const updateSelection = async () => {
    const val = customer.value || '';
    if(val == posFrm.value.doc.customer) return;
    posFrm.value.doc.customer = val?.name || '';
    await posFrm.value.script_manager.trigger("customer", "Sales Invoice", posFrm.value.doc.name);
  }

  const prepareCheckout = async () => {
    if (!hasCartItems.value) return;
    await posFrm.value.save();
    await posFrm.value.cscript.set_default_payment(posFrm.value.doc.grand_total, true);
    posFrm.value.refresh_field("payments");
    activeTab.value = 'checkout';
  }

  const changePaymentAmount = async (item_name) => {
    await posFrm.value.script_manager.trigger("amount", "Sales Invoice Payment", item_name);
  }

  const ChangePayment = async (item) => {
      item.amount = posFrm.value.doc.grand_total;
      posPayments.value.forEach(payment => {
        if (payment.name !== item.name) {
          payment.amount = 0;
        }
      });
      await posFrm.value.script_manager.trigger("amount", "Sales Invoice Payment", item.name);
  }

  const submitInvoice = async (print=false) =>{
    await posFrm.value.savesubmit();
    activeTab.value = 'pos';
    frappe.show_alert({
      indicator: "green",
      message: __("Sales invoice {0} created successfully", [posFrm.value.doc.name]),
    });
    if(print) printInvoice(posFrm.value.doc.name);    
    await make_new_invoice();
    await fetchCustomers();
  }

  const saveAsSalesOrder = async () => {
    await posFrm.value.save();
    frappe.call({
      method: "maxit_pos.maxit_pos.page.maxit_pos.api.api.save_invoice_as_sales_order",
      args: {
        invoice_name: posFrm.value.doc.name
      },
      freeze: true,
    }).then((response) => {
      const sales_order = response.message;
      frappe.show_alert({
        indicator: "green",
        message: __("Sales order {0} created successfully", [sales_order]),
      });
    });
  }

  const printInvoice = (invoice) => {
    const doctype = "Sales Invoice";
    const printFormat = 'Standard';
    const printUrl = `/printview?doctype=${doctype}&name=${invoice}&
format=${printFormat}&no_letterhead=1&letterhead=No%20Letterhead&settings=%7B%7D&_lang=en&
pdf_generator=wkhtmltopdf&trigger_print=1`;
    window.open(printUrl, '_blank');
  }

  const printLastInvoice = () => {
    console.log("Printing last invoice");
  }

  const resetForm = () => {
    make_new_invoice().then(() => {
      // isLoading.value = false;
      activeTab.value = 'pos';
      customer.value = posFrm.value.doc.customer;
      fetchCustomers()
    })
  }

  const clearLoadInvoiceList = () => {
    heldInvoices.value = [];
  }

  const showLoadInvoiceDialog = (is_sales_order=false) => {
    const method = (is_sales_order ? "get_sales_orders" : "get_held_invoices");
    const args = is_sales_order ? {} : {pos_profile: pos_profile.value};
    frappe.call({
      method: `maxit_pos.maxit_pos.page.maxit_pos.api.api.${method}`,
      freeze: true,
      args: args,
    }).then((response) => {
      heldInvoices.value = response.message;
      LoadInvoiceDialogToggle.value = true;
    });
  }

  const load_invoice = (invoice) => {
      clearLoadInvoiceList();
      if(invoice.doctype == "Sales Order") {
        sales_order_to_invoice(invoice.name).then(() => {
          activeTab.value = 'pos';
          customer.value = posFrm.value.doc.customer;
        });
      }
      else{
        edit_invoice(invoice.name).then(() => {
          activeTab.value = 'pos';
          customer.value = posFrm.value.doc.customer;
        })
      }
  }

  const fetch_opening_entry = async () => {
    return frappe.call("erpnext.selling.page.point_of_sale.point_of_sale.check_opening_entry", {
        user: frappe.session.user,
    });
  }

  const create_opening_voucher = async () => {
    const me = this;
    const table_fields = [
      {
        fieldname: "mode_of_payment",
        fieldtype: "Link",
        in_list_view: 1,
        label: __("Mode of Payment"),
        options: "Mode of Payment",
        reqd: 1,
      },
      {
        fieldname: "opening_amount",
        fieldtype: "Currency",
        in_list_view: 1,
        label: __("Opening Amount"),
        options: "company:company_currency",
        onchange: function () {
          dialog.fields_dict.balance_details.df.data.some((d) => {
            if (d.idx == this.doc.idx) {
              d.opening_amount = this.value;
              dialog.fields_dict.balance_details.grid.refresh();
              return true;
            }
          });
        },
      },
    ];
    const fetch_pos_payment_methods = () => {
      const pos_profile = dialog.fields_dict.pos_profile.get_value();
      if (!pos_profile) return;
      frappe.db.get_doc("POS Profile", pos_profile).then(({ payments }) => {
        dialog.fields_dict.balance_details.df.data = [];
        payments.forEach((pay) => {
          const { mode_of_payment } = pay;
          dialog.fields_dict.balance_details.df.data.push({ mode_of_payment, opening_amount: "0" });
        });
        dialog.fields_dict.balance_details.grid.refresh();
      });
    };

    const dialog = new frappe.ui.Dialog({
      title: __("Create POS Opening Entry"),
      static: true,
      fields: [
        {
          fieldtype: "Link",
          label: __("Company"),
          default: frappe.defaults.get_default("company"),
          options: "Company",
          fieldname: "company",
          reqd: 1,
        },
        {
          fieldtype: "Link",
          label: __("POS Profile"),
          options: "POS Profile",
          fieldname: "pos_profile",
          reqd: 1,
          get_query: () => pos_profile_query(),
          onchange: () => fetch_pos_payment_methods(),
        },
        {
          fieldname: "balance_details",
          fieldtype: "Table",
          label: __("Opening Balance Details"),
          cannot_add_rows: false,
          in_place_edit: true,
          reqd: 1,
          data: [],
          fields: table_fields,
        },
      ],
      primary_action: async function ({ company, pos_profile, balance_details }) {
        if (!balance_details.length) {
          frappe.show_alert({
            message: __("Please add Mode of payments and opening balance details."),
            indicator: "red",
          });
          return frappe.utils.play_sound("error");
        }

        // filter balance details for empty rows
        balance_details = balance_details.filter((d) => d.mode_of_payment);

        const method = "erpnext.selling.page.point_of_sale.point_of_sale.create_opening_voucher";
        const res = await frappe.call({
          method,
          args: { pos_profile, company, balance_details },
          freeze: true,
        });

        !res.exc && setPosOpening(res.message);
        initialize_Invoice();
        dialog.hide();
      },
      primary_action_label: __("Submit"),
    });
    dialog.show();
    
    const pos_profile_query = () => {
      return {
        query: "erpnext.accounts.doctype.pos_profile.pos_profile.pos_profile_query",
        filters: { company: dialog.fields_dict.company.get_value() },
      };
    };
  }

  const check_opening_entry = () => {
    fetch_opening_entry().then((r) => {
        if (r.message.length) {
          setPosOpening(r.message[0]);
          initialize_Invoice();
        } else {
          create_opening_voucher();
        }
    });
  }

  const initialize_Invoice = async () => {
    if (!posFrm.value || posFrm.value.is_new()) {
      make_new_invoice().then(() => {
        // isLoading.value = false;
        activeTab.value = 'pos';
        fetchCustomers()
      })
    } else {
      activeTab.value = 'pos';
      fetchCustomers()
      customer.value = posFrm.value.doc.customer;
    }
    searchItems();
  };

  if(!pos_opening.value) {
    check_opening_entry()
  }
  else{
    initialize_Invoice();
  }

  
</script>

<template>
  <v-main class="pos-view pa-3 pa-md-6">
    <v-row class="pos-shell" align="stretch">
      <v-col cols="12">
        <v-card class="pos-panel mb-4" rounded="xl" variant="flat">
          <v-card-item class="pb-2">
            <v-tabs
              v-model="activeTab"
              color="primary"
              fixed-tabs
              class="pos-tabs"
            >
              <v-tab value="pos">{{ __('POS') }}
                <v-chip v-if="isReturnInvoice" class="ml-1" size="x-small" density="comfortable" color="error" variant="tonal">
                  {{ __('Return') }}
                </v-chip>
              </v-tab>
              <v-tab value="checkout" :disabled="!hasCartItems">{{ __('Checkout') }}</v-tab>
            </v-tabs>
          </v-card-item>
        </v-card>
      </v-col>

      <v-col cols="12">
        <v-window v-model="activeTab">
          <v-window-item value="pos">
            <v-row class="pos-content" dense align="stretch">
              <v-col cols="12" lg="8">
                <v-card class="pos-panel h-90" rounded="xl" variant="flat" :disabled="isReturnInvoice">
                  <v-card-item class="pb-1">
                    <div class="text-subtitle-1 font-weight-bold">{{ __('Browse Items') }}</div>
                  </v-card-item>
                  <v-card-text>
                    <FiltersSection
                      :customFilters="posProfileData.custom_filters"
                      :allowedItemGroups="posProfileData.item_groups"
                      @getItems="searchItems"
                    />
                    <ItemsList :items="items"/>
                  </v-card-text>
                </v-card>
              </v-col>

              <v-col cols="12" lg="4">
                <v-card class="pos-panel h-40" rounded="xl" variant="flat">
                  <v-card-text>
                    <v-combobox
                      v-model="customer"
                      :items="customers"
                      item-title="name"
                      item-value="name"
                      :search="customerSearch"
                      @update:search="customerSearch = $event"
                      @update:model-value="updateSelection"
                      variant="solo-filled"
                      density="comfortable"
                      rounded="lg"
                      :loading="loading"
                      :rules="[customers.length == 0 ? () => 'No customers found' : () => true]"
                      :disabled="isReturnInvoice"
                    >
                      <template #append-inner>
                        <v-btn
                          icon="mdi-plus"
                          size="small"
                          variant="text"
                          @click.stop="openAddCustomerDialog"
                        />
                      </template>
                    </v-combobox>

                    <Cart @checkout="prepareCheckout" />

                    <v-card class="section-card mt-4" rounded="lg" variant="outlined">
                      <v-card-text class="pt-4">
                        <div class="actions-wrap">
                          <v-btn
                            block
                            color="primary"
                            variant="elevated"
                            rounded="lg"
                            prepend-icon="mdi-printer"
                            @click="printLastInvoice()"
                          >
                            {{ __('Print Last Invoice') }}
                          </v-btn>

                          <v-btn
                            block
                            color="secondary"
                            variant="tonal"
                            rounded="lg"
                            @click="showLoadInvoiceDialog()"
                          >
                            {{ __('Load') }}
                          </v-btn>

                          <v-btn
                            block
                            color="secondary"
                            variant="tonal"
                            rounded="lg"
                            @click="showLoadInvoiceDialog(true)"
                          >
                            {{ __('Load SO') }}
                          </v-btn>

                          <v-btn
                            block
                            color="warning"
                            variant="tonal"
                            rounded="lg"
                            :disabled="!hasCartItems"
                            @click="saveAsSalesOrder()"
                          >
                            {{ __('Save SO') }}
                          </v-btn>

                          <v-btn
                            block
                            color="primary"
                            variant="tonal"
                            rounded="lg"
                            :disabled="!hasCartItems"
                            @click="posFrm.save()"
                          >
                            {{ __('Save') }}
                          </v-btn>

                          <v-btn
                            block
                            color="info"
                            variant="tonal"
                            rounded="lg"
                            @click="resetForm()"
                          >
                            {{ __('New') }}
                          </v-btn>
                        </div>
                      </v-card-text>
                    </v-card>
                  </v-card-text>
                </v-card>
              </v-col>
            </v-row>
          </v-window-item>

          <v-window-item value="checkout">
            <v-row justify="center">
              <v-col cols="12" md="9" lg="8">
                <v-card class="pos-panel" rounded="xl" variant="flat">
                  <v-card-item class="pb-1">
                    <div class="text-overline text-medium-emphasis">{{ __('Invoice Settlement') }}</div>
                    <div class="text-h6 font-weight-bold">{{ __('Checkout') }}</div>
                  </v-card-item>

                  <v-card-text>
                    <v-card class="section-card" rounded="lg" variant="outlined">
                      <v-card-text>
                        <v-list class="checkout-list">
                          <v-list-item
                            v-for="payment in posPayments"
                            :key="payment.idx"
                            class="border-b"
                          >
                            <v-row align="center" dense>
                              <v-col cols="12" sm="5" align-self="center" align="start">
                                {{ payment.mode_of_payment }}
                              </v-col>
                              <v-col cols="9" sm="5" align-self="center" align="end">
                                <v-number-input
                                  class="mt-2"
                                  v-model="payment.amount"
                                  control-variant="hidden"
                                  variant="outlined"
                                  density="compact"
                                  :precision="2"
                                  :label="priceListCurrency"
                                  @change="changePaymentAmount(payment.item_name)"
                                />
                              </v-col>
                              <v-col cols="3" sm="2" align-self="center" align="end">
                                <v-btn
                                  icon="mdi-cash-marker"
                                  variant="text"
                                  color="primary"
                                  @click="ChangePayment(payment)"
                                />
                              </v-col>
                            </v-row>
                          </v-list-item>
                        </v-list>
                      </v-card-text>
                    </v-card>

                    <v-row dense class="mt-2">
                      <v-col cols="12" sm="6" md="3">
                        <v-card class="stat-card" rounded="lg" variant="tonal" color="primary">
                          <v-card-text>
                            <div class="text-caption text-medium-emphasis">{{ __('Customer') }}</div>
                            <div class="text-body-2 font-weight-bold text-truncate">{{ posFrm?.doc?.customer_name || '' }}</div>
                          </v-card-text>
                        </v-card>
                      </v-col>
                      <v-col cols="12" sm="6" md="3">
                        <v-card class="stat-card" rounded="lg" variant="tonal" color="success">
                          <v-card-text>
                            <div class="text-caption text-medium-emphasis">{{ __('Total') }}</div>
                            <div class="text-body-2 font-weight-bold">{{ posFrm?.doc?.grand_total || 0 }} {{ posFrm?.doc?.price_list_currency || '' }}</div>
                          </v-card-text>
                        </v-card>
                      </v-col>
                      <v-col cols="12" sm="6" md="3">
                        <v-card class="stat-card" rounded="lg" variant="tonal" color="info">
                          <v-card-text>
                            <div class="text-caption text-medium-emphasis">{{ __('Paid Amount') }}</div>
                            <div class="text-body-2 font-weight-bold">{{ posFrm?.doc?.grand_total - posFrm?.doc?.outstanding_amount || 0 }} {{ posFrm?.doc?.price_list_currency || '' }}</div>
                          </v-card-text>
                        </v-card>
                      </v-col>
                      <v-col cols="12" sm="6" md="3">
                        <v-card class="stat-card" rounded="lg" variant="tonal" color="warning">
                          <v-card-text>
                            <div class="text-caption text-medium-emphasis">{{ __('Remaining') }}</div>
                            <div class="text-body-2 font-weight-bold">{{ posFrm?.doc?.outstanding_amount || 0 }} {{ posFrm?.doc?.price_list_currency || '' }}</div>
                          </v-card-text>
                        </v-card>
                      </v-col>
                    </v-row>

                    <v-row dense class="mt-3">
                      <v-col cols="12" md="4" class="ms-md-auto">
                        <v-btn
                          block
                          color="primary"
                          variant="elevated"
                          rounded="lg"
                          prepend-icon="mdi-cash-check"
                          :disabled="!hasCartItems"
                          @click="submitInvoice(true)"
                        >
                          {{ __('Pay & Print') }}
                        </v-btn>
                      </v-col>
                    </v-row>
                  </v-card-text>
                </v-card>
              </v-col>
            </v-row>
          </v-window-item>
        </v-window>
      </v-col>
    </v-row>

    <LoadInvoiceDialog
      v-model="LoadInvoiceDialogToggle"
      :invoices="heldInvoices"
      @load="load_invoice"
      @close="clearLoadInvoiceList()"
    />
  </v-main>
</template>

<style scoped>
.pos-view {
  background:
    radial-gradient(circle at top right, rgba(25, 118, 210, 0.09), transparent 42%),
    radial-gradient(circle at left bottom, rgba(76, 175, 80, 0.08), transparent 38%);
}

.pos-panel {
  border: 1px solid rgba(120, 144, 156, 0.24);
  background: linear-gradient(180deg, rgba(255, 255, 255, 0.94), rgba(248, 251, 255, 0.96));
  box-shadow: 0 10px 24px rgba(12, 28, 43, 0.08);
}

.pos-tabs :deep(.v-tab--selected) {
  font-weight: 700;
}

.section-card {
  border-color: rgba(120, 144, 156, 0.28) !important;
}

.stat-card {
  border: 1px solid rgba(120, 144, 156, 0.18);
}

.actions-wrap {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 10px;
}

.checkout-list {
  max-height: 34vh;
  overflow-y: auto;
}

@media (max-width: 1264px) {
  .actions-wrap {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 960px) {
  .pos-view {
    padding: 10px;
  }
}
</style>