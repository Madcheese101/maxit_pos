frappe.provide("maxit_pos.utils");
frappe.provide("log_");
import {isProxy} from 'vue';

maxit_pos.utils.check_serial_no_availablilty = async function(item_code, warehouse, serial_no) {
		const method = "erpnext.stock.doctype.serial_no.serial_no.get_pos_reserved_serial_nos";
		const args = { filters: { item_code, warehouse } };
		const res = await frappe.call({ method, args });

		if (res.message.includes(serial_no)) {
			frappe.throw({
				title: __("Not Available"),
				message: __("Serial No: {0} has already been transacted into another POS Invoice.", [
					serial_no.bold(),
				]),
			});
		}
}

log_ = function(...args) {
    args = args.map(ob => {
        if (isProxy(ob)) {
			return Object.keys(ob).reduce((dict, key) => {
            dict[key] = ob[key];
            return dict;
			}, {});
        }
        return ob;
    });
    console.log(...args); // Spread syntax to log them like console.log
}