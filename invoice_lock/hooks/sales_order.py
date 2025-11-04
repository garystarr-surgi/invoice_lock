import frappe
from frappe import _

def validate(doc, method):
    customer = frappe.get_doc("Customer", doc.customer)
    if customer.custom_account_locked:
        frappe.throw(_("Customer {0} is locked and cannot be used for {1}.").format(customer.name, doc.doctype))
