import json

import frappe
from erpnext.setup.utils import get_exchange_rate
from frappe import _
from frappe.query_builder import DocType, Order
from frappe.utils import flt, nowdate


EXPENSE_ACCESS_ROLES = (
	"Expense User",
	"Expense Manager",
	"Accounts User",
	"Accounts Manager",
	"Administrator",
	"System Manager",
)


@frappe.whitelist()
def get_expense_list(search_term="", expense_type=None, from_date=None, to_date=None, status=None, view_mode="expanded"):
	_ensure_expense_access()
	branch = _get_user_branch()
	docstatus = _get_docstatus_filter(status)
	fields = [
		"name",
		"docstatus",
		"posting_date",
		"branch",
	]
	view_mode = (view_mode or "expanded").strip().lower()

	if view_mode == "grouped":
		fields.append("total_claimed_amount as amount")
	else:
		fields.extend([
			"expenses.name as row_id",
			"expenses.expense_type as expense_type",
			"expenses.amount as amount",
		])

	filters = {"branch": branch}
	if docstatus is not None:
		filters["docstatus"] = docstatus
	if expense_type:
		filters["expenses.expense_type"] = expense_type
	if from_date and to_date:
		filters["posting_date"] = ["between", [from_date, to_date]]
	elif from_date:
		filters["posting_date"] = [">=", from_date]
	elif to_date:
		filters["posting_date"] = ["<=", to_date]

	or_filters = None
	search_term = (search_term or "").strip()
	if search_term:
		search_value = f"%{search_term}%"
		or_filters = [
			["name", "like", search_value],
			["remark", "like", search_value],
		]

	rows = frappe.qb.get_query(
		"Expense Claim",
		fields=fields,
		filters=filters,
		or_filters=or_filters,
		order_by="posting_date desc, modified desc",
		limit=200 if search_term else 50,
		ignore_permissions=True,
	).run(as_dict=True)

	return rows


@frappe.whitelist()
def get_expense_details(name):
	_ensure_expense_access()

	if not name:
		frappe.throw(_("Expense Claim is required."))

	doc = frappe.get_doc("Expense Claim", name)
	_ensure_expense_doc_access(doc)
	return doc.as_dict()

@frappe.whitelist()
def create_expense(doc):
	_ensure_expense_access()

	payload = _parse_payload(doc)
	employee = frappe.get_doc("Employee", frappe.session.data.get("employee"))
	posting_date = payload.get("posting_date") or nowdate()
	branch = employee.get("branch") or _get_user_branch()
	if not branch:
		frappe.throw(_("User does not have a branch assigned."))

	expense_approver = employee.get("expense_approver")
	if not expense_approver:
		frappe.throw(_("Employee Expense Approver is required before creating an Expense Claim."))

	company = employee.get("company") or frappe.session.data.get("company")
	if not company:
		frappe.throw(_("Employee Company is required before creating an Expense Claim."))

	company_currency = frappe.get_cached_value("Company", company, "default_currency")
	currency = company_currency

	payable_account = frappe.get_cached_value("Company", company, "default_expense_claim_payable_account")
	if not payable_account:
		frappe.throw(_("Company Default Expense Claim Payable Account is required before creating an Expense Claim."))

	cost_center = _get_expense_cost_center(branch, company)
	if not cost_center:
		frappe.throw(_("A branch or company Cost Center is required before creating an Expense Claim."))

	expense_rows = payload.get("expenses")
	remark = payload.get("remark") or payload.get("notes")

	expense_claim = frappe.new_doc("Expense Claim")
	expense_claim.employee = employee.name
	expense_claim.employee_name = employee.employee_name
	expense_claim.company = company
	expense_claim.posting_date = posting_date
	expense_claim.remark = remark
	expense_claim.approval_status = "Approved"
	expense_claim.expense_approver = expense_approver
	expense_claim.currency = currency
	expense_claim.exchange_rate = _get_claim_exchange_rate(currency, company_currency, posting_date)
	expense_claim.payable_account = payable_account
	expense_claim.cost_center = cost_center
	expense_claim.branch = branch

	for row in expense_rows:
		expense_claim.append(
			"expenses",
			{
				"expense_date": posting_date,
				"expense_type": row["expense_type"],
				"amount": flt(row["amount"]),
				"sanctioned_amount": flt(row["amount"]),
				"cost_center": cost_center,
			},
		)

	expense_claim.set_expense_account()
	expense_claim.calculate_total_amount()
	expense_claim.calculate_taxes()
	_populate_claim_advances(expense_claim)
	_update_employee_advance_claimed_amount(expense_claim)
	expense_claim.flags.ignore_permissions = True
	expense_claim.save()
	expense_claim.submit()
	return expense_claim.name


@frappe.whitelist()
def cancel_expense(name):
	_ensure_expense_access()

	if not name:
		frappe.throw(_("Expense Claim is required."))

	doc = frappe.get_doc("Expense Claim", name)
	_ensure_expense_doc_access(doc)
	if doc.docstatus != 1:
		frappe.throw(_("Only submitted Expense Claim records can be cancelled."))

	doc.flags.ignore_permissions = True
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


def _ensure_expense_access():
	if set(frappe.get_roles(frappe.session.user)).intersection(EXPENSE_ACCESS_ROLES):
		return

	frappe.throw(_("You do not have permission to manage expenses."), frappe.PermissionError)


def _ensure_expense_doc_access(doc):
	if doc.get("branch") == _get_user_branch():
		return

	frappe.throw(_("You do not have permission to access this Expense Claim."), frappe.PermissionError)

def _get_user_branch():
	branch = frappe.session.data.get("user_branch")
	if branch:
		return branch

	frappe.throw(_("User does not have a branch assigned."))

def _get_expense_cost_center(branch, company):
	branch_cost_center = frappe.db.get_value("Branch", branch, "branch_cost_center") if branch else None
	if branch_cost_center:
		return branch_cost_center

	return frappe.get_cached_value("Company", company, "cost_center")


def _get_claim_exchange_rate(currency, company_currency, posting_date):
	if not currency or currency == company_currency:
		return 1

	return flt(get_exchange_rate(currency, company_currency, posting_date)) or 1


def _populate_claim_advances(expense_claim):
	try:
		get_advances = frappe.get_attr("hrms.hr.doctype.expense_claim.expense_claim.get_advances")
	except Exception as exc:
		frappe.throw(
			_("HRMS Expense Claim advances helper is unavailable: {0}").format(str(exc)),
			frappe.DoesNotExistError,
		)

	get_advances(expense_claim)


def _update_employee_advance_claimed_amount(expense_claim):
	amount_to_be_allocated = flt(expense_claim.total_sanctioned_amount) + flt(
		expense_claim.total_taxes_and_charges
	)
	total_advance_amount = 0

	for advance in expense_claim.get("advances") or []:
		max_allocatable = flt(advance.unclaimed_amount) - flt(advance.return_amount)
		if max_allocatable < 0:
			max_allocatable = 0

		advance.allocated_amount = flt(
			min(amount_to_be_allocated, max_allocatable),
			advance.precision("allocated_amount"),
		)
		expense_claim.set_base_fields_amount(advance, ["allocated_amount"])
		amount_to_be_allocated = max(flt(amount_to_be_allocated) - flt(advance.allocated_amount), 0)
		total_advance_amount += flt(advance.allocated_amount)

	expense_claim.total_advance_amount = flt(
		total_advance_amount,
		expense_claim.precision("total_advance_amount"),
	)
	expense_claim.set_base_fields_amount(expense_claim, ["total_advance_amount"])
	expense_claim.calculate_taxes()


def _parse_payload(doc):
	if not doc:
		return {}
	if isinstance(doc, str):
		return json.loads(doc)
	return doc