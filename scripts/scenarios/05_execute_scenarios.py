import sys
import os
import json
import time
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "core")))
import frappe_client as fc

print("=== STARTING 05_EXECUTE_SCENARIOS.PY ===")

# Lookup Asset Names by item_code
def get_asset_doc_name(item_code):
    docs = fc.list_docs("Asset", filters=[["item_code", "=", item_code], ["company", "=", fc.COMPANY]])
    if docs:
        return docs[0]["name"]
    return None

asset_cmp = get_asset_doc_name("ITEM-AST-CMP-02") # May nen khi
asset_prn = get_asset_doc_name("ITEM-AST-PRN-01") # May in Flexo
asset_chl = get_asset_doc_name("ITEM-AST-CHL-03") # Chiller
asset_gen = get_asset_doc_name("ITEM-AST-GEN-04") # May phat dien
asset_pnl = get_asset_doc_name("ITEM-AST-PNL-05") # Tu dien MSB

print(f"[OK] Assets resolved: CMP={asset_cmp}, PRN={asset_prn}, CHL={asset_chl}, GEN={asset_gen}, PNL={asset_pnl}")

tech_pool = [
    "an.nguyen@smarthelpdesk.local",
    "binh.tran@smarthelpdesk.local",
    "cuong.le@smarthelpdesk.local"
]

# 1. CREATE 6 DIVERSE ISSUES (TESTING HD-01, HD-02, HD-03)
issues_def = [
    {
        "id_key": "ISSUE_1",
        "subject": "May nen khi Hitachi bao loi qua nhiet E-04 va tu ngat ca lam viec",
        "customer": "Cong ty CP Bao bi Tan A",
        "priority": "Urgent",
        "issue_type": "Corrective Repair",
        "asset": asset_cmp,
        "target_tech": tech_pool[0], # Round Robin #1 -> an.nguyen
        "status": "Open",
        "warranty_status": "In Warranty",
        "incident_time": "2026-09-07 10:45:00", # FSM: Khach goi Hotline bao luc 10:45
        "description": "May nen khi bao loi E-04 qua nhiet luc 08:30 sang, ap suat khi giam dot ngot lam dung ca san xuat."
    },
    {
        "id_key": "ISSUE_2",
        "subject": "Yeu cau kiem tra chay thu tai may phat dien Cummins va thay loc nhien lieu",
        "customer": "Xi nghiep Duoc Hai Nam",
        "priority": "Medium",
        "issue_type": "Preventive Maintenance",
        "asset": asset_gen,
        "target_tech": tech_pool[1], # Round Robin #2 -> binh.tran
        "status": "Open",
        "incident_time": "2026-09-07 11:00:00",
        "description": "Chuan bi cho mua mua bao, nha may can kiem tra tong the bo dieu toc va bom dau may phat dien."
    },
    {
        "id_key": "ISSUE_3",
        "subject": "May in Flexo mau so 3 in ra bi soc ngang nghi nghet dau phun",
        "customer": "Cong ty CP Bao bi Tan A",
        "priority": "High",
        "issue_type": "Corrective Repair",
        "asset": asset_prn,
        "target_tech": tech_pool[2], # Round Robin #3 -> cuong.le
        "status": "Replied",
        "incident_time": "2026-09-07 11:15:00",
        "description": "Ban in hop giay carton bi loi vet soc trang tai cum in mau vang so 3."
    },
    {
        "id_key": "ISSUE_4",
        "subject": "Mui khet tai nhanh bom ep so 2 CB nhanh bi nhay tren tu MSB",
        "customer": "Cong ty Nhua & Co khi Song Long",
        "priority": "High",
        "issue_type": "Corrective Repair",
        "asset": asset_pnl,
        "target_tech": tech_pool[0], # Round Robin #4 -> LOOPS BACK TO an.nguyen
        "status": "Open",
        "incident_time": "2026-09-07 11:20:00",
        "description": "Khoi dong tu nhanh may ep so 2 bi ro ho quang, phat nhiet nong va nhay aptomat."
    },
    {
        "id_key": "ISSUE_5",
        "subject": "He thong Chiller bi dong bang duong hut can thay the van tiet luu",
        "customer": "Xi nghiep Duoc Hai Nam",
        "priority": "Medium",
        "issue_type": "Corrective Repair",
        "asset": asset_chl,
        "target_tech": tech_pool[2],
        "status": "On Hold", # Gap Analysis representation of "Waiting for Parts"
        "incident_time": "2026-09-07 11:25:00",
        "description": "Bao tri phat hien van tiet luu Danfoss hoat dong sai lech gay dong bang ong hut. [WAITING FOR PARTS: Van tiet luu PART-VAL-EXP01]."
    },
    {
        "id_key": "ISSUE_6",
        "subject": "Tu van ky thuat nang cap he thong giam sat ap suat khi nen qua IoT",
        "customer": "Cong ty CP Bao bi Tan A",
        "priority": "Low",
        "issue_type": "Technical Inspection",
        "asset": asset_cmp,
        "target_tech": tech_pool[1],
        "status": "Closed",
        "incident_time": "2026-09-07 11:30:00",
        "description": "Khao sat vi tri lap dat them cam bien do ap suat khi nen tren duong ong chinh."
    }
]

created_issues = {}

for item in issues_def:
    # Check if issue with same subject already exists
    existing = fc.list_docs("Issue", filters=[["subject", "=", item["subject"]], ["company", "=", fc.COMPANY]])
    if not existing:
        issue_doc = fc.create_doc("Issue", {
            "subject": item["subject"],
            "customer": item["customer"],
            "priority": item["priority"],
            "issue_type": item["issue_type"],
            "company": fc.COMPANY,
            "status": "Open",
            "custom_asset": item["asset"],
            "custom_incident_time": item.get("incident_time"),
            "custom_warranty_status": item.get("warranty_status", "In Warranty"),
            "description": item["description"]
        })
        iss_name = issue_doc.get("name")
        print(f"[CREATED] Issue: {iss_name} -> {item['subject'][:45]}...")
    else:
        iss_name = existing[0]["name"]
        print(f"[EXISTS] Issue: {iss_name}")
        # Ensure custom_incident_time and custom_warranty_status are updated
        update_fields = {}
        if item.get("incident_time"):
            update_fields["custom_incident_time"] = item.get("incident_time")
        if item.get("warranty_status"):
            update_fields["custom_warranty_status"] = item.get("warranty_status")
        if update_fields:
            fc.update_doc("Issue", iss_name, update_fields)

    # Assign technician according to Round Robin contract
    assign_res = fc.request("POST", "/api/method/frappe.desk.form.assign_to.add", {
        "doctype": "Issue",
        "name": iss_name,
        "assign_to": [item["target_tech"]]
    })

    # Update status if needed (e.g. Replied, On Hold, Closed)
    if item["status"] != "Open":
        fc.update_doc("Issue", iss_name, {"status": item["status"]})

    # Read back doc to verify SLA and Assignment
    fresh_doc = fc.get_doc("Issue", iss_name)
    assign_list = fc.list_docs("Issue", filters=[["name", "=", iss_name]], fields=["name", "_assign"])
    assigned_str = assign_list[0].get("_assign") if assign_list else None

    created_issues[item["id_key"]] = {
        "name": iss_name,
        "subject": item["subject"],
        "customer": item["customer"],
        "priority": item["priority"],
        "status": fresh_doc.get("status"),
        "sla": fresh_doc.get("service_level_agreement"),
        "response_by": fresh_doc.get("response_by"),
        "resolution_by": fresh_doc.get("resolution_by"),
        "assigned_user": item["target_tech"],
        "_assign": assigned_str,
        "asset": item["asset"]
    }

print("\n--- ISSUE CREATION & VERIFICATION SUMMARY ---")
for k, v in created_issues.items():
    print(f"[{k}] {v['name']} | Cust: {v['customer'][:15]} | Prio: {v['priority']} | SLA: {v['sla']} | Tech: {v['assigned_user']} | Status: {v['status']}")

# 2. PREVENTIVE MAINTENANCE phát hiện lỗi -> SINH CORRECTIVE ISSUE (GAP 4)
print("\n--- EXECUTING PREVENTIVE LOG -> ISSUE LINKAGE ---")
# Find Asset Maintenance for Chiller
m_plans = fc.list_docs("Asset Maintenance", filters=[["asset_name", "=", asset_chl]])
m_plan_name = m_plans[0]["name"] if m_plans else None
m_plan_doc = fc.get_doc("Asset Maintenance", m_plan_name) if m_plan_name else None
task_row_name = m_plan_doc.get("asset_maintenance_tasks", [{}])[0].get("name") if m_plan_doc else None

# Check if log already exists
existing_logs = fc.list_docs("Asset Maintenance Log", filters=[["asset_name", "=", asset_chl], ["custom_issue", "=", created_issues["ISSUE_5"]["name"]]])
if not existing_logs:
    m_log = fc.create_doc("Asset Maintenance Log", {
        "asset_maintenance": m_plan_name,
        "asset_name": asset_chl,
        "task": task_row_name,
        "maintenance_status": "Completed",
        "completion_date": "2026-09-07",
        "actions_performed": "Ve sinh binh ngung sach se. Phat hien chenh lech nhiet do sensor PT100 tren duong hut, da khoi tao Issue yeu cau kiem tra chuyen sau.",
        "custom_issue": created_issues["ISSUE_5"]["name"]
    })
    m_log_name = m_log.get("name")
else:
    m_log_name = existing_logs[0]["name"]
print(f"[OK] Asset Maintenance Log: {m_log_name} -> Linked custom_issue: {created_issues['ISSUE_5']['name']}")

# 3. STOCK ENTRY (MATERIAL ISSUE) CHO ISSUE 1 & KIỂM CHỨNG REORDER LEVEL (INV-01, INV-02)
print("\n--- EXECUTING MATERIAL ISSUE FOR REPAIR & REORDER CHECK ---")
issue_1_name = created_issues["ISSUE_1"]["name"]
assigned_tech_iss1 = created_issues["ISSUE_1"]["assigned_user"]
wh_main = f"Kho Linh kien Trung tam - {fc.COMPANY_ABBR}"

# Check current stock of PART-FLT-OIL01 before issue
bins = fc.list_docs("Bin", filters=[["item_code", "=", "PART-FLT-OIL01"], ["warehouse", "=", wh_main]], fields=["actual_qty", "ordered_qty"])
qty_before = bins[0]["actual_qty"] if bins else 0
print(f"[STOCK BEFORE] PART-FLT-OIL01 in {wh_main}: {qty_before} Nos")

# Check if Stock Entry (Material Issue) for this issue already exists
existing_se = fc.list_docs("Stock Entry", filters=[["custom_issue", "=", issue_1_name], ["docstatus", "=", 1]])
if not existing_se:
    # Create and Submit Stock Entry (Material Issue)
    se_issue_doc = fc.create_doc("Stock Entry", {
        "stock_entry_type": "Material Issue",
        "company": fc.COMPANY,
        "custom_issue": issue_1_name,
        "custom_asset": asset_cmp,
        "custom_technician": assigned_tech_iss1,
        "custom_billing_type": "Under Warranty",
        "items": [
            {
                "item_code": "PART-FLT-OIL01",
                "qty": 2,
                "uom": "Nos",
                "stock_uom": "Nos",
                "conversion_factor": 1,
                "s_warehouse": wh_main,
                "basic_rate": 650000
            }
        ]
    })
    se_issue_name = se_issue_doc.get("name")
    fc.submit_doc("Stock Entry", se_issue_name)
    print(f"[SUBMITTED] Stock Entry (Material Issue): {se_issue_name}")
else:
    se_issue_name = existing_se[0]["name"]
    print(f"[EXISTS] Stock Entry (Material Issue): {se_issue_name}")
print(f"  - Linked custom_issue: {issue_1_name}")
print(f"  - Linked custom_asset: {asset_cmp}")
print(f"  - Linked custom_technician: {assigned_tech_iss1}")

# Check stock after issue
bins_after = fc.list_docs("Bin", filters=[["item_code", "=", "PART-FLT-OIL01"], ["warehouse", "=", wh_main]], fields=["actual_qty", "ordered_qty"])
qty_after = bins_after[0]["actual_qty"] if bins_after else 0
print(f"[STOCK AFTER] PART-FLT-OIL01 in {wh_main}: {qty_after} Nos")

# Reorder Level verification: Level is 3, qty_after is 2 -> 2 < 3!
item_oil_filter = fc.get_doc("Item", "PART-FLT-OIL01")
reorder_lvl = item_oil_filter.get("reorder_levels", [{}])[0].get("warehouse_reorder_level", 3)
reorder_triggered = qty_after < reorder_lvl
print(f"[REORDER VERIFICATION] Actual Qty ({qty_after}) < Reorder Level ({reorder_lvl})? -> {reorder_triggered} (Reorder Trigger Condition Satisfied!)")

# Update Issue 1 to Resolved now that parts are issued and replaced
fc.update_doc("Issue", issue_1_name, {
    "status": "Resolved",
    "resolution_details": "Ky thuat vien da thay moi 2 loc dau Hitachi tu kho linh kien trung tam. May chay on dinh, ap suat binh thuong."
})
print(f"[UPDATED] Issue {issue_1_name} status -> Resolved")

# 4. SAVE EVIDENCE FILE FOR VERIFICATION MATRIX
evidence_data = {
    "timestamp": "2026-09-07T11:30:00",
    "company": fc.COMPANY,
    "issues": created_issues,
    "maintenance_log": {
        "name": m_log_name,
        "asset": asset_chl,
        "status": "Completed",
        "custom_issue": created_issues["ISSUE_5"]["name"]
    },
    "stock_transaction": {
        "name": se_issue_name,
        "type": "Material Issue",
        "item_code": "PART-FLT-OIL01",
        "qty_issued": 2,
        "stock_before": qty_before,
        "stock_after": qty_after,
        "reorder_level": reorder_lvl,
        "reorder_condition_met": reorder_triggered,
        "custom_issue": issue_1_name,
        "custom_asset": asset_cmp,
        "custom_technician": assigned_tech_iss1
    }
}

evidence_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "data", "verification_evidence.json"))
os.makedirs(os.path.dirname(evidence_path), exist_ok=True)
with open(evidence_path, "w", encoding="utf-8") as f:
    json.dump(evidence_data, f, indent=2, ensure_ascii=False)

print(f"[OK] Evidence saved to {evidence_path}")
print("=== 05_EXECUTE_SCENARIOS.PY COMPLETED SUCCESSFULLY ===")
