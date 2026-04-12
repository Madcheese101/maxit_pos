import json

import frappe
from frappe import _
from frappe.utils import cint, flt, nowdate
from erpnext.accounts.utils import get_account_currency

CASH_NOTES = (5, 10, 20, 50)
CLOSE_DAY_PAYMENT_REMARK = "Close Day Settlement"

@frappe.whitelist()
def get_mode_of_payments(mode_of_payments, company=None):
	return _get_mode_of_payment_meta(mode_of_payments, company=company)

@frappe.whitelist()
def get_note_count_options(posting_date=None, mode_of_payments=None):
	modes = _extract_mode_names(mode_of_payments)
	filters = {"docstatus": 1}
	if posting_date:
		filters["posting_date"] = posting_date
	if modes:
		filters["mode_of_payment"] = ("in", modes)

	rows = frappe.get_all(
		"Note Count",
		fields=["name", "posting_date", "mode_of_payment", "type", "total"],
		filters=filters,
		order_by="mode_of_payment asc, creation desc",
		limit_page_length=500,
	)

	return [
		{
			"name": row.get("name"),
			"posting_date": row.get("posting_date"),
			"mode_of_payment": row.get("mode_of_payment"),
			"type": row.get("type"),
			"total": flt(row.get("total")),
		}
		for row in rows
	]

@frappe.whitelist()
def get_note_count_list(search_term=""):
	filters = {}
	or_filters = []
	if search_term:
		search_value = f"%{search_term.strip()}%"
		or_filters = [
			["Note Count", "name", "like", search_value],
			["Note Count", "mode_of_payment", "like", search_value],
			["Note Count", "type", "like", search_value],
		]

	return frappe.get_all(
		"Note Count",
		fields=["name", "posting_date", "mode_of_payment", "type", "total", "docstatus"],
		filters=filters,
		or_filters=or_filters,
		order_by="creation desc",
		limit_page_length=200 if search_term else 50,
	)

@frappe.whitelist()
def get_note_count_detail(name):
	doc = frappe.get_doc("Note Count", name)
	return {
		"name": doc.name,
		"posting_date": doc.posting_date,
		"mode_of_payment": doc.mode_of_payment,
		"type": doc.type,
		"total": flt(doc.total),
		"docstatus": doc.docstatus,
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

@frappe.whitelist()
def create_note_count(doc):
	payload = _parse_payload(doc)
	mode_of_payment = payload.get("mode_of_payment")
	if not mode_of_payment:
		frappe.throw(_("Mode of Payment is required."))

	type_ = frappe.db.get_value("Mode of Payment", mode_of_payment, "type")
	if not type_:
		frappe.throw(_("Unable to determine the payment type for the selected Mode of Payment."))

	posting_date = payload.get("posting_date") or nowdate()
	cash_rows = []
	bank_rows = []
	total = 0

	if type_ == "Cash":
		rows_by_note = {}
		for row in payload.get("cash") or []:
			note = cint((row or {}).get("note") or (row or {}).get("denomination"))
			if note not in CASH_NOTES:
				continue
			rows_by_note[note] = max(cint((row or {}).get("count") or 0), 0)

		for note in CASH_NOTES:
			count = rows_by_note.get(note, 0)
			amount = flt(note) * count
			cash_rows.append(
				{
					"note": str(note),
					"count": count,
					"amount": amount,
				}
			)
			total += amount
	elif type_ == "Bank":
		for row in payload.get("bank") or []:
			row = row or {}
			reference_number = (row.get("reference_number") or "").strip()
			amount = flt(row.get("amount"))
			bank = (row.get("bank") or "").strip()
			bank_branch = (row.get("bank_branch") or "").strip()
			account_number = (row.get("account_number") or "").strip()
			mobile_no = (row.get("mobile_no") or "").strip()

			if not any([reference_number, amount, bank, bank_branch, account_number, mobile_no]):
				continue

			bank_rows.append(
				{
					"reference_number": reference_number,
					"amount": amount,
					"bank": bank,
					"bank_branch": bank_branch,
					"account_number": account_number,
					"mobile_no": mobile_no,
				}
			)
			total += amount

		if not bank_rows:
			frappe.throw(_("At least one bank row with values is required for Bank Note Count."))
	else:
		frappe.throw(_("Only Cash and Bank payment types are supported for Note Count."))

	note_count = frappe.new_doc("Note Count")
	note_count.posting_date = posting_date
	note_count.mode_of_payment = mode_of_payment
	note_count.type = type_
	note_count.total = flt(total)

	for row in cash_rows:
		note_count.append("cash", row)

	for row in bank_rows:
		note_count.append("bank", row)

	note_count.flags.ignore_permissions = True
	note_count.insert()
	note_count.submit()

	return get_note_count_detail(note_count.name)

@frappe.whitelist()
def create_payment_entries(doc):
	payload = _parse_payload(doc)
	posting_date = payload.get("posting_date") or nowdate()
	company = _get_default_company(payload.get("company"))
	pos_profile = payload.get("pos_profile")
	cost_center = payload.get("cost_center")
	note_count_enabled = cint(payload.get("note_count_enabled"))
	if not company:
		frappe.throw(_("Company is required to create Close Day Payment Entries."))
	if not pos_profile:
		frappe.throw(_("POS Profile is required to create Close Day Payment Entries."))

	payment_rows = payload.get("payments") or []
	if not payment_rows:
		frappe.throw(_("At least one payment row is required."))

	mode_details = _get_mode_of_payment_meta(payment_rows, company=company)
	mode_detail_map = {row.get("name"): row for row in mode_details}
	created_entries = []

	for row in payment_rows:
		row = row or {}
		mode_of_payment = row.get("mode_of_payment")
		if not mode_of_payment:
			continue

		mode_detail = mode_detail_map.get(mode_of_payment)
		if not mode_detail:
			frappe.throw(_("Unable to load account details for Mode of Payment {0}.").format(mode_of_payment))

		note_count = (row.get("note_count") or "").strip()
		amount = flt(row.get("amount"))
		if note_count_enabled:
			if note_count:
				note_count_doc = frappe.get_doc("Note Count", note_count)
				if note_count_doc.docstatus != 1:
					frappe.throw(_("Note Count {0} must be submitted before it can be used.").format(note_count))
				if note_count_doc.mode_of_payment != mode_of_payment:
					frappe.throw(_("Note Count {0} does not match Mode of Payment {1}.").format(note_count, mode_of_payment))
				if str(note_count_doc.posting_date) != str(posting_date):
					frappe.throw(_("Note Count {0} does not match posting date {1}.").format(note_count, posting_date))
				amount = flt(note_count_doc.total)
			else:
				amount = 0

		if amount <= 0:
			continue

		middle_man_account = mode_detail.get("middle_man_account")
		default_account = mode_detail.get("default_account")
		if not middle_man_account:
			frappe.throw(_("Middle Man Account is required for Mode of Payment {0}.").format(mode_of_payment))
		if not default_account:
			frappe.throw(_("Default Account is required for Mode of Payment {0}.").format(mode_of_payment))
		if middle_man_account == default_account:
			frappe.throw(_("Mode of Payment {0} must have different source and target accounts.").format(mode_of_payment))

		paid_from_account_currency = get_account_currency(middle_man_account)
		paid_to_account_currency = get_account_currency(default_account)
		if paid_from_account_currency != paid_to_account_currency:
			frappe.throw(
				_(
					"Close Day Payment Entries require matching account currency for Mode of Payment {0}."
				).format(mode_of_payment)
			)

		payment_entry = frappe.new_doc("Payment Entry")
		payment_entry.payment_type = "Internal Transfer"
		payment_entry.company = company
		payment_entry.posting_date = posting_date
		payment_entry.cost_center = cost_center
		payment_entry.mode_of_payment = mode_of_payment
		payment_entry.paid_from = default_account
		payment_entry.paid_to = middle_man_account
		payment_entry.paid_from_account_currency = paid_to_account_currency
		payment_entry.paid_to_account_currency = paid_from_account_currency
		payment_entry.source_exchange_rate = 1
		payment_entry.target_exchange_rate = 1
		payment_entry.paid_amount = amount
		payment_entry.received_amount = amount
		payment_entry.reference_no = note_count
		payment_entry.reference_date = posting_date
		payment_entry.remarks = _build_payment_entry_remarks(
			pos_profile,
			posting_date,
			{
				"mode_of_payment": mode_of_payment,
				"note_count": note_count,
			},
		)
		payment_entry.flags.ignore_permissions = True
		payment_entry.set_missing_values()
		payment_entry.insert()
		payment_entry.submit()
		created_entries.append(get_payment_entry_detail(payment_entry.name))

	if not created_entries:
		frappe.throw(_("Enter at least one payment row with a positive amount."))

	return created_entries

@frappe.whitelist()
def get_payment_entry_list(cost_center, search_term=""):
	filters = {
		"cost_center": cost_center,
		"docstatus": 1,
	}
	or_filters = []
	if search_term:
		search_value = f"%{search_term.strip()}%"
		or_filters = [
			["Payment Entry", "name", "like", search_value],
			["Payment Entry", "mode_of_payment", "like", search_value],
			["Payment Entry", "reference_no", "like", search_value],
			["Payment Entry", "paid_from", "like", search_value],
			["Payment Entry", "paid_to", "like", search_value],
		]

	return frappe.get_all(
		"Payment Entry",
		fields=[
			"name",
			"posting_date",
			"mode_of_payment",
			"paid_amount",
			"received_amount",
			"paid_from",
			"paid_to",
			"reference_no",
			"remarks",
			"docstatus",
		],
		filters=filters,
		or_filters=or_filters,
		order_by="creation desc",
		limit_page_length=200 if search_term else 50,
	)

@frappe.whitelist()
def get_payment_entry_detail(name):
	doc = frappe.get_doc("Payment Entry", name)
	return {
		"name": doc.name,
		"posting_date": doc.posting_date,
		"mode_of_payment": doc.mode_of_payment,
		"paid_amount": flt(doc.paid_amount),
		"received_amount": flt(doc.received_amount),
		"docstatus": doc.docstatus,
		"reference_no": doc.reference_no,
		"remarks": doc.remarks,
		"paid_from": doc.paid_from,
		"paid_to": doc.paid_to,
		"cost_center": doc.cost_center,
		"company": doc.company,
	}

def cancel_note_count(name):
	doc = frappe.get_doc("Note Count", name)
	doc.cancel()

def _parse_payload(doc):
	if isinstance(doc, str):
		return json.loads(doc)
	return doc or {}

def _extract_mode_names(mode_of_payments):
	mode_of_payments = _parse_payload(mode_of_payments)
	mode_names = []
	seen_modes = set()

	for row in mode_of_payments or []:
		mode_name = (row or {}).get("mode_of_payment") or (row or {}).get("name")
		if not mode_name or mode_name in seen_modes:
			continue
		seen_modes.add(mode_name)
		mode_names.append(mode_name)

	return mode_names

def _get_default_company(company=None):
	return company or frappe.defaults.get_user_default("Company") or frappe.db.get_single_value("Global Defaults", "default_company")

def _get_mode_of_payment_meta(mode_of_payments, company=None):
	modes = _extract_mode_names(mode_of_payments)
	if not modes:
		return []

	mode_rows = frappe.get_all(
		"Mode of Payment",
		fields=["name", "type", "middle_man_account"],
		filters={"name": ("in", modes)},
		limit_page_length=len(modes),
	)
	mode_map = {row.get("name"): row for row in mode_rows}

	account_filters = {
		"parenttype": "Mode of Payment",
		"parentfield": "accounts",
		"parent": ("in", modes),
	}
	resolved_company = _get_default_company(company)
	if resolved_company:
		account_filters["company"] = resolved_company

	account_rows = frappe.get_all(
		"Mode of Payment Account",
		fields=["parent", "default_account", "company"],
		filters=account_filters,
		order_by="idx asc",
		limit_page_length=max(len(modes), 1) * 10,
	)
	account_map = {}
	for row in account_rows:
		account_map.setdefault(row.get("parent"), row.get("default_account"))

	result = []
	for mode in modes:
		mode_row = mode_map.get(mode)
		if not mode_row:
			continue
		result.append(
			{
				"name": mode_row.get("name"),
				"type": mode_row.get("type"),
				"middle_man_account": mode_row.get("middle_man_account"),
				"default_account": account_map.get(mode),
			}
		)

	return result
def _build_payment_entry_remarks(pos_profile, posting_date, row):
	parts = [
		CLOSE_DAY_PAYMENT_REMARK,
		f"POS Profile: {pos_profile}",
		f"Posting Date: {posting_date}",
		f"Mode of Payment: {row.get('mode_of_payment')}",
		f"Note Count: {row.get('note_count') or '-'}",
	]
	return " | ".join(parts)
