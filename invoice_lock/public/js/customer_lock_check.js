// Handler for Sales Order
frappe.ui.form.on('Sales Order', {
  customer: function(frm) {
    if (!frm.doc.customer) return;

    frappe.call({
      method: "frappe.client.get",
      args: {
        doctype: "Customer",
        name: frm.doc.customer
      },
      callback: function(r) {
        console.log("Sales Order customer check:", r.message);
        if (r.message && r.message.custom_account_locked) {
          frappe.msgprint({
            title: __("Customer Locked"),
            message: __("This customer is locked and cannot be used for Sales Orders.")
          });
        }
      }
    });
  }
});

// Handler for Quotation
frappe.ui.form.on('Quotation', {
  customer: function(frm) {
    if (!frm.doc.customer) return;

    frappe.call({
      method: "frappe.client.get",
      args: {
        doctype: "Customer",
        name: frm.doc.customer
      },
      callback: function(r) {
        console.log("Quotation customer check:", r.message);
        if (r.message && r.message.custom_account_locked) {
          frappe.msgprint({
            title: __("Customer Locked"),
            message: __("This customer is locked and cannot be used for Quotations.")
          });
        }
      }
    });
  }
});
