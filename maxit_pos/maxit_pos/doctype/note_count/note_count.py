# Copyright (c) 2026, MaxITly.com and contributors
# For license information, please see license.txt

# import frappe
from frappe.model.document import Document


class NoteCount(Document):
	def before_save(self):
		# remove Notes with count 0 from cash table
		if self.get("cash"):
			self.set("cash",[d for d in self.cash_table if d.count != 0])
