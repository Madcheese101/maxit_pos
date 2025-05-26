import frappe

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
            mapper[field["label"]] = {"fieldname": field["fieldname"], 
                                      "fieldtype": field["fieldtype"], 
                                      "options": field["options"]}


    result = {"field_labels": field_labels, "mapper": mapper}
    return result