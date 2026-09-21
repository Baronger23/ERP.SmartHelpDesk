import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "core")))
import frappe_client as fc

print("=== STARTING 03_SETUP_CUSTOM_FIELDS.PY ===")

custom_fields = [
    # 1. Issue -> Asset
    {
        "dt": "Issue",
        "fieldname": "custom_asset",
        "label": "Related Asset",
        "fieldtype": "Link",
        "options": "Asset",
        "insert_after": "customer"
    },
    # 1b. Issue -> custom_asset_category (Skill-based Routing)
    {
        "dt": "Issue",
        "fieldname": "custom_asset_category",
        "label": "Asset Category (Chuyen mon thiet bi)",
        "fieldtype": "Link",
        "options": "Asset Category",
        "fetch_from": "custom_asset.asset_category",
        "insert_after": "custom_asset"
    },
    # 2. Issue -> custom_incident_time (FSM Actual Incident Time)
    {
        "dt": "Issue",
        "fieldname": "custom_incident_time",
        "label": "Actual Incident Time (Thoi diem khach bao)",
        "fieldtype": "Datetime",
        "insert_after": "custom_asset_category"
    },
    # 3. Issue -> custom_related_issue (Callback / Incident Chain Link)
    {
        "dt": "Issue",
        "fieldname": "custom_related_issue",
        "label": "Related Original Issue (Callback Ref)",
        "fieldtype": "Link",
        "options": "Issue",
        "insert_after": "custom_incident_time"
    },
    # 4. Issue -> custom_root_cause (Root Cause Category)
    {
        "dt": "Issue",
        "fieldname": "custom_root_cause",
        "label": "Root Cause Category",
        "fieldtype": "Select",
        "options": "Hardware Failure\nOperator Error\nFalse Alarm / No Fault Found\nAdjustment Only\nEnvironmental",
        "insert_after": "custom_related_issue"
    },
    # 5. Issue -> custom_has_callback (Flag on Original Issue)
    {
        "dt": "Issue",
        "fieldname": "custom_has_callback",
        "label": "Has Callback / Recall",
        "fieldtype": "Check",
        "insert_after": "custom_root_cause"
    },
    # 6. Stock Entry -> Issue
    {
        "dt": "Stock Entry",
        "fieldname": "custom_issue",
        "label": "Helpdesk Issue",
        "fieldtype": "Link",
        "options": "Issue",
        "insert_after": "purpose"
    },
    # 3. Stock Entry -> Asset
    {
        "dt": "Stock Entry",
        "fieldname": "custom_asset",
        "label": "Target Asset",
        "fieldtype": "Link",
        "options": "Asset",
        "insert_after": "custom_issue"
    },
    # 4. Stock Entry -> Technician (Link User as requested!)
    {
        "dt": "Stock Entry",
        "fieldname": "custom_technician",
        "label": "Technician",
        "fieldtype": "Link",
        "options": "User",
        "insert_after": "custom_asset"
    },
    # 5. Asset Maintenance Log -> Issue
    {
        "dt": "Asset Maintenance Log",
        "fieldname": "custom_issue",
        "label": "Corrective Issue",
        "fieldtype": "Link",
        "options": "Issue",
        "insert_after": "maintenance_status"
    },
    # 6. Asset -> custom_customer (Hạt sạn 1: Gán máy móc cho Khách hàng cụ thể)
    {
        "dt": "Asset",
        "fieldname": "custom_customer",
        "label": "Customer / Owner (Khach hang so huu)",
        "fieldtype": "Link",
        "options": "Customer",
        "insert_after": "item_code"
    },
    # 7. Asset -> custom_is_customer_equipment (Đánh dấu máy khách để loại trừ kế toán)
    {
        "dt": "Asset",
        "fieldname": "custom_is_customer_equipment",
        "label": "Is Customer Equipment (Thiet bi cua khach hang)",
        "fieldtype": "Check",
        "default": "1",
        "insert_after": "custom_customer"
    },
    # 8. Asset -> custom_qr_url (Hạt sạn 3: URL để quét QR tạo nhanh ticket)
    {
        "dt": "Asset",
        "fieldname": "custom_qr_url",
        "label": "Quick Issue URL (Link bao loi nhanh)",
        "fieldtype": "Small Text",
        "read_only": 1,
        "insert_after": "custom_is_customer_equipment"
    },
    # 9. Asset -> custom_qr_code_html (Hạt sạn 3: Hiển thị hình ảnh mã QR ngay trên máy)
    {
        "dt": "Asset",
        "fieldname": "custom_qr_code_html",
        "label": "Equipment QR Code (Tem QR May)",
        "fieldtype": "HTML",
        "insert_after": "custom_qr_url"
    },
    # 10. Stock Entry -> custom_billing_type (Hạt sạn 2: Phân định Bảo hành vs Tính phí khách hàng)
    {
        "dt": "Stock Entry",
        "fieldname": "custom_billing_type",
        "label": "Billing Type (Phan loai chi phi)",
        "fieldtype": "Select",
        "options": "Under Warranty\nBillable to Customer\nGoodwill",
        "default": "Under Warranty",
        "insert_after": "custom_technician"
    },
    # 11. Stock Entry -> custom_sales_invoice (Hạt sạn 2: Nối hóa đơn nếu là Billable)
    {
        "dt": "Stock Entry",
        "fieldname": "custom_sales_invoice",
        "label": "Sales Invoice Ref (Hoa don tinh phi)",
        "fieldtype": "Link",
        "options": "Sales Invoice",
        "insert_after": "custom_billing_type"
    },
    # 12. Issue -> custom_warranty_status
    {
        "dt": "Issue",
        "fieldname": "custom_warranty_status",
        "label": "Warranty Status (Trang thai bao hanh)",
        "fieldtype": "Select",
        "options": "In Warranty\nOut of Warranty\nGoodwill",
        "default": "In Warranty",
        "insert_after": "custom_asset"
    }
]

for cf in custom_fields:
    cf_name = f"{cf['dt']}-{cf['fieldname']}"
    if not fc.exists_doc("Custom Field", cf_name):
        try:
            res = fc.create_doc("Custom Field", cf)
            print(f"[CREATED] Custom Field: {cf_name}")
        except Exception as e:
            print(f"[ERROR] Custom Field {cf_name}: {e}")
    else:
        print(f"[EXISTS] Custom Field: {cf_name}")

print("=== 03_SETUP_CUSTOM_FIELDS.PY COMPLETED SUCCESSFULLY ===")
