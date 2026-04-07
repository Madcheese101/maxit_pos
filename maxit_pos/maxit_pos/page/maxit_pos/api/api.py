import json
from unittest import result
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
from erpnext.accounts.doctype.pos_closing_entry.pos_closing_entry import get_invoices

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
def get_last_invoice_for_print(pos_profile, creator_only=False):
    filters={
        "pos_profile": pos_profile, 
        "docstatus": 1,
        "posting_date": frappe.utils.today(),
        }
    if creator_only:
        filters["owner"] = frappe.session.user
    try:
        sales_invoice = frappe.get_last_doc('Sales Invoice', filters=filters)
    except:
        sales_invoice = None
    result = sales_invoice.name if sales_invoice else ''
    return result

@frappe.whitelist()
def create_and_submit_pos_closing_entry(pos_profile, company, pos_opening_entry):
    opening_entry = frappe.get_doc("POS Opening Entry", pos_opening_entry)

    if opening_entry.status != "Open":
        frappe.throw(_("Selected POS Opening Entry should be open."), title=_("Invalid Opening Entry"))

    end_time = frappe.utils.now_datetime()
    data = get_invoices(opening_entry.period_start_date, end_time, pos_profile, frappe.session.user)

    closing_entry = frappe.new_doc("POS Closing Entry")
    closing_entry.pos_profile = pos_profile
    closing_entry.user = frappe.session.user
    closing_entry.company = company
    closing_entry.pos_opening_entry = pos_opening_entry
    closing_entry.period_start_date = opening_entry.period_start_date
    closing_entry.period_end_date = end_time
    closing_entry.posting_date = frappe.utils.nowdate()
    closing_entry.posting_time = frappe.utils.nowtime()

    for detail in opening_entry.balance_details:
        closing_entry.append(
            "payment_reconciliation",
            {
                "mode_of_payment": detail.mode_of_payment,
                "opening_amount": detail.opening_amount,
                "expected_amount": detail.opening_amount,
                "closing_amount": detail.opening_amount,
                "difference": 0,
            },
        )

    for invoice in data.get("invoices", []):
        if invoice.get("doctype") == "POS Invoice":
            closing_entry.append(
                "pos_invoices",
                {
                    "posting_date": invoice.get("posting_date"),
                    "grand_total": invoice.get("grand_total"),
                    "customer": invoice.get("customer"),
                    "is_return": invoice.get("is_return"),
                    "return_against": invoice.get("return_against"),
                    "pos_invoice": invoice.get("name"),
                },
            )
        else:
            closing_entry.append(
                "sales_invoices",
                {
                    "posting_date": invoice.get("posting_date"),
                    "grand_total": invoice.get("grand_total"),
                    "customer": invoice.get("customer"),
                    "is_return": invoice.get("is_return"),
                    "return_against": invoice.get("return_against"),
                    "sales_invoice": invoice.get("name"),
                },
            )

        closing_entry.grand_total = (closing_entry.grand_total or 0) + (invoice.get("grand_total") or 0)
        closing_entry.net_total = (closing_entry.net_total or 0) + (invoice.get("net_total") or 0)
        closing_entry.total_quantity = (closing_entry.total_quantity or 0) + (invoice.get("total_qty") or 0)
        closing_entry.total_taxes_and_charges = (closing_entry.total_taxes_and_charges or 0) + (
            invoice.get("total_taxes_and_charges") or 0
        )

    for payment in data.get("payments", []):
        existing = next(
            (
                row
                for row in closing_entry.payment_reconciliation
                if row.mode_of_payment == payment.get("mode_of_payment")
            ),
            None,
        )

        if existing:
            existing.expected_amount = (existing.expected_amount or 0) + (payment.get("amount") or 0)
            existing.closing_amount = existing.expected_amount
            existing.difference = 0
        else:
            amount = payment.get("amount") or 0
            closing_entry.append(
                "payment_reconciliation",
                {
                    "mode_of_payment": payment.get("mode_of_payment"),
                    "opening_amount": 0,
                    "expected_amount": amount,
                    "closing_amount": amount,
                    "difference": 0,
                },
            )

    for tax in data.get("taxes", []):
        closing_entry.append(
            "taxes",
            {
                "account_head": tax.get("account_head"),
                "amount": tax.get("tax_amount"),
            },
        )

    closing_entry.flags.ignore_permissions = True
    closing_entry.insert()
    closing_entry.submit()

    return closing_entry.name

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
def get_sales_invoice_list(pos_profile, search_term="", customer=""):
    SalesInvoice = DocType("Sales Invoice")
    query = (frappe.qb.from_(SalesInvoice)
        .select(
            SalesInvoice.name,
            SalesInvoice.customer,
            SalesInvoice.grand_total,
            SalesInvoice.status
        )
        .where(SalesInvoice.pos_profile == pos_profile)
        .where(SalesInvoice.docstatus == 1)
        .orderby(SalesInvoice.modified, order=Order.desc)
        .limit(50)
    )

    if customer:
        query = query.where(SalesInvoice.customer == customer)

    if search_term:
        query = query.where(
            SalesInvoice.name.like(f"%{search_term}%")
            | SalesInvoice.customer.like(f"%{search_term}%")
        )

    invoices = query.run(as_dict=1)

    return invoices

@frappe.whitelist()
def get_customers_list(search_term=""):
    Customer = DocType("Customer")
    query = (
        frappe.qb.from_(Customer)
        .select(
            Customer.name,
            Customer.customer_name,
            Customer.customer_primary_contact,
            Customer.customer_primary_address,
            Customer.mobile_no,
            Customer.email_id,
        )
        .orderby(Customer.modified, order=Order.desc)
        .limit(200)
    )

    if search_term:
        query = query.where(
            Customer.name.like(f"%{search_term}%")
            | Customer.customer_name.like(f"%{search_term}%")
            | Customer.mobile_no.like(f"%{search_term}%")
        )

    customers = query.run(as_dict=1)

    customer_names = [customer.get("name") for customer in customers if customer.get("name")]

    customer_contact_names_map = {name: [] for name in customer_names}
    customer_address_names_map = {name: [] for name in customer_names}

    if customer_names:
        dynamic_links = frappe.get_all(
            "Dynamic Link",
            filters={
                "link_doctype": "Customer",
                "link_name": ["in", customer_names],
                "parenttype": ["in", ["Contact", "Address"]],
            },
            fields=["parent", "parenttype", "link_name"],
            limit=5000,
        )

        for link in dynamic_links:
            customer_name = link.get("link_name")
            parent_name = link.get("parent")
            parenttype = link.get("parenttype")

            if not customer_name or not parent_name:
                continue

            if parenttype == "Contact" and parent_name not in customer_contact_names_map.get(customer_name, []):
                customer_contact_names_map[customer_name].append(parent_name)

            if parenttype == "Address" and parent_name not in customer_address_names_map.get(customer_name, []):
                customer_address_names_map[customer_name].append(parent_name)

    contact_names = list(
        {
            contact_name
            for contact_list in customer_contact_names_map.values()
            for contact_name in contact_list
        }
    )
    address_names = list(
        {
            address_name
            for address_list in customer_address_names_map.values()
            for address_name in address_list
        }
    )

    for customer in customers:
        primary_contact = customer.get("customer_primary_contact")
        primary_address = customer.get("customer_primary_address")
        customer_name = customer.get("name")

        if primary_contact and primary_contact not in customer_contact_names_map.get(customer_name, []):
            customer_contact_names_map[customer_name].append(primary_contact)
            contact_names.append(primary_contact)

        if primary_address and primary_address not in customer_address_names_map.get(customer_name, []):
            customer_address_names_map[customer_name].append(primary_address)
            address_names.append(primary_address)

    addresses_map = {}
    if address_names:
        addresses = frappe.get_all(
            "Address",
            filters={"name": ["in", address_names]},
            fields=["name", "address_line1", "address_line2", "city", "state", "country", "pincode"],
            limit=500,
        )
        addresses_map = {address.get("name"): address for address in addresses}

    invoices_count_map = {}
    if customer_names:
        invoice_counts = frappe.qb.get_query(
            "Sales Invoice",
            filters={
                "customer": ["in", customer_names],
                "docstatus": ["!=", 2],
            },
            fields=["customer", {"COUNT": "name", "as": "invoice_count"}],
            group_by="customer",
            limit=500,
        ).run(as_dict=True)
        invoices_count_map = {
            row.get("customer"): int(row.get("invoice_count") or 0)
            for row in invoice_counts
        }

    enriched_customers = []
    for customer in customers:
        customer_name = customer.get("name")
        address = addresses_map.get(customer.get("customer_primary_address"), {})

        contact_options = sorted(customer_contact_names_map.get(customer_name, []))
        address_options = sorted(customer_address_names_map.get(customer_name, []))

        full_address = ", ".join(
            [
                part
                for part in [
                    address.get("address_line1"),
                    address.get("address_line2"),
                    address.get("city"),
                    address.get("state"),
                    address.get("country"),
                    address.get("pincode"),
                ]
                if part
            ]
        )

        enriched_customers.append(
            {
                **customer,
                "address_display": full_address,
                "linked_invoices": invoices_count_map.get(customer_name, 0),
                "contact_options": contact_options,
                "address_options": address_options,
            }
        )

    return enriched_customers

@frappe.whitelist()
def update_customer_name(customer, customer_name=None, customer_primary_contact=None, customer_primary_address=None):
    if not customer:
        frappe.throw(_("Customer is required."))

    customer_doc = frappe.get_doc("Customer", customer)
    customer_links = _get_customer_links(customer)

    contact_value = customer_primary_contact.strip() if isinstance(customer_primary_contact, str) else customer_primary_contact
    address_value = customer_primary_address.strip() if isinstance(customer_primary_address, str) else customer_primary_address

    if contact_value and contact_value not in customer_links.get("contacts", []) and contact_value != customer_doc.customer_primary_contact:
        frappe.throw(_("Contact {0} is not linked to Customer {1}.").format(contact_value, customer))

    if address_value and address_value not in customer_links.get("addresses", []) and address_value != customer_doc.customer_primary_address:
        frappe.throw(_("Address {0} is not linked to Customer {1}.").format(address_value, customer))

    if customer_name is not None:
        customer_doc.customer_name = customer_name or customer

    if customer_primary_contact is not None:
        customer_doc.customer_primary_contact = contact_value or None

    if customer_primary_address is not None:
        customer_doc.customer_primary_address = address_value or None

    customer_doc.save()

    contact_doc = None
    if customer_doc.customer_primary_contact:
        contact_doc = frappe.db.get_value(
            "Contact",
            customer_doc.customer_primary_contact,
            ["email_id", "mobile_no", "phone"],
            as_dict=True,
        )

    address_doc = None
    if customer_doc.customer_primary_address:
        address_doc = frappe.db.get_value(
            "Address",
            customer_doc.customer_primary_address,
            ["address_line1", "address_line2", "city", "state", "country", "pincode"],
            as_dict=True,
        )

    address_display = ""
    if address_doc:
        address_display = ", ".join(
            [
                part
                for part in [
                    address_doc.get("address_line1"),
                    address_doc.get("address_line2"),
                    address_doc.get("city"),
                    address_doc.get("state"),
                    address_doc.get("country"),
                    address_doc.get("pincode"),
                ]
                if part
            ]
        )

    contact_options = set(customer_links.get("contacts", []))
    address_options = set(customer_links.get("addresses", []))

    if customer_doc.customer_primary_contact:
        contact_options.add(customer_doc.customer_primary_contact)

    if customer_doc.customer_primary_address:
        address_options.add(customer_doc.customer_primary_address)

    return {
        "name": customer_doc.name,
        "customer_name": customer_doc.customer_name,
        "customer_primary_contact": customer_doc.customer_primary_contact,
        "customer_primary_address": customer_doc.customer_primary_address,
        "email_id": (contact_doc or {}).get("email_id", ""),
        "mobile_no": (contact_doc or {}).get("mobile_no", ""),
        "phone": (contact_doc or {}).get("phone", ""),
        "address_display": address_display,
        "contact_options": sorted(contact_options),
        "address_options": sorted(address_options),
    }

def _get_customer_links(customer_name):
    links = frappe.get_all(
        "Dynamic Link",
        filters={
            "link_doctype": "Customer",
            "link_name": customer_name,
            "parenttype": ["in", ["Contact", "Address"]],
        },
        fields=["parent", "parenttype"],
        limit=1000,
    )

    contact_names = []
    address_names = []

    for link in links:
        parent_name = link.get("parent")
        parenttype = link.get("parenttype")

        if parenttype == "Contact" and parent_name and parent_name not in contact_names:
            contact_names.append(parent_name)

        if parenttype == "Address" and parent_name and parent_name not in address_names:
            address_names.append(parent_name)

    return {
        "contacts": contact_names,
        "addresses": address_names,
    }

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
        field_options = frappe.get_list(filter["field_options"], pluck="name")
        filters.append({
            "field_type": filter["field_type"],
            "fieldname": filter["item_field_name"],
            "label": filter["item_field"],
            "doctype": filter["field_options"],
            "options": field_options,
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

def _build_pos_item_group_cache_key(pos_profile):
    profile_key = str(pos_profile or "default")
    return f"pos_item_groups::{profile_key}"

def _clear_pos_item_group_cache_for_profile(pos_profile):
    frappe.cache().delete_value(_build_pos_item_group_cache_key(pos_profile))

def _clear_pos_item_group_cache_for_all_profiles():
    profiles = frappe.get_all("POS Profile", pluck="name")
    for profile_key in profiles:
        frappe.cache().delete_value(f"pos_item_groups::{profile_key}")

def on_pos_profile_cache_invalidate(doc=None, method=None, *args, **kwargs):
    _clear_pos_item_group_cache_for_profile(doc.name)

def on_item_group_cache_invalidate(doc=None, method=None, *args, **kwargs):
    _clear_pos_item_group_cache_for_all_profiles()

@frappe.whitelist()
def reset_item_group_cache(pos_profile=None):
    if pos_profile:
        _clear_pos_item_group_cache_for_profile(pos_profile)
        return {
            "status": "ok",
            "scope": "profile",
            "pos_profile": pos_profile,
        }

    _clear_pos_item_group_cache_for_all_profiles()
    return {
        "status": "ok",
        "scope": "all",
    }

@frappe.whitelist()
def get_item_group_list(allowed_item_groups, pos_profile):
    if isinstance(allowed_item_groups, str):
        allowed_item_groups = json.loads(allowed_item_groups)

    allowed_item_groups = allowed_item_groups or []
    cache_key = _build_pos_item_group_cache_key(pos_profile)
    cached = frappe.cache().get_value(cache_key)
    if cached is not None:
        return cached

    data = []
    parents = []
    seen = set()
    
    def add_group(name):
        if name and name not in seen:
            seen.add(name)
            data.append(name)

    for item_group in allowed_item_groups:
        if item_group.get("is_group"):
            parents.append(item_group.get("item_group"))
        else:
            add_group(item_group.get("item_group"))

    # Fetch descendants of all parent groups and add only leaf (is_group=0) groups
    for name in parents:
        child_groups = frappe.get_list(
            "Item Group",
            filters={"name": ['descendants of', name], "is_group": 0},
            pluck="name"
        )
        for cg in child_groups:
            add_group(cg)

    # If no data, fetch all groups
    if not data:
        data = frappe.get_list("Item Group", filters={"is_group": 0}, pluck="name", group_by="name") or []

    frappe.cache().set_value(cache_key, data)
    return data

def _attach_item_attributes(items):
    item_codes = [item.get("item_code") for item in items if item.get("item_code")]
    if not item_codes:
        return

    ItemVariantAttribute = DocType("Item Variant Attribute")
    attribute_rows = (
        frappe.qb.from_(ItemVariantAttribute)
        .select(
            ItemVariantAttribute.parent,
            ItemVariantAttribute.attribute,
            ItemVariantAttribute.attribute_value,
        )
        .where(ItemVariantAttribute.parent.isin(item_codes))
    ).run(as_dict=True)

    attributes_map = {}
    for row in attribute_rows:
        item_code = row.get("parent")
        attribute_label = row.get("attribute") or ""
        attribute_value = row.get("attribute_value")
        if not item_code or not attribute_label:
            continue

        fieldname = attribute_label.lower().replace(" ", "_")
        if item_code not in attributes_map:
            attributes_map[item_code] = {}
        attributes_map[item_code][fieldname] = attribute_value

    for item in items:
        item_attributes = attributes_map.get(item.get("item_code"), {})
        item["attributes"] = item_attributes
        item["size"] = item_attributes.get("size", "")
        item["color"] = item_attributes.get("color", "")

        for key, value in item_attributes.items():
            if key not in item:
                item[key] = value

def _is_active_browser_filter(filter_dict):
    if filter_dict.get("field_type") == "Check":
        return filter_dict.get("selected") is True
    selected = filter_dict.get("selected")
    return selected not in (None, "")

def _append_browser_filter(query_filters, attribute_filters, filter_dict):
    if not _is_active_browser_filter(filter_dict):
        return

    if filter_dict.get("doctype") == "Item Attribute Value":
        attribute_filters.append(filter_dict.get("selected"))
        return

    fieldname = filter_dict.get("fieldname")
    field_type = filter_dict.get("field_type")
    selected = filter_dict.get("selected")

    if not fieldname:
        return

    if field_type == "Check":
        query_filters.append([fieldname, "=", 1])
    elif field_type in ("Select", "Link"):
        query_filters.append([fieldname, "=", selected])
    else:
        query_filters.append([fieldname, "like", f"%{selected}%"])

@frappe.whitelist()
def get_items_browser(pos_profile_data, search_term="", custom_filters=[]):
    if isinstance(pos_profile_data, str):
        pos_profile_data = json.loads(pos_profile_data)

    if isinstance(custom_filters, str):
        custom_filters = json.loads(custom_filters)

    pos_profile_data = frappe._dict(pos_profile_data)

    warehouse = pos_profile_data.warehouse
    price_list = pos_profile_data.selling_price_list
    hide_unavailable_items = pos_profile_data.hide_unavailable_items
    allowed_item_groups = pos_profile_data.item_groups or []
    item_table = frappe.qb.DocType("Item")

    attribute_values_filter = []
    result = []
    items_uoms = {}
    filters = [
        ["disabled", "=", 0],
        ["has_variants", "=", 0],
        ["is_sales_item", "=", 1],
        ["is_fixed_asset", "=", 0],
    ]
    if allowed_item_groups:
        allowed_groups = get_item_group_list(allowed_item_groups, pos_profile_data.name)
        filters.append(["item_group", "in", allowed_groups])

    if search_term:
        search_term = search_term.strip()
        filters.append(
            (item_table.name.like(f"%{search_term}%")) | (item_table.item_name.like(f"%{search_term}%"))
        )

    query_fields = [
        "name",
        "name as item_code",
        "description",
        "stock_uom",
        "image as item_image",
        "is_stock_item",
        "sales_uom",
        "item_group",
        "item_name",
        {"uoms": ["uom"]},
    ]

    extra_item_fields = []
    for custom_filter in custom_filters or []:
        _append_browser_filter(filters, attribute_values_filter, custom_filter)

        fieldname = custom_filter.get("fieldname") or custom_filter.get("item_field_name")
        if not fieldname:
            continue
        if custom_filter.get("doctype") == "Item Attribute Value":
            continue
        if fieldname in [
            "name",
            "item_code",
            "description",
            "stock_uom",
            "item_image",
            "is_stock_item",
            "sales_uom",
            "item_group",
            "item_name",
        ]:
            continue
        extra_item_fields.append(fieldname)

    query_fields.extend(list(set(extra_item_fields)))

    query = frappe.qb.get_query(
        "Item",
        fields=query_fields,
        filters=filters,
    )

    query = join_bin(query, warehouse, hide_unavailable_items, item_table)

    if attribute_values_filter:
        att_table = DocType("Item Variant Attribute")
        subquery = (
            frappe.qb
            .from_(att_table)
            .select(att_table.parent)
            .where(att_table.attribute_value.isin(attribute_values_filter))
            .groupby(att_table.parent)
            .having(functions.Count("*") == len(attribute_values_filter))
        )
        query = query.where(item_table.name.isin(subquery))

    items_data = query.run(as_dict=True)
    if not items_data:
        return {"items": result, "items_uoms": items_uoms}

    process_items_data(result, items_uoms, items_data, hide_unavailable_items, warehouse, price_list)
    _attach_item_attributes(result)

    return {"items": result, "items_uoms": items_uoms}

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
    allowed_item_groups = pos_profile_data.item_groups or []
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

    if allowed_item_groups and not item_group:
        allowed_groups = get_item_group_list(allowed_item_groups, pos_profile_data.name)
        filters.append(["item_group", "in", allowed_groups])

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
            "max_discount",
            {"uoms": ["uom"]}
        ],
        filters=filters,
        limit=pos_profile_data.max_items_listing or 100,
        offset=0,
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
        items_uoms[item.item_code] = [u.uom for u in item.get("uoms", [])]
        
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