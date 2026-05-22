import frappe
from frappe import _
from pypika.terms import Case, ValueWrapper
from frappe.query_builder import Field, functions, Query, DocType

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