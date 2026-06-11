frappe.provide("frappe.MaxItPOS");
import App from '../../../maxit_pos/page/maxit_pos/app.vue';
import router from '../../../maxit_pos/page/maxit_pos/router';
import { createVuetify } from 'vuetify'
import * as components from 'vuetify/components'
import * as directives from 'vuetify/directives'
import { ar, en } from 'vuetify/locale'
import { VDateInput } from 'vuetify/labs/VDateInput'
import { VNumberInput } from 'vuetify/labs/VNumberInput'
import { createApp } from "vue";
import { createPinia } from 'pinia'
import { resolveInitialVuetifyTheme, vuetifyThemes } from '../../../maxit_pos/page/maxit_pos/themeConfig'

frappe.MaxItPOS.Controller = class {
	constructor({page, wrapper}) {
    this.$wrapper = $(wrapper);
		this.page = page;
    // $('.page-head').remove();

    this.check_opening_entry();
		// this.make_app();
	}

    make_app(posProfileData, appDefaults) {
        $('.sticky-top').remove();
        $('.body-sidebar').remove();
        $('.body-sidebar-container').remove();
        $('.body-sidebar-container').removeClass('expanded');
        this.$el = this.$wrapper.get(0);
        const appLanguage = (frappe.boot?.lang || 'en').toLowerCase();
        const vuetifyLocale = appLanguage.startsWith('ar') ? 'ar' : 'en';
        const pinia = createPinia()
        const vuetify = createVuetify({
          theme: {
            defaultTheme: resolveInitialVuetifyTheme(),
            themes: vuetifyThemes,
          },
          locale: {
            locale: vuetifyLocale,
            fallback: 'en',
            messages: { ar, en },
            rtl: {
              ar: true,
              en: false,
            },
          },
          defaults: {
            VDialog: {
              retainFocus: false,
              zIndex: 1010,
            },
            VBtn: {
              rounded: 'lg',
              class: 'text-none',
            },
            VCard: {
              rounded: 'xl',
            },
            VChip: {
              size: 'small',
            },
            VTextField: {
              hideDetails: 'auto',
            },
            VSelect: {
              hideDetails: 'auto',
            },
            VAutocomplete: {
              hideDetails: 'auto',
            },
            VCombobox: {
              hideDetails: 'auto',
            },
            VDateInput: {
              hideDetails: 'auto',
            },
            VNumberInput: {
              hideDetails: 'auto',
            },
            VDataTable: {
              density: 'compact',
            },
            VDataTableVirtual: {
              density: 'compact',
            },
          },
            components: {...components, VDateInput, VNumberInput},
            directives,
        });
        let app = createApp(App, {posProfileData, appDefaults}).use(vuetify).use(router).use(pinia);
        this.$component = app.mount(this.$wrapper.get(0));
    }

    fetch_opening_entry() {
        return frappe.call("erpnext.selling.page.point_of_sale.point_of_sale.check_opening_entry", {
            user: frappe.session.user,
        });
    }
    create_opening_voucher () {
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
            !res.exc && me.prepare_app_defaults(res.message);
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
  
    async prepare_app_defaults (data){
        const pos_opening = data.name;
        const company = data.company;
        const pos_profile = data.pos_profile;
        const pos_opening_time = data.period_start_date;
        const item_stock_map = {};
        var allow_negative_stock = false;
        var customer_groups = [];
        
        frappe.db.get_value("Stock Settings", undefined, "allow_negative_stock").then(({ message }) => {
            allow_negative_stock = flt(message.allow_negative_stock) || false;
        });

        frappe.call({
            method: "erpnext.selling.page.point_of_sale.point_of_sale.get_pos_profile_data",
            args: { pos_profile: pos_profile },
            callback: (res) => {
                const posProfileData = res.message;
                // Object.assign(this.settings, profile);
                // this.settings.customer_groups = profile.customer_groups.map((group) => group.name);
                customer_groups = posProfileData.customer_groups.map((group) => group.name);
                const appDefaults = {
                    pos_opening,    
                    company,
                    pos_profile,
                    pos_opening_time,
                    item_stock_map,
                    allow_negative_stock,
                    customer_groups
                };
                this.make_app(posProfileData, appDefaults);
            },
        });

        frappe.realtime.on(`poe_${this.pos_opening}_closed`, (data) => {
            if (data) {
            frappe.dom.freeze();
            frappe.msgprint({
                title: __("POS Closed"),
                indicator: "orange",
                message: __("POS has been closed at {0}. Please refresh the page.", [
                frappe.datetime.str_to_user(data.creation).bold(),
                ]),
                primary_action_label: __("Refresh"),
                primary_action: {
                action() {
                    window.location.reload();
                },
                },
            });
            }
        });
    }
    
    check_opening_entry () {
        this.fetch_opening_entry().then((r) => {
            if (r.message.length) {
            // assuming only one opening voucher is available for the current user
                this.prepare_app_defaults(r.message[0]);
            } else {
                this.create_opening_voucher();
            }
        });
    }
}

