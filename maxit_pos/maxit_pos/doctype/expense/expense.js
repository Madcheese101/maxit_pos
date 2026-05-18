// Copyright (c) 2026, MaxITly.com and contributors
// For license information, please see license.txt

frappe.ui.form.on("Expense", {
	before_validate(frm) {
		frm.call("set_missing_fields");
	},
	refresh(frm) {
        let is_allowed = frappe.user_roles.includes('Accounts Manager');
		if(is_allowed) {
			frm.set_df_property('branch', 'read_only', false);
			return;
		}
		frm.call("set_missing_fields");
	},
});
