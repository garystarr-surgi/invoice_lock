import frappe
from frappe import _

from invoice_lock.overdue import CUSTOM_LOCK_DAYS_FIELD, CUSTOM_LOCK_STATUS_FIELD, CUSTOM_LOCKED_FIELD


def validate_customer_not_locked(doc, method):
    """Prevent saving Sales Order or Quotation if customer is locked"""
    if not doc.customer:
        return
    
    lock_data = frappe.db.get_value(
        "Customer",
        doc.customer,
        [CUSTOM_LOCKED_FIELD, CUSTOM_LOCK_STATUS_FIELD, CUSTOM_LOCK_DAYS_FIELD],
        as_dict=True,
    )

    if not lock_data or not lock_data.get(CUSTOM_LOCKED_FIELD):
        return

    status = lock_data.get(CUSTOM_LOCK_STATUS_FIELD) or _("Locked")
    days_overdue = lock_data.get(CUSTOM_LOCK_DAYS_FIELD) or 0

    frappe.throw(
        _(
            "Cannot save {doctype}. Customer {customer} is {status} due to invoices {days} days past due."
        ).format(
            doctype=doc.doctype,
            customer=doc.customer,
            status=status,
            days=days_overdue,
        ),
        title=_("Customer Locked"),
    )


@frappe.whitelist()
def check_customer_lock_status(customer):
    """Server-side method to check if customer is locked (for client-side validation)"""
    if not customer:
        return {"locked": False}

    lock_data = frappe.db.get_value(
        "Customer",
        customer,
        [CUSTOM_LOCKED_FIELD, CUSTOM_LOCK_STATUS_FIELD, CUSTOM_LOCK_DAYS_FIELD],
        as_dict=True,
    )

    if not lock_data:
        return {"locked": False}

    return {
        "locked": bool(lock_data.get(CUSTOM_LOCKED_FIELD)),
        "status": lock_data.get(CUSTOM_LOCK_STATUS_FIELD),
        "days_overdue": lock_data.get(CUSTOM_LOCK_DAYS_FIELD),
    }


def enforce_customer_unlock_permissions(doc, method):
    """Allow only Customer Unlocker role to clear lock flags."""
    if doc.is_new():
        return

    lock_data = frappe.db.get_value(
        "Customer",
        doc.name,
        [CUSTOM_LOCKED_FIELD, CUSTOM_LOCK_STATUS_FIELD, CUSTOM_LOCK_DAYS_FIELD],
        as_dict=True,
    ) or {}

    previous_locked = bool(lock_data.get(CUSTOM_LOCKED_FIELD))

    unlocking = bool(previous_locked) and not bool(doc.get(CUSTOM_LOCKED_FIELD))

    if not unlocking:
        return

    if frappe.session.user == "Administrator":
        return

    if not frappe.has_role("Customer Unlocker"):
        frappe.throw(
            _("Only users with the Customer Unlocker role can unlock customers."),
            title=_("Insufficient Permission"),
        )

    # Clear lock metadata when unlocking
    doc.set(CUSTOM_LOCK_STATUS_FIELD, None)
    doc.set(CUSTOM_LOCK_DAYS_FIELD, None)

