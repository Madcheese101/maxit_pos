import frappe
from frappe import _
from frappe.utils import cint, flt, get_link_to_form, nowtime

import erpnext.accounts.doctype.pos_invoice.pos_invoice as pos_invoice_file
from erpnext.controllers.selling_controller import SellingController
from erpnext.accounts.doctype.pos_opening_entry.pos_opening_entry import POSOpeningEntry
from erpnext.accounts.doctype.sales_invoice.sales_invoice import SalesInvoice

def custom_get_bin_qty(item_code, warehouse):
    actual_qty = 0
    bin_qty = frappe.db.get_all(
        "Bin",
        fields=["actual_qty", "reserved_qty"],
        filters={
            "item_code": item_code,
            "warehouse": warehouse,
        },
        limit=1
    )
    if bin_qty:
        actual_qty = bin_qty[0].actual_qty - bin_qty[0].reserved_qty

    return actual_qty

def check_open_pos_exists(self):
    if frappe.db.exists("POS Opening Entry", {
        "pos_profile": self.pos_profile, 
        "user": self.user,
        "status": "Open",
        "name": ["!=", self.name] if self.name else None
        }):
        frappe.throw(
            title=_("POS Opening Entry Exists"),
            msg=_(
                "{0} is open. Close the POS or cancel the existing POS Opening Entry to create a new POS Opening Entry."
            ).format(frappe.bold(self.pos_profile)),
        )

def validate_pos_opening_entry(self):
    opening_entries = frappe.get_all(
        "POS Opening Entry",
        fields=["name", "period_start_date"],
        filters={
            "pos_profile": self.pos_profile,
            "user": frappe.session.user, 
            "status": "Open"
        },
        order_by="period_start_date desc",
    )
    if not opening_entries:
        frappe.throw(
            title=_("POS Opening Entry Missing"),
            msg=_("No open POS Opening Entry found for POS Profile {0}.").format(
                frappe.bold(self.pos_profile)
            ),
        )
    # if len(opening_entries) > 1:
    # 	frappe.throw(
    # 		title=_("Multiple POS Opening Entry"),
    # 		msg=_(
    # 			"POS Profile - {0} has multiple open POS Opening Entries. Please close or cancel the existing entries before proceeding."
    # 		).format(self.pos_profile),
    # 	)
    if frappe.utils.get_date_str(opening_entries[0].get("period_start_date")) != frappe.utils.today():
        frappe.throw(
            title=_("Outdated POS Opening Entry"),
            msg=_(
                "POS Opening Entry - {0} is outdated. Please close the POS and create a new POS Opening Entry."
            ).format(opening_entries[0].get("name")),
        )

def validate_max_discount_(self):
    for d in self.get("items"):
        if d.item_code:
            discount = flt(frappe.get_cached_value("Item", d.item_code, "max_discount"))
            if discount and flt(d.discount_percentage) > discount:
                frappe.throw(f"Discount for {d.item_code} in row {d.idx} cannot exceed {discount}%")

def override_methods():
    pos_invoice_file.get_bin_qty = custom_get_bin_qty
    SellingController.validate_max_discount = validate_max_discount_
    POSOpeningEntry.check_open_pos_exists = check_open_pos_exists
    SalesInvoice.validate_pos_opening_entry = validate_pos_opening_entry