app_name = "invoice_lock"
app_title = "Invoice Lock"
app_publisher = "SurgiShop"
app_description = "Locks customers with overdue invoices"
app_email = "gary.starr@surgishop.com"
app_license = "MIT"

# Daily scheduled tasks
scheduler_events = {
    "daily": [
        "invoice_lock.overdue.check_overdue_invoices_and_lock_customers",
        "invoice_lock.tasks.notify_locked_customers"
    ]
}

# Fixtures for deployment
fixtures = [
    "Custom Field",
    {
        "doctype": "Role",
        "filters": [["name", "in", ["Customer Unlocker"]]]
    }
]

# Include JS for client-side lock check
app_include_js = "/assets/invoice_lock/js/customer_lock_check.js"

# Server-side validation and lock enforcement
doc_events = {
    "Sales Order": {
        "validate": "invoice_lock.validation.validate_customer_not_locked"
    },
    "Quotation": {
        "validate": "invoice_lock.validation.validate_customer_not_locked"
    },
    "Customer": {
        "validate": [
            "invoice_lock.validation.enforce_customer_unlock_permissions",
            "invoice_lock.customer_hooks.set_locked_status"
        ]
    }
}
