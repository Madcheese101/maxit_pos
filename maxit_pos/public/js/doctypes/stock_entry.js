let OUTGOING = ''
const IS_SUPER_USER = frappe.user_roles.includes("System Manager") || frappe.user_roles.includes("Accounts Manager")
const USER_WAREHOUSE = frappe.boot.user_warehouse;

frappe.ui.form.on('Stock Entry', {
	refresh(frm) {
        OUTGOING = frm.doc.outgoing_stock_entry
		if(!OUTGOING && frm.is_new()){
            frm.set_value("stock_entry_type", "Material Transfer");
        }
        if(OUTGOING && frm.is_dirty() && frm.doc.to_branch){
            frappe.call(
                "maxit_pos.maxit_pos.api.get__warehouse", 
                {branch_name: frm.doc.to_branch}
            ).then(result => {
                frm.set_value("to_warehouse", result.message);
            });
        }
        if(IS_SUPER_USER && frm.is_dirty()){
            frm.set_df_property("from_branch", "read_only", false);
        }
	},
    stock_entry_type(frm){
        if(frm.doc.stock_entry_type == "Material Transfer" && frm.is_new() && !OUTGOING){
            frm.set_value("add_to_transit", 1);
        }
    },
    add_to_transit(frm){
        if(frm.is_new() && !OUTGOING && !IS_SUPER_USER){
            frm.set_value("from_warehouse", USER_WAREHOUSE);
        }
    },
    from_branch(frm){
        if(!OUTGOING && frm.is_dirty() && frm.doc.from_branch){
            frappe.call(
                "maxit_pos.maxit_pos.api.get__warehouse", 
                {branch_name: frm.doc.from_branch, get_transfer: true}
            ).then(result => {
                console.log(result);
                frm.set_value("from_warehouse", result.message[0]);
                frm.set_value("to_warehouse", result.message[1]);
            });
        }
    },

})