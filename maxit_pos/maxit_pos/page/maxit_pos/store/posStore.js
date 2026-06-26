import {defineStore} from "pinia"
import {computed, ref, nextTick, triggerRef} from "vue"
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
    const posFrm = ref();
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
    const set_pos_profile_data = () => {
		if (posProfileData.value.company && !posFrm.value.doc.company) posFrm.value.doc.company = posProfileData.value.company;
		if (
			(posProfileData.value.name && !posFrm.value.doc.pos_profile) |
			(posFrm.value.doc.is_return && posProfileData.value.name != posFrm.value.doc.pos_profile)
		) {
			posFrm.value.doc.pos_profile = posProfileData.value.name;
		}
		posFrm.value.doc.set_warehouse = posProfileData.value.warehouse;

		if (!posFrm.value.doc.company) return;

		return posFrm.value.trigger("set_pos_data");
	}

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
    

    const make_new_invoice = () => {
		return frappe.run_serially([
			() => make_sales_invoice_frm(),
			() => set_pos_profile_data(),
			// () => cart.load_invoice(),
		]);
	}
    const process_return = (doctype, name) => {
        frappe.db.get_doc(doctype, name).then((doc) => {
            frappe.run_serially([
                () => make_sales_invoice_frm(doc.doctype, 1),
                () => make_return_invoice(doc),
                () => returnAgainst.value = posFrm.value.doc.return_against || null,
                () => triggerRef(posFrm),
            ]);
        });
    }
    const toggle_is_return = async (value) => {
        posFrm.value.doc.is_return = value ? 1 : 0;
        for (const item of posFrm.value.doc.items) {
            item.qty = value ? -Math.abs(flt(item.qty)) : Math.abs(flt(item.qty));
            await posFrm.value.script_manager.trigger("qty", item.doctype, item.name);
        }
        if (!value) returnAgainst.value = null;
        triggerRef(posFrm);
    }
    const edit_invoice = (invoice_name) => {
        return frappe.run_serially([
            () => make_sales_invoice_frm(),
            () => sync_draft_invoice_to_frm(invoice_name),
            () => posFrm.value.refresh(invoice_name),
            () => posFrm.value.call("reset_mode_of_payments"),
            // () => posFrm.value.trigger('refresh_totals')
        ]);
    }
    const sales_order_to_invoice = (sales_order) => {
        return frappe.run_serially([
            () => make_sales_invoice_frm(),
            () => load_sales_order(sales_order),
            () => triggerRef(posFrm),
        ]);
    }
    const load_sales_order = (sales_order) => {
        if (!sales_order) return Promise.resolve();

        return frappe.call({
            method: "erpnext.selling.doctype.sales_order.sales_order.make_sales_invoice",
            args: {
                source_name: sales_order,
                target_doc: posFrm.value.doc,
            },
            callback: (r) => {
                if (r.exc || !r.message) return;
                frappe.model.sync(r.message);
                posFrm.value.doc.items = [...(r.message.items || [])];
                posFrm.value.refresh(r.message.name);
            },
        });
    }
    const make_sales_invoice_frm = (doctype_, is_return=0) => {
		const doctype = "Sales Invoice";
		return new Promise((resolve) => {
			if (posFrm.value) {
				posFrm.value = get_new_frm(posFrm.value);
				posFrm.value.doc.items = [];
				posFrm.value.doc.is_pos = 1;
                if (doctype == "Sales Invoice") posFrm.value.doc.is_created_using_pos = 1;
                if (is_return) posFrm.value.doc.is_return = 1;
                if (!is_return) returnAgainst.value = null;
				resolve();
			} 
            else {
				frappe.model.with_doctype(doctype, () => {
					posFrm.value = get_new_frm();
					posFrm.value.doc.items = [];
					posFrm.value.doc.is_pos = 1;
                    if (doctype == "Sales Invoice") posFrm.value.doc.is_created_using_pos = 1;
                    if (is_return) posFrm.value.doc.is_return = 1;
                    if (!is_return) returnAgainst.value = null;
					resolve();
				});
			}
		});
	}

    const get_new_frm = (_frm) => {
		const doctype = "Sales Invoice";
		const page = $("<div>");
		const frm = _frm || new frappe.ui.form.Form(doctype, page, false);
		const name = frappe.model.make_new_doc_and_get_name(doctype, true);
		frm.refresh(name);

		return frm;
	}

    const sync_draft_invoice_to_frm = (invoice) => {
		return frappe.db.get_doc("Sales Invoice", invoice).then((doc) => {
			frappe.model.sync(doc);
		});
	}

    const make_return_invoice = async (doc) => {
		return frappe.call({
			method:
				doc.doctype == "POS Invoice"
					? "erpnext.accounts.doctype.pos_invoice.pos_invoice.make_sales_return"
					: "erpnext.accounts.doctype.sales_invoice.sales_invoice.make_sales_return",
			args: {
				source_name: doc.name,
				target_doc: posFrm.value.doc,
			},
			callback: (r) => {
				frappe.model.sync(r.message);
				frappe.get_doc(r.message.doctype, r.message.name).__run_link_triggers = false;
				// this.set_pos_profile_data();
                const items = r.message.items || [];
                posFrm.value.doc.items = [...items];
                posFrm.value.doc.sales_person = doc.sales_person || r.message.sales_person || "";
                // above line sets pos profile data for invoice according to current pos profile
                // useful when returning an invoice created in different pos profile.
			},
		});
	}
    const update_cart = async (args) => {
        
        let { field, value, item, is_number } = args;
        item["uom"] = item["uom"] || item["stock_uom"];
        const index = get_item_from_frm(item);
        const item_row_exists = index >= 0;
        // const item_row_exists = 0;
        const from_selector = field === "qty" && value === "+1";
        const item_row = item_row_exists ? posFrm.value.doc.items[index] : {};

        if (from_selector) {
            const step = posFrm.value.doc.is_return ? -1 : 1;
            value = flt(item_row.qty) + step;
        }

        if (item_row_exists) {
            update_item(field, value, item_row, item, is_number, from_selector);
            
        } else {
            add_item(field, value, item);
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
            await frappe.model.set_value(
                item_row.doctype,
                item_row.name,
                "serial_no",
                item_row.serial_no + `\n${item.serial_no}`
            );
        }
        trigger_item_update(field, item_row.doctype, item_row.name);
    }
    const add_item = async function(field, value, item) {
        
        if (!posFrm.value.doc.customer) return maxit_pos.utils.errors.customer_required();
        
        const { item_name, item_code, batch_no, serial_no, rate, uom, stock_uom, uoms, max_discount } = item;

        if (!item_code) return;
        if (rate == undefined || rate == 0) return maxit_pos.utils.errors.price_required();

        const new_item = { item_code, item_name, batch_no, rate, amount: rate, uom, uoms, [field]: value, stock_uom, is_selected: false, max_discount, discount_type: "Percentage" };

        if (serial_no) {
            await maxit_pos.utils.check_serial_no_availablilty(item_code, 
                pos_warehouse.value, 
                serial_no);
            new_item["serial_no"] = serial_no;
        }
        new_item["use_serial_batch_fields"] = 1;
        new_item["warehouse"] = pos_warehouse.value;
        
        if (field === "serial_no") new_item["qty"] = value.split(`\n`).length || 0;
        
        if (field === "qty" && value > 0 && !posFrm.value.allow_negative_stock) {
            const qty_needed = value * new_item.conversion_factor;
            const is_low_stock = await check_stock_availability(new_item, qty_needed, pos_warehouse.value);
            if (is_low_stock) return;
        }
        const frm_item_row = posFrm.value.add_child("items", new_item);            
        
        await trigger_new_item_events(frm_item_row);
    }
    
    const trigger_new_item_events = async function(item_row, rate_only = false) {
		await posFrm.value.script_manager.trigger("item_code", item_row.doctype, item_row.name);
		await posFrm.value.script_manager.trigger("qty", item_row.doctype, item_row.name);
        triggerRef(posFrm);
	}
    
    const trigger_item_update = async function(field, doctype, name) {
        if(field==="rate") field = "update_rate";
        await posFrm.value.script_manager.trigger(field, doctype, name);
        triggerRef(posFrm);
    }

    const get_item_from_frm = ({ name, item_code, batch_no, uom, rate }) =>{
        const frm = posFrm.value;
        let index = null;
		if (name) {
            index = frm.doc.items.findIndex((i) => i.name == name);
		} else {
			// if item is clicked twice from item selector
			// then "item_code, batch_no, uom, rate" will help in getting the exact item
			// to increase the qty by one
			const has_batch_no = batch_no !== "null" && batch_no !== null;
            index = frm.doc.items.findIndex(
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
                company: posFrm.value.doc.company,
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
        posFrm,
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
        trigger_item_update,
        process_return,
        toggle_is_return,
        hydrateThemePreferences,
        setThemePreferences
    }
})