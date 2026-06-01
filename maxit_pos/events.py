import frappe

def before_stock_entry_save(doc, method):
    if doc.outgoing_stock_entry:
        doc.add_to_transit = 0