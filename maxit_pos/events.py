import frappe

def stock_entry_before_submit(doc, method):
    if doc.outgoing_stock_entry:
        doc.add_to_transit = 0

def purchase_receipt_before_cancel(doc, method):
    doc.status_updater = [
        d for d in doc.status_updater
        if not (d.get("percent_join_field_parent") and not doc.get(d["percent_join_field_parent"]))
    ]
