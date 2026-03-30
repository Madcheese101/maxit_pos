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
  import SimpleCartItems from './components/pos/SimpleCartItems.vue';
  import LoadInvoiceDialog from './components/pos/LoadInvoiceDialog.vue';
  
  const posStore = usePosStore();
  const {posProfileData, pos_profile, pos_opening,
    posFrm, reactiveTotalQty, reactiveGrandTotal} = storeToRefs(posStore);
  const {make_new_invoice, update_cart, edit_invoice, setPosOpening, sales_order_to_invoice} = posStore;
  // Local State
  const tab = ref(1);
  const items = ref([]);
  const items_uoms = ref([]);
  const posPayments = computed(() => posFrm.value?.doc?.payments || [])
  const priceListCurrency = computed(() => posFrm.value?.doc?.price_list_currency || "")
  const customerSearch = ref('')
  const customers = ref([])
  const loading = ref(false)
  const customer = ref(posProfileData.value.customer);
  const LoadInvoiceDialogToggle = ref(false);
  const heldInvoices = ref([]);

  
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

  const addItem = async (item) => {
      update_cart({
          field: "qty",
          value: "+1",
          item: item
      });
  }

  const goToCheckout = async () => {
    tab.value = 3;
    await posFrm.value.save();
    await posFrm.value.cscript.set_default_payment(posFrm.value.doc.grand_total, true);
    posFrm.value.refresh_field("payments");
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
    frappe.show_alert({
      indicator: "green",
      message: __("Sales invoice {0} created successfully", [posFrm.value.doc.name]),
    });
    if(print) printInvoice(posFrm.value.doc.name);    
    await make_new_invoice();
    tab.value = 1;
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
      console.log("New Invoice Created");
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
          customer.value = posFrm.value.doc.customer;
        });
      }
      else{
        edit_invoice(invoice.name).then(() => {
          customer.value = posFrm.value.doc.customer;
        })
      }
  }

  const loadFromSalesOrder = () => {
    
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
        fetchCustomers()
      })
    } else {
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
    <v-app class="pos-view-container">
      <v-main class="ma-10 mt-0">
        <v-tabs v-model="tab" grow color="deep-purple-accent-4">
          <v-tab prepend-icon="mdi-package-variant" :value="1">{{__("Item")}}</v-tab>
          <v-tab prepend-icon="mdi-cart" :value="2" :class="{ 'no-click': posFrm === undefined || posFrm.doc.items.length === 0}">{{__("Cart")}} {{ posFrm ? posFrm.doc.total_qty : 0 }}</v-tab>
          <v-tab prepend-icon="mdi-credit-card-multiple" class="no-click" :value="3">{{__("Checkout")}}</v-tab>
        </v-tabs>

        <v-tabs-window v-model="tab">
          <!-- Items -->
          <v-tabs-window-item :value="1" :disabled="tab!==1">
            <v-row dense>
              <v-col cols="8">
                <FiltersSection :customFilters="posProfileData.custom_filters" 
              :allowedItemGroups="posProfileData.item_groups"
              @getItems="searchItems"/>
                <ItemsList :items="items" @addItemToCart="addItem"/>
              </v-col>
              <v-col cols="1" class="ms-0" align-self="center">
                <v-btn
                  color="deep-purple-accent-4"
                  variant="contained"
                  text="Print Last"
                  width="100%"
                  @click="printLastInvoice()"
                />
                <v-btn
                  color="deep-purple-accent-4"
                  variant="contained"
                  text="Save SO"
                  width="100%"
                  :disabled="posFrm === undefined || posFrm.doc.items.length === 0"
                  @click="saveAsSalesOrder()"
                />
                <v-btn
                  color="deep-purple-accent-4"
                  variant="contained"
                  text="Save"
                  width="100%"
                  :disabled="posFrm === undefined || posFrm.doc.items.length === 0"
                  @click="posFrm.save()"
                />
                <v-btn
                  color="deep-purple-accent-4"
                  variant="contained"
                  text="Load"
                  width="100%"
                  @click="showLoadInvoiceDialog()"
                />
                <v-btn
                  color="deep-purple-accent-4"
                  variant="contained"
                  text="Load SO"
                  width="100%"
                  @click="showLoadInvoiceDialog(true)"
                />
                <v-btn
                  color="deep-purple-accent-4"
                  variant="contained"
                  text="New"
                  width="100%"
                  @click="resetForm()"
                />
              </v-col>
              <v-col cols="3">
                <v-row dense>
                </v-row>
                <v-row dense class="m-4 mb-0 ms-0">
                  <!-- <CustomerField :defaultCustomer="posProfileData.customer"/> -->
                  <v-combobox
                    v-model="customer"
                    :items="customers"
                    item-title="name"
                    item-value="name"
                    :search="customerSearch"
                    @update:search="customerSearch = $event"
                    @update:model-value="updateSelection"
                    variant="solo"
                    :loading="loading"
                    :rules="[customers.length == 0 ? () => 'No customers found' : () => true]"
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
                  <SimpleCartItems/>
                </v-row>
              </v-col>
            </v-row>
            <LoadInvoiceDialog 
              v-model="LoadInvoiceDialogToggle" 
              :invoices="heldInvoices" 
              @load="load_invoice"
              @close="clearLoadInvoiceList()"
            />
          </v-tabs-window-item>

          <!-- Cart -->
          <v-tabs-window-item :value="2" :disabled="tab!==2">
            <Cart @checkout="goToCheckout"/>
          </v-tabs-window-item>

          <!-- Checkout -->
          <v-tabs-window-item :value="3" :disabled="tab!==2">
            <VCard rounded="lg" class="ma-auto" min-height="70vh" width="80%" flat>
              <v-row>
                <v-col cols="10">
                  <v-list>
                    <v-list-item
                        v-for="payment in posPayments"
                        :key="payment.idx"
                        class="border-b"
                    >
                      <v-row align="center">
                      <!-- Payment Mode Name -->
                      <v-col cols="5" align-self="center" fill-height align="start">
                          {{ payment.mode_of_payment }}
                      </v-col>
                      <!-- Amnount Input -->
                      <v-col cols="2" align-self="center" align="end">
                          <v-number-input
                          class="mt-3"
                          v-model="payment.amount"
                          control-variant="hidden"
                          variant="outlined"
                          density="compact"
                          :precision="2"
                          :label="priceListCurrency"
                          @change="changePaymentAmount(payment.item_name)"
                          />
                      </v-col>
                      <!-- Set All here Button -->
                      <v-col cols="1" align-self="center" class="text-right" align="end">
                          <v-btn
                          icon="mdi-cash-marker"
                          variant="text"
                          @click="ChangePayment(payment)"
                          />
                      </v-col>
                      </v-row>
                    </v-list-item>
                  </v-list>
                </v-col>
                <v-col>
                  <div>{{ __('Customer') }}: {{ posFrm.doc.customer_name }}</div>
                  <div>{{__("Total")}}: {{posFrm.doc.grand_total}} {{posFrm.doc.price_list_currency}}</div>
                  <div>{{__("Paid Amount")}}: {{ posFrm.doc.paid_amount }} {{posFrm.doc.price_list_currency}}</div>
                  <div>{{ __("Remaining Amount") }}: {{posFrm.doc.outstanding_amount}} {{posFrm.doc.price_list_currency}}</div>
                  <v-btn
                    class="ma-5"
                    color="deep-purple-accent-4"
                    variant="contained"
                    @click="submitInvoice(true)"
                  >
                    {{ __("Pay & Print") }}
                  </v-btn>
                </v-col>
              </v-row>
            </VCard>
          </v-tabs-window-item>
        </v-tabs-window>
      </v-main>
    </v-app>
</template>

<style scoped>
  .container1 {
    margin-top: 0px;
  }
  .pos-view-container{
    background: #edf2f5;
  }
  .no-click {
    pointer-events: none;
  }
</style>