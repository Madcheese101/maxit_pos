import {defineStore} from "pinia"
import {computed, ref, nextTick} from "vue"
import { readStoredThemePreferences, persistThemePreferences, resolveVuetifyThemeName } from "../themeConfig"
frappe.provide("log_");
frappe.provide("maxit_pos.utils");
frappe.provide("maxit_pos.utils.errors");

export const usePosStore = defineStore('posStore', () => {
    // states
    const posProfileData = ref({});
    const pos_opening = ref("");
    const company = ref("");
    const pos_profile = ref("");
    const pos_opening_time = ref();
    const item_stock_map = ref({});
    const allow_negative_stock = ref(false);
    const pos_warehouse = ref("");
    const customer_groups = ref([]);
    const invoice = ref(null);
    const payment_modes = ref([]);
    const currency_fraction = ref(0);
    const itemsUpdated = ref(0);
    const cart_items = ref([]);
    const reactiveTotal = ref(0);
    const reactiveGrandTotal = ref(0);
    const reactiveTotalQty = ref(0);
    const reactivePaidAmount = ref(0);
    const reactiveOutstandingAmount = ref(0);
    const storedThemePreferences = readStoredThemePreferences();
    const themeMode = ref(storedThemePreferences.mode);
    const darkPalette = ref(storedThemePreferences.darkPalette);
    const activeVuetifyTheme = computed(() => {
        return resolveVuetifyThemeName(themeMode.value, darkPalette.value);
    });
    const returnAgainst = ref(null);

    const getAppLanguage = () => {
        return frappe.boot?.lang || frappe.boot?.user?.language || 'en';
    }

    const isAppRTL = () => {
        return frappe.utils.is_rtl();
    }

    const getAppDirection = () => {
        return isAppRTL() ? 'rtl' : 'ltr';
    }

    const hydrateThemePreferences = () => {
        const storedPreferences = readStoredThemePreferences();
        themeMode.value = storedPreferences.mode;
        darkPalette.value = storedPreferences.darkPalette;
    }

    const setThemePreferences = ({ mode, darkPalette: selectedDarkPalette }) => {
        const storedPreferences = persistThemePreferences({
            mode,
            darkPalette: selectedDarkPalette,
        });

        themeMode.value = storedPreferences.mode;
        darkPalette.value = storedPreferences.darkPalette;

        return activeVuetifyTheme.value;
    }

    const buildPrintViewUrl = ({
        doctype,
        name,
        format = 'Standard',
        no_letterhead = 1,
        letterhead = 'No Letterhead',
        settings = '{}',
    }) => {
        const params = new URLSearchParams({
            doctype,
            name,
            format,
            no_letterhead: String(no_letterhead),
            letterhead,
            settings,
            _lang: getAppLanguage(),
            pdf_generator: 'wkhtmltopdf',
            trigger_print: '1',
        });
        return `/printview?${params.toString()}`;
    }

    // actions
    const setAppDefaults = (posProfile, appDefaults) => {
        posProfileData.value = posProfile;
        pos_opening.value = appDefaults.pos_opening;
        company.value = appDefaults.company;
        pos_profile.value = appDefaults.pos_profile;
        pos_opening_time.value = appDefaults.pos_opening_time;
        item_stock_map.value = appDefaults.item_stock_map;
        allow_negative_stock.value = appDefaults.allow_negative_stock;
        customer_groups.value = appDefaults.customer_groups;
        pos_warehouse.value = posProfile.warehouse;
    }

    const ITEM_DOCTYPE = "Sales Invoice Item";

    // The invoice is a plain object edited locally; the server only sees it on
    // save/submit, where SalesInvoice.validate recalculates totals and fills
    // accounts, cost centers and other missing item details.
    const prec = (fieldname, doctype = "Sales Invoice") => {
        return frappe.meta.get_field_precision(frappe.meta.get_docfield(doctype, fieldname), invoice.value);
    }

    // Sales Invoice meta (for precision), POS payment modes with their accounts and
    // the currency rounding fraction are loaded once per session.
    let pos_settings_promise = null;
    const load_pos_settings = () => {
        pos_settings_promise ||= (async () => {
            await new Promise((resolve) => frappe.model.with_doctype("Sales Invoice", resolve));
            const [modes, currency] = await Promise.all([
                frappe.call({
                    method: "maxit_pos.maxit_pos.page.maxit_pos.api.api.get_pos_payment_modes",
                    args: { pos_profile: posProfileData.value.name, company: posProfileData.value.company },
                }),
                frappe.db.get_value("Currency", posProfileData.value.currency, "smallest_currency_fraction_value"),
            ]);
            payment_modes.value = modes.message || [];
            currency_fraction.value = flt(currency.message?.smallest_currency_fraction_value);
        })();
        return pos_settings_promise;
    }

    const make_payments = () => {
        return payment_modes.value.map((mode, i) => ({ ...mode, idx: i + 1, amount: 0, base_amount: 0 }));
    }

    const make_invoice_doc = (is_return = 0) => {
        const profile = posProfileData.value;
        // copied from the profile like SalesInvoice.set_pos_fields does for a new POS invoice
        const pos_fields = {};
        for (const fieldname of ["letter_head", "tc_name", "select_print_heading", "write_off_account",
            "write_off_cost_center", "cost_center", "taxes_and_charges", "tax_category", "ignore_pricing_rule"]) {
            pos_fields[fieldname] = profile[fieldname];
        }
        return {
            ...pos_fields,
            doctype: "Sales Invoice",
            company: profile.company,
            pos_profile: profile.name,
            is_pos: 1,
            is_created_using_pos: 1,
            is_return,
            update_stock: profile.update_stock,
            set_warehouse: profile.warehouse,
            currency: profile.currency,
            selling_price_list: profile.selling_price_list,
            apply_discount_on: profile.apply_discount_on || "Grand Total",
            disable_rounded_total: cint(frappe.sys_defaults.disable_rounded_total),
            customer: "",
            customer_name: "",
            sales_person: "",
            discount_amount: 0,
            additional_discount_percentage: 0,
            items: [],
            payments: make_payments(),
        };
    }

    const make_new_invoice = async () => {
        await load_pos_settings();
        invoice.value = make_invoice_doc();
        returnAgainst.value = null;
        await set_customer(posProfileData.value.customer);
    }

    const set_customer = async (customer) => {
        const doc = invoice.value;
        doc.customer = customer || "";
        doc.customer_name = "";
        let price_list = posProfileData.value.selling_price_list;

        if (customer) {
            const { message } = await frappe.db.get_value("Customer", customer,
                ["customer_name", "default_price_list", "customer_group"]);
            doc.customer_name = message?.customer_name || customer;
            // same order as SalesInvoice.set_pos_fields, which sets the price list on submit
            let customer_price_list = message?.default_price_list;
            if (!customer_price_list && message?.customer_group) {
                const group = await frappe.db.get_value("Customer Group", message.customer_group, "default_price_list");
                customer_price_list = group.message?.default_price_list;
            }
            price_list = customer_price_list || price_list;
        }

        if (price_list !== doc.selling_price_list) {
            doc.selling_price_list = price_list;
            await reprice_items(doc);
        }
    }

    const reprice_items = async (doc) => {
        if (!doc.items.length) return;
        const { message } = await frappe.call({
            method: "erpnext.stock.get_item_details.apply_price_list",
            args: {
                ctx: {
                    doctype: doc.doctype,
                    company: doc.company,
                    customer: doc.customer,
                    currency: doc.currency,
                    conversion_rate: doc.conversion_rate || 1,
                    selling_price_list: doc.selling_price_list,
                    transaction_date: frappe.datetime.get_today(),
                    items: doc.items.map((row) => ({
                        doctype: "Sales Invoice Item",
                        item_code: row.item_code,
                        uom: row.uom,
                        stock_uom: row.stock_uom,
                        conversion_factor: row.conversion_factor,
                        qty: row.qty,
                    })),
                },
            },
        });
        message.children.forEach((child, i) => {
            const row = doc.items[i];
            row.price_list_rate = flt(child.price_list_rate);
            calculate_row(row, "discount_percentage");
        });
        calculate_totals(doc);
    }

    const process_return = async (doctype, name) => {
        await load_pos_settings();
        const source = await frappe.db.get_doc(doctype, name);
        const { message } = await frappe.call({
            method:
                doctype == "POS Invoice"
                    ? "erpnext.accounts.doctype.pos_invoice.pos_invoice.make_sales_return"
                    : "erpnext.accounts.doctype.sales_invoice.sales_invoice.make_sales_return",
            args: {
                source_name: name,
                target_doc: make_invoice_doc(1),
            },
        });
        message.sales_person = source.sales_person || message.sales_person || "";
        // ERPNext skips repopulating payments for returns (for_validate=True), so a
        // return only keeps the source invoice's surviving (non-zero) payment rows.
        // Use the full POS profile mode list so every method is selectable at checkout.
        message.payments = make_payments();
        invoice.value = message;
        returnAgainst.value = message.return_against || null;
        calculate_totals();
    }

    const toggle_is_return = (value) => {
        const doc = invoice.value;
        doc.is_return = value ? 1 : 0;
        for (const row of doc.items) {
            row.qty = value ? -Math.abs(flt(row.qty)) : Math.abs(flt(row.qty));
            calculate_row(row);
        }
        doc.payments.forEach((payment) => { payment.amount = 0; });
        if (!value) {
            returnAgainst.value = null;
        }
        calculate_totals();
    }

    const edit_invoice = async (invoice_name) => {
        await load_pos_settings();
        const doc = await frappe.db.get_doc("Sales Invoice", invoice_name);
        doc.payments = make_payments();
        invoice.value = doc;
        returnAgainst.value = null;
        calculate_totals();
    }

    const sales_order_to_invoice = async (sales_order) => {
        if (!sales_order) return;
        await load_pos_settings();
        const { message } = await frappe.call({
            method: "erpnext.selling.doctype.sales_order.sales_order.make_sales_invoice",
            args: {
                source_name: sales_order,
                target_doc: make_invoice_doc(),
            },
        });
        if (!message) return;
        message.payments = make_payments();
        invoice.value = message;
        returnAgainst.value = null;
        calculate_totals();
    }

    // Saves (docstatus 0) or submits (docstatus 1) the invoice in one request and
    // replaces the local invoice with the server's version.
    const save_invoice = async (docstatus = 0) => {
        const { message } = await frappe.call({
            method: "frappe.client.save",
            args: { doc: { ...invoice.value, docstatus } },
            freeze: true,
        });
        invoice.value = message;
        return message;
    }

    const update_cart = async (args) => {
        let { field, value, item, is_number } = args;
        item["uom"] = item["uom"] || item["stock_uom"];
        const doc = invoice.value;
        let index = doc.items.indexOf(item);
        if (index < 0) index = get_item_row_index(item);
        const item_row = index >= 0 ? doc.items[index] : null;
        const from_selector = field === "qty" && value === "+1";

        if (from_selector) {
            const step = doc.is_return ? -1 : 1;
            value = flt(item_row?.qty) + step;
        }

        if (item_row) {
            await update_item(field, value, item_row, item, is_number, from_selector);
        } else {
            await add_item(field, value, item);
        }
    }

    const update_item = async function(field, value, item_row, item, is_number, from_selector) {
        if (is_number) value = flt(value);

        if ((["qty", "conversion_factor"].includes(field))
            && value > 0 && !allow_negative_stock.value) {
            const qty_needed = field === "qty" ? value * item_row.conversion_factor : item_row.qty * value;
            const is_low_stock = await check_stock_availability(item_row, qty_needed, pos_warehouse.value);

            if (is_low_stock) {
                // item_row[field] -= 1; //return to previous value
                return;
            };
        }
        item_row[field] = value;
        // now update serial no field if needed
        if (item.serial_no && from_selector) {
            item_row.serial_no = item_row.serial_no + `\n${item.serial_no}`;
        }
        calculate_row(item_row, field);
        validate_max_discount(item_row);
        calculate_totals();
    }

    const add_item = async function(field, value, item) {
        const doc = invoice.value;
        if (!doc.customer) return maxit_pos.utils.errors.customer_required();

        const { item_name, item_code, batch_no, serial_no, rate, uom, stock_uom, max_discount } = item;

        if (!item_code) return;
        if (rate == undefined || rate == 0) return maxit_pos.utils.errors.price_required();

        const new_item = {
            item_code, item_name, batch_no, uom, stock_uom, max_discount,
            conversion_factor: flt(item.conversion_factor) || 1,
            price_list_rate: flt(rate),
            rate: flt(rate),
            discount_percentage: 0,
            discount_amount: 0,
            discount_type: "Percentage",
            use_serial_batch_fields: 1,
            warehouse: pos_warehouse.value,
            [field]: value,
        };
        // get_item_details takes these from the POS profile for POS invoices; the server
        // won't on save since cost_center already has the company default by then
        for (const fieldname of ["income_account", "cost_center", "expense_account"]) {
            if (posProfileData.value[fieldname]) new_item[fieldname] = posProfileData.value[fieldname];
        }

        if (serial_no) {
            await maxit_pos.utils.check_serial_no_availablilty(item_code,
                pos_warehouse.value,
                serial_no);
            new_item["serial_no"] = serial_no;
        }

        if (field === "serial_no") new_item["qty"] = value.split(`\n`).length || 0;

        if (field === "qty" && value > 0 && !allow_negative_stock.value) {
            const qty_needed = value * new_item.conversion_factor;
            const is_low_stock = await check_stock_availability(new_item, qty_needed, pos_warehouse.value);
            if (is_low_stock) return;
        }
        calculate_row(new_item);
        new_item.idx = doc.items.length + 1;
        doc.items.push(new_item);
        calculate_totals();
    }

    const remove_item = (item_row) => {
        const doc = invoice.value;
        const index = doc.items.indexOf(item_row);
        if (index === -1) return;
        doc.items.splice(index, 1);
        doc.items.forEach((row, i) => { row.idx = i + 1; });
        calculate_totals();
    }

    const get_item_row_index = ({ name, item_code, batch_no, uom, rate }) => {
        const items = invoice.value.items;
        let index = null;
		if (name) {
            index = items.findIndex((i) => i.name == name);
		} else {
			// if item is clicked twice from item selector
			// then "item_code, batch_no, uom, rate" will help in getting the exact item
			// to increase the qty by one
			const has_batch_no = batch_no !== "null" && batch_no !== null;
            index = items.findIndex(
				(i) =>
					i.item_code === item_code
                    &&
					(!has_batch_no || (has_batch_no && i.batch_no === batch_no))
                    &&
					i.uom === uom
                    &&
					i.price_list_rate === flt(rate)
			);
		}

		return index;
	}

    // Mirrors the ERPNext TransactionController rate / discount handlers for the
    // field that was just edited, then recalculates the row amount.
    const calculate_row = (row, field) => {
        const price_list_rate = flt(row.price_list_rate);

        if (field === "rate") {
            if (!price_list_rate) {
                row.discount_percentage = 0;
                row.discount_amount = 0;
                row.margin_type = "";
                row.margin_rate_or_amount = 0;
            } else if (flt(row.rate) > price_list_rate) {
                // rate above price list rate is kept as a margin
                row.margin_type = "Amount";
                row.margin_rate_or_amount = flt(row.rate - price_list_rate, prec("margin_rate_or_amount", ITEM_DOCTYPE));
                row.rate_with_margin = row.rate;
                row.discount_percentage = 0;
                row.discount_amount = 0;
            } else {
                row.margin_type = "";
                row.margin_rate_or_amount = 0;
                row.rate_with_margin = price_list_rate;
                row.discount_percentage = flt((1 - row.rate / price_list_rate) * 100.0, prec("discount_percentage", ITEM_DOCTYPE));
                row.discount_amount = flt(price_list_rate - row.rate, prec("discount_amount", ITEM_DOCTYPE));
            }
        } else if (["discount_percentage", "discount_amount"].includes(field)) {
            const margin = flt(row.margin_rate_or_amount);
            const rate_with_margin = row.margin_type === "Percentage"
                ? price_list_rate + price_list_rate * margin / 100
                : price_list_rate + margin;
            row.rate_with_margin = rate_with_margin;

            if (field === "discount_percentage") {
                row.discount_amount = flt(rate_with_margin * flt(row.discount_percentage) / 100, prec("discount_amount", ITEM_DOCTYPE));
            } else {
                row.discount_percentage = rate_with_margin ? flt(100 * flt(row.discount_amount) / rate_with_margin, prec("discount_percentage", ITEM_DOCTYPE)) : 0;
            }
            row.rate = flt(rate_with_margin - flt(row.discount_amount), prec("rate", ITEM_DOCTYPE));
        }

        row.amount = flt(flt(row.rate) * flt(row.qty), prec("amount", ITEM_DOCTYPE));
    }

    const validate_max_discount = (row) => {
        if (!flt(row.max_discount) || flt(row.discount_percentage) <= flt(row.max_discount)) return;

        row.rate = row.price_list_rate;
        calculate_row(row, "rate");
        frappe.show_alert({
            message: __('Discount percentage cannot be greater than {0}%', [row.max_discount]),
            indicator: 'orange'
        });
    }

    // Same as round_based_on_smallest_currency_fraction on the server.
    const round_total = (value) => {
        const fraction = currency_fraction.value;
        const precision = prec("rounded_total");
        if (!fraction) return flt(_round(value), precision);

        const remainder_val = remainder(value, fraction, precision);
        value += remainder_val > fraction / 2 ? fraction - remainder_val : -remainder_val;
        return flt(value, precision);
    }

    const get_total_to_pay = (doc) => {
        return flt((doc.rounded_total || doc.grand_total) - flt(doc.write_off_amount), prec("grand_total"));
    }

    const calculate_totals = (doc = invoice.value) => {
        let total = 0;
        let total_qty = 0;
        for (const row of doc.items) {
            total += flt(row.amount);
            total_qty += flt(row.qty);
        }
        doc.total_qty = total_qty;
        doc.total = flt(total, prec("total"));

        // no taxes on POS invoices, so Grand Total and Net Total discounts are the same
        if (flt(doc.additional_discount_percentage)) {
            doc.discount_amount = flt(doc.total * doc.additional_discount_percentage / 100, prec("discount_amount"));
        }
        doc.net_total = doc.grand_total = flt(doc.total - flt(doc.discount_amount), prec("grand_total"));

        if (cint(doc.disable_rounded_total)) {
            doc.rounded_total = 0;
            doc.rounding_adjustment = 0;
        } else {
            doc.rounded_total = round_total(doc.grand_total);
            doc.rounding_adjustment = flt(doc.rounded_total - doc.grand_total, prec("rounding_adjustment"));
        }

        if (!doc.is_return && cint(posProfileData.value.set_grand_total_to_default_mop ?? 1)) {
            set_default_payment(doc);
        }
        calculate_paid_amount(doc);
    }

    const set_default_payment = (doc) => {
        const total_to_pay = get_total_to_pay(doc);
        if (total_to_pay <= 0) return;

        let default_set = false;
        for (const payment of doc.payments) {
            if (payment.default && !default_set) {
                payment.amount = total_to_pay;
                default_set = true;
            } else {
                payment.amount = 0;
            }
        }
    }

    const calculate_paid_amount = (doc = invoice.value) => {
        const paid_amount = doc.payments.reduce((sum, payment) => sum + flt(payment.amount), 0);
        doc.paid_amount = flt(paid_amount, prec("paid_amount"));

        doc.change_amount = 0;
        if (!doc.is_return && doc.paid_amount > doc.grand_total
            && doc.payments.some((payment) => payment.type === "Cash")) {
            doc.change_amount = flt(doc.paid_amount - (doc.rounded_total || doc.grand_total), prec("change_amount"));
        }
        doc.outstanding_amount = flt(get_total_to_pay(doc) - doc.paid_amount + doc.change_amount, prec("outstanding_amount"));
    }

    const check_stock_availability = async function(item_row, qty_needed, warehouse) {
        const resp = (await get_available_stock(item_row.item_code, warehouse)).message;
        const available_qty = resp[0];
        const is_stock_item = resp[1];

        const bold_uom = item_row.stock_uom.bold();
        const bold_item_code = item_row.item_code.bold();
        const bold_warehouse = warehouse.bold();
        const bold_available_qty = available_qty.toString().bold();
        const is_low_stock = maxit_pos.utils.errors.low_stock({
            available_qty,
            qty_needed,
            is_stock_item,
            bold_available_qty,
            bold_item_code,
            bold_warehouse,
            bold_uom
        })
        return is_low_stock;
    }

    const get_available_stock = (item_code, warehouse) => {
        return frappe.call({
            method: "erpnext.accounts.doctype.pos_invoice.pos_invoice.get_stock_availability",
            args: {
                item_code: item_code,
                warehouse: warehouse,
            },

            callback(res) {
                if (!item_stock_map.value[item_code]) item_stock_map.value[item_code] = {};
                item_stock_map.value[item_code][warehouse] = res.message;
            },
        });
    }
    
    const setPosOpening = (opening_entry) => {
        pos_opening.value = opening_entry.name;
        pos_opening_time.value = opening_entry.period_start_date;
    }
    
    const close_pos = async () => {
        if (!pos_opening.value) {
            frappe.msgprint({
                title: __('Missing Opening Entry'),
                indicator: 'orange',
                message: __('No open POS Opening Entry found for this session.'),
            });
            return;
        }

        frappe.dom.freeze(__('Closing POS and submitting entry...'));

        return frappe.call({
            method: 'maxit_pos.maxit_pos.page.maxit_pos.api.api.create_and_submit_pos_closing_entry',
            args: {
                pos_profile: pos_profile.value,
                company: company.value,
                pos_opening_entry: pos_opening.value,
            },
            freeze: true,
        }).then((response) => {
            const closingEntryName = response.message[0];
            const closingEntryUser = response.message[1];

            pos_opening.value = '';
            pos_opening_time.value = null;

            frappe.show_alert({
                indicator: 'green',
                message: __('POS Closing Entry {0} submitted successfully', [closingEntryName]),
            });
            
            frappe.dom.unfreeze();
            window.location.reload();
        }).catch((error) => {
            frappe.dom.unfreeze();
            frappe.msgprint({
                title: __('POS Closing Failed'),
                indicator: 'red',
                message: error?.message || __('Unable to create POS Closing Entry.'),
            });
            throw error;
        });
    }
    
    return {
        // states
        
        posProfileData,
        pos_profile,
        invoice,
        itemsUpdated,
        cart_items,
        reactiveTotal,
        reactiveGrandTotal,
        reactiveTotalQty,
        reactivePaidAmount,
        reactiveOutstandingAmount,
        themeMode,
        darkPalette,
        activeVuetifyTheme,
        returnAgainst,
        getAppLanguage,
        isAppRTL,
        getAppDirection,
        buildPrintViewUrl,
        // company,
        pos_opening,
        close_pos,
        // pos_opening_time,
        // item_stock_map,
        // allow_negative_stock,
        // customer_groups,

        // actions
        setAppDefaults,
        make_new_invoice,
        sales_order_to_invoice,
        update_cart,
        edit_invoice,
        setPosOpening,
        set_customer,
        remove_item,
        calculate_totals,
        calculate_paid_amount,
        save_invoice,
        process_return,
        toggle_is_return,
        hydrateThemePreferences,
        setThemePreferences
    }
})