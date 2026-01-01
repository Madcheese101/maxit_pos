frappe.provide("maxit_pos.utils.errors");

maxit_pos.utils.errors.customer_required = function () {
    frappe.show_alert({
        message: __("You must select a customer before adding an item."),
        indicator: "orange",
    });
    frappe.utils.play_sound("error");
};

maxit_pos.utils.errors.price_required = function () {
    frappe.show_alert({
        message: __("Price is not set for the item."),
        indicator: "orange",
    });
    frappe.utils.play_sound("error");
};

maxit_pos.utils.errors.low_stock = function (args) {
    const { 
        bold_available_qty,
        bold_item_code, 
        bold_warehouse, 
        bold_uom,
        available_qty, 
        qty_needed, 
        is_stock_item
    } = args;
    
    if (available_qty <= 0) {
        if (is_stock_item) {
            // frappe.model.clear_doc(item_row.doctype, item_row.name);
            frappe.msgprint({
                title: __("Not Available"),
                message: __("Item Code: {0} is not available under warehouse {1}.", [
                    bold_item_code,
                    bold_warehouse,
                ]),
            });
            return true;
        } else {
            return false;
        }
    } else if (is_stock_item && available_qty < qty_needed) {
        frappe.msgprint({
            message: __(
                "Stock quantity not enough for Item Code: {0} under warehouse {1}. Available quantity {2} {3}.",
                [bold_item_code, bold_warehouse, bold_available_qty, bold_uom]
            ),
            indicator: "orange",
        });
        frappe.utils.play_sound("error");
        return true;
    }
};