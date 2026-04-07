frappe.require("erpnext/public/js/controllers/taxes_and_totals.js");

erpnext.taxes_and_totals = class customTaxesAndTotals extends erpnext.TaxesAndTotals {
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

		if (item.discount_percentage && !item.discount_amount) {
			item.discount_amount = (flt(item.rate_with_margin) * flt(item.discount_percentage)) / 100;
		}

		if (item.discount_amount > 0) {
			item_rate = flt(item.rate_with_margin - item.discount_amount, precision("rate", item));
			item.discount_percentage = (100 * flt(item.discount_amount)) / flt(item.rate_with_margin);
		}

		frappe.model.set_value(item.doctype, item.name, "rate", item_rate);
	}
};