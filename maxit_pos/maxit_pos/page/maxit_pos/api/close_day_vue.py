import json

import frappe
from frappe import _
from frappe.utils import cint, flt, nowdate


CASH_NOTES = (5, 10, 20, 50)


@frappe.whitelist()
def get_mode_of_payments(mode_of_payments):
    if isinstance(mode_of_payments, str):
        mode_of_payments = json.loads(mode_of_payments)
    modes = [i.get("mode_of_payment") for i in mode_of_payments]
    return frappe.get_all(
        "Mode of Payment",
        fields=["name", "type"],
        filters={"name": ("in", modes)},
        order_by="name asc",
    )


@frappe.whitelist()
def get_note_count_list(search_term=""):
	rows = frappe.get_all(
		"Note Count",
		fields=["name", "posting_date", "mode_of_payment", "type", "total", "docstatus"],
		order_by="creation desc",
		limit_page_length=200 if search_term else 50,
	)

	if search_term:
		search_lower = search_term.strip().lower()
		rows = [
			row
			for row in rows
			if search_lower in (row.get("name") or "").lower()
			or search_lower in (row.get("mode_of_payment") or "").lower()
			or search_lower in (row.get("type") or "").lower()
		]

	result = []
	for row in rows:
		status, status_color = _get_status_meta(row.get("docstatus"))
		result.append(
			{
				"name": row.get("name"),
				"posting_date": row.get("posting_date"),
				"mode_of_payment": row.get("mode_of_payment"),
				"type": row.get("type"),
				"total": flt(row.get("total")),
				"docstatus": row.get("docstatus"),
				"status": status,
				"statusColor": status_color,
				"subtitle": _build_subtitle(row.get("mode_of_payment"), row.get("type")),
			}
		)

	return result


@frappe.whitelist()
def get_note_count_detail(name):
	doc = frappe.get_doc("Note Count", name)
	return _serialize_note_count(doc)


@frappe.whitelist()
def create_note_count(doc):
	payload = _parse_payload(doc)
	normalized = _normalize_note_count_payload(payload)

	note_count = frappe.new_doc("Note Count")
	note_count.posting_date = normalized["posting_date"]
	note_count.mode_of_payment = normalized["mode_of_payment"]
	note_count.type = normalized["type"]
	note_count.total = normalized["total"]

	for row in normalized["cash"]:
		note_count.append("cash", row)

	for row in normalized["bank"]:
		note_count.append("bank", row)

	note_count.flags.ignore_permissions = True
	note_count.insert()
	note_count.submit()

	return _serialize_note_count(note_count)

def cancel_note_count(name):
	doc = frappe.get_doc("Note Count", name)
	doc.cancel()
def _parse_payload(doc):
	if isinstance(doc, str):
		return json.loads(doc)
	return doc or {}


def _normalize_note_count_payload(payload):
	mode_of_payment = payload.get("mode_of_payment")
	if not mode_of_payment:
		frappe.throw(_("Mode of Payment is required."))

	type_ = frappe.db.get_value("Mode of Payment", mode_of_payment, "type")
	if not type_:
		frappe.throw(_("Unable to determine the payment type for the selected Mode of Payment."))

	posting_date = payload.get("posting_date") or nowdate()
	if type_ == "Cash":
		cash_rows = _normalize_cash_rows(payload.get("cash") or [])
		bank_rows = []
		total = sum(flt(row.get("amount")) for row in cash_rows)
	elif type_ == "Bank":
		cash_rows = []
		bank_rows = _normalize_bank_rows(payload.get("bank") or [])
		if not bank_rows:
			frappe.throw(_("At least one bank row with values is required for Bank Note Count."))
		total = sum(flt(row.get("amount")) for row in bank_rows)
	else:
		frappe.throw(_("Only Cash and Bank payment types are supported for Note Count."))

	return {
		"posting_date": posting_date,
		"mode_of_payment": mode_of_payment,
		"type": type_,
		"cash": cash_rows,
		"bank": bank_rows,
		"total": flt(total),
	}


def _normalize_cash_rows(rows):
	rows_by_note = {}
	for row in rows:
		note = cint((row or {}).get("note") or (row or {}).get("denomination"))
		if note not in CASH_NOTES:
			continue
		rows_by_note[note] = max(cint((row or {}).get("count") or 0), 0)

	normalized = []
	for note in CASH_NOTES:
		count = rows_by_note.get(note, 0)
		amount = flt(note) * count
		normalized.append(
			{
				"note": str(note),
				"count": count,
				"amount": amount,
			}
		)

	return normalized


def _normalize_bank_rows(rows):
	normalized = []
	for row in rows:
		row = row or {}
		reference_number = (row.get("reference_number") or "").strip()
		amount = flt(row.get("amount"))
		bank = (row.get("bank") or "").strip()
		bank_branch = (row.get("bank_branch") or "").strip()
		account_number = (row.get("account_number") or "").strip()
		mobile_no = (row.get("mobile_no") or "").strip()

		if not any([reference_number, amount, bank, bank_branch, account_number, mobile_no]):
			continue

		normalized.append(
			{
				"reference_number": reference_number,
				"amount": amount,
				"bank": bank,
				"bank_branch": bank_branch,
				"account_number": account_number,
				"mobile_no": mobile_no,
			}
		)

	return normalized


def _serialize_note_count(doc):
	status, status_color = _get_status_meta(doc.docstatus)
	return {
		"name": doc.name,
		"posting_date": doc.posting_date,
		"mode_of_payment": doc.mode_of_payment,
		"type": doc.type,
		"total": flt(doc.total),
		"docstatus": doc.docstatus,
		"status": status,
		"statusColor": status_color,
		"subtitle": _build_subtitle(doc.mode_of_payment, doc.type),
		"cash": [
			{
				"note": row.note,
				"count": cint(row.count),
				"amount": flt(row.amount),
			}
			for row in (doc.cash or [])
		],
		"bank": [
			{
				"reference_number": row.reference_number,
				"amount": flt(row.amount),
				"bank": row.bank,
				"bank_branch": row.bank_branch,
				"account_number": row.account_number,
				"mobile_no": row.mobile_no,
			}
			for row in (doc.bank or [])
		],
	}


def _build_subtitle(mode_of_payment, type_):
	parts = [value for value in [mode_of_payment, type_] if value]
	return " - ".join(parts)


def _get_status_meta(docstatus):
	if docstatus == 1:
		return _("Submitted"), "success"
	if docstatus == 2:
		return _("Cancelled"), "error"
	return _("Draft"), "info"
