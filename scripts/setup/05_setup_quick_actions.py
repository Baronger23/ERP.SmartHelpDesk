import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "core")))
import frappe_client as fc

print("=== STARTING 05_SETUP_QUICK_ACTIONS.PY ===")

# Client Script code for Technician Mobile Quick Actions on Issue
issue_client_script_code = """
frappe.ui.form.on('Issue', {
    refresh: function(frm) {
        if (frm.is_new()) return;

        // Action 1: Check-in / Start Work (When Status is Open)
        if (frm.doc.status === 'Open') {
            frm.add_custom_button(__('Bắt đầu xử lý (Check-in)'), function() {
                frappe.confirm(
                    __('Xác nhận Kỹ thuật viên đã có mặt tại hiện trường và bắt đầu xử lý sự cố?'),
                    function() {
                        frm.set_value('status', 'In Progress');
                        frm.save().then(() => {
                            frappe.show_alert({
                                message: __('Đã bắt đầu xử lý sự cố. Thời gian làm việc đã được ghi nhận!'),
                                indicator: 'green'
                            });
                        });
                    }
                );
            }).addClass('btn-primary').css({'font-weight': 'bold'});
        }

        // Action 2: Quick Material Issue (Xuất linh kiện sửa từ Kho Xe KTV)
        frm.add_custom_button(__('Xuất linh kiện sửa'), function() {
            let billing_type = frm.doc.custom_warranty_status === 'In Warranty' ? 'Under Warranty' : 'Billable to Customer';
            frappe.new_doc('Stock Entry', {
                purpose: 'Material Issue',
                custom_issue: frm.doc.name,
                custom_asset: frm.doc.custom_asset,
                custom_technician: frappe.session.user,
                custom_billing_type: billing_type
            });
        }, __('Tác vụ hiện trường')).addClass('btn-warning');

        // Action 3: Quick Resolve / Finish Work (Khi đang In Progress hoặc Open)
        if (frm.doc.status === 'In Progress' || frm.doc.status === 'Open') {
            frm.add_custom_button(__('Hoàn thành ca (Resolve)'), function() {
                let d = new frappe.ui.Dialog({
                    title: __('Nghiệm thu & Hoàn thành sự cố'),
                    fields: [
                        {
                            label: __('Phân loại Nguyên nhân gốc (Root Cause)'),
                            fieldname: 'root_cause',
                            fieldtype: 'Select',
                            options: 'Hardware Failure\\nOperator Error\\nFalse Alarm / No Fault Found\\nAdjustment Only\\nEnvironmental',
                            reqd: 1,
                            default: frm.doc.custom_root_cause || 'Hardware Failure'
                        },
                        {
                            label: __('Phân loại Chi phí / Bảo hành'),
                            fieldname: 'warranty_status',
                            fieldtype: 'Select',
                            options: 'In Warranty\\nOut of Warranty\\nGoodwill',
                            reqd: 1,
                            default: frm.doc.custom_warranty_status || 'In Warranty'
                        },
                        {
                            label: __('Biên bản nghiệm thu & Ghi chú xử lý'),
                            fieldname: 'resolution_details',
                            fieldtype: 'Small Text',
                            reqd: 1,
                            default: 'Kỹ thuật viên đã kiểm tra hiện trường, thay thế linh kiện và máy đã được chạy thử tải đạt yêu cầu.'
                        }
                    ],
                    primary_action_label: __('Xác nhận Đóng ca & Bàn giao'),
                    primary_action: function(values) {
                        frm.set_value('custom_root_cause', values.root_cause);
                        frm.set_value('custom_warranty_status', values.warranty_status);
                        frm.set_value('resolution_details', values.resolution_details);
                        frm.set_value('status', 'Resolved');
                        frm.save().then(() => {
                            d.hide();
                            frappe.msgprint({
                                title: __('Đã Hoàn Thành'),
                                message: __('Sự cố đã được đóng và ghi nhận nghiệm thu thành công!'),
                                indicator: 'green'
                            });
                        });
                    }
                });
                d.show();
            }).addClass('btn-success').css({'font-weight': 'bold'});
        }
    }
});
"""

client_scripts = [
    {
        "name": "Issue Technician Quick Actions",
        "dt": "Issue",
        "script_type": "DocType Event",
        "view": "Form",
        "enabled": 1,
        "script": issue_client_script_code
    }
]

for cs in client_scripts:
    if not fc.exists_doc("Client Script", cs["name"]):
        try:
            fc.create_doc("Client Script", cs)
            print(f"[CREATED] Client Script: {cs['name']}")
        except Exception as e:
            print(f"[ERROR] Client Script {cs['name']}: {e}")
    else:
        try:
            fc.update_doc("Client Script", cs["name"], cs)
            print(f"[UPDATED] Client Script: {cs['name']}")
        except Exception as e:
            print(f"[ERROR Updating] Client Script {cs['name']}: {e}")

print("=== 05_SETUP_QUICK_ACTIONS.PY COMPLETED SUCCESSFULLY ===")
