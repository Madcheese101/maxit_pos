# Copyright (c) 2026, MaxITly.com and Contributors
# See license.txt

import frappe
from frappe.tests import IntegrationTestCase


# On IntegrationTestCase, the doctype test records and all
# link-field test record dependencies are recursively loaded
# Use these module variables to add/remove to/from that list
EXTRA_TEST_RECORD_DEPENDENCIES = []  # eg. ["User"]
IGNORE_TEST_RECORD_DEPENDENCIES = []  # eg. ["User"]



class IntegrationTestExpense(IntegrationTestCase):
	"""
	Integration tests for Expense.
	Use this class for testing interactions between multiple components.
	"""

	def test_amount_must_be_positive(self):
		expense_type = self._make_expense_type()
		branch = self._make_branch()

		expense = frappe.new_doc("Expense")
		expense.expense_type = expense_type.name
		expense.expense_type_account = expense_type.account
		expense.amount = -10
		expense.posting_date = frappe.utils.nowdate()
		expense.branch = branch.name
		expense.branch_custody_account = branch.branch_custody_account
		expense.branch_cost_center = branch.branch_cost_center

		with self.assertRaisesRegex(frappe.ValidationError, "Amount must be greater than zero"):
			expense.insert()

	def test_cancel_also_cancels_linked_journal_entry(self):
		expense_type = self._make_expense_type()
		branch = self._make_branch()

		expense = frappe.new_doc("Expense")
		expense.expense_type = expense_type.name
		expense.expense_type_account = expense_type.account
		expense.amount = 25
		expense.posting_date = frappe.utils.nowdate()
		expense.branch = branch.name
		expense.branch_custody_account = branch.branch_custody_account
		expense.branch_cost_center = branch.branch_cost_center
		expense.insert()
		expense.submit()

		self.assertTrue(expense.journal_entry)
		journal_entry = frappe.get_doc("Journal Entry", expense.journal_entry)
		self.assertEqual(journal_entry.docstatus, 1)

		expense.cancel()

		journal_entry.reload()
		self.assertEqual(expense.docstatus, 2)
		self.assertEqual(journal_entry.docstatus, 2)

	def _make_expense_type(self):
		expense_account = self._get_expense_account()
		return frappe.get_doc(
			{
				"doctype": "Expense Type",
				"expense_name": f"Test Expense Type {frappe.generate_hash(length=6)}",
				"account": expense_account,
			}
		).insert()

	def _make_branch(self):
		branch_custody_account = self._get_branch_custody_account()
		branch_cost_center = self._get_cost_center()
		branch = frappe.get_doc(
			{
				"doctype": "Branch",
				"branch": f"Test Expense Branch {frappe.generate_hash(length=6)}",
				"branch_custody_account": branch_custody_account,
				"branch_cost_center": branch_cost_center,
			}
		).insert()
		return branch

	def _get_company(self):
		company = frappe.defaults.get_global_default("company")
		if company:
			return company

		company = frappe.get_all("Company", pluck="name", limit=1)
		if not company:
			self.fail("No Company is available for Expense integration tests.")

		return company[0]

	def _get_expense_account(self):
		company = self._get_company()
		accounts = frappe.get_all(
			"Account",
			filters={
				"company": company,
				"root_type": "Expense",
				"is_group": 0,
			},
			pluck="name",
			limit=1,
		)
		if not accounts:
			self.fail("No expense account is available for Expense integration tests.")

		return accounts[0]

	def _get_branch_custody_account(self):
		company = self._get_company()
		accounts = frappe.get_all(
			"Account",
			filters={
				"company": company,
				"root_type": "Asset",
				"is_group": 0,
				"account_type": ["in", ["Cash", "Bank"]],
			},
			pluck="name",
			limit=1,
		)
		if not accounts:
			accounts = frappe.get_all(
				"Account",
				filters={
					"company": company,
					"root_type": "Asset",
					"is_group": 0,
				},
				pluck="name",
				limit=1,
			)
		if not accounts:
			self.fail("No branch custody account is available for Expense integration tests.")

		return accounts[0]

	def _get_cost_center(self):
		company = self._get_company()
		cost_centers = frappe.get_all(
			"Cost Center",
			filters={
				"company": company,
				"is_group": 0,
			},
			pluck="name",
			limit=1,
		)
		if not cost_centers:
			self.fail("No cost center is available for Expense integration tests.")

		return cost_centers[0]
