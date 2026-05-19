# Copyright (c) 2026, MaxITly.com and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document

class Expense(Document):
	def validate(self):
		self.set_missing_fields()

		if self.amount <= 0:
			frappe.throw("Amount must be greater than zero.")

	def on_submit(self):
		doc = frappe.new_doc('Journal Entry')
		doc.voucher_type = "Journal Entry"
		doc.user_remark = self.notes
		doc.posting_date = self.posting_date

		# money to account
		to_ = {
			"account":self.expense_type_account,
			"cost_center": self.branch_cost_center,
			"debit_in_account_currency": self.amount
		}
		# money from account
		from_ = {
			"account":self.branch_custody_account,
			"cost_center": self.branch_cost_center,
			"credit_in_account_currency": self.amount
		}
		
		doc.append("accounts",to_)
		doc.append("accounts",from_)

		doc.save(ignore_permissions=True)
		doc.submit()

		self.db_set('journal_entry', doc.name)

	def on_cancel(self):
		if not self.journal_entry:
			return

		journal_entry = frappe.get_doc("Journal Entry", self.journal_entry)
		if journal_entry.docstatus == 1:
			journal_entry.cancel()
	
	@frappe.whitelist()
	def set_missing_fields(self):
		branch = frappe.session.data.get("user_branch")
		if not self.branch and branch:
			self.branch = branch
			bdoc = frappe.get_doc("Branch", branch)
			self.branch_custody_account = bdoc.branch_custody_account
			self.branch_cost_center = bdoc.branch_cost_center

		if self.expense_type and not self.expense_type_account:
			self.expense_type_account = frappe.db.get_value("Expense Type", self.expense_type, "account")
		
		if not self.branch:
			frappe.throw("Branch is required. Please contact administrator to set default branch for your user's employee record.")
		if not self.branch_custody_account:
			frappe.throw("Branch Custody Account is required. Please contact administrator to set default branch custody account for your branch.")
		if not self.branch_cost_center:
			frappe.throw("Branch Cost Center is required. Please contact administrator to set default branch cost center for your branch.")
		if not self.expense_type_account:
			frappe.throw("Expense Type Account is required. Please set an account on the selected Expense Type.")