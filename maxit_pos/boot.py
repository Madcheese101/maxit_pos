import frappe
def extend_boot_info(bootinfo):
    if "user_branch" not in frappe.session.data:
        set_user_branch_in_session()

    branch = frappe.session.data.get("user_branch", None)
    user_warehouse = frappe.session.data.get("user_warehouse", None)
    bootinfo["user_branch"] = branch
    bootinfo["user_warehouse"] = user_warehouse

def set_user_branch_in_session():
    branch = None
    expense_approver = None
    company = None
    empl_exists = frappe.db.exists("Employee", {"user_id": frappe.session.user})
    if empl_exists:
        branch, expense_approver, company = frappe.db.get_value("Employee", {"user_id": frappe.session.user}, ["branch", "expense_approver", "company"])
    # Adding data to the session  
    frappe.session.data["user_branch"] = branch
    frappe.session.data["expense_approver"] = expense_approver
    frappe.session.data["company"] = company
    if branch:
        frappe.session.data["user_warehouse"] = frappe.db.get_value("Branch", branch, "material_warehouse")
    # Persisting the change to the database and cache  
    frappe.local.session_obj.update(force=True)