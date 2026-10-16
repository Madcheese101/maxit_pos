import frappe

__version__ = "0.0.1"


def check_app_permission():
	# show the POS on the apps screen only to users whose roles may open its page
	return frappe.get_cached_doc("Page", "maxit-pos").is_permitted()
