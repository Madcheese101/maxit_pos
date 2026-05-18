import frappe

def on_session_created(login_manager):
    branch = frappe.db.get_value("Employee", {"user_id": login_manager.user}, "branch")
    # Adding data to the session  
    frappe.session.data["user_branch"] = branch
    # Persisting the change to the database and cache  
    frappe.local.session_obj.update(force=True)