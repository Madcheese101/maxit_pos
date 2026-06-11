import frappe
from frappe import _
from pypika.terms import Case, ValueWrapper
from frappe.query_builder import Field, functions, Query, DocType
from frappe.desk.search import (
    search_widget,
    build_for_autosuggest,
    sanitize_searchfield,
)
from frappe.utils.caching import http_cache

def _get_user_branch():
    user_branch = frappe.session.data.get("user_branch")
    if not user_branch:
        frappe.throw(_("User Branch not set in session or user does not have a branch assigned to his/her employee record"))
    return user_branch

@frappe.whitelist()
def get_item_doctype_fields():
    doctype = (frappe.get_meta('Item')).as_dict()
    fields = doctype.get("fields")
    
    allowedFieldTypes = [
        "Data", "Link", "Select", "Check", "Int", "Float", "Currency"
    ]
    excluded_fields = ["Item Group", "Item Code", "Item Name", "Description", "Company"]
    field_labels = []
    mapper = {}
    for field in fields:
        if field["fieldtype"] in allowedFieldTypes and field["label"] not in excluded_fields:
            field_labels.append(field["label"])
            mapper[field["label"]] = {
                "fieldname": field["fieldname"], 
                "fieldtype": field["fieldtype"], 
                "options": field["options"]
            }


    result = {"field_labels": field_labels, "mapper": mapper}
    return result

@frappe.whitelist()
def get__warehouse(branch_name=None, get_transfer=False):
    user_branch = _get_user_branch()
    transfer_warehouse = ''
    branch_name_ = branch_name if branch_name else user_branch
    branch = frappe.get_doc("Branch", branch_name_)
    if not branch.transfer_warehouse and get_transfer:
        transfer_warehouse = frappe.db.get_value("Warehouse", branch_name_, "default_in_transit_warehouse")
    if get_transfer:
        return branch.material_warehouse, transfer_warehouse or branch.transfer_warehouse
    return branch.material_warehouse

@frappe.whitelist()
@http_cache(max_age=60, stale_while_revalidate=5 * 60)
def custom_search_link(
    doctype: str,
    txt: str,
    query: str | None = None,
    filters: str | dict | list | None = None,
    page_length: int = 10,
    searchfield: str | None = None,
    reference_doctype: str | None = None,
    ignore_user_permissions: bool = False,
    label_fieldname: str | None = None,
    *,
    link_fieldname: str | None = None,
):
    results = search_widget(
        doctype,
        txt.strip(),
        query,
        searchfield=searchfield,
        page_length=page_length,
        filters=filters,
        reference_doctype=reference_doctype,
        ignore_user_permissions=ignore_user_permissions,
        link_fieldname=link_fieldname,
    )

    rows = build_for_autosuggest(results, doctype=doctype)

    if not label_fieldname:
        return rows

    sanitize_searchfield(label_fieldname)

    meta = frappe.get_meta(doctype)
    if label_fieldname != "name" and not meta.has_field(label_fieldname):
        frappe.throw(_("Invalid label field {0}").format(label_fieldname))

    names = [row.get("value") for row in rows if row.get("value")]
    if not names:
        return rows

    if label_fieldname == "name":
        labels = {name: name for name in names}
    else:
        label_rows = frappe.get_list(
            doctype,
            filters={"name": ["in", names]},
            fields=["name", label_fieldname],
            limit_page_length=0,
        )
        labels = {
            row.name: row.get(label_fieldname)
            for row in label_rows
        }

    for row in rows:
        value = row.get("value")
        if value in labels:
            row["label"] = labels[value]

    return rows