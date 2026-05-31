app_name = "maxit_pos"
app_title = "MaxIT POS"
app_publisher = "MaxITly.com"
app_description = "an elegant POS for erpnext 15"
app_email = "info@maxitly.com"
app_license = "bsl-1.0"

# Apps
# ------------------

# required_apps = []

# Each item in the list will be shown as an app in the apps page
# add_to_apps_screen = [
# 	{
# 		"name": "maxit_pos",
# 		"logo": "/assets/maxit_pos/logo.png",
# 		"title": "MaxIT POS",
# 		"route": "/maxit_pos",
# 		"has_permission": "maxit_pos.api.permission.has_app_permission"
# 	}
# ]

# Includes in <head>
# ------------------

# include js, css files in header of desk.html
# app_include_css = "/assets/maxit_pos/css/maxit_pos.css"
# app_include_js = "/assets/maxit_pos/js/maxit_pos.js"
app_include_js = [
    "maxit-pos.bundle.js",
]

# include js, css files in header of web template
# web_include_css = "/assets/maxit_pos/css/maxit_pos.css"
# web_include_js = "/assets/maxit_pos/js/maxit_pos.js"

# include custom scss in every website theme (without file extension ".scss")
# website_theme_scss = "maxit_pos/public/scss/website"

# include js, css files in header of web form
# webform_include_js = {"doctype": "public/js/doctype.js"}
# webform_include_css = {"doctype": "public/css/doctype.css"}

# include js in page
# page_js = {"page" : "public/js/file.js"}

# include js in doctype views
# doctype_js = {"doctype" : "public/js/doctype.js"}
doctype_js = {
    "POS Profile" : "public/js/doctypes/pos_profile.js",
    "Sales Invoice" : "public/js/doctypes/sales_invoice.js",
    "Stock Entry" : "public/js/doctypes/stock_entry.js"
}
# doctype_list_js = {"doctype" : "public/js/doctype_list.js"}
# doctype_tree_js = {"doctype" : "public/js/doctype_tree.js"}
# doctype_calendar_js = {"doctype" : "public/js/doctype_calendar.js"}

# Svg Icons
# ------------------
# include app icons in desk
# app_include_icons = "maxit_pos/public/icons.svg"

# Home Pages
# ----------

# application home page (will override Website Settings)
# home_page = "login"

# website user home page (by Role)
# role_home_page = {
# 	"Role": "home_page"
# }

# Generators
# ----------

# automatically create page for each record of this doctype
# website_generators = ["Web Page"]

# Jinja
# ----------

# add methods and filters to jinja environment
# jinja = {
# 	"methods": "maxit_pos.utils.jinja_methods",
# 	"filters": "maxit_pos.utils.jinja_filters"
# }

# Installation
# ------------

# before_install = "maxit_pos.install.before_install"
# after_install = "maxit_pos.install.after_install"

# Uninstallation
# ------------

# before_uninstall = "maxit_pos.uninstall.before_uninstall"
# after_uninstall = "maxit_pos.uninstall.after_uninstall"

# Integration Setup
# ------------------
# To set up dependencies/integrations with other apps
# Name of the app being installed is passed as an argument

# before_app_install = "maxit_pos.utils.before_app_install"
# after_app_install = "maxit_pos.utils.after_app_install"

# Integration Cleanup
# -------------------
# To clean up dependencies/integrations with other apps
# Name of the app being uninstalled is passed as an argument

# before_app_uninstall = "maxit_pos.utils.before_app_uninstall"
# after_app_uninstall = "maxit_pos.utils.after_app_uninstall"

# Desk Notifications
# ------------------
# See frappe.core.notifications.get_notification_config

# notification_config = "maxit_pos.notifications.get_notification_config"

# Permissions
# -----------
# Permissions evaluated in scripted ways

# permission_query_conditions = {
# 	"Event": "frappe.desk.doctype.event.event.get_permission_query_conditions",
# }
#
# has_permission = {
# 	"Event": "frappe.desk.doctype.event.event.has_permission",
# }

# DocType Class
# ---------------
# Override standard doctype classes

# override_doctype_class = {
# 	"ToDo": "custom_app.overrides.CustomToDo"
# }

# Document Events
# ---------------
# Hook on document methods and events

# doc_events = {
# 	"*": {
# 		"on_update": "method",
# 		"on_cancel": "method",
# 		"on_trash": "method"
# 	}
# }

doc_events = {
    "POS Profile": {
        "on_update": "maxit_pos.maxit_pos.page.maxit_pos.api.api.on_pos_profile_cache_invalidate",
        "on_trash": "maxit_pos.maxit_pos.page.maxit_pos.api.api.on_pos_profile_cache_invalidate",
    },
    "Item Group": {
        "on_update": "maxit_pos.maxit_pos.page.maxit_pos.api.api.on_item_group_cache_invalidate",
        "on_trash": "maxit_pos.maxit_pos.page.maxit_pos.api.api.on_item_group_cache_invalidate",
        "after_rename": "maxit_pos.maxit_pos.page.maxit_pos.api.api.on_item_group_cache_invalidate",
    },
}

# Scheduled Tasks
# ---------------

scheduler_events = {
	# "all": [
	# 	"maxit_pos.tasks.all"
	# ],
	# "daily": [
	# 	"maxit_pos.tasks.daily"
	# ],
	# "hourly": [
	# 	"maxit_pos.tasks.hourly"
	# ],
	# "weekly": [
	# 	"maxit_pos.tasks.weekly"
	# ],
	# "monthly": [
	# 	"maxit_pos.tasks.monthly"
	# ],
    "cron": {
        # run at 12AM
        "0 0 * * *":[
            "maxit_pos.tasks.close_sifts",
        ]
	}
}

# Testing
# -------

# before_tests = "maxit_pos.install.before_tests"

# Overriding Methods
# ------------------------------
#
override_whitelisted_methods = {
	"from erpnext.accounts.doctype.pos_invoice.pos_invoice.get_stock_availability": "maxit_pos.overrides.get_stock_availability"
}
#
# each overriding function accepts a `data` argument;
# generated from the base implementation of the doctype dashboard,
# along with any modifications made in other Frappe apps
# override_doctype_dashboards = {
# 	"Task": "maxit_pos.task.get_dashboard_data"
# }

# exempt linked doctypes from being automatically cancelled
#
# auto_cancel_exempted_doctypes = ["Auto Repeat"]

# Ignore links to specified DocTypes when deleting documents
# -----------------------------------------------------------

# ignore_links_on_delete = ["Communication", "ToDo"]

# Request Events
# ----------------
# before_request = ["maxit_pos.utils.before_request"]
# after_request = ["maxit_pos.utils.after_request"]

# Job Events
# ----------
# before_job = ["maxit_pos.utils.before_job"]
# after_job = ["maxit_pos.utils.after_job"]

# User Data Protection
# --------------------

# user_data_fields = [
# 	{
# 		"doctype": "{doctype_1}",
# 		"filter_by": "{filter_by}",
# 		"redact_fields": ["{field_1}", "{field_2}"],
# 		"partial": 1,
# 	},
# 	{
# 		"doctype": "{doctype_2}",
# 		"filter_by": "{filter_by}",
# 		"partial": 1,
# 	},
# 	{
# 		"doctype": "{doctype_3}",
# 		"strict": False,
# 	},
# 	{
# 		"doctype": "{doctype_4}"
# 	}
# ]

# Authentication and authorization
# --------------------------------

# auth_hooks = [
# 	"maxit_pos.auth.validate"
# ]

# Automatically update python controller files with type annotations for this app.
# export_python_type_annotations = True

# default_log_clearing_doctypes = {
# 	"Logging DocType Name": 30  # days to retain logs
# }
extend_bootinfo = "maxit_pos.boot.extend_boot_info"
on_session_creation = "maxit_pos.login.on_session_created"
fixtures = [
    {
        "doctype": "Custom Field",
        "filters": [
            
            [
                "name",
                "in",
                [
                    "POS Profile-custom_advanced_filters",
                    "POS Profile-custom_payment_entry_print_format",
                    "POS Profile-custom_allow_print_last_invoice",
                    "POS Item Group-custom_is_group",
                    "POS Profile-custom_print_last_invoice_for_creator_only",
                    "POS Profile-custom_max_items_listing",
                    "POS Profile-custom_allow_purchase",
                    "POS Profile-custom_purchase_invoice_print_format",
                    "POS Profile-custom_show_closing_balance",
                    "POS Profile-custom_enable_note_count",
                    "POS Profile-custom_note_count_print_format",
                    "Sales Invoice Item-custom_max_discount_",
                    "Purchase Invoice-custom_supplier_branch",
                    "Purchase Receipt-custom_supplier_branch",
                    "Purchase Receipt-custom_supplier_invoice",
                    "Purchase Receipt-custom_supplier_invoice_no",
                    "Purchase Receipt-custom_column_break_hbo4b",
                    "Purchase Receipt-custom_supplier_invoice_date",
                    "Mode of Payment-custom_middle_man_account",
                    "Payment Entry-custom_note_count",
                    "Payment Entry-custom_pos_profile",
                    "Payment Entry-custom_is_closing_entry",
                    "Branch-custom_cost_center",
                    "Branch-custom_branch_custody_account",
                    "Branch-custom_damaged_warehouse",
                    "Branch-custom_transfer_warehouse",
                    "Branch-custom_material_warehouse",
                    "Branch-custom_column_break_19mks",
                    "Stock Entry-custom_from_branch",
                    "Stock Entry-custom_to_branch",
                    "Employee Advance-custom_branch",
                    "Expense Claim-custom_branch",
                ]
            ]
        ]
    },
    {
        "doctype": "Property Setter",
        "filters": [
            [
                "name",
                "in",
                [
                    "Stock Entry-naming_series-options",
                    "Stock Entry-naming_series-default",
                    "Employee Advance-advance_account-fetch_from",
                ]
            ]
        ]
    },
    {
        "doctype": "Custom DocPerm",
        "filters": {
            "parent": [
                "in",
                [
                    "POS Closing Entry", 
                    "POS Opening Entry",
                ]
            ]
        }
    },
]

from maxit_pos.overrides import override_methods
override_methods()