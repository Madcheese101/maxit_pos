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
  import PageSurface from './components/ui/PageSurface.vue';
  import SurfaceCard from './components/ui/SurfaceCard.vue';
  import StatMetricCard from './components/ui/StatMetricCard.vue';
  
  const posStore = usePosStore();
  const {posProfileData, pos_profile, pos_opening, posFrm, returnAgainst} = storeToRefs(posStore);
  const {make_new_invoice, update_cart, edit_invoice, setPosOpening, sales_order_to_invoice, buildPrintViewUrl, toggle_is_return} = posStore;
  // Local State
  const activeTab = ref('pos')
  const customerSearch = ref('')
  const items = ref([]);
  const ITEM_VIEW_MODE_STORAGE_KEY = 'maxit-pos-item-view-mode';
  const getSavedItemViewMode = () => {
    try {
      const savedViewMode = window.localStorage.getItem(ITEM_VIEW_MODE_STORAGE_KEY);
      return ["grid", "list"].includes(savedViewMode) ? savedViewMode : "grid";
    } catch (error) {
      return "grid";
    }
  };
  const itemViewMode = ref(getSavedItemViewMode());
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

  const isLinkedReturn = computed(() => isReturnInvoice.value && returnAgainst.value);

  const isReturn = computed({
    get: () => !!posFrm.value?.doc?.is_return,
    set: (val) => toggle_is_return(val),
  });

  const salesPersonOptions = ref([]);
  const salesPersonLoading = ref(false);
  const salesPersonSearch = ref('');

  const showSalesPerson = computed(() => !!posProfileData.value?.allow_set_sales_person);
  const salesPersonRequired = computed(() => !!posProfileData.value?.sales_person_is_mandatory);
  const salesPersonUsers = computed(() =>
    (posProfileData.value?.applicable_for_users || []).map(r => r.user).filter(Boolean));
  const salesPerson = computed({
    get: () => posFrm.value?.doc?.sales_person || null,
    set: (val) => { if (posFrm.value) posFrm.value.doc.sales_person = val || ''; },
  });
  const salesPersonRules = computed(() =>
    salesPersonRequired.value ? [v => !!v || __('Sales Person is required')] : []);

  const loadSalesPersonOptions = async (search = '') => {
    salesPersonLoading.value = true;
    try {
      const response = await frappe.call({
        method: 'maxit_pos.maxit_pos.api.custom_search_link',
        args: {
          doctype: 'Employee',
          txt: search || '',
          page_length: 20,
          ignore_user_permissions: 1,
          reference_doctype: 'Sales Invoice',
          link_fieldname: 'sales_person',
          label_fieldname: 'employee_name',
          filters: { user_id: ['in', salesPersonUsers.value] },
        },
      });
      salesPersonOptions.value = (response.message || []).map(item => ({
        value: item.value,
        label: item.label || item.value,
        description: item.description || '',
      }));
    } catch (error) {
      frappe.msgprint({ title: __('Sales Person search failed'), indicator: 'red', message: error?.message || String(error) });
    } finally {
      salesPersonLoading.value = false;
    }
  };

  // make sure the currently selected employee is present in the options so the
  // autocomplete can render its label (e.g. when loaded from a return invoice)
  const ensureSalesPersonOption = async (employee) => {
    if (!employee) return;
    if (salesPersonOptions.value.some(o => o.value === employee)) return;
    const employee_name = await frappe.db.get_value('Employee', employee, 'employee_name')
      .then(r => r?.message?.employee_name)
      .catch(() => null);
    salesPersonOptions.value = [
      { value: employee, label: employee_name || employee, description: '' },
      ...salesPersonOptions.value,
    ];
  };

  let salesPersonTimeout;
  watch(salesPersonSearch, (val) => {
    clearTimeout(salesPersonTimeout);
    salesPersonTimeout = setTimeout(() => loadSalesPersonOptions(val), 300);
  });
  if (showSalesPerson.value) loadSalesPersonOptions();

  // when a return invoice loads its source's sales person, surface it in the field
  watch(() => posFrm.value?.doc?.sales_person, (val) => {
    if (showSalesPerson.value) ensureSalesPersonOption(val);
  });

  const customerRules = computed(() => [
    () => customers.value.length > 0 || __('No customers found'),
  ]);

  const searchItems = async (filters) => {
    const search_term = filters ? filters.search_term : "";
    const item_group = filters ? filters.item_group : null;
    const custom_filters = filters ? filters.filters : [];
    let isReturn = 0;
    if(isReturnInvoice.value){
      isReturn = returnAgainst.value ? 1 : 0;
    };
    console.log("isReturn:", isReturn);
    const response = await frappe.call({
			method: "maxit_pos.maxit_pos.page.maxit_pos.api.api.get_items",
			freeze: true,
			args: {pos_profile_data: posProfileData.value,
        search_term: search_term,
        item_group: item_group,
        custom_filters: custom_filters,
        is_return: isReturn},
      });
    // items.value = response.message.items;
    items.value = response.message[0];
    items_uoms.value = response.message[1];
  };

  // re-fetch items when toggling return so unavailable items become listable
  watch(isReturnInvoice, () => {
    if (returnAgainst.value) return;
    searchItems()
  });

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

  watch(itemViewMode, (value) => {
    try {
      window.localStorage.setItem(ITEM_VIEW_MODE_STORAGE_KEY, value);
    } catch (error) {
      console.warn('Unable to persist POS item view mode.', error);
    }
  })

  const openAddCustomerDialog = () => {
  //   frappe.new_doc('Customer')
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
    if (!validate()) return;
    const save_error = await posFrm.value.save();
    if(save_error) return;
    await posFrm.value.cscript.set_default_payment(posFrm.value.doc.grand_total, true);
    posFrm.value.refresh_field("payments");
    activeTab.value = 'checkout';
  }

  const validate = () => {
    var value = true;
    posFrm.value.doc.items.forEach((item, index) => {
      if(!item.item_code) {
        frappe.show_alert({
          indicator: "red",
          message: __("Item code is required for item at row {0}", [item.idx]),
        });
        value = false;
      }
      if(item.rate == undefined || item.rate == 0) {
        frappe.show_alert({
          indicator: "red",
          message: __("Rate is required for item at row {0}", [item.idx]),
        });
        value = false;
      }
      if(item.max_discount && item.discount_percentage > item.max_discount) {
        frappe.show_alert({
          indicator: "red",
          message: __("Discount for item at row {0} cannot exceed {1}%", [item.idx, item.max_discount]),
        });
        value = false;
      }
    });
    if (salesPersonRequired.value && !posFrm.value.doc.sales_person) {
      frappe.show_alert({ indicator: 'red', message: __('Sales Person is required') });
      value = false;
    }
    return value;
  }

  const changePaymentAmount = async (item_name) => {
    if (isReturnInvoice.value) {
      const payment = posPayments.value.find(p => p.item_name === item_name);
      if (payment && Number(payment.amount) > 0) {
        payment.amount = 0;
        frappe.show_alert({ indicator: "red", message: __("Return payment amount cannot be positive") });
      }
    }
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
    const printFormat = posProfileData.value?.print_format || 'Standard';
    const letterHead = posProfileData.value?.letter_head || 'No Letterhead';
    const no_letterhead = letterHead === 'No Letterhead' ? 1 : 0;
    const printUrl = buildPrintViewUrl({
      doctype,
      name: invoice,
      format: printFormat,
      no_letterhead,
      letterhead: letterHead,
    });
    window.open(printUrl, '_blank');
  }

  const printLastInvoice = () => {
    frappe.call({
      method: "maxit_pos.maxit_pos.page.maxit_pos.api.api.get_last_invoice_for_print",
      args: {
        pos_profile: pos_profile.value,
        creator_only: posProfileData.value.print_last_invoice_for_creator_only
      },
      freeze: true,
    }).then((response) => {
      const last_invoice = response.message;
      if(last_invoice) printInvoice(last_invoice);
      else frappe.show_alert({
        indicator: "blue",
        message: __("No previous invoice found for this POS Profile."),
      });
    });
  }

  const resetForm = () => {
    make_new_invoice().then(() => {
      // isLoading.value = false;
      activeTab.value = 'pos';
      customer.value = posFrm.value.doc.customer;
      fetchCustomers()
      searchItems();
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
  <PageSurface glow="info-success" class="pos-view pa-3 pa-md-6">
    <SurfaceCard class="pos-panel">
      <v-card-item class="pb-1">
        <v-tabs
          v-model="activeTab"
          color="primary"
          fixed-tabs
          class="pos-tabs"
        >
          <v-tab value="pos">{{ __('POS') }}
            <v-chip v-if="isReturnInvoice" class="ms-1" size="x-small" density="comfortable" color="error" variant="tonal">
              {{ __('Return') }}
            </v-chip>
          </v-tab>
          <v-tab value="checkout" :disabled="!hasCartItems">{{ __('Checkout') }}</v-tab>
        </v-tabs>
      </v-card-item>
    </SurfaceCard>

    <v-window v-model="activeTab" class="mt-3">
          <v-window-item value="pos">
            <v-row class="pos-content" dense>
              <v-col cols="12" lg="6">
                <SurfaceCard class="pos-panel items-side-panel" :disabled="isLinkedReturn">
                  <v-card-text class="items-panel-body">
                    <FiltersSection
                      :customFilters="posProfileData.custom_filters"
                      :allowedItemGroups="posProfileData.item_groups"
                      :posProfile="pos_profile"
                      @getItems="searchItems"
                    />
                    <div class="items-toolbar">
                      <div class="text-caption text-medium-emphasis">{{ __('Item View') }}</div>
                      <v-btn-toggle
                        v-model="itemViewMode"
                        color="primary"
                        density="comfortable"
                        mandatory
                        rounded="lg"
                        variant="outlined"
                      >
                        <v-btn value="grid" icon="mdi-view-grid-outline" :aria-label="__('Card View')" />
                        <v-btn value="list" icon="mdi-format-list-bulleted" :aria-label="__('List View')" />
                      </v-btn-toggle>
                    </div>
                    <ItemsList :items="items" :view-mode="itemViewMode"/>
                  </v-card-text>
                </SurfaceCard>
              </v-col>

              <v-col cols="12" lg="6">
                <SurfaceCard class="pos-panel cart-side-panel">
                  <v-card-text>
                    <div class="d-flex align-center ga-3 mb-1 flex-wrap">
                      <v-combobox
                        v-model="customer"
                        :items="customers"
                        item-title="customer_name"
                        item-value="name"
                        :label="__('Customer')"
                        :search="customerSearch"
                        @update:search="customerSearch = $event"
                        @update:model-value="updateSelection"
                        variant="solo-filled"
                        density="comfortable"
                        rounded="lg"
                        :loading="loading"
                        :rules="customerRules"
                        :disabled="isLinkedReturn"
                        class="flex-grow-1"
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
                      <v-autocomplete
                        v-if="showSalesPerson"
                        v-model="salesPerson"
                        :items="salesPersonOptions"
                        item-title="label"
                        item-value="value"
                        :label="__('Sales Person')"
                        :search="salesPersonSearch"
                        @update:search="salesPersonSearch = $event"
                        variant="solo-filled"
                        density="comfortable"
                        rounded="lg"
                        hide-details="auto"
                        :loading="salesPersonLoading"
                        :rules="salesPersonRules"
                        class="flex-grow-1"
                      />
                      <v-checkbox
                        v-if="posProfileData?.allow_unlinked_return_invoice"
                        v-model="isReturn"
                        :label="__('Is Return')"
                        color="error"
                        density="comfortable"
                        hide-details
                        :disabled="isLinkedReturn"
                        class="flex-grow-0"
                      />
                    </div>

                    <Cart @checkout="prepareCheckout" />

                    <SurfaceCard surface="section" class="section-card mt-2">
                      <v-card-text class="pt-4">
                        <v-defaults-provider :defaults="{ VBtn: { block: true, rounded: 'lg' } }">
                        <div class="actions-wrap">
                          <v-btn
                            v-if="posProfileData?.allow_print_last_invoice"
                            color="primary"
                            variant="elevated"
                            prepend-icon="mdi-printer"
                            @click="printLastInvoice()"
                          >
                            {{ __('Print Last Invoice') }}
                          </v-btn>

                          <v-btn
                            color="secondary"
                            variant="tonal"
                            @click="showLoadInvoiceDialog()"
                          >
                            {{ __('Load') }}
                          </v-btn>

                          <v-btn
                            v-if="posProfileData?.allow_sales_order"
                            color="secondary"
                            variant="tonal"
                            @click="showLoadInvoiceDialog(true)"
                          >
                            {{ __('Load SO') }}
                          </v-btn>

                          <v-btn
                            v-if="posProfileData?.allow_sales_order"
                            color="warning"
                            variant="tonal"
                            :disabled="!hasCartItems"
                            @click="saveAsSalesOrder()"
                          >
                            {{ __('Save SO') }}
                          </v-btn>

                          <v-btn
                            color="primary"
                            variant="tonal"
                            :disabled="!hasCartItems"
                            @click="posFrm.save()"
                          >
                            {{ __('Save') }}
                          </v-btn>

                          <v-btn
                            color="info"
                            variant="tonal"
                            @click="resetForm()"
                          >
                            {{ __('New') }}
                          </v-btn>
                        </div>
                    </v-defaults-provider>
                      </v-card-text>
                    </SurfaceCard>
                  </v-card-text>
                </SurfaceCard>
              </v-col>
            </v-row>
          </v-window-item>

          <v-window-item value="checkout">
            <v-row justify="center">
              <v-col cols="12" md="9" lg="8">
                <SurfaceCard class="pos-panel checkout-panel">
                  <v-card-item class="pb-1">
                    <div class="text-overline text-medium-emphasis">{{ __('Invoice Settlement') }}</div>
                    <div class="text-h6 font-weight-bold">{{ __('Checkout') }}</div>
                  </v-card-item>

                  <v-card-text>
                    <SurfaceCard surface="section" class="section-card">
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
                                  :max="isReturnInvoice ? 0 : undefined"
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
                    </SurfaceCard>

                    <v-row dense class="mt-2">
                      <v-col cols="12" sm="6" md="3">
                        <StatMetricCard
                          class="stat-card"
                          color="primary"
                          :label="__('Customer')"
                          :value="posFrm?.doc?.customer_name || ''"
                          truncate
                          compact
                        />
                      </v-col>
                      <v-col cols="12" sm="6" md="3">
                        <StatMetricCard
                          class="stat-card"
                          color="success"
                          :label="__('Total')"
                          :value="`${posFrm?.doc?.grand_total || 0} ${posFrm?.doc?.price_list_currency || ''}`"
                          compact
                        />
                      </v-col>
                      <v-col cols="12" sm="6" md="3">
                        <StatMetricCard
                          class="stat-card"
                          color="info"
                          :label="__('Paid Amount')"
                          :value="`${(posFrm?.doc?.grand_total || 0) - (posFrm?.doc?.outstanding_amount || 0)} ${posFrm?.doc?.price_list_currency || ''}`"
                          compact
                        />
                      </v-col>
                      <v-col cols="12" sm="6" md="3">
                        <StatMetricCard
                          class="stat-card"
                          color="warning"
                          :label="__('Remaining')"
                          :value="`${posFrm?.doc?.outstanding_amount || 0} ${posFrm?.doc?.price_list_currency || ''}`"
                          compact
                        />
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
                </SurfaceCard>
              </v-col>
            </v-row>
          </v-window-item>
        </v-window>

    <LoadInvoiceDialog
      v-model="LoadInvoiceDialogToggle"
      :invoices="heldInvoices"
      @load="load_invoice"
      @close="clearLoadInvoiceList()"
    />
  </PageSurface>
</template>

<style scoped>
.pos-view {
  background:
    radial-gradient(circle at top right, var(--v-pos-info-glow), transparent 42%),
    radial-gradient(circle at left bottom, var(--v-pos-success-glow), transparent 38%);
}

.pos-panel {
  border: 1px solid var(--v-pos-panel-border);
  background: var(--v-pos-panel-background);
  box-shadow: var(--v-pos-panel-shadow);
  transition: var(--v-theme-transition);
}

.pos-tabs :deep(.v-tab--selected) {
  font-weight: 700;
}

.section-card {
  border-color: var(--v-pos-panel-border-strong) !important;
}

.stat-card {
  border: 1px solid var(--v-pos-panel-border-soft);
  transition: var(--v-theme-transition);
}

.actions-wrap {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 10px;
}

.items-side-panel {
  max-height: clamp(360px, 78dvh, 1100px);
  display: flex;
  flex-direction: column;
  min-height: 0;
}

.items-panel-body {
  display: flex;
  flex-direction: column;
  flex: 1;
  min-height: 0;
}

.cart-side-panel {
  max-height: clamp(380px, 80dvh, 1100px);
  overflow-y: auto;
}

.checkout-list {
  max-height: clamp(180px, 34dvh, 520px);
  overflow-y: auto;
}

.items-toolbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  margin: 8px 0 16px;
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

  .items-toolbar {
    align-items: stretch;
    flex-direction: column;
  }
}
</style>