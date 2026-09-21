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

# 4. Skill-Based Assignment Rules (Phân bổ công việc dựa trên năng lực chuyên môn)
# Tắt quy tắc Round Robin mù cũ nếu tồn tại
old_rule = "Round Robin Assignment for Issues"
if fc.exists_doc("Assignment Rule", old_rule):
    try:
        fc.update_doc("Assignment Rule", old_rule, {"disabled": 1})
        print(f"[DISABLED] Old Generic Rule: {old_rule}")
    except Exception as e:
        print(f"[NOTE] Disabling old rule: {e}")

days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]

skill_rules = [
    {
        "name": "Skill Rule - Co khi va Khi nen",
        "document_type": "Issue",
        "description": "Dinh tuyen su co may nen khi va may in cong nghiep toi Chuyen vien Co khi: Nguyen Van An",
        "priority": 1,
        "assign_condition": 'custom_asset_category in ["Compressor", "Industrial Printing"]',
        "rule": "Round Robin",
        "assignment_days": [{"day": d} for d in days],
        "users": [{"user": "an.nguyen@smarthelpdesk.local"}]
    },
    {
        "name": "Skill Rule - Dien cong nghiep va Tu dong hoa",
        "document_type": "Issue",
        "description": "Dinh tuyen su co tu dien va may phat dien toi Chuyen vien Dien: Tran Dinh Binh",
        "priority": 1,
        "assign_condition": 'custom_asset_category in ["Electrical Panel", "Generator"]',
        "rule": "Round Robin",
        "assignment_days": [{"day": d} for d in days],
        "users": [{"user": "binh.tran@smarthelpdesk.local"}]
    },
    {
        "name": "Skill Rule - Nhiet lanh HVAC",
        "document_type": "Issue",
        "description": "Dinh tuyen su co he thong Chiller toi Chuyen vien Nhiet Lanh: Le Hoang Cuong",
        "priority": 1,
        "assign_condition": 'custom_asset_category in ["HVAC & Cooling"]',
        "rule": "Round Robin",
        "assignment_days": [{"day": d} for d in days],
        "users": [{"user": "cuong.le@smarthelpdesk.local"}]
    },
    {
        "name": "Skill Rule - Fallback Mac dinh",
        "document_type": "Issue",
        "description": "Quy tac du phong: Xoay vong deu khi su co chua xac dinh duoc thiet bi hoac ngoai danh muc",
        "priority": 5,
        "assign_condition": 'status == "Open"',
        "rule": "Round Robin",
        "assignment_days": [{"day": d} for d in days],
        "users": [{"user": t["email"]} for t in techs]
    }
]

for r in skill_rules:
    if not fc.exists_doc("Assignment Rule", r["name"]):
        try:
            fc.create_doc("Assignment Rule", r)
            print(f"[CREATED] Skill-Based Assignment Rule: {r['name']}")
        except Exception as e:
            print(f"[ERROR] Creating Rule {r['name']}: {e}")
    else:
        try:
            fc.update_doc("Assignment Rule", r["name"], r)
            print(f"[UPDATED] Skill-Based Assignment Rule: {r['name']}")
        except Exception as e:
            print(f"[ERROR] Updating Rule {r['name']}: {e}")

print("=== 02_SETUP_TECHNICIANS_AND_RULES.PY COMPLETED SUCCESSFULLY ===")
