import sys
import os
sys.path.append(os.path.dirname(__file__))
import frappe_client as fc

print("=== STARTING 04_SETUP_SLA_AND_PLANS.PY ===")

# 1. Enable SLA in Support Settings
fc.update_doc("Support Settings", "Support Settings", {"track_service_level_agreement": 1})
print("[OK] Track SLA enabled in Support Settings")

# 2. Issue Priorities (Ensure Urgent exists)
for prio in ["Urgent", "High", "Medium", "Low"]:
    if not fc.exists_doc("Issue Priority", prio):
        fc.create_doc("Issue Priority", {"name": prio})
        print(f"[CREATED] Issue Priority: {prio}")
    else:
        print(f"[EXISTS] Issue Priority: {prio}")

# 3. Issue Types
issue_types = ["Corrective Repair", "Preventive Maintenance", "Technical Inspection", "Callback / Recall"]
for it in issue_types:
    if not fc.exists_doc("Issue Type", it):
        fc.create_doc("Issue Type", {"name": it})
        print(f"[CREATED] Issue Type: {it}")
    else:
        print(f"[EXISTS] Issue Type: {it}")

# 4. Holiday List
hl_name = "Lich Nghi Le 2026 - AIS"
if not fc.exists_doc("Holiday List", hl_name):
    fc.create_doc("Holiday List", {
        "holiday_list_name": hl_name,
        "from_date": "2026-01-01",
        "to_date": "2026-12-31",
        "weekly_off": "Sunday"
    })
    print(f"[CREATED] Holiday List: {hl_name}")
else:
    print(f"[EXISTS] Holiday List: {hl_name}")

workdays = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"]

# 5. VIP Customer SLA (Specific to Customer: Cong ty CP Bao bi Tan A)
vip_sla_name = "SLA Khach hang VIP"
vip_doc_name = f"SLA-Issue-{vip_sla_name}"
vip_priorities = [
    {"priority": "Urgent", "default_priority": 1, "response_time": 1800, "resolution_time": 14400},   # 30m / 4h
    {"priority": "High", "default_priority": 0, "response_time": 3600, "resolution_time": 28800},     # 1h / 8h
    {"priority": "Medium", "default_priority": 0, "response_time": 14400, "resolution_time": 86400},  # 4h / 24h
    {"priority": "Low", "default_priority": 0, "response_time": 28800, "resolution_time": 172800}     # 8h / 48h
]

target_vip_name = vip_doc_name if fc.exists_doc("Service Level Agreement", vip_doc_name) else (vip_sla_name if fc.exists_doc("Service Level Agreement", vip_sla_name) else None)
if not target_vip_name:
    res_vip = fc.create_doc("Service Level Agreement", {
        "service_level": vip_sla_name,
        "document_type": "Issue",
        "entity_type": "Customer",
        "entity": "Cong ty CP Bao bi Tan A",
        "holiday_list": hl_name,
        "enabled": 1,
        "priorities": vip_priorities,
        "sla_fulfilled_on": [{"status": "Resolved"}, {"status": "Closed"}],
        "support_and_resolution": [
            {"workday": d, "start_time": "08:00:00", "end_time": "17:30:00"} for d in workdays
        ]
    })
    print(f"[CREATED] VIP SLA: {vip_sla_name}")
else:
    fc.update_doc("Service Level Agreement", target_vip_name, {"priorities": vip_priorities})
    print(f"[UPDATED] VIP SLA priorities (2D Matrix): {target_vip_name}")

# 6. Standard Customer SLA (Default SLA for all other customers)
std_sla_name = "SLA Khach hang Standard"
std_doc_name = f"SLA-Issue-{std_sla_name}"
std_priorities = [
    {"priority": "Urgent", "default_priority": 0, "response_time": 3600, "resolution_time": 28800},    # 1h / 8h
    {"priority": "High", "default_priority": 0, "response_time": 14400, "resolution_time": 86400},    # 4h / 24h
    {"priority": "Medium", "default_priority": 1, "response_time": 28800, "resolution_time": 172800}, # 8h / 48h
    {"priority": "Low", "default_priority": 0, "response_time": 86400, "resolution_time": 259200}     # 24h / 72h
]

target_std_name = std_doc_name if fc.exists_doc("Service Level Agreement", std_doc_name) else (std_sla_name if fc.exists_doc("Service Level Agreement", std_sla_name) else None)
if not target_std_name:
    res_std = fc.create_doc("Service Level Agreement", {
        "service_level": std_sla_name,
        "document_type": "Issue",
        "default_service_level_agreement": 1,
        "holiday_list": hl_name,
        "enabled": 1,
        "priorities": std_priorities,
        "sla_fulfilled_on": [{"status": "Resolved"}, {"status": "Closed"}],
        "support_and_resolution": [
            {"workday": d, "start_time": "08:00:00", "end_time": "17:30:00"} for d in workdays
        ]
    })
    print(f"[CREATED] Standard SLA: {std_sla_name}")
else:
    fc.update_doc("Service Level Agreement", target_std_name, {"priorities": std_priorities})
    print(f"[UPDATED] Standard SLA priorities (2D Matrix): {target_std_name}")

# 7. 3 Asset Maintenance Plans
# Lookup Asset document names by item_code
team_name = "Doi Ky thuat Bao tri Alpha"
plans = [
    {
        "item_code": "ITEM-AST-CMP-02",
        "task": "Bao tri may nen khi: ve sinh loc gio, xao nuoc ngung, do dong tai",
        "periodicity": "Monthly",
        "assign": "an.nguyen@smarthelpdesk.local"
    },
    {
        "item_code": "ITEM-AST-CHL-03",
        "task": "Bao duong Chiller: ve sinh binh ngung, do ap gas R134a, kiem tra sensor",
        "periodicity": "Quarterly",
        "assign": "cuong.le@smarthelpdesk.local"
    },
    {
        "item_code": "ITEM-AST-PNL-05",
        "task": "Kiem tra tu dien MSB: quet nhiet busbar, siet tiep diem bu-long",
        "periodicity": "Half-yearly",
        "assign": "binh.tran@smarthelpdesk.local"
    }
]

for p in plans:
    assets = fc.list_docs("Asset", filters=[["item_code", "=", p["item_code"]], ["company", "=", fc.COMPANY]])
    if not assets:
        print(f"[WARN] Asset for {p['item_code']} not found, skipping plan.")
        continue
    asset_doc_name = assets[0]["name"]
    
    # Check if Asset Maintenance already exists for this asset
    existing_plan = fc.list_docs("Asset Maintenance", filters=[["asset_name", "=", asset_doc_name]])
    if not existing_plan:
        m_doc = fc.create_doc("Asset Maintenance", {
            "asset_name": asset_doc_name,
            "company": fc.COMPANY,
            "maintenance_team": team_name,
            "maintenance_manager": "an.nguyen@smarthelpdesk.local",
            "asset_maintenance_tasks": [
                {
                    "maintenance_task": p["task"],
                    "maintenance_type": "Preventive Maintenance",
                    "maintenance_status": "Planned",
                    "start_date": "2026-01-01",
                    "periodicity": p["periodicity"],
                    "assign_to": p["assign"]
                }
            ]
        })
        print(f"[CREATED] Asset Maintenance Plan for {p['item_code']} -> {m_doc.get('name')}")
    else:
        print(f"[EXISTS] Asset Maintenance Plan for {p['item_code']} ({existing_plan[0]['name']})")

print("=== 04_SETUP_SLA_AND_PLANS.PY COMPLETED SUCCESSFULLY ===")
