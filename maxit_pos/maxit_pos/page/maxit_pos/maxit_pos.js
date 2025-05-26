frappe.provide("MaxItPOS");
frappe.pages['maxit-pos'].on_page_load = function(wrapper) {
	var page = frappe.ui.make_app_page({
		parent: wrapper,
		title: 'MaxIT POS',
		single_column: true
	});

	$("head").append("<link href='/assets/maxit_pos/node_modules/vuetify/dist/vuetify.min.css' rel='stylesheet'>");
	$("head").append("<link rel='stylesheet' href='https://cdn.jsdelivr.net/npm/@mdi/font@6.x/css/materialdesignicons.min.css'>");
	$("head").append("<link rel='stylesheet' href='https://fonts.googleapis.com/css?family=Roboto:100,300,400,500,700,900' />");

	this.page.$MaxItPOS = new frappe.MaxItPOS.Controller(this.page);
}

frappe.pages["maxit-pos"].refresh = function (wrapper) {
	if (document.scannerDetectionData) {
		onScan.detachFrom(document);
		wrapper.$MaxItPOS.wrapper.html("");
		wrapper.$MaxItPOS.check_opening_entry();
	}
};