const get_discount_percentage_from_rate = (row) => {
    if (!row.price_list_rate) {
        return 0;
    }

    return flt(
        (1 - flt(row.rate) / flt(row.price_list_rate)) * 100.0,
        precision('discount_percentage', row)
    );
};

frappe.ui.form.on('Sales Invoice Item', {
    async rate(frm, cdt, cdn) {
		const row = locals[cdt][cdn];
        if (row.max_discount === undefined || row.max_discount === null || row.max_discount === '') {
            return;
        }

        const discount_percentage = get_discount_percentage_from_rate(row);

        if (discount_percentage > flt(row.max_discount)) {
            await frappe.model.set_value(cdt, cdn, 'rate', row.price_list_rate);
            // await frm.script_manager.trigger('update_rate', cdt, cdn);

            frappe.show_alert({
                message: __(`Discount percentage cannot be greater than ${row.max_discount} .....%`),
                indicator: 'orange'
            });
        }
	},
});