import frappe
from frappe import _
from frappe.utils import strip_html

from invoice_lock.overdue import (
    CUSTOM_LOCK_DAYS_FIELD,
    CUSTOM_LOCK_STATUS_FIELD,
    CUSTOM_LOCKED_FIELD,
    ensure_customer_lock_fields,
)


def validate_customer_not_locked(doc, method):
    """Prevent saving Sales Order or Quotation if customer is locked"""
    if not doc.customer:
        return

    ensure_customer_lock_fields()

    # Use get_doc to safely access HTML field
    customer_doc = frappe.get_doc("Customer", doc.customer)

    if not customer_doc.get(CUSTOM_LOCKED_FIELD):
        return

    status_html = customer_doc.get(CUSTOM_LOCK_STATUS_FIELD)
    status = strip_html(status_html) if status_html else _("Locked")
    days_overdue = customer_doc.get(CUSTOM_LOCK_DAYS_FIELD) or 0

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

    ensure_customer_lock_fields()

    customer_doc = frappe.get_doc("Customer", customer)

    return {
        "locked": bool(customer_doc.get(CUSTOM_LOCKED_FIELD)),
        "status": customer_doc.get(CUSTOM_LOCK_STATUS_FIELD),
        "status_label": strip_html(customer_doc.get(CUSTOM_LOCK_STATUS_FIELD) or "") or None,
        "days_overdue": customer_doc.get(CUSTOM_LOCK_DAYS_FIELD),
    }


def enforce_customer_unlock_permissions(doc, method):
    """Allow only Customer Unlocker role to clear lock flags."""
    if doc.is_new():
        return

    ensure_customer_lock_fields()

    customer_doc = frappe.get_doc("Customer", doc.name)

    previous_locked = bool(customer_doc.get(CUSTOM_LOCKED_FIELD))
    unlocking = bool(previous_locked) and not bool(doc.get(CUSTOM_LOCKED_FIELD))

    if not unlocking:
        return

    if frappe.session.user == "Administrator":
        return

    if "Customer Unlocker" not in frappe.get_roles(frappe.session.user):
        frappe.throw(
            _("Only users with the Customer Unlocker role can unlock customers."),
            title=_("Insufficient Permission"),
        )

    # Clear lock metadata when unlocking
    doc.set(CUSTOM_LOCK_STATUS_FIELD, None)
    doc.set(CUSTOM_LOCK_DAYS_FIELD, None)
