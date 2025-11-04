app_name = "invoice_lock"
app_title = "Invoice Lock"
app_publisher = "SurgiShop"
app_description = "Locks customers with overdue invoices"
app_email = "gary.starr@surgishop.com"
app_license = "MIT"

scheduler_events = {
    "daily": [
        "invoice_lock.overdue.check_overdue_invoices_and_lock_customers"
    ]
}

fixtures = [
    "Custom Field",
    {
        "doctype": "Role",
        "filters": [["name", "in", ["Customer Unlocker"]]]
    }
]

doc_events = {
    "Quotation": {
        "validate": "invoice_lock.hooks.quotation.validate"
    },
    "Sales Order": {
        "validate": "invoice_lock.hooks.sales_order.validate"
    }
}
