<script setup>
  $('.body-sidebar-container').removeClass('expanded');
  const frappe_ = frappe;
  const __ = window.__;
  
  import {storeToRefs} from 'pinia';
  import { ref, computed, watch } from 'vue'
  import { useDisplay } from 'vuetify';
  import { usePosStore } from '../store/posStore';
  import Cart from './components/pos/Cart.vue';
  import ItemsList from './components/pos/ItemsList.vue';
  import FiltersSection from './components/pos/FiltersSection.vue';
  import LoadInvoiceDialog from './components/pos/LoadInvoiceDialog.vue';
  import PageSurface from './components/ui/PageSurface.vue';
  import SurfaceCard from './components/ui/SurfaceCard.vue';
  
  const posStore = usePosStore();
  const {posProfileData, pos_profile, pos_opening, invoice, returnAgainst} = storeToRefs(posStore);
  const {make_new_invoice, update_cart, edit_invoice, setPosOpening, sales_order_to_invoice, buildPrintViewUrl, toggle_is_return, set_customer, calculate_paid_amount, save_invoice, isAppRTL} = posStore;
  // Local State
  const activeTab = ref('pos')
  // below 768px the items pane and the cart/checkout pane are shown one at a time
  const { width } = useDisplay();
  const isCompact = computed(() => width.value < 768);
  const mobilePane = ref('items');
  const backIcon = computed(() => isAppRTL() ? 'mdi-arrow-right' : 'mdi-arrow-left');
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
  const posPayments = computed(() => invoice.value?.payments || [])
  const priceListCurrency = computed(() => invoice.value?.currency || "")
  const hasCartItems = computed(() => (invoice.value?.items || []).length > 0)
  const cartCount = computed(() => (invoice.value?.items || []).length)
  const amountDue = computed(() => invoice.value?.rounded_total || invoice.value?.grand_total || 0)
  const formatCurrency = (value) => format_currency(value || 0, priceListCurrency.value);
  const isReturnInvoice = computed(() => {
    return invoice.value?.is_return || false;
  });

  const isLinkedReturn = computed(() => isReturnInvoice.value && returnAgainst.value);

  const isReturn = computed({
    get: () => !!invoice.value?.is_return,
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
    get: () => invoice.value?.sales_person || null,
    set: (val) => { if (invoice.value) invoice.value.sales_person = val || ''; },
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
  watch(() => invoice.value?.sales_person, (val) => {
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
    const response = await frappe.call({
			method: "maxit_pos.maxit_pos.page.maxit_pos.api.api.get_items",
			freeze: true,
			// list prices from the invoice's price list (customer specific when set)
			args: {pos_profile_data: {...posProfileData.value, selling_price_list: invoice.value?.selling_price_list || posProfileData.value.selling_price_list},
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

  // re-fetch items when the customer changes the invoice price list
  watch(() => invoice.value?.selling_price_list, (val, oldVal) => {
    if (oldVal) searchItems();
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
    if(val == invoice.value.customer) return;
    await set_customer(val?.name || '');
  }

  const prepareCheckout = async () => {
    if (!hasCartItems.value) return;
    if (!validate()) return;
    activeTab.value = 'checkout';
    mobilePane.value = 'side';
  }

  const validate = () => {
    var value = true;
    invoice.value.items.forEach((item, index) => {
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
    if (salesPersonRequired.value && !invoice.value.sales_person) {
      frappe.show_alert({ indicator: 'red', message: __('Sales Person is required') });
      value = false;
    }
    return value;
  }

  const changePaymentAmount = (payment) => {
    if (isReturnInvoice.value && Number(payment.amount) > 0) {
      payment.amount = 0;
      frappe.show_alert({ indicator: "red", message: __("Return payment amount cannot be positive") });
    }
    calculate_paid_amount();
  }

  const ChangePayment = (item) => {
      item.amount = amountDue.value;
      posPayments.value.forEach(payment => {
        if (payment !== item) {
          payment.amount = 0;
        }
      });
      calculate_paid_amount();
  }

  const submitInvoice = (print=false) => {
    frappe.confirm(__("Permanently Submit {0}?", [invoice.value.name || __("Sales Invoice")]), async () => {
      // Standalone return left fully unpaid: clear payments so ERPNext's
      // set_total_amount_to_default_mop (runs on the submit-time recalc) has no
      // default row to refill, leaving the return as an outstanding credit note
      // instead of auto-refunding the total to the default mode of payment.
      if (isReturnInvoice.value) {
        const enteredPaid = posPayments.value.reduce((sum, p) => sum + (Number(p.amount) || 0), 0);
        if (!enteredPaid) invoice.value.payments = [];
      }
      const doc = await save_invoice(1);
      activeTab.value = 'pos';
      mobilePane.value = 'items';
      frappe.show_alert({
        indicator: "green",
        message: __("Sales invoice {0} created successfully", [doc.name]),
      });
      if(print) printInvoice(doc.name);
      await make_new_invoice();
      await fetchCustomers();
    });
  }

  const saveInvoice = async () => {
    await save_invoice();
    frappe.show_alert({ indicator: "green", message: __("Saved") });
  }

  const saveAsSalesOrder = async () => {
    await save_invoice();
    frappe.call({
      method: "maxit_pos.maxit_pos.page.maxit_pos.api.api.save_invoice_as_sales_order",
      args: {
        invoice_name: invoice.value.name
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
      mobilePane.value = 'items';
      customer.value = invoice.value.customer;
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
          customer.value = posStore.invoice.customer;
        });
      }
      else{
        edit_invoice(invoice.name).then(() => {
          activeTab.value = 'pos';
          customer.value = posStore.invoice.customer;
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
    if (!invoice.value) {
      make_new_invoice().then(() => {
        // isLoading.value = false;
        activeTab.value = 'pos';
        fetchCustomers()
      })
    } else {
      activeTab.value = 'pos';
      fetchCustomers()
      customer.value = invoice.value.customer;
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
  <PageSurface glow="info-success" class="pos-view pa-2">
    <div class="pos-layout" :class="{ 'pos-layout--compact': isCompact }">
      <SurfaceCard
        v-show="!isCompact || mobilePane === 'items'"
        class="pos-pane pos-pane--items"
        :disabled="isLinkedReturn"
      >
        <div class="pos-pane__body">
          <FiltersSection
            :customFilters="posProfileData.custom_filters"
            :allowedItemGroups="posProfileData.item_groups"
            :posProfile="pos_profile"
            @getItems="searchItems"
          >
            <v-btn
              :icon="itemViewMode === 'grid' ? 'mdi-format-list-bulleted' : 'mdi-view-grid-outline'"
              size="small"
              variant="tonal"
              :title="itemViewMode === 'grid' ? __('List View') : __('Card View')"
              :aria-label="itemViewMode === 'grid' ? __('List View') : __('Card View')"
              @click="itemViewMode = itemViewMode === 'grid' ? 'list' : 'grid'"
            />
          </FiltersSection>
          <ItemsList :items="items" :view-mode="itemViewMode"/>
        </div>
      </SurfaceCard>

      <SurfaceCard
        v-show="!isCompact || mobilePane === 'side'"
        class="pos-pane pos-pane--side"
      >
        <div v-if="activeTab === 'pos'" class="pos-pane__body">
          <div class="side-header">
            <v-btn
              v-if="isCompact"
              :icon="backIcon"
              size="small"
              variant="text"
              :aria-label="__('Back')"
              @click="mobilePane = 'items'"
            />
            <div class="side-header__title">
              {{ __('Cart') }}
              <v-chip v-if="isReturnInvoice" size="x-small" color="error" variant="tonal">
                {{ __('Return') }}
              </v-chip>
            </div>
            <v-spacer />
            <v-btn
              icon="mdi-file-document-plus-outline"
              size="small"
              variant="text"
              :title="__('New')"
              :aria-label="__('New')"
              @click="resetForm()"
            />
            <v-btn
              icon="mdi-content-save-outline"
              size="small"
              variant="text"
              :disabled="!hasCartItems"
              :title="__('Save')"
              :aria-label="__('Save')"
              @click="saveInvoice()"
            />
            <v-btn
              icon="mdi-folder-open-outline"
              size="small"
              variant="text"
              :title="__('Load')"
              :aria-label="__('Load')"
              @click="showLoadInvoiceDialog()"
            />
            <v-menu v-if="posProfileData?.allow_print_last_invoice || posProfileData?.allow_sales_order">
              <template #activator="{ props: menuProps }">
                <v-btn
                  v-bind="menuProps"
                  icon="mdi-dots-vertical"
                  size="small"
                  variant="text"
                  :aria-label="__('More')"
                />
              </template>
              <v-list density="compact">
                <v-list-item
                  v-if="posProfileData?.allow_print_last_invoice"
                  prepend-icon="mdi-printer"
                  :title="__('Print Last Invoice')"
                  @click="printLastInvoice()"
                />
                <v-list-item
                  v-if="posProfileData?.allow_sales_order"
                  prepend-icon="mdi-folder-download-outline"
                  :title="__('Load SO')"
                  @click="showLoadInvoiceDialog(true)"
                />
                <v-list-item
                  v-if="posProfileData?.allow_sales_order"
                  prepend-icon="mdi-content-save-move-outline"
                  :title="__('Save SO')"
                  :disabled="!hasCartItems"
                  @click="saveAsSalesOrder()"
                />
              </v-list>
            </v-menu>
          </div>

          <div class="side-fields">
            <v-combobox
              v-model="customer"
              :items="customers"
              item-title="customer_name"
              item-value="name"
              :label="__('Customer')"
              :search="customerSearch"
              @update:search="customerSearch = $event"
              @update:model-value="updateSelection"
              variant="outlined"
              density="compact"
              :loading="loading"
              :rules="customerRules"
              :disabled="isLinkedReturn"
              class="side-fields__customer"
            >
              <template #append-inner>
                <v-btn
                  icon="mdi-plus"
                  size="x-small"
                  variant="text"
                  :aria-label="__('New')"
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
              variant="outlined"
              density="compact"
              hide-details="auto"
              :loading="salesPersonLoading"
              :rules="salesPersonRules"
              class="side-fields__customer"
            />
            <v-checkbox
              v-if="posProfileData?.allow_unlinked_return_invoice"
              v-model="isReturn"
              :label="__('Is Return')"
              color="error"
              density="compact"
              hide-details
              :disabled="isLinkedReturn"
              class="flex-grow-0"
            />
          </div>

          <Cart @checkout="prepareCheckout" />
        </div>

        <div v-else class="pos-pane__body">
          <div class="side-header">
            <v-btn
              :icon="backIcon"
              size="small"
              variant="text"
              :aria-label="__('Back')"
              @click="activeTab = 'pos'"
            />
            <div class="side-header__title">{{ __('Checkout') }}</div>
          </div>

          <div class="checkout-due">
            <div class="text-caption text-medium-emphasis text-truncate">{{ invoice?.customer_name || '' }}</div>
            <div class="checkout-due__amount">{{ formatCurrency(amountDue) }}</div>
          </div>

          <div class="checkout-payments">
            <div v-for="payment in posPayments" :key="payment.idx" class="payment-row">
              <div class="payment-row__mode">{{ payment.mode_of_payment }}</div>
              <v-number-input
                v-model="payment.amount"
                control-variant="hidden"
                variant="outlined"
                density="compact"
                :precision="2"
                :max="isReturnInvoice ? 0 : undefined"
                hide-details
                class="payment-row__input"
                @change="changePaymentAmount(payment)"
              />
              <v-btn
                icon="mdi-cash-marker"
                variant="text"
                color="primary"
                size="small"
                :title="__('Pay full amount')"
                :aria-label="__('Pay full amount')"
                @click="ChangePayment(payment)"
              />
            </div>
          </div>

          <div class="checkout-summary">
            <div class="checkout-summary__row">
              <span>{{ __('Paid Amount') }}</span>
              <span>{{ formatCurrency(invoice?.paid_amount) }}</span>
            </div>
            <div class="checkout-summary__row checkout-summary__row--strong">
              <span>{{ __('Remaining') }}</span>
              <span>{{ formatCurrency(invoice?.outstanding_amount) }}</span>
            </div>
            <div v-if="invoice?.change_amount" class="checkout-summary__row text-success">
              <span>{{ __('Change Due') }}</span>
              <span>{{ formatCurrency(invoice.change_amount) }}</span>
            </div>
          </div>

          <v-btn
            block
            size="large"
            color="primary"
            variant="elevated"
            prepend-icon="mdi-cash-check"
            class="flex-grow-0"
            :disabled="!hasCartItems"
            @click="submitInvoice(true)"
          >
            {{ __('Pay & Print') }}
          </v-btn>
        </div>
      </SurfaceCard>
    </div>

    <div v-if="isCompact && mobilePane === 'items'" class="pos-bottom-bar">
      <v-btn variant="tonal" class="pos-bottom-bar__cart" @click="mobilePane = 'side'">
        <v-badge :content="cartCount" :model-value="cartCount > 0" color="primary">
          <v-icon icon="mdi-cart-outline" />
        </v-badge>
        <span class="ms-3">{{ formatCurrency(invoice?.grand_total) }}</span>
      </v-btn>
      <v-btn
        color="success"
        variant="elevated"
        :disabled="!hasCartItems"
        @click="prepareCheckout()"
      >
        {{ __('Checkout') }}
      </v-btn>
    </div>

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

.pos-layout {
  display: flex;
  gap: 8px;
  flex: 1;
  min-height: 0;
}

.pos-pane {
  display: flex;
  flex-direction: column;
  min-height: 0;
  border: 1px solid var(--v-pos-panel-border);
  background: var(--v-pos-panel-background);
  box-shadow: var(--v-pos-panel-shadow);
  transition: var(--v-theme-transition);
}

.pos-pane--items {
  flex: 1;
  min-width: 0;
}

.pos-pane--side {
  flex: 0 0 clamp(320px, 34%, 420px);
}

.pos-layout--compact .pos-pane--side {
  flex: 1;
}

.pos-pane__body {
  display: flex;
  flex-direction: column;
  gap: 8px;
  flex: 1;
  min-height: 0;
  padding: 10px;
}

.side-header {
  display: flex;
  align-items: center;
  gap: 2px;
  min-height: 36px;
}

.side-header__title {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 1rem;
  font-weight: 700;
  padding-inline: 4px;
}

.side-fields {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 8px;
}

.side-fields__customer {
  flex: 1 1 200px;
}

.checkout-due {
  padding: 10px 12px;
  border-radius: 10px;
  background: rgba(var(--v-theme-primary), 0.08);
}

.checkout-due__amount {
  font-size: 1.5rem;
  font-weight: 800;
  line-height: 1.3;
}

.checkout-payments {
  display: flex;
  flex-direction: column;
  gap: 6px;
  min-height: 0;
  overflow-y: auto;
}

.payment-row {
  display: flex;
  align-items: center;
  gap: 8px;
}

.payment-row__mode {
  flex: 1;
  min-width: 0;
  font-size: 0.875rem;
  font-weight: 600;
}

.payment-row__input {
  flex: 0 0 120px;
}

.checkout-summary {
  display: flex;
  flex-direction: column;
  gap: 4px;
  margin-block-start: auto;
  padding-block-start: 8px;
  border-top: 1px solid var(--v-pos-panel-border-soft);
}

.checkout-summary__row {
  display: flex;
  justify-content: space-between;
  gap: 12px;
  font-size: 0.875rem;
}

.checkout-summary__row--strong {
  font-size: 1rem;
  font-weight: 700;
}

.pos-bottom-bar {
  display: flex;
  gap: 8px;
  padding-block-start: 8px;
}

.pos-bottom-bar__cart {
  flex: 1;
  justify-content: start;
}
</style>
