from typing import Optional

import frappe
from frappe.utils import add_days, getdate, now

CUSTOM_LOCKED_FIELD = "custom_account_locked"
CUSTOM_LOCK_STATUS_FIELD = "custom_account_lock_status"
CUSTOM_LOCK_DAYS_FIELD = "custom_account_lock_days_overdue"

SOFT_LOCK_THRESHOLD = 40
HARD_LOCK_THRESHOLD = 50

SOFT_LOCK_VALUE = "Soft Locked"
HARD_LOCK_VALUE = "Hard Locked"


def check_overdue_invoices_and_lock_customers():
    today = getdate(now())
    oldest_due_date = add_days(today, -SOFT_LOCK_THRESHOLD)

    overdue_invoices = frappe.get_list(
        "Sales Invoice",
        filters={
            "docstatus": 1,
            "outstanding_amount": (">", 0),
            "due_date": ("<", oldest_due_date),
        },
        fields=[
            "name",
            "customer",
            "due_date",
            "outstanding_amount",
            "customer_name",
            "company",
        ],
    )

    locks_by_customer = {}

    for invoice in overdue_invoices:
        days_overdue = (today - getdate(invoice.due_date)).days
        lock_status = _get_lock_status_for_days(days_overdue)

        if not lock_status:
            continue

        existing = locks_by_customer.get(invoice.customer)
        if not existing or days_overdue > existing["days_overdue"]:
            locks_by_customer[invoice.customer] = {
                "invoice": invoice,
                "days_overdue": days_overdue,
                "lock_status": lock_status,
            }

    for customer_name, lock_info in locks_by_customer.items():
        _apply_lock(customer_name, lock_info, today)

    frappe.db.commit()


def _get_lock_status_for_days(days_overdue: int) -> Optional[str]:
    if days_overdue >= HARD_LOCK_THRESHOLD:
        return HARD_LOCK_VALUE
    if days_overdue >= SOFT_LOCK_THRESHOLD:
        return SOFT_LOCK_VALUE
    return None


def _apply_lock(customer_name, lock_info, today):
    invoice = lock_info["invoice"]
    days_overdue = lock_info["days_overdue"]
    new_status = lock_info["lock_status"]

    customer_doc = frappe.get_doc("Customer", customer_name)
    current_locked = bool(customer_doc.get(CUSTOM_LOCKED_FIELD))
    current_status = customer_doc.get(CUSTOM_LOCK_STATUS_FIELD)
    current_days = customer_doc.get(CUSTOM_LOCK_DAYS_FIELD)

    status_changed = (current_status != new_status) or (not current_locked)
    needs_save = status_changed or current_days != days_overdue

    if not needs_save:
        return

    customer_doc.set(CUSTOM_LOCKED_FIELD, 1)
    customer_doc.set(CUSTOM_LOCK_STATUS_FIELD, new_status)
    customer_doc.set(CUSTOM_LOCK_DAYS_FIELD, days_overdue)
    customer_doc.save(ignore_permissions=True)

    if status_changed:
        _notify_account_manager(customer_doc, invoice, new_status, days_overdue, today)


def _notify_account_manager(customer_doc, invoice_doc, lock_status, days_overdue, today):
    account_manager = customer_doc.account_manager
    email = frappe.db.get_value("User", account_manager, "email") if account_manager else None

    if not email:
        return

    currency = frappe.db.get_value("Company", invoice_doc.company, "default_currency")

    if lock_status == SOFT_LOCK_VALUE:
        subject = f"Customer {customer_doc.name} soft locked at {days_overdue} days overdue"
        body = f"""
            <p>Customer <strong>{customer_doc.name}</strong> is now <strong>soft locked</strong>
            because invoice <strong>{invoice_doc.name}</strong> is
            <strong>{days_overdue} days overdue</strong> (Due: {invoice_doc.due_date}).</p>
            <p>Outstanding Amount: {invoice_doc.outstanding_amount} {currency}</p>
            <p><strong>Action:</strong> Please coordinate with Accounting. Customer access is limited until resolved.</p>
        """
    else:
        subject = f"Customer {customer_doc.name} locked at {days_overdue}+ days overdue"
        body = f"""
            <p>Customer <strong>{customer_doc.name}</strong> is now <strong>hard locked</strong>
            because invoice <strong>{invoice_doc.name}</strong> is
            <strong>{days_overdue} days overdue</strong> (Due: {invoice_doc.due_date}).</p>
            <p>Outstanding Amount: {invoice_doc.outstanding_amount} {currency}</p>
            <p><strong>Action:</strong> Customer is fully locked. Please escalate with Accounting.</p>
        """

    frappe.sendmail(
        recipients=[email],
        subject=subject,
        message=f"""
            {body}
            <p>Lock enforced on {today}. Only users with the Customer Unlocker role can restore access.</p>
        """,
    )


@frappe.whitelist()
def run_invoice_lock():
    check_overdue_invoices_and_lock_customers()
