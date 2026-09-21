import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "core")))
import frappe_client as fc

print("=== STARTING 02_SETUP_TECHNICIANS_AND_RULES.PY ===")

# 1. 3 Technicians (Users)
techs = [
    {"email": "an.nguyen@smarthelpdesk.local", "first_name": "Nguyen Van", "last_name": "An", "spec": "Co khi - Khi nen"},
    {"email": "binh.tran@smarthelpdesk.local", "first_name": "Tran Dinh", "last_name": "Binh", "spec": "Dien cong nghiep - Tu dong hoa"},
    {"email": "cuong.le@smarthelpdesk.local", "first_name": "Le Hoang", "last_name": "Cuong", "spec": "Dien lanh - HVAC & May phat dien"}
]

roles_to_assign = ["Support Team", "Maintenance User", "Stock User", "Desk User"]

for t in techs:
    email = t["email"]
    if not fc.exists_doc("User", email):
        user_doc = fc.create_doc("User", {
            "email": email,
            "first_name": t["first_name"],
            "last_name": t["last_name"],
            "send_welcome_email": 0,
            "user_type": "System User",
            "roles": [{"role": r} for r in roles_to_assign]
        })
        print(f"[CREATED] User: {email} ({t['first_name']} {t['last_name']})")
    else:
        # Ensure roles exist
        user_doc = fc.get_doc("User", email)
        existing_roles = [r["role"] for r in user_doc.get("roles", [])]
        needed_roles = [r for r in roles_to_assign if r not in existing_roles]
        if needed_roles:
            new_role_list = user_doc.get("roles", []) + [{"role": r} for r in needed_roles]
            fc.update_doc("User", email, {"roles": new_role_list})
            print(f"[UPDATED ROLES] User: {email}")
        else:
            print(f"[EXISTS] User: {email}")

# 2. Employees linked to Company SmartHelpDeskBaro
for t in techs:
    email = t["email"]
    emp_list = fc.list_docs("Employee", filters=[["user_id", "=", email], ["company", "=", fc.COMPANY]])
    if not emp_list:
        try:
            emp = fc.create_doc("Employee", {
                "first_name": t["first_name"],
                "last_name": t["last_name"],
                "user_id": email,
                "company": fc.COMPANY,
                "gender": "Male",
                "date_of_birth": "1990-01-01",
                "status": "Active",
                "date_of_joining": "2025-01-01"
            })
            print(f"[CREATED] Employee: {t['first_name']} {t['last_name']} -> {emp.get('name')}")
        except Exception as e:
            print(f"[NOTE] Employee creation for {email}: {e}")
    else:
        print(f"[EXISTS] Employee for user: {email} ({emp_list[0]['name']})")

# 3. Asset Maintenance Team
team_name = "Doi Ky thuat Bao tri Alpha"
if not fc.exists_doc("Asset Maintenance Team", team_name):
    fc.create_doc("Asset Maintenance Team", {
        "maintenance_team_name": team_name,
        "company": fc.COMPANY,
        "maintenance_manager": techs[0]["email"],
        "maintenance_team_members": [
            {"team_member": t["email"], "maintenance_role": "Maintenance User"} for t in techs
        ]
    })
    print(f"[CREATED] Asset Maintenance Team: {team_name}")
else:
    print(f"[EXISTS] Asset Maintenance Team: {team_name}")

# 4. Assignment Rule (Round Robin for Issue)
rule_name = "Round Robin Assignment for Issues"
days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]

if not fc.exists_doc("Assignment Rule", rule_name):
    rule_doc = fc.create_doc("Assignment Rule", {
        "name": rule_name,
        "document_type": "Issue",
        "description": "Tu dong gan Ky thuat vien theo vong tron Round Robin",
        "assign_condition": 'status == "Open"',
        "rule": "Round Robin",
        "assignment_days": [{"day": d} for d in days],
        "users": [{"user": t["email"]} for t in techs]
    })
    print(f"[CREATED] Assignment Rule: {rule_name} (Round Robin for 3 Techs)")
else:
    print(f"[EXISTS] Assignment Rule: {rule_name}")

print("=== 02_SETUP_TECHNICIANS_AND_RULES.PY COMPLETED SUCCESSFULLY ===")
