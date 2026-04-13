import json

import frappe
from frappe import _
from frappe.utils import cint, flt, formatdate, now_datetime, nowdate
from frappe.www.printview import get_letter_head
from erpnext.accounts.utils import get_account_currency, get_balance_on

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
		payment_entry.note_count = note_count
		payment_entry.paid_from_account_currency = paid_to_account_currency
		payment_entry.paid_to_account_currency = paid_from_account_currency
		payment_entry.source_exchange_rate = 1
		payment_entry.target_exchange_rate = 1
		payment_entry.paid_amount = amount
		payment_entry.received_amount = amount
		payment_entry.reference_no = note_count or "-"
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


@frappe.whitelist()
def get_close_day_payment_report_html(
	posting_date=None,
	pos_profile=None,
	mode_of_payments=None,
	company=None,
	cost_center=None,
	letter_head=None,
):
	context = _build_close_day_payment_report_context(
		posting_date=posting_date,
		pos_profile=pos_profile,
		mode_of_payments=mode_of_payments,
		company=company,
		cost_center=cost_center,
		letter_head=letter_head,
	)
	html = frappe.render_template(
		"maxit_pos/templates/includes/close_day_payment_report.html",
		context,
		is_path=True,
	)
	return {
		"html": html,
		"title": context.get("title"),
	}

def cancel_note_count(name):
	doc = frappe.get_doc("Note Count", name)
	doc.cancel()


def _build_close_day_payment_report_context(
	posting_date=None,
	pos_profile=None,
	mode_of_payments=None,
	company=None,
	cost_center=None,
	letter_head=None,
):
	if not pos_profile:
		frappe.throw(_("POS Profile is required to print the Close Day report."))

	posting_date = posting_date or nowdate()
	pos_profile_doc = frappe.get_doc("POS Profile", pos_profile)
	company = company or pos_profile_doc.company or _get_default_company(company)
	cost_center = cost_center or pos_profile_doc.cost_center
	configured_modes = _parse_payload(mode_of_payments) or [
		{"mode_of_payment": row.mode_of_payment} for row in (pos_profile_doc.payments or [])
	]
	configured_mode_names = _extract_mode_names(configured_modes)
	if not configured_mode_names:
		frappe.throw(_("No Mode of Payments are configured for POS Profile {0}.").format(pos_profile))

	mode_detail_map = {
		row.get("name"): row for row in _get_mode_of_payment_meta(configured_modes, company=company)
	}
	entry_summary = _get_close_day_payment_entry_summary(
		posting_date=posting_date,
		pos_profile=pos_profile,
		mode_names=configured_mode_names,
		company=company,
		cost_center=cost_center,
	)
	# frappe.throw(str(json.dumps(entry_summary)))
	company_currency = frappe.get_cached_value("Company", company, "default_currency") if company else None
	balance_cache = {}
	rows = []

	for mode_name in configured_mode_names:
		mode_detail = mode_detail_map.get(mode_name, {})
		summary = entry_summary.get(mode_name, {})
		default_account = mode_detail.get("default_account") or ""
		default_account_balance = None
		if default_account:
			if default_account not in balance_cache:
				balance_cache[default_account] = _get_default_account_balance(
					account=default_account,
					posting_date=posting_date,
					company=company,
				)
			default_account_balance = balance_cache.get(default_account)

		paid_amount = flt(summary.get("paid_amount"))
		received_amount = flt(summary.get("received_amount"))
		entry_names = summary.get("entry_names") or []
		row = {
			"mode_of_payment": mode_name,
			"type": mode_detail.get("type") or "",
			"default_account": default_account,
			"middle_man_account": mode_detail.get("middle_man_account") or "",
			"paid_amount": paid_amount,
			"received_amount": received_amount,
			"default_account_balance": default_account_balance,
			"entry_count": len(entry_names),
			"entry_names": entry_names,
			"formatted_paid_amount": _format_amount(paid_amount),
			"formatted_received_amount": _format_amount(received_amount),
			"formatted_default_account_balance": _format_amount(default_account_balance)
			if default_account_balance is not None
			else "",
		}
		rows.append(row)

	total_paid = sum(flt(row.get("paid_amount")) for row in rows)
	total_received = sum(flt(row.get("received_amount")) for row in rows)
	balance_rows = [flt(row.get("default_account_balance")) for row in rows if row.get("default_account_balance") is not None]
	letter_head_data = _get_rendered_letter_head(pos_profile_doc, letter_head)
	generated_by = frappe.get_cached_value("User", frappe.session.user, "full_name") or frappe.session.user

	return {
		"title": _("Close Day Report"),
		"subtitle": _("Mode of Payment Summary"),
		"company": company or "",
		"company_currency": company_currency or "",
		"pos_profile": pos_profile_doc.name,
		"cost_center": cost_center or _("Not Set"),
		"posting_date": posting_date,
		"posting_date_label": formatdate(posting_date),
		"generated_on": now_datetime().strftime("%Y-%m-%d %H:%M:%S"),
		"generated_by": generated_by,
		"letter_head": letter_head_data.get("content") or "",
		"letter_head_footer": letter_head_data.get("footer") or "",
		"rows": rows,
		"row_count": len(rows),
		"totals": {
			"paid_amount": total_paid,
			"received_amount": total_received,
			"default_account_balance": sum(balance_rows),
			"formatted_paid_amount": _format_amount(total_paid),
			"formatted_received_amount": _format_amount(total_received),
			"formatted_default_account_balance": _format_amount(sum(balance_rows)),
		},
	}

def _parse_payload(doc):
	if isinstance(doc, str):
		return json.loads(doc)
	return doc or {}


def _parse_payment_entry_remarks(remarks):
	metadata = {}
	for part in str(remarks or "").split("|")[1:]:
		if ":" not in part:
			continue

		key, value = part.split(":", 1)
		metadata[key.strip().lower().replace(" ", "_")] = value.strip()

	return metadata


def _normalize_metadata_value(value):
	return value if value and value != "-" else ""

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


def _get_close_day_payment_entry_summary(posting_date, pos_profile, mode_names, company=None, cost_center=None):
	filters = {
		"docstatus": 1,
		"payment_type": "Internal Transfer",
		"posting_date": posting_date,
	}
	if company:
		filters["company"] = company
	if cost_center:
		filters["cost_center"] = cost_center
	if mode_names:
		filters["mode_of_payment"] = ("in", mode_names)
	payment_entries = frappe.get_all(
		"Payment Entry",
		fields=["name", "mode_of_payment", "paid_amount", "received_amount", "remarks"],
		filters=filters,
		order_by="creation asc",
		limit_page_length=max(len(mode_names or []), 1) * 20,
	)

	summary = {}
	
	for entry in payment_entries:
		mode_of_payment = entry.get("mode_of_payment")
		if not mode_of_payment:
			continue

		bucket = summary.setdefault(
			mode_of_payment,
			{
				"paid_amount": 0,
				"received_amount": 0,
				"entry_names": [],
			},
		)
		bucket["paid_amount"] += flt(entry.get("paid_amount"))
		bucket["received_amount"] += flt(entry.get("received_amount"))
		bucket["entry_names"].append(entry.get("name"))
	return summary


def _get_default_account_balance(account, posting_date, company=None):
	if not account:
		return None

	return flt(
		get_balance_on(
			account=account,
			date=posting_date,
			company=company,
			ignore_account_permission=True,
		)
	)


def _get_rendered_letter_head(pos_profile_doc, letter_head=None):
	letter_head_name = (letter_head or pos_profile_doc.get("letter_head") or "").strip()
	if not letter_head_name or letter_head_name == "No Letterhead":
		return {"content": "", "footer": ""}

	letter_head_doc = frappe._dict(get_letter_head(pos_profile_doc, False, letter_head_name) or {})
	if letter_head_doc.content:
		letter_head_doc.content = frappe.render_template(
			letter_head_doc.content,
			{"doc": pos_profile_doc.as_dict()},
		)
		if letter_head_doc.header_script:
			letter_head_doc.content += f"<script>{letter_head_doc.header_script}</script>"

	if letter_head_doc.footer:
		letter_head_doc.footer = frappe.render_template(
			letter_head_doc.footer,
			{"doc": pos_profile_doc.as_dict()},
		)
		if letter_head_doc.footer_script:
			letter_head_doc.footer += f"<script>{letter_head_doc.footer_script}</script>"

	return letter_head_doc


def _format_amount(value):
	if value is None:
		return ""
	return f"{flt(value):,.2f}"

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
