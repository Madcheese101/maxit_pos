import frappe
from maxit_pos.maxit_pos.page.maxit_pos.api.api import create_and_submit_pos_closing_entry
def close_sifts():
    opening_shifts = frappe.get_all("POS Opening Entry", filters={"status": "Open"}, fields=["name", "pos_profile", "company"])
    for shift in opening_shifts:
        closing_entry_name, user = create_and_submit_pos_closing_entry(shift["pos_profile"], shift["company"], shift["name"])
        publish_progress(closing_entry_name, user)

def publish_progress(closing_entry_name, user_name):
    frappe.publish_realtime(
        "shift_closed",
        {
            "closing_entry_name": closing_entry_name,
            "user_name": user_name
        },
        user=user_name
    )