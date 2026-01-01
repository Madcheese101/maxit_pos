import frappe
from pypika.terms import Case, ValueWrapper
from frappe.query_builder import Field, functions, Query, DocType

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


def console_test():
    # Define tables
    item_table = DocType("Item")
    att_table = DocType("Item Variant Attribute")

    # Values to check for
    required_values = ['Large']
   
    # Subquery: item names that have all required values
    subquery = (
        frappe.qb
        .from_(att_table)
        .select(att_table.parent)
        .where(att_table.attribute_value.isin(required_values))
        .groupby(att_table.parent)
        .having(functions.Count("*") == len(required_values))
    )

    # Main query: filter Item names that are in the subquery
    query = (
        frappe.qb.get_query(
            "Item",
            fields=["name"],
            filters={"variant_of": ["is", "set"]}
        )
        .where(item_table.name.isin(subquery))
    )

    print(query.get_sql())
    results = query.run(as_dict=True)
    print(str(results))
# from maxit_pos.maxit_pos.api import console_test
# console_test()

def console_method_test():
    from maxit_pos.maxit_pos.page.maxit_pos.api.api import get_items
    pos_profile = frappe.get_doc("POS Profile", "Demo POS Profile")
    custom_filters = [
            {"doctype": "Item Attribute", "selected": "Large"},
        ]
    results = get_items(pos_profile, search_term="", item_group="", custom_filters=[])
    print(str(results))
# from maxit_pos.maxit_pos.api import console_method_test