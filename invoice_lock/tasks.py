import frappe
from frappe.utils import nowdate, getdate
from frappe.utils import strip_html
from invoice_lock.overdue import (
    CUSTOM_LOCKED_FIELD,
    CUSTOM_LOCK_STATUS_FIELD,
    CUSTOM_LOCK_DAYS_FIELD,
    SOFT_LOCK_VALUE,
    HARD_LOCK_VALUE,
)

def notify_locked_customers():
    customers = frappe.get_all("Customer", fields=["name", "account_manager"])

    for cust in customers:
        invoices = frappe.get_all("Sales Invoice", filters={
            "customer": cust.name,
            "outstanding_amount": [">", 0],
            "docstatus": 1
        }, fields=["posting_date"])

        if not invoices:
            continue

        max_days = max([(getdate(nowdate()) - getdate(inv.posting_date)).days for inv in invoices])

        if max_days >= 40:
            level = "Locked" if max_days >= 50 else "Soft Locked"
            message = f"{cust.name} is {level} ({max_days} days past due)"
            account_manager = frappe.db.get_value("User", cust.account_manager, "email")

            if account_manager:
                frappe.sendmail(
                    recipients=[account_manager],
                    subject=f"Customer {level} Alert",
                    message=message
                )


def send_weekly_locked_customers_summary():
    """Send weekly email to each account manager listing their locked customers"""
    # Get all customers that are locked
    locked_customers = frappe.get_all(
        "Customer",
        filters={CUSTOM_LOCKED_FIELD: 1},
        fields=["name", "account_manager", CUSTOM_LOCK_STATUS_FIELD, CUSTOM_LOCK_DAYS_FIELD]
    )
    
    if not locked_customers:
        return
    
    # Group customers by account manager
    customers_by_manager = {}
    for customer in locked_customers:
        account_manager = customer.account_manager
        if not account_manager:
            continue
        
        if account_manager not in customers_by_manager:
            customers_by_manager[account_manager] = []
        
        # Determine lock type from status field
        status_html = customer.get(CUSTOM_LOCK_STATUS_FIELD) or ""
        status_text = strip_html(status_html).lower()
        days_overdue = customer.get(CUSTOM_LOCK_DAYS_FIELD) or 0
        
        if "hard locked" in status_text or days_overdue >= 50:
            lock_type = HARD_LOCK_VALUE
        elif "soft locked" in status_text or days_overdue >= 40:
            lock_type = SOFT_LOCK_VALUE
        else:
            lock_type = "Locked"
        
        customers_by_manager[account_manager].append({
            "name": customer.name,
            "lock_type": lock_type,
            "days_overdue": days_overdue
        })
    
    # Send email to each account manager
    for account_manager, customers in customers_by_manager.items():
        email = frappe.db.get_value("User", account_manager, "email")
        if not email:
            continue
        
        # Group customers by lock type
        soft_locked = [c for c in customers if c["lock_type"] == SOFT_LOCK_VALUE]
        hard_locked = [c for c in customers if c["lock_type"] == HARD_LOCK_VALUE]
        
        # Build email content
        body = "<h2>Weekly Locked Customers Summary</h2>"
        body += "<p>Below is a summary of your locked customers:</p>"
        
        if hard_locked:
            body += f"<h3>Hard Locked Customers ({len(hard_locked)}):</h3>"
            body += "<ul>"
            for customer in sorted(hard_locked, key=lambda x: x["days_overdue"], reverse=True):
                body += f'<li><strong>{customer["name"]}</strong> - {customer["days_overdue"]} days overdue</li>'
            body += "</ul>"
        
        if soft_locked:
            body += f"<h3>Soft Locked Customers ({len(soft_locked)}):</h3>"
            body += "<ul>"
            for customer in sorted(soft_locked, key=lambda x: x["days_overdue"], reverse=True):
                body += f'<li><strong>{customer["name"]}</strong> - {customer["days_overdue"]} days overdue</li>'
            body += "</ul>"
        
        total_count = len(customers)
        subject = f"Weekly Summary: {total_count} Locked Customer{'s' if total_count != 1 else ''}"
        
        frappe.sendmail(
            recipients=[email],
            subject=subject,
            message=body
        )
