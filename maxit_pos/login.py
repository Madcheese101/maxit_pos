import frappe

def on_session_created(login_manager):
    branch = None
    expense_approver = None
    company = None
    empl_exists = frappe.db.exists("Employee", {"user_id": login_manager.user})
    if empl_exists:
        branch, expense_approver, company = frappe.db.get_value("Employee", {"user_id": login_manager.user}, ["branch", "expense_approver", "company"])
    # Adding data to the session  
    frappe.session.data["user_branch"] = branch
    frappe.session.data["expense_approver"] = expense_approver
    frappe.session.data["company"] = company
    if branch:
        frappe.session.data["user_warehouse"] = frappe.db.get_value("Branch", branch, "material_warehouse")
    # Persisting the change to the database and cache  
    frappe.local.session_obj.update(force=True)