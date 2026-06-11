import frappe

def stock_entry_before_submit(doc, method):
    if doc.outgoing_stock_entry:
        doc.add_to_transit = 0