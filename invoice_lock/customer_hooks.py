from typing import Optional

from frappe.utils import cint

from invoice_lock.overdue import (
    CUSTOM_LOCK_DAYS_FIELD,
    CUSTOM_LOCK_STATUS_FIELD,
    CUSTOM_LOCKED_FIELD,
    HARD_LOCK_THRESHOLD,
    SOFT_LOCK_THRESHOLD,
    ensure_customer_lock_fields,
)


def _build_status_html(days_overdue: Optional[int]) -> str:
    days = cint(days_overdue or 0)

    if days >= HARD_LOCK_THRESHOLD:
        return f'<span class="text-danger">Hard Locked ({days}+ days past due)</span>'
    if days >= SOFT_LOCK_THRESHOLD:
        return f'<span class="text-warning">Soft Locked ({days} days past due)</span>'

    return '<span class="text-muted">Locked</span>'


def set_locked_status(doc, method):
    """Ensure the Customer lock status HTML field stays in sync with lock metadata."""
    ensure_customer_lock_fields()

    if not doc.get(CUSTOM_LOCKED_FIELD):
        doc.set(CUSTOM_LOCK_STATUS_FIELD, None)
        doc.set(CUSTOM_LOCK_DAYS_FIELD, None)
        return

    status_html = _build_status_html(doc.get(CUSTOM_LOCK_DAYS_FIELD))
    doc.set(CUSTOM_LOCK_STATUS_FIELD, status_html)

