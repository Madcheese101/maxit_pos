# Copyright (c) 2026, MaxITly.com and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document


class NoteCount(Document):
	def before_save(self):
		# remove Notes with count 0 from cash table
		if self.get("cash"):
			self.set("cash",[d for d in self.cash if d.count != 0])
	
	def validate(self):
		exists = frappe.db.exists("Note Count", {
			"posting_date": self.posting_date, 
			"mode_of_payment": self.mode_of_payment,
			"docstatus": 1,
		})
		if exists:
			frappe.throw(f"Note Count for {self.posting_date} and {self.mode_of_payment} already exists.")