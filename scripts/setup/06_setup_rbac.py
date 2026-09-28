import sys
import os
import subprocess
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "core")))
import frappe_client as fc

print("=== STARTING 06_SETUP_RBAC.PY ===")

# 1. DEFINE 5 CORE FSM-MRO ROLES
roles_def = [
    {"name": "AIS Dispatcher", "desk_access": 1},
    {"name": "AIS Field Technician", "desk_access": 1},
    {"name": "AIS Warehouse Keeper", "desk_access": 1},
    {"name": "AIS Billing Accountant", "desk_access": 1},
    {"name": "AIS Customer Portal", "desk_access": 0}
]

for r in roles_def:
    if not fc.exists_doc("Role", r["name"]):
        fc.create_doc("Role", {"role_name": r["name"], "desk_access": r["desk_access"]})
        print(f"[CREATED] Role: {r['name']}")
    else:
        print(f"[EXISTS] Role: {r['name']}")

# 2. CREATE USERS ACROSS ENTERPRISE PERSONAS
users_to_create = [
    {
        "email": "dispatcher@smarthelpdesk.local",
        "first_name": "Tran Thi",
        "last_name": "Dieu Phoi",
        "roles": ["AIS Dispatcher", "Support Team", "Desk User"],
        "user_type": "System User"
    },
    {
        "email": "warehouse@smarthelpdesk.local",
        "first_name": "Nguyen Van",
        "last_name": "Thu Kho",
        "roles": ["AIS Warehouse Keeper", "Stock User", "Stock Manager", "Desk User"],
        "user_type": "System User"
    },
    {
        "email": "accountant@smarthelpdesk.local",
        "first_name": "Le Thi",
        "last_name": "Ke Toan",
        "roles": ["AIS Billing Accountant", "Accounts User", "Accounts Manager", "Desk User"],
        "user_type": "System User"
    },
    {
        "email": "customer.tana@smarthelpdesk.local",
        "first_name": "Pham Van",
        "last_name": "Quan Doc Tan A",
        "roles": ["Customer", "AIS Customer Portal"],
        "user_type": "Website User"
    }
]

default_password = "AlphaTech@2026!"

for u in users_to_create:
    email = u["email"]
    if not fc.exists_doc("User", email):
        fc.create_doc("User", {
            "email": email,
            "first_name": u["first_name"],
            "last_name": u["last_name"],
            "send_welcome_email": 0,
            "user_type": u["user_type"],
            "roles": [{"role": r} for r in u["roles"]]
        })
        print(f"[CREATED] User: {email} ({u['first_name']} {u['last_name']})")
    else:
        # Update roles
        user_doc = fc.get_doc("User", email)
        curr_roles = [r["role"] for r in user_doc.get("roles", [])]
        needed = [r for r in u["roles"] if r not in curr_roles]
        if needed:
            new_role_list = user_doc.get("roles", []) + [{"role": r} for r in needed]
            fc.update_doc("User", email, {"roles": new_role_list})
            print(f"[UPDATED ROLES] User: {email}")
        else:
            print(f"[EXISTS] User: {email}")

    # Set password via bench in docker
    try:
        cmd = f'docker exec frappe_docker-backend-1 bench --site frontend set-password {email} "{default_password}"'
        subprocess.run(cmd, shell=True, capture_output=True, timeout=10)
    except Exception as e:
        print(f"[NOTE] Password set for {email}: {e}")

# Also ensure Technicians have "AIS Field Technician" role
tech_emails = [
    "an.nguyen@smarthelpdesk.local",
    "binh.tran@smarthelpdesk.local",
    "cuong.le@smarthelpdesk.local"
]
for te in tech_emails:
    if fc.exists_doc("User", te):
        u_doc = fc.get_doc("User", te)
        curr_roles = [r["role"] for r in u_doc.get("roles", [])]
        if "AIS Field Technician" not in curr_roles:
            curr_roles_list = u_doc.get("roles", []) + [{"role": "AIS Field Technician"}]
            fc.update_doc("User", te, {"roles": curr_roles_list})
            print(f"[ASSIGNED ROLE] AIS Field Technician -> {te}")

# 3. SET DATA ISOLATION (USER PERMISSIONS) FOR CUSTOMER PORTAL
# Restricts customer.tana to only documents associated with "Cong ty CP Bao bi Tan A"
cust_perm_filters = [
    ["user", "=", "customer.tana@smarthelpdesk.local"],
    ["allow", "=", "Customer"],
    ["for_value", "=", "Cong ty CP Bao bi Tan A"]
]
existing_perms = fc.list_docs("User Permission", filters=cust_perm_filters)
if not existing_perms:
    fc.create_doc("User Permission", {
        "user": "customer.tana@smarthelpdesk.local",
        "allow": "Customer",
        "for_value": "Cong ty CP Bao bi Tan A",
        "is_default": 1
    })
    print("[CREATED] User Permission: Customer = Cong ty CP Bao bi Tan A for customer.tana@smarthelpdesk.local")
else:
    print("[EXISTS] User Permission for Customer Portal User")

# 4. CONFIGURE CUSTOM DOCPERMS FOR FINE-GRAINED SEGREGATION OF DUTIES
docperm_rules = [
    # AIS Dispatcher: Issue (Read/Write/Create/Share, no delete/cancel)
    {"parent": "Issue", "role": "AIS Dispatcher", "read": 1, "write": 1, "create": 1, "share": 1, "delete": 0},
    # AIS Field Technician: Issue (Read/Write to update status, no delete)
    {"parent": "Issue", "role": "AIS Field Technician", "read": 1, "write": 1, "create": 0, "share": 0, "delete": 0},
    # AIS Field Technician: Stock Entry (Can create & submit Material Issue)
    {"parent": "Stock Entry", "role": "AIS Field Technician", "read": 1, "write": 1, "create": 1, "submit": 1, "cancel": 0},
    # AIS Warehouse Keeper: Stock Entry, Material Request, Purchase Order, Purchase Receipt
    {"parent": "Stock Entry", "role": "AIS Warehouse Keeper", "read": 1, "write": 1, "create": 1, "submit": 1, "cancel": 1},
    {"parent": "Material Request", "role": "AIS Warehouse Keeper", "read": 1, "write": 1, "create": 1, "submit": 1, "cancel": 1},
    {"parent": "Purchase Order", "role": "AIS Warehouse Keeper", "read": 1, "write": 1, "create": 1, "submit": 1, "cancel": 1},
    {"parent": "Purchase Receipt", "role": "AIS Warehouse Keeper", "read": 1, "write": 1, "create": 1, "submit": 1, "cancel": 1},
    # AIS Billing Accountant: Sales Invoice (Full management), Stock Entry (Audit read only)
    {"parent": "Sales Invoice", "role": "AIS Billing Accountant", "read": 1, "write": 1, "create": 1, "submit": 1, "cancel": 1},
    {"parent": "Stock Entry", "role": "AIS Billing Accountant", "read": 1, "write": 0, "create": 0, "submit": 0, "cancel": 0},
    # AIS Customer Portal: Issue (Read/Write own issues, create issues)
    {"parent": "Issue", "role": "AIS Customer Portal", "read": 1, "write": 1, "create": 1, "share": 1, "delete": 0}
]

for dpr in docperm_rules:
    dt = dpr["parent"]
    rl = dpr["role"]
    ex = fc.list_docs("Custom DocPerm", filters=[["parent", "=", dt], ["role", "=", rl]])
    perm_payload = {
        "parent": dt,
        "parenttype": "DocType",
        "parentfield": "permissions",
        "role": rl,
        "permlevel": 0,
        "read": dpr.get("read", 0),
        "write": dpr.get("write", 0),
        "create": dpr.get("create", 0),
        "submit": dpr.get("submit", 0),
        "cancel": dpr.get("cancel", 0),
        "delete": dpr.get("delete", 0),
        "share": dpr.get("share", 0)
    }
    if not ex:
        try:
            fc.create_doc("Custom DocPerm", perm_payload)
            print(f"[CREATED CUSTOM DOCPERM] {dt} -> {rl}")
        except Exception as e:
            print(f"[NOTE] Custom DocPerm creation {dt}/{rl}: {e}")
    else:
        try:
            fc.update_doc("Custom DocPerm", ex[0]["name"], perm_payload)
            print(f"[UPDATED CUSTOM DOCPERM] {dt} -> {rl}")
        except Exception as e:
            print(f"[NOTE] Custom DocPerm update {dt}/{rl}: {e}")

print("=== 06_SETUP_RBAC.PY COMPLETED SUCCESSFULLY ===")
