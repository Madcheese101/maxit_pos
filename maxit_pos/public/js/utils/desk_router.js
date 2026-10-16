// Frappe v16 reads a leading module slug as a sidebar "shell" when the next segment names a
// doctype or workspace. The POS page shares its name with the MaxIT POS module's slug, so
// /desk/maxit-pos/stock-entry opened the Stock Entry list (and /expenses the HRMS Expenses
// workspace) instead of the POS view. The POS page never sits in a shell.
const beginsWithShell = frappe.router?.begins_with_shell;
if (beginsWithShell) {
	frappe.router.begins_with_shell = function (route) {
		if (route?.[0] === 'maxit-pos') return false;
		return beginsWithShell.call(this, route);
	};
}
