import frappe
import requests
import json
from frappe import _
from frappe.query_builder import Field, functions, Query, DocType, Order
from pypika.terms import Case, ValueWrapper

@frappe.whitelist()
def get_purchase_invoice_list(pos_profile, search_term=""):
    if isinstance(pos_profile, str):
        pos_profile = json.loads(pos_profile)

    PurchaseInvoice = DocType("Purchase Invoice")
    query = (frappe.qb.from_(PurchaseInvoice)
        .select(
            PurchaseInvoice.name,
            PurchaseInvoice.posting_date,
            PurchaseInvoice.status,
            PurchaseInvoice.supplier_branch,
            PurchaseInvoice.bill_no,
            PurchaseInvoice.bill_date,
        )
        .where(PurchaseInvoice.cost_center == pos_profile.get("cost_center"))
        .orderby(PurchaseInvoice.modified, order=Order.desc)
        .limit(50)
    )

    if search_term:
        query = query.where(
            PurchaseInvoice.name.like(f"%{search_term}%")
            | PurchaseInvoice.bill_no.like(f"%{search_term}%")
        )

    invoices = query.run(as_dict=1)

    return invoices

@frappe.whitelist()
def sync_invoices(pos_profile):
    if isinstance(pos_profile, str):
        pos_profile = json.loads(pos_profile)
    invoices_done = []

    supplier_branch = frappe.get_all("Supplier Branch", 
        filters={"cost_center": pos_profile.get("cost_center")}, 
        fields=["name", "supplier","supplier_pos_profile"])
    
    supplier_branch_map = {sb.supplier_pos_profile: sb for sb in supplier_branch}
    
    if not supplier_branch_map:
        frappe.throw(_("No Supplier Branches found for the given POS Profile's Cost Center."))

    result = get_parent_company_sales_invoices()
    if isinstance(result, str):
        result = json.loads(result)
    
    invoices_map = [inv.get("name") for inv in result]
    existsing_invoices = frappe.db.get_list("Purchase Invoice", filters={"bill_no": ["in", invoices_map]}, pluck="bill_no")
    for invoice in result:
        if invoice.get("name") in existsing_invoices:
            continue
        done = create_purchase_invoice(invoice, pos_profile, supplier_branch_map)
        if done: invoices_done.append(invoice.get("name"))
        if invoices_done:
            set_invoices_as_paid(invoices_done)
    return len(invoices_done)

def set_invoices_as_paid(invoices):
    if isinstance(invoices, str):
        invoices = json.loads(invoices)

    endpoint, headers, timeout = _get_parent_company_request_config("/api/method/invoices_synced")
    try:        
        response = requests.post(endpoint, headers=headers, timeout=timeout, json={"invoices": invoices})
        response.raise_for_status()
        payload = response.json() or {}
    except requests.exceptions.Timeout as exc:
        frappe.throw(f"Timed out while setting invoices as paid on the parent ERPNext site: {exc}")
    except requests.exceptions.HTTPError as exc:
        message = _extract_remote_error_message(exc.response)
        status = exc.response.status_code if exc.response else "unknown"
        frappe.throw(f"Parent ERPNext request failed (HTTP {status}): {message}")
    except requests.exceptions.RequestException as exc:
        frappe.throw(f"Unable to reach the parent ERPNext site: {exc}")
    except ValueError as exc:
        frappe.throw(f"Parent ERPNext returned an invalid response: {exc}")

    return payload.get("message", [])

def get_parent_company_sales_invoices():

    endpoint, headers, timeout = _get_parent_company_request_config("/api/method/get_internal_customer_invoices")

    try:
        response = requests.get(endpoint, headers=headers, timeout=timeout, params={})
        response.raise_for_status()
        payload = response.json() or {}
    except requests.exceptions.Timeout as exc:
        frappe.throw(f"Timed out while fetching invoices from the parent ERPNext site: {exc}")
    except requests.exceptions.HTTPError as exc:
        message = _extract_remote_error_message(exc.response)
        status = exc.response.status_code if exc.response else "unknown"
        frappe.throw(f"Parent ERPNext request failed (HTTP {status}): {message}")
    except requests.exceptions.RequestException as exc:
        frappe.throw(f"Unable to reach the parent ERPNext site: {exc}")
    except ValueError as exc:
        frappe.throw(f"Parent ERPNext returned an invalid response: {exc}")

    return payload.get("message", [])

def _get_parent_company_request_config(endpoint_path):
    config = frappe.get_conf() or {}
    base_url = (config.get("parent_erpnext_url") or "").rstrip("/")
    api_key = config.get("parent_erpnext_api_key")
    api_secret = config.get("parent_erpnext_api_secret")
    timeout = config.get("parent_erpnext_timeout") or 150
    # frappe.throw(f"{base_url} - {api_key} - {api_secret}")
    if not base_url or not api_key or not api_secret:
        frappe.throw(
            "Missing parent ERPNext configuration. Set parent_erpnext_url, "
            "parent_erpnext_api_key, and parent_erpnext_api_secret in site_config.json."
        )

    try:
        timeout = int(timeout)
    except (TypeError, ValueError):
        timeout = 150

    endpoint = f"{base_url}{endpoint_path}"
    headers = {
        "Authorization": f"token {api_key}:{api_secret}",
        "Accept": "application/json",
    }
    return endpoint, headers, max(timeout, 1)

def create_purchase_invoice(invoice, pos_profile, supplier_branch_map):
    # Implement the logic to create a purchase invoice based on the provided data
    # You can use the pos_profile data to set additional fields or configurations
    pinv = frappe.new_doc("Purchase Invoice")
    pinv.supplier = supplier_branch_map.get(invoice.get("pos_profile")).supplier
    pinv.supplier_branch = supplier_branch_map.get(invoice.get("pos_profile")).name
    pinv.cost_center = pos_profile.get("cost_center")
    pinv.bill_no = invoice.get("name")
    pinv.bill_date = invoice.get("posting_date")
    pinv.posting_date = invoice.get("posting_date")
    pinv.set_warehouse = pos_profile.get("warehouse")
    pinv.update_stock = 1
    pinv.set_posting_time = 1

    for item in invoice.get("items", []):
        pinv.append("items", {
            "item_code": item.get("item_code"),
            "item_name": item.get("item_name"),
            "item_group": item.get("item_group"),
            "received_qty": item.get("qty"),
            "qty": item.get("qty"),
            "uom": item.get("uom"),
            "conversion_factor": item.get("conversion_factor") or 1,
            "rate": item.get("rate"),
            "amount": item.get("amount"),
        })
    pinv.set_missing_values()
    pinv.save()
    pinv.submit()
    return True

@frappe.whitelist()
def create_return_invoice(supplier_branch, items, cost_center, warehouse):
    if isinstance(items, str): items = json.loads(items)
    supplier = frappe.db.get_value("Supplier Branch", supplier_branch, "supplier")
    
    pinv = frappe.new_doc("Purchase Invoice")
    pinv.supplier = supplier
    pinv.supplier_branch = supplier_branch
    pinv.cost_center = cost_center
    pinv.is_return = 1
    pinv.update_stock = 1
    pinv.posting_date = frappe.utils.today()
    pinv.price_list = "Standard Buying"
    pinv.set_warehouse = warehouse
    pinv.naming_series = "ACC-PINV-RET-.YYYY.-"
    for item in items:
        pinv.append("items", {
            "item_code": item.get("item_code"),
            "received_qty": item.get("qty") * -1,
            "qty": item.get("qty") * -1,
            "conversion_factor": item.get("conversion_factor", 1),
        })
    pinv.set_missing_values()
    pinv.save()
    pinv.submit()

def _extract_remote_error_message(response):
    if response is None:
        return "Unknown error"

    body = ""
    try:
        body = (response.text or "").strip()
    except Exception:
        body = ""

    try:
        payload = response.json() or {}
    except ValueError:
        payload = {}

    if isinstance(payload, dict) and payload:
        for key in ("exception", "exc", "message", "_error_message"):
            if payload.get(key):
                return str(payload.get(key))

        server_messages = payload.get("_server_messages")
        if server_messages:
            try:
                decoded = json.loads(server_messages)
                if isinstance(decoded, list) and decoded:
                    first = decoded[0]
                    if isinstance(first, str) and first.strip():
                        return first
            except Exception:
                pass

    if body and body not in ("{}", "[]"):
        return body[:400]

    status_text = response.reason or "Unknown"
    return f"No error details returned by remote server ({response.status_code} {status_text})"