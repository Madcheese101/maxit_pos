import {defineStore} from "pinia"
import {ref, nextTick} from "vue"
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

    const make_new_invoice = () => {
		return frappe.run_serially([
			() => make_sales_invoice_frm(),
			() => set_pos_profile_data(),
			// () => cart.load_invoice(),
		]);
	}

    const make_sales_invoice_frm = () => {
		const doctype = "POS Invoice";
		return new Promise((resolve) => {
			if (posFrm.value) {
				posFrm.value = get_new_frm(posFrm.value);
				posFrm.value.doc.items = [];
				posFrm.value.doc.is_pos = 1;
				resolve();
			} 
            else {
				frappe.model.with_doctype(doctype, () => {
					posFrm.value = get_new_frm();
					posFrm.value.doc.items = [];
					posFrm.value.doc.is_pos = 1;
					resolve();
				});
			}
		});
	}

    const get_new_frm = (_frm) => {
		const doctype = "POS Invoice";
		const page = $("<div>");
		const frm = _frm || new frappe.ui.form.Form(doctype, page, false);
		const name = frappe.model.make_new_doc_and_get_name(doctype, true);
		frm.refresh(name);

		return frm;
	}

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

    const update_cart = async (args) => {
        
        let { field, value, item, is_number } = args;        
        const index = get_item_from_frm(item);
        const item_row_exists = index >= 0;
        const from_selector = field === "qty" && value === "+1";
        const item_row = item_row_exists ? posFrm.value.doc.items[index] : {};

        if (from_selector) value = flt(item_row.qty) + flt(value);

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
        
        const { item_name, item_code, batch_no, serial_no, rate, uom, stock_uom, uoms } = item;

        if (!item_code) return;
        if (rate == undefined || rate == 0) return maxit_pos.utils.errors.price_required();

        const new_item = { item_code, item_name, batch_no, rate, amount: rate, uom, uoms, [field]: value, stock_uom, is_selected: false};
        
        if (serial_no) {
            await maxit_pos.utils.check_serial_no_availablilty(item_code, 
                pos_warehouse.value, 
                serial_no);
            new_item["serial_no"] = serial_no;
        }
        new_item["use_serial_batch_fields"] = 1;
        new_item["warehouse"] = pos_warehouse.value;
        
        if (field === "serial_no") new_item["qty"] = value.split(`\n`).length || 0;
        
        if (field === "qty" && value !== 0 && !posFrm.value.allow_negative_stock) {
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
	}
    
    const trigger_item_update = async function(field, doctype, name) {
        if(field==="rate") field = "update_rate";
        await posFrm.value.script_manager.trigger(field, doctype, name);
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
					i.item_code === item_code &&
					(!has_batch_no || (has_batch_no && i.batch_no === batch_no)) &&
					i.uom === uom &&
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
    
    
    
    
    return {
        // states
        
        posProfileData,
        pos_profile,
        posFrm,
        itemsUpdated,
        cart_items,
        // company,
        // pos_opening,
        // pos_opening_time,
        // item_stock_map,
        // allow_negative_stock,
        // customer_groups,

        // actions
        setAppDefaults,
        make_new_invoice,
        update_cart,
        trigger_item_update,
    }
})