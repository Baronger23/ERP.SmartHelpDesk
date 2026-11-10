app_name = "smart_helpdesk"
app_title = "Smart Helpdesk"
app_publisher = "AIS"
app_description = "Industrial service operations, design v3"
app_email = "maintainers@example.invalid"
app_license = "MIT"
required_apps = ["erpnext"]
after_install = "smart_helpdesk.install.sync"
after_migrate = "smart_helpdesk.install.sync"

from smart_helpdesk.schema import SCHEMAS as _SCHEMAS

doc_events = {
    "*": {
        "validate": "smart_helpdesk.security.guard_write",
        "on_trash": "smart_helpdesk.security.guard_delete",
    },
    "Stock Entry": {
        "before_submit": "smart_helpdesk.inventory.protect_holds",
        "before_cancel": "smart_helpdesk.inventory.protect_holds",
    },
    "Stock Ledger Entry": {"before_insert": "smart_helpdesk.inventory.protect_ledger"},
    "File": {"validate": "smart_helpdesk.security.protect_file"},
    "Sales Invoice": {
        "validate": "smart_helpdesk.commercial.validate_invoice",
        "before_submit": "smart_helpdesk.commercial.validate_invoice",
        "on_submit": "smart_helpdesk.commercial.invoice_event",
        "before_cancel": "smart_helpdesk.commercial.protect_invoice_cancel",
        "on_cancel": "smart_helpdesk.commercial.invoice_event",
    },
    "Purchase Order": {"before_submit": "smart_helpdesk.inventory.protect_purchase_order"},
}
permission_query_conditions = {
    name: "smart_helpdesk.security.query_" + name[4:].lower().replace(" ", "_")
    for name in _SCHEMAS
}
has_permission = {name: "smart_helpdesk.security.has_permission" for name in _SCHEMAS}
doctype_js = {name: "public/js/operations.js" for name in _SCHEMAS}
doctype_list_js = {name: "public/js/operations.js" for name in _SCHEMAS}
scheduler_events = {"daily": ["smart_helpdesk.tasks.generate_due_pm", "smart_helpdesk.tasks.build_daily_reports"]}
