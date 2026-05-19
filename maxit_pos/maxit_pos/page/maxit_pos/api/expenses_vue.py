import json

import frappe
from frappe import _
from frappe.utils import flt, nowdate


@frappe.whitelist()
def get_expense_list(search_term="", expense_type=None, from_date=None, to_date=None, status=None):
	filters = {}
	docstatus = _get_docstatus_filter(status)
	branch = frappe.session.data.get("user_branch")
	if branch:
		filters["branch"] = branch
	else:
		frappe.throw(_("User does not have a branch assigned."))
	if docstatus is not None:
		filters["docstatus"] = docstatus
	if expense_type:
		filters["expense_type"] = expense_type
	if from_date:
		filters["posting_date"] = [">=", from_date]
	if from_date and to_date:
		filters["posting_date"] = ["between", [from_date, to_date]]
	elif to_date:
		filters["posting_date"] = ["<=", to_date]

	or_filters = []
	search_term = (search_term or "").strip()
	if search_term:
		search_value = f"%{search_term}%"
		or_filters = [
			["Expense", "name", "like", search_value],
			["Expense", "notes", "like", search_value],
		]

	rows = frappe.get_all(
		"Expense",
		fields=[
			"name",
			"expense_type",
			"amount",
			"posting_date",
			"branch",
			"notes",
			"journal_entry",
			"docstatus",
		],
		filters=filters,
		or_filters=or_filters,
		order_by="creation desc",
		limit_page_length=200 if search_term else 50,
	)

	return rows


@frappe.whitelist()
def create_expense(doc):
	payload = _parse_payload(doc)
	expense = frappe.new_doc("Expense")
	expense.expense_type = payload.get("expense_type")
	expense.amount = flt(payload.get("amount"))
	expense.posting_date = payload.get("posting_date") or nowdate()
	expense.notes = payload.get("notes")
	expense.insert()
	expense.submit()
	return expense.name


@frappe.whitelist()
def cancel_expense(name):
	if not name:
		frappe.throw(_("Expense is required."))

	doc = frappe.get_doc("Expense", name)
	if doc.docstatus != 1:
		frappe.throw(_("Only submitted Expense records can be cancelled."))

	doc.cancel()
	return doc.name


def _get_docstatus_filter(status):
	if status is None or status == "":
		return None

	status_map = {
		"draft": 0,
		"submitted": 1,
		"cancelled": 2,
	}
	if isinstance(status, str):
		status_key = status.strip().lower()
		if status_key in status_map:
			return status_map[status_key]
		if status_key.isdigit():
			return int(status_key)

	return status


def _parse_payload(doc):
	if not doc:
		return {}
	if isinstance(doc, str):
		return json.loads(doc)
	return doc