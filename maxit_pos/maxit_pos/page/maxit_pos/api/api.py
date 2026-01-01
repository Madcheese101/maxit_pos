import json
import frappe

from erpnext.stock.get_item_details import get_conversion_factor
from frappe.query_builder import Field, functions, Query, DocType
from erpnext.selling.page.point_of_sale.point_of_sale import (
    search_by_term, 
    filter_result_items, 
    get_stock_availability,
)

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

@frappe.whitelist()
def get_item_group_list():
    return frappe.get_all("Item Group", filters={"is_group": 0}, pluck="name", group_by="name") or []

@frappe.whitelist()
def get_items(pos_profile_data, search_term="", item_group=None, custom_filters=[]):
    
    if isinstance(pos_profile_data, str):
        pos_profile_data = json.loads(pos_profile_data)

    if isinstance(custom_filters, str):
        custom_filters = json.loads(custom_filters)

    pos_profile_data = frappe._dict(pos_profile_data)

    warehouse = pos_profile_data.warehouse
    price_list = pos_profile_data.selling_price_list
    pos_profile = pos_profile_data.name
    hide_unavailable_items = pos_profile_data.hide_unavailable_items
    item_table = frappe.qb.DocType("Item")

    attribute_values_filter = []
    result = []
    filters = [
        ["disabled", "=", 0],
        ["has_variants", "=", 0],
        ["is_sales_item", "=", 1],
        ["is_fixed_asset", "=", 0]
    ]

    if search_term: 
        # this will look for items by barcode, batch_no, serial_no
        result = search_by_term(search_term, warehouse, price_list) or []
        filter_result_items(result, pos_profile)
        if result:
            return result
        # if no result then search by name
        filters.append(
            (item_table.name.like(f"%{search_term}%")) | (item_table.item_name.like(f"%{search_term}%"))
        )
    
    
    if item_group:
        filters.append(["item_group", "=", item_group])
        
    for filter in custom_filters:
        if not filter["selected"]: continue
        # frappe.throw(str(filter))

        if filter["doctype"] == "Item Attribute Value":
            attribute_values_filter.append(filter["selected"])
        else:
            filters.append(
                [filter["fieldname"], "like", f"%{filter['selected']}%"]
            )

    # base query
    query = frappe.qb.get_query(
        "Item",
        fields=[
            "name",
            "name as item_code",
            "description",
            "stock_uom",
			"image as item_image",
			"is_stock_item",
			"sales_uom",
            "item_group",
            "item_name",
            {"uoms": ["uom"]}
        ],
        filters=filters
    )

    query = join_bin(query, warehouse, hide_unavailable_items, item_table)
    
    # filter item names that have all required attribute values
    if attribute_values_filter:
        att_table = DocType("Item Variant Attribute")
        # item names that have all required values
        subquery = (
            frappe.qb
                .from_(att_table)
                .select(att_table.parent)
                .where(att_table.attribute_value.isin(attribute_values_filter))
                .groupby(att_table.parent)
                .having(functions.Count("*") == len(attribute_values_filter))
        )
        # update query filters
        query = query.where(item_table.name.isin(subquery))
    
    items_data = query.run(as_dict=True)
    
    if not items_data: return result
    
    process_items_data(result, items_data, hide_unavailable_items, warehouse, price_list)

    return result

def join_bin(query, warehouse, hide_unavailable_items,item_table):
    bin_table = frappe.qb.DocType("Bin")
    
    # update query
    if hide_unavailable_items:
        bin_filter = (item_table.is_stock_item == 0) | (bin_table.warehouse == warehouse) & (bin_table.actual_qty > 0)
        actual_qty = functions.Coalesce(
            (bin_table.actual_qty - 
            bin_table.reserved_qty), 0).as_("actual_qty")
        query = (query
            # .select(actual_qty)
            .join(bin_table)
            .on(bin_table.item_code == item_table.name)
            .where(bin_filter)
        )
    return query

def process_items_data(result: list, items_data: list, hide_unavailable_items, warehouse: str, price_list: str):
    current_date = frappe.utils.today()
    for item in items_data:
        item.pop("name")
        if item.is_stock_item:
            item.actual_qty, _ = get_stock_availability(item.item_code, warehouse)
        else:
            item.actual_qty = 0
        
        if item.is_stock_item and hide_unavailable_items and item.actual_qty == 0:
            continue
        item_prices = frappe.get_all(
            "Item Price",
            fields=["price_list_rate", "currency", "uom", "batch_no", "valid_from", "valid_upto"],
            filters={
                "price_list": price_list,
                "item_code": item.item_code,
                "selling": True,
                "valid_from": ["<=", current_date],
                "valid_upto": ["in", [None, "", current_date]],
            },
            order_by="valid_from desc",
        )

        stock_uom_price = next((d for d in item_prices if d.get("uom") == item.stock_uom), {})
        item_uom = item.stock_uom
        item_uom_price = stock_uom_price

        if item.sales_uom and item.sales_uom != item.stock_uom:
            item_uom = item.sales_uom
            sales_uom_price = next((d for d in item_prices if d.get("uom") == item.sales_uom), {})
            if sales_uom_price:
                item_uom_price = sales_uom_price

        if item_prices and not item_uom_price:
            item_uom = item_prices[0].get("uom")
            item_uom_price = item_prices[0]

        item_conversion_factor = get_conversion_factor(item.item_code, item_uom).get("conversion_factor")

        if item.stock_uom != item_uom:
            item.actual_qty = item.actual_qty // item_conversion_factor

        if item_uom_price and item_uom != item_uom_price.get("uom"):
            item_uom_price.price_list_rate = item_uom_price.price_list_rate * item_conversion_factor
        
        item.uoms = [u.uom for u in item.uoms]
        result.append(
            {
                **item,
                "price_list_rate": item_uom_price.get("price_list_rate"),
                "rate": item_uom_price.get("price_list_rate"),
                "currency": item_uom_price.get("currency"),
                "uom": item_uom,
                "batch_no": item_uom_price.get("batch_no"),
            }
        )