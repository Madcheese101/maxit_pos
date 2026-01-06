import frappe

import erpnext.accounts.doctype.pos_invoice.pos_invoice as pos_invoice_file

def custom_get_bin_qty(item_code, warehouse):
    actual_qty = 0
    bin_qty = frappe.db.get_all(
        "Bin",
        fields=["actual_qty", "reserved_qty"],
        filters={
            "item_code": item_code,
            "warehouse": warehouse,
        },
        limit=1
    )
    if bin_qty:
        actual_qty = bin_qty[0].actual_qty - bin_qty[0].reserved_qty

    return actual_qty


def override_methods():
    pos_invoice_file.get_bin_qty = custom_get_bin_qty