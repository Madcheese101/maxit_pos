import frappe
def extend_boot_info(bootinfo):
    if "user_branch" not in frappe.session.data:
        set_user_branch_in_session()

    branch = frappe.session.data.get("user_branch", None)
    bootinfo["user_branch"] = branch

def set_user_branch_in_session():
    branch = frappe.db.get_value("Employee", {"user_id": frappe.session.user}, "branch")
    # Adding data to the session
    frappe.session.data["user_branch"] = branch
    # Persisting the change to the database and cache  
    frappe.local.session_obj.update(force=True)