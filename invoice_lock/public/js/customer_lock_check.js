// Handler for Sales Order
function show_customer_lock_banner(frm) {
  if (!frm.doc.customer) {
    frm.customer_lock_warning_state = null;
    frm.dashboard && frm.dashboard.clear_headline();
    return;
  }

  frappe.call({
    method: "invoice_lock.validation.check_customer_lock_status",
    args: {
      customer: frm.doc.customer
    },
    callback: function(r) {
      frm.dashboard && frm.dashboard.clear_headline();

      if (!r.message || !r.message.locked) {
        frm.customer_lock_warning_state = null;
        return;
      }

      const status = (r.message.status || "").toLowerCase();
      const isHardLock = status.includes("hard");
      const bannerText = isHardLock
        ? __("Customer is Locked 50+ Days Past Due")
        : __("Customer is Soft Locked 40 Days Past Due");
      const bannerColor = isHardLock ? "red" : "yellow";

      if (frm.dashboard && frm.dashboard.set_headline_alert) {
        frm.dashboard.set_headline_alert(bannerText, bannerColor);
      }

      if (frm.customer_lock_warning_state !== status) {
        frappe.msgprint({
          title: __("Customer Locked"),
          message: __("This customer is locked and cannot be used for {0}.").format(frm.doctype)
        });
        frm.customer_lock_warning_state = status;
      }
    }
  });
}

frappe.ui.form.on('Sales Order', {
  customer: function(frm) {
    show_customer_lock_banner(frm);
  }
});

frappe.ui.form.on('Quotation', {
  customer: function(frm) {
    show_customer_lock_banner(frm);
  }
});
