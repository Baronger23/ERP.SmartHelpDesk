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
    # 2. Issue -> custom_incident_time (FSM Actual Incident Time)
    {
        "dt": "Issue",
        "fieldname": "custom_incident_time",
        "label": "Actual Incident Time (Thoi diem khach bao)",
        "fieldtype": "Datetime",
        "insert_after": "custom_asset"
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
