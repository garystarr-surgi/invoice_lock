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

# INCLUDE JS FILE FOR SALES ORDER AND QUOTATION
app_include_js = "/assets/invoice_lock/js/customer_lock_check.js"

# Server-side validation hooks
doc_events = {
    "Sales Order": {
        "validate": "invoice_lock.validation.validate_customer_not_locked"
    },
    "Quotation": {
        "validate": "invoice_lock.validation.validate_customer_not_locked"
    },
    "Customer": {
        "validate": "invoice_lock.validation.enforce_customer_unlock_permissions"
    },
}


