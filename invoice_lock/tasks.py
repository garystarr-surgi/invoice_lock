import frappe
from frappe.utils import nowdate, getdate

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
