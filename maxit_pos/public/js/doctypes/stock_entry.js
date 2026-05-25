let OUTGOING = ''
const IS_SUPER_USER = frappe.user_roles.includes("System Manager") || frappe.user_roles.includes("Accounts Manager")
const USER_BRANCH = frappe.boot.user_branch;
const USER_WAREHOUSE = frappe.boot.user_warehouse;

frappe.ui.form.on('Stock Entry', {
	refresh(frm) {
        OUTGOING = frm.doc.outgoing_stock_entry
        if(!USER_WAREHOUSE){
            frappe.alert(
                "Your user does not have a default warehouse set. Please contact your administrator.", 
                {indicator: 'orange'});
        }
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
        if(IS_SUPER_USER && frm.is_dirty() && !USER_WAREHOUSE){
            frm.set_df_property("from_branch", "read_only", false);
        }
	},
    stock_entry_type(frm){
        if(frm.doc.stock_entry_type == "Material Transfer" && frm.is_new() && !OUTGOING){
            frm.set_value("add_to_transit", 1);
        }
    },
    add_to_transit(frm){
        if(frm.is_new() && !OUTGOING && !IS_SUPER_USER && USER_WAREHOUSE){
            frm.set_value("from_branch", USER_BRANCH);
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
    validate_user_defaults(frm){
        if(!USER_BRANCH && !IS_SUPER_USER){
            frappe.alert(
                "Your user does not have a default branch set. Please contact your administrator.", 
                {indicator: 'red'}
            );
        }
        if(!USER_WAREHOUSE && USER_BRANCH){
            frappe.alert(
                "Your branch does not have a default warehouse set. Please contact your administrator.", 
                {indicator: 'red'}
            );
        }
    }
})