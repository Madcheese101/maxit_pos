import frappe
from frappe import _
from frappe.utils import cint, flt
from frappe.model.mapper import get_mapped_doc
from frappe.model.document import Document

def _get_user_branch():
    user_branch = frappe.session.data.get("user_branch")
    if not user_branch:
        frappe.throw(_("User Branch not set in session or user does not have a branch assigned to his/her employee record"))
    return user_branch


def _parse_filters(filters):
    if not filters:
        return {}
    if isinstance(filters, str):
        return frappe.parse_json(filters)
    return filters

@frappe.whitelist()
def create_transfer_stock_entry(to_branch, items):
    user_branch = _get_user_branch()
    if isinstance(items, str):
        items = frappe.parse_json(items)
    if user_branch == to_branch:
        frappe.throw(_("Source and destination branches cannot be the same"))

    source_warehouse = frappe.db.get_value("Branch", user_branch, "material_warehouse")
    transit_warehouse = frappe.db.get_value("Warehouse", source_warehouse, "default_in_transit_warehouse")
    
    if not transit_warehouse:
        frappe.throw(_("Default In Transit Warehouse not set for {source_warehouse}").format(source_warehouse=source_warehouse))

    stock_entry = frappe.get_doc({
        "naming_series": "MAT-TRANS-",
        "doctype": "Stock Entry",
        "stock_entry_type": "Material Transfer",
        "add_to_transit": 1,
        "from_warehouse": source_warehouse,
        "to_warehouse": transit_warehouse,
        "from_branch": user_branch,
        "to_branch": to_branch
    })

    for item in items:
        stock_entry.append("items", item)

    stock_entry.save()
    stock_entry.submit()

@frappe.whitelist()
def make_stock_in_entry(source_name: str, target_doc: str | Document | None = None):
    user_branch = _get_user_branch()
    source_doc = frappe.get_doc("Stock Entry", source_name)
    to_warehouse = frappe.db.get_value("Branch", user_branch, "material_warehouse")
    add_to_transit = cint(source_doc.add_to_transit)

    if user_branch != source_doc.to_branch:
        frappe.throw(_("User Branch does not match the destination branch of the stock entry"))
    if not to_warehouse:
        frappe.throw(_("Destination warehouse must be specified"))

    def set_missing_values(source, target):
        target.naming_series = "MAT-REC-"
        target.stock_entry_type = "Material Transfer"
        target.add_to_transit = 0
        target.from_warehouse = source.to_warehouse
        target.to_warehouse = to_warehouse
        target.from_branch = source.from_branch
        target.to_branch = source.to_branch
        target.set_missing_values()

        if not frappe.get_single_value("Stock Settings", "use_serial_batch_fields"):
            target.make_serial_and_batch_bundle_for_transfer()

    def update_item(source_item, target_item, source_parent):
        target_item.t_warehouse = ""

        if source_item.material_request_item and source_item.material_request and add_to_transit:
            warehouse = frappe.get_value(
                "Material Request Item", source_item.material_request_item, "warehouse"
            )
            target_item.t_warehouse = warehouse

        target_item.s_warehouse = source_item.t_warehouse
        target_item.qty = source_item.qty - source_item.transferred_qty

    doclist = get_mapped_doc(
        "Stock Entry",
        source_name,
        {
            "Stock Entry": {
                "doctype": "Stock Entry",
                "field_map": {"name": "outgoing_stock_entry"},
                "validation": {"docstatus": ["=", 1]},
            },
            "Stock Entry Detail": {
                "doctype": "Stock Entry Detail",
                "field_map": {
                    "name": "ste_detail",
                    "parent": "against_stock_entry",
                    "serial_no": "serial_no",
                    "batch_no": "batch_no",
                },
                "postprocess": update_item,
                "condition": lambda doc: flt(doc.qty) - flt(doc.transferred_qty) > 0.00001,
            },
        },
        target_doc,
        set_missing_values,
    )

    doclist.naming_series = "MAT-REC-"
    doclist.stock_entry_type = "Material Transfer"
    doclist.add_to_transit = 0
    doclist.from_warehouse = source_doc.to_warehouse
    doclist.to_warehouse = to_warehouse
    doclist.from_branch = source_doc.from_branch
    doclist.to_branch = source_doc.to_branch

    previous_mute_messages = frappe.flags.mute_messages
    frappe.flags.mute_messages = True
    try:
        doclist.save()
        doclist.submit()
    finally:
        frappe.flags.mute_messages = previous_mute_messages

    return doclist

@frappe.whitelist()
def cancel_transfer_stock_entry(docname):
    if not docname:
        frappe.throw(_("Stock Entry is required"))

    doc = frappe.get_doc("Stock Entry", docname)
    if doc.docstatus != 1:
        frappe.throw(_("Only submitted Stock Entry records can be cancelled"))

    if cint(doc.add_to_transit) == 1 and flt(doc.per_transferred) > 0:
        frappe.throw(_("Transferred in-transit Stock Entry records cannot be cancelled"))
    

    doc.cancel()
    return doc.name

@frappe.whitelist()
def get_outgoing_transfers(filters): # filters should be a dict with keys (from_date, to_date, to_branch, item_code)
    user_branch = _get_user_branch()
    filters = _parse_filters(filters)
    query_filters = {
        "stock_entry_type": "Material Transfer",
        "from_branch": user_branch,
        "add_to_transit": 1,
    }

    if filters.get("from_date") and filters.get("to_date"):
        query_filters["posting_date"] = ["between", [filters.get("from_date"), filters.get("to_date")]]
    elif filters.get("from_date"):
        query_filters["posting_date"] = [">=", filters.get("from_date")]
    elif filters.get("to_date"):
        query_filters["posting_date"] = ["<=", filters.get("to_date")]

    if filters.get("to_branch"):
        query_filters["to_branch"] = filters.get("to_branch")
    if filters.get("item_code"):
        query_filters["items.item_code"] = filters.get("item_code")
    
    out_going = frappe.qb.get_query(
        "Stock Entry",
        filters=query_filters,
        fields=["posting_date", "name", "from_branch", "to_branch", "per_transferred", "add_to_transit", "docstatus"],
        order_by="posting_date desc, modified desc",
        distinct=bool(filters.get("item_code"))
    ).run(as_dict=True)

    return out_going

@frappe.whitelist()
def get_incoming_transfers(filters): # filters should be a dict with keys (from_date, to_date, from_branch, item_code)
    user_branch = _get_user_branch()
    filters = _parse_filters(filters)
    query_filters = [
        ["to_branch", "=", user_branch],
        "and",
        ["docstatus", "=", 1],
        "and",
        [
            ["add_to_transit", "=", 0],
            "or",
            [
                ["add_to_transit", "=", 1],
                "and",
                ["per_transferred", "=", 0],
            ],
        ],
    ]

    if filters.get("from_date"):
        query_filters.extend(["and", ["posting_date", ">=", filters.get("from_date")]])
    if filters.get("to_date"):
        query_filters.extend(["and", ["posting_date", "<=", filters.get("to_date")]])
    if filters.get("from_branch"):
        query_filters.extend(["and", ["from_branch", "=", filters.get("from_branch")]])
    if filters.get("item_code"):
        query_filters.extend(["and", ["items.item_code", "=", filters.get("item_code")]])
    
    recieved = frappe.qb.get_query(
        "Stock Entry",
        filters=query_filters,
        fields=["posting_date", "name", "from_branch", "to_branch", "per_transferred", "add_to_transit", "docstatus"],
        order_by="posting_date desc, modified desc",
        distinct=bool(filters.get("item_code"))
    ).run(as_dict=True)

    return recieved