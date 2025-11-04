frappe.ui.form.on(['Sales Order', 'Quotation'], {
  refresh(frm) {
    // Trigger on form load if customer already set
    check_customer_lock(frm);
  },
  customer(frm) {
    // Trigger when customer field changes
    check_customer_lock(frm);
  },
  validate(frm) {
    // Prevent saving if customer is locked
    if (frm.doc.customer_locked) {
      frappe.throw(__('Cannot save this document. Customer is locked due to overdue invoices.'));
    }
  }
});

// Extra check for Quotation dynamic fields after rendering
frappe.ui.form.on('Quotation', {
  onload_post_render(frm) {
    check_customer_lock(frm);
  }
});

function check_customer_lock(frm) {
  if (!frm.doc.customer) return;

  frappe.call({
    method: "frappe.client.get",
    args: {
      doctype: "Customer",
      name: frm.doc.customer
    },
    callback: function(r) {
      if (r.message && r.message.custom_account_locked) {
        frappe.msgprint({
          title: __("Customer Locked"),
          message: __("This customer is locked and cannot be used for Sales Orders or Quotations."),
          indicator: "red"
        });
        frm.set_value('customer', '');
        frm.doc.customer_locked = true;  // Flag to prevent saving
      } else {
        frm.doc.customer_locked = false;
      }
    }
  });
}
