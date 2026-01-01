erpnext.TransactionController = class customTransactionController extends erpnext.TransactionController {

    uom(doc, cdt, cdn) {
		var me = this;
		var item = frappe.get_doc(cdt, cdn);
		item.pricing_rules = "";
		if (item.item_code && item.uom) {
			return this.frm.call({
				method: "erpnext.stock.get_item_details.get_conversion_factor",
				args: {
					item_code: item.item_code,
					uom: item.uom,
				},
				callback: function (r) {
					if (!r.exc) {
						frappe.model.set_value(cdt, cdn, "conversion_factor", r.message.conversion_factor);
                        me.apply_price_list(item, true, true);
					}
				},
			});
		}
		me.calculate_stock_uom_rate(doc, cdt, cdn);
	}

    calculate_stock_uom_rate(doc, cdt, cdn) {
		let item = frappe.get_doc(cdt, cdn);

		if (item?.rate || item?.price_list_rate) {
            const rate = item.rate; //use_price_list_rate ? item.price_list_rate :
			item.stock_uom_rate = flt(rate) / flt(item.conversion_factor);
			refresh_field("stock_uom_rate", item.name, item.parentfield);
		}
	}

    apply_price_list(item, reset_plc_conversion, is_uom_change=false) {
		// We need to reset plc_conversion_rate sometimes because the call to
		// `erpnext.stock.get_item_details.apply_price_list` is sensitive to its value


		if (this.frm.doc.doctype === "Material Request") {
			return;
		}

		if (!reset_plc_conversion) {
			this.frm.set_value("plc_conversion_rate", "");
		}

		let me = this;
		let args = this._get_args(item);
		if (!((args.items && args.items.length) || args.price_list)) {
			return;
		}

		if (me.in_apply_price_list == true) return;

		me.in_apply_price_list = true;
		return this.frm.call({
			method: "erpnext.stock.get_item_details.apply_price_list",
			args: {	args: args, doc: me.frm.doc },
			callback: function(r) {
				if (!r.exc) {
					frappe.run_serially([
						() => {
							if (r.message.parent.price_list_currency)
								me.frm.set_value("price_list_currency", r.message.parent.price_list_currency);
						},
						() => {
							if (r.message.parent.plc_conversion_rate)
								me.frm.set_value("plc_conversion_rate", r.message.parent.plc_conversion_rate);
						},
						() => {
							if(args.items.length) {
								me._set_values_for_item_list(r.message.children);
								$.each(r.message.children || [], function(i, d) {
									me.apply_discount_on_item(d, d.doctype, d.name, 'discount_percentage', is_uom_change);
								});
							}
						},
						() => { me.in_apply_price_list = false; }
					]);

				} else {
					me.in_apply_price_list = false;
				}
			}
		}).always(() => {
			me.in_apply_price_list = false;
		});
	}

    apply_discount_on_item(doc, cdt, cdn, field, is_uom_change=false) {
		var item = frappe.get_doc(cdt, cdn);
		if(item && !item.price_list_rate) {
			item[field] = 0.0;
		} else {
			this.price_list_rate(doc, cdt, cdn, is_uom_change);
		}
		this.set_gross_profit(item);
	}

    price_list_rate(doc, cdt, cdn, is_uom_change=false) {
		var item = frappe.get_doc(cdt, cdn);
		frappe.model.round_floats_in(item, ["price_list_rate", "discount_percentage"]);

		// check if child doctype is Sales Order Item/Quotation Item and calculate the rate
		if (in_list(["Quotation Item", "Sales Order Item", "Delivery Note Item", "Sales Invoice Item", "POS Invoice Item", 
            "Purchase Invoice Item", "Purchase Order Item", "Purchase Receipt Item"]), cdt)
			{
                this.apply_pricing_rule_on_item(item, is_uom_change);}
		else
			item.rate = flt(item.price_list_rate * (1 - item.discount_percentage / 100.0),
				precision("rate", item));

		this.calculate_taxes_and_totals();
	}

    apply_pricing_rule_on_item(item, is_uom_change=false) {
		let effective_item_rate = item.price_list_rate;
		let item_rate = item.rate;
		if (["Sales Order", "Quotation"].includes(item.parenttype) && item.blanket_order_rate) {
			effective_item_rate = item.blanket_order_rate;
		}
		if (item.margin_type == "Percentage") {
			item.rate_with_margin =
				flt(effective_item_rate) + flt(effective_item_rate) * (flt(item.margin_rate_or_amount) / 100);
		} else {
			item.rate_with_margin = flt(effective_item_rate) + flt(item.margin_rate_or_amount);
		}
		item.base_rate_with_margin = flt(item.rate_with_margin) * flt(this.frm.doc.conversion_rate);

		item_rate = flt(item.rate_with_margin, precision("rate", item));

        if(item.discount_percentage && !item.discount_amount && !is_uom_change) {
			item.discount_amount = (flt(item.rate_with_margin) * flt(item.discount_percentage)) / 100;
		}

		if (item.discount_amount > 0 && !is_uom_change) {
			item_rate = flt(item.rate_with_margin - item.discount_amount, precision("rate", item));
			item.discount_percentage = (100 * flt(item.discount_amount)) / flt(item.rate_with_margin);
		}

		frappe.model.set_value(item.doctype, item.name, "rate", item_rate);
	}
    
    update_rate(doc, cdt, cdn){
        const frm = cur_frm;
        var item = frappe.get_doc(cdt, cdn);
        var has_margin_field = frappe.meta.has_field(cdt, 'margin_type');
        frappe.model.round_floats_in(item, ["rate", "price_list_rate"]);

        if(item.price_list_rate && !item.blanket_order_rate) {
            if(item.rate > item.price_list_rate && has_margin_field) {
                // if rate is greater than price_list_rate, set margin
                // or set discount
                item.discount_percentage = 0;
                item.margin_type = 'Amount';
                item.margin_rate_or_amount = flt(item.rate - item.price_list_rate,
                    precision("margin_rate_or_amount", item));
                item.rate_with_margin = item.rate;
            } else {
                item.discount_percentage = flt((1 - item.rate / item.price_list_rate) * 100.0,
                    precision("discount_percentage", item));
                item.discount_amount = flt(item.price_list_rate) - flt(item.rate);
                item.margin_type = '';
                item.margin_rate_or_amount = 0;
                item.rate_with_margin = 0;
            }
        } else {
            item.discount_percentage = 0.0;
            item.margin_type = '';
            item.margin_rate_or_amount = 0;
            item.rate_with_margin = 0;
        }
        item.base_rate_with_margin = item.rate_with_margin * flt(frm.doc.conversion_rate);

        if (item.item_code && item.rate) {
            frappe.call({
                method: "erpnext.stock.get_item_details.get_item_tax_template",
                args: {
                    args: {
                        item_code: item.item_code,
                        company: frm.doc.company,
                        base_net_rate: item.base_net_rate,
                        tax_category: frm.doc.tax_category,
                        item_tax_template: item.item_tax_template,
                        posting_date: frm.doc.posting_date,
                        bill_date: frm.doc.bill_date,
                        transaction_date: frm.doc.transaction_date,
                    }
                },
                callback: function(r) {
                    const item_tax_template = r.message;
                    frappe.model.set_value(cdt, cdn, 'item_tax_template', item_tax_template);
                }
            });
        }

        this.set_gross_profit(item);
        this.calculate_taxes_and_totals();
        this.calculate_stock_uom_rate(doc, cdt, cdn);
    }
    refresh_dom(doc, cdt, cdn){
        let item = frappe.get_doc(cdt, cdn);
        refresh_field("uom", item.name, item.parentfield);
        // refresh_field("items", cdt, cdn);
    }
}