import frappe
import requests
from frappe import _
from maxit_pos.maxit_pos.page.maxit_pos.api.purchase_vue import _get_parent_company_request_config, _extract_remote_error_message

@frappe.whitelist()
def get_item_stock_from_main_company(item_code, item_name):
    endpoint, headers, timeout = _get_parent_company_request_config("/api/method/get_company_item_stock")

    try:
        response = requests.get(
            endpoint, 
            headers=headers, 
            timeout=timeout, 
            json={"item_code": item_code, "item_name": item_name}
        )
        response.raise_for_status()
        payload = response.json() or {}
    except requests.exceptions.Timeout as exc:
        frappe.throw(f"Timed out while fetching item stock from the parent ERPNext site: {exc}")
    except requests.exceptions.HTTPError as exc:
        message = _extract_remote_error_message(exc.response)
        status = exc.response.status_code if exc.response else "unknown"
        frappe.throw(f"Parent ERPNext request failed (HTTP {status}): {message}")
    except requests.exceptions.RequestException as exc:
        frappe.throw(f"Unable to reach the parent ERPNext site: {exc}")
    except ValueError as exc:
        frappe.throw(f"Parent ERPNext returned an invalid response: {exc}")
    
    msg = payload.get("message", {})
    if msg:
        frappe.msgprint(payload.get("message"))
    else:
        frappe.msgprint(_("No stock information found for item {0}").format(item_name))

@frappe.whitelist()
def get_item_stock_from_sister_branches(item_code, item_name, warehouse=None):
    msg = ""
    filters = {"item_code": item_code, "actual_qty": ['>', 0]}
    if warehouse:
        filters["warehouse"] = ["!=", warehouse]

    wh_list = frappe.db.get_all('Bin',
        fields=["warehouse","actual_qty"],
        filters=filters,
        order_by="actual_qty desc"
        # as_list=True,
        # pluck='warehouse'
        # as_dict=True
        )
    if wh_list:
        msg=msg + item_name +"<hr>" + "<ul>"
        for wh in wh_list:
            msg=msg+"<li>"+wh["warehouse"].replace("BC","")+"  ("+str(wh["actual_qty"])+") </li>"
        msg = msg + "</ul><hr>"
    
    if msg:
        frappe.msgprint(msg)
    else:
        frappe.msgprint(_("No stock information found for item {0}").format(item_name))