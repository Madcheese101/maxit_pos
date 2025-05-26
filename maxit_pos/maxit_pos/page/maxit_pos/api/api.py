import json
import frappe

@frappe.whitelist()
def get_advanced_item_filters_dict(custom_filters):
    custom_filters = json.loads(custom_filters)
    filters = []

    for filter in custom_filters:
        if filter["type"] == "Item":
            get_item_filters(filter, filters)
        
        if filter["type"] == "Item Attribute":
            options = [""]
            options.extend(frappe.get_all("Item Attribute Value",filters={"parent": filter["attribute"]}, pluck="attribute_value"))
            field_name = filter["attribute"].lower().replace(" ", "_")
            filters.append({
                "doctype": "Item Attribute Value",
                "field_type": "Select",
                "fieldname": field_name,
                "label": filter["attribute"],
                "options": options,
                "selected": None
            })
    return filters

def get_item_filters(filter, filters):
    if filter["field_type"] == "Link":
        filters.append({
            "field_type": filter["field_type"],
            "fieldname": filter["item_field_name"],
            "label": filter["item_field"],
            "doctype": filter["field_options"],
            "options": None,
            "selected": None
        })
    elif filter["field_type"] == "Select":
        options = [""]
        options.extend(filter["field_options"].split("\n"))
        filters.append({
            "doctype": None,
            "field_type": filter["field_type"],
            "fieldname": filter["item_field_name"],
            "label": filter["item_field"],
            "options": options,
            "selected": None
        })
    else:
        filters.append({
            "doctype": None,
            "field_type": filter["field_type"],
            "fieldname": filter["item_field_name"],
            "label": filter["item_field"],
            "options": None,
            "selected": None
        })
