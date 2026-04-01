import json
import frappe
from frappe import _
from pypika.terms import Case, ValueWrapper
from frappe.query_builder import DocType, Order
from erpnext.stock.get_item_details import get_conversion_factor
from frappe.query_builder import Field, functions, Query, DocType
from erpnext.selling.page.point_of_sale.point_of_sale import (
    search_by_term, 
    filter_result_items, 
    get_stock_availability,
)
from erpnext.accounts.party import get_party_account
from erpnext.accounts.utils import get_account_currency
from erpnext.accounts.doctype.journal_entry.journal_entry import (
    get_default_bank_cash_account,
)
from erpnext.setup.utils import get_exchange_rate
from erpnext.accounts.doctype.bank_account.bank_account import get_party_bank_account

@frappe.whitelist()
def save_invoice_as_sales_order(invoice_name):
    invoice = frappe.get_doc("Sales Invoice", invoice_name)

    sales_order = frappe.new_doc("Sales Order")
    sales_order.customer = invoice.customer
    sales_order.company = invoice.company
    sales_order.transaction_date = frappe.utils.today()
    # sales_order.po_no = invoice.po_no
    # sales_order.po_date = invoice.po_date
    sales_order.currency = invoice.currency
    sales_order.selling_price_list = invoice.selling_price_list
    sales_order.price_list_currency = invoice.price_list_currency
    sales_order.conversion_rate = invoice.conversion_rate
    sales_order.set_warehouse = invoice.set_warehouse
    for item in invoice.items:
        sales_order.append("items", {
            "delivery_date": frappe.utils.today(),
            "item_code": item.item_code,
            "item_name": item.item_name,
            "description": item.description,
            "qty": item.qty,
            "uom": item.uom,
            "stock_uom": item.stock_uom,
            "conversion_factor": item.conversion_factor,
            "rate": item.rate,
            "price_list_rate": item.price_list_rate,
            "amount": item.amount,
            "warehouse": item.warehouse,
            "batch_no": item.batch_no,
            "serial_no": item.serial_no,
            "income_account": item.income_account,
            "cost_center": item.cost_center,
        })

    # Copy taxes and charges if any
    for tax in invoice.taxes:
        sales_order.append("taxes", {
            "charge_type": tax.charge_type,
            "account_head": tax.account_head,
            "description": tax.description,
            "rate": tax.rate,
            "tax_amount": tax.tax_amount,
            "total": tax.total,
            "tax_amount_after_discount_amount": tax.tax_amount_after_discount_amount,
        })

    # Copy other fields as needed
    sales_order.ignore_permissions = True
    sales_order.save()
    return sales_order.name

@frappe.whitelist()
def cancel_invoice(name):
    invoice = frappe.get_doc("Sales Invoice", name)
    if invoice.docstatus == 1:
        invoice.cancel()
    return invoice

@frappe.whitelist()
def delete_invoice(name):
    invoice = frappe.get_doc("Sales Invoice", name)
    if invoice.docstatus == 0:
        invoice.delete()

@frappe.whitelist()
def pay_invoice(doc, payments):
    sinv = json.loads(doc)
    payment_type = "Receive"
    payments = json.loads(payments)
    for payment in payments:
        if payment.get("amount") <= 0: continue
        party_account = get_party_account("Customer", sinv.get("customer"), sinv.get("company"))
        party_account_currency = get_account_currency(party_account)
        if party_account_currency != sinv.get("price_list_currency"):
            frappe.throw(
                _(
                    "Currency is not correct, party account currency is {party_account_currency} and transaction currency is {currency}"
                ).format(party_account_currency=party_account_currency, currency=payment.get("price_list_currency"))
            )

        bank = get_bank_cash_account(sinv.get("company"), payment.get("mode_of_payment"))
        company_currency = frappe.get_value("Company", sinv.get("company"), "default_currency")
        conversion_rate = get_exchange_rate(payment.get("price_list_currency"), company_currency, frappe.utils.today(), "for_selling")
        paid_amount, received_amount = set_paid_amount_and_received_amount(
            party_account_currency, bank, payment.get("amount"), payment_type, None, conversion_rate
        )

        payment_doc = frappe.new_doc("Payment Entry")
        payment_doc.posting_date = frappe.utils.today()
        payment_doc.mode_of_payment = payment.get("mode_of_payment")
        payment_doc.payment_type = payment_type
        payment_doc.party_type = "Customer"
        payment_doc.party = sinv.get("customer")
        payment_doc.paid_from = party_account if payment_type == "Receive" else bank.account
        payment_doc.paid_to = party_account if payment_type == "Pay" else bank.account
        payment_doc.paid_from_account_currency = (
            party_account_currency if payment_type == "Receive" else bank.account_currency
        )
        payment_doc.paid_to_account_currency = (
            party_account_currency if payment_type == "Pay" else bank.account_currency
        )
        payment_doc.paid_amount = paid_amount
        payment_doc.received_amount = received_amount
        payment_doc.reference_no = sinv.get("name")
        payment_doc.reference_date = frappe.utils.today()
        if payment_doc.party_type in ["Customer", "Supplier"]:
            bank_account = get_party_bank_account(payment_doc.party_type, payment_doc.party)
            payment_doc.set("bank_account", bank_account)
            payment_doc.set_bank_account_data()

        payment_doc.append("references", {
            "reference_doctype": "Sales Invoice",
            "reference_name": sinv.get("name"),
            "allocated_amount": paid_amount,
            "total_amount": sinv.get("grand_total"),
            "outstanding_amount": sinv.get("outstanding_amount"),
        })
        payment_doc.setup_party_account_field()
        payment_doc.set_missing_values()
        if party_account and bank:
            payment_doc.set_amounts()
        payment_doc.ignore_permissions = True
        payment_doc.save()
        payment_doc.submit()

@frappe.whitelist()
def get_invoice_payment_entries(sales_invoice):
    entries = frappe.qb.get_query(
        "Payment Entry",
        fields=[
            "name",
            "posting_date",
            "mode_of_payment",
            "paid_amount",
            "received_amount",
            "paid_from_account_currency",
            "paid_to_account_currency",
        ],
        filters={
            "docstatus": 1,
            "references.reference_name": sales_invoice
        }
    ).run(as_dict=True)
    return entries

def get_bank_cash_account(company, mode_of_payment, bank_account=None):
    bank = get_default_bank_cash_account(
        company, "Bank", mode_of_payment=mode_of_payment, account=bank_account
    )

    if not bank:
        bank = get_default_bank_cash_account(
            company, "Cash", mode_of_payment=mode_of_payment, account=bank_account
        )

    return bank

def set_paid_amount_and_received_amount(
    party_account_currency,
    bank,
    outstanding_amount,
    payment_type,
    bank_amount,
    conversion_rate,
):
    paid_amount = received_amount = 0
    if party_account_currency == bank.account_currency:
        paid_amount = received_amount = abs(outstanding_amount)
    elif payment_type == "Receive":
        paid_amount = abs(outstanding_amount)
        if bank_amount:
            received_amount = bank_amount
        else:
            received_amount = paid_amount * conversion_rate

    else:
        received_amount = abs(outstanding_amount)
        if bank_amount:
            paid_amount = bank_amount
        else:
            # if party account currency and bank currency is different then populate paid amount as well
            paid_amount = received_amount * conversion_rate

    return paid_amount, received_amount

@frappe.whitelist()
def get_held_invoices(pos_profile):
    SalesInvoice = DocType("Sales Invoice")
    invoices = (frappe.qb.from_(SalesInvoice)
        .select(
            SalesInvoice.name,
            SalesInvoice.customer,
            SalesInvoice.grand_total,
            ValueWrapper("Sales Invoice").as_("doctype"),
        )
        .where(SalesInvoice.pos_profile == pos_profile)
        .where(SalesInvoice.docstatus == 0)
        .where(SalesInvoice.is_return == 0)
        .where(SalesInvoice.posting_date == frappe.utils.today())
        .orderby(SalesInvoice.modified, order=Order.desc)
        .limit(50)
    ).run(as_dict=1)

    return invoices

@frappe.whitelist()
def get_sales_orders():
    SalesOrder = DocType("Sales Order")
    invoices = (frappe.qb.from_(SalesOrder)
        .select(
            SalesOrder.name,
            SalesOrder.customer,
            SalesOrder.grand_total,
            ValueWrapper("Sales Order").as_("doctype")
        )
        .where(SalesOrder.docstatus == 1)
        .where(SalesOrder.per_billed ==0) 
        .orderby(SalesOrder.modified, order=Order.desc)
        .limit(50)
    ).run(as_dict=1)

    return invoices

@frappe.whitelist()
def get_sales_invoice_list(pos_profile, search_term=""):
    SalesInvoice = DocType("Sales Invoice")
    invoices = (frappe.qb.from_(SalesInvoice)
        .select(
            SalesInvoice.name,
            SalesInvoice.customer,
            SalesInvoice.grand_total,
            SalesInvoice.status
        )
        .where(SalesInvoice.pos_profile == pos_profile)
        .where(SalesInvoice.docstatus == 1)
        .where(SalesInvoice.name.like(f"%{search_term}%") | 
            SalesInvoice.customer.like(f"%{search_term}%")  
            # | SalesInvoice.mobile_no.like(f"%{search_term}%")
        )
        .orderby(SalesInvoice.modified, order=Order.desc)
        .limit(50)
    ).run(as_dict=1)

    return invoices

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
    items_uoms = {}

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
            return result, items_uoms
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
    
    if not items_data: return result, items_uoms
    
    process_items_data(result, items_uoms, items_data, hide_unavailable_items, warehouse, price_list)

    return result, items_uoms

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

def process_items_data(result: list, items_uoms: list, items_data: list, hide_unavailable_items, warehouse: str, price_list: str):
    current_date = frappe.utils.today()
    for item in items_data:
        item.pop("name")
        if item.is_stock_item:
            item.actual_qty, _, is_negative_stock_allowed = get_stock_availability(item.item_code, warehouse)
        else:
            item.actual_qty = 0
        
        if item.is_stock_item and hide_unavailable_items and item.actual_qty == 0:
            continue
        ItemPrice = DocType("Item Price")
        item_prices = (
            frappe.qb.from_(ItemPrice)
            .select(
                ItemPrice.price_list_rate,
                ItemPrice.currency,
                ItemPrice.uom,
                ItemPrice.batch_no,
                ItemPrice.valid_from,
                ItemPrice.valid_upto,
            )
            .where(ItemPrice.price_list == price_list)
            .where(ItemPrice.item_code == item.item_code)
            .where(ItemPrice.selling == 1)
            .where((ItemPrice.valid_from <= current_date) | (ItemPrice.valid_from.isnull()))
            .where((ItemPrice.valid_upto >= current_date) | (ItemPrice.valid_upto.isnull()))
            .orderby(ItemPrice.valid_from, order=Order.desc)
        ).run(as_dict=True)

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
        
        # item.uoms = [u.uom for u in item.uoms]
        items_uoms[item.item_code] = [u.uom for u in item.uoms]
        
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