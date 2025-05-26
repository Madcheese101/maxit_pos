var fieldMapper = null;

frappe.ui.form.on('POS Profile', {
	async refresh(frm) {
		result = await frappe.call('maxit_pos.maxit_pos.api.get_item_doctype_fields');
		frm.fields_dict.custom_filters.grid.update_docfield_property("item_field", "options", result.message.field_labels);
	    this.fieldMapper = result.message.mapper;
	}
})

frappe.ui.form.on('POS Advanced Filters', {
	type(frm, cdt, cdn){
		const row = locals[cdt][cdn];
		if(row.type === "Item" && row.attribute !== ""){
		    frappe.model.set_value(cdt, cdn, 'attribute', null);
		    return;
		}
		if(row.type === "Item Attribute" && row.item_field !== ""){
		    frappe.model.set_value(cdt, cdn, 'item_field', null);
		    frappe.model.set_value(cdt, cdn, 'item_field_name', null);
		    frappe.model.set_value(cdt, cdn, 'field_type', null);
		    frappe.model.set_value(cdt, cdn, 'field_options', null);
		}
	},
	item_field(frm, cdt, cdn){
	    const row = locals[cdt][cdn];
		if(row.item_field === "" || row.type !== "Item") return;
	    frappe.model.set_value(cdt, cdn, 'item_field_name', this.fieldMapper[row.item_field].fieldname);
	    frappe.model.set_value(cdt, cdn, 'field_type', this.fieldMapper[row.item_field].fieldtype);
	    frappe.model.set_value(cdt, cdn, 'field_options', this.fieldMapper[row.item_field].options);
	}
})