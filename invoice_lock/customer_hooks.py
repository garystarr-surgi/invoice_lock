import frappe
from frappe.utils import nowdate, getdate

def set_locked_status(doc, method):
    invoices = frappe.get_all("Sales Invoice", filters={
        "customer": doc.name,
        "outstanding_amount": [">", 0],
        "docstatus": 1
    }, fields=["posting_date"])

    if not invoices:
        doc.custom_locked_status = ""
        return

    max_days = max([(getdate(nowdate()) - getdate(inv.posting_date)).days for inv in invoices])

    if max_days >= 50:
        doc.custom_locked_status = "<div style='color:red;'>Customer is Locked (50+ days past due)</div>"
    elif max_days >= 40:
        doc.custom_locked_status = "<div style='color:orange;'>Customer is Soft Locked (40+ days past due) See Accounting</div>"
    else:
        doc.custom_locked_status = ""
