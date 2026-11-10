import frappe
from smart_helpdesk.schema import COMMON, SCHEMAS, ROLES, field


def sync():
    """Additive, repeatable migration; never imports demo data or broadens native roles."""
    frappe.flags.shd_install = True
    try:
        for role in ROLES:
            if not frappe.db.exists("Role", role):
                frappe.get_doc({"doctype": "Role", "role_name": role,
                                "desk_access": int(role != "AIS Customer Portal")}).insert(ignore_permissions=True)
        if not frappe.db.exists("Module Def", "Smart Helpdesk"):
            frappe.get_doc({"doctype": "Module Def", "module_name": "Smart Helpdesk", "app_name": "smart_helpdesk"}).insert(ignore_permissions=True)
        # First create all schemas without Link validation, then reload references.
        for name, extra in SCHEMAS.items():
            existing = frappe.db.exists("DocType", name)
            doc = frappe.get_doc("DocType", name) if existing else frappe.new_doc("DocType")
            doc.update({"name": name, "module": "Smart Helpdesk", "custom": 1,
                        "autoname": "prompt" if name == "SHD Command" else "hash", "track_changes": 1, "allow_rename": 0,
                        "sort_field": "modified", "sort_order": "DESC"})
            fields = [dict(f) for f in COMMON + extra if not (name == "SHD Site" and f["fieldname"] == "site")]
            for f in fields:
                if name == "SHD Command" and f["fieldname"] == "company":
                    f["reqd"] = 0
                f["read_only"] = 1
                if f["fieldname"] in ("cost_rate", "unit_cost"):
                    f["permlevel"] = 1
                if f["fieldname"] in ("status", "customer", "company", "title", "subject"):
                    f["in_list_view"] = 1
            doc.set("fields", fields)
            # Commands are the only write path. Desk/REST are read-only.
            permissions = [{"role": role, "read": 1, "export": 0, "print": 0} for role in ROLES]
            if any(f.get("permlevel") == 1 for f in fields):
                permissions += [{"role": role, "permlevel": 1, "read": 1} for role in ("AIS Service Manager", "AIS Billing Accountant")]
            doc.set("permissions", permissions)
            doc.flags.ignore_links = True
            doc.flags.ignore_validate = True
            doc.save(ignore_permissions=True)
        for name, fields in [
            ("SHD Work Order", ["source", "package_key", "generation_version"]),
            ("SHD PM Occurrence", ["plan", "plan_version", "equipment", "period_key"]),
            ("SHD Compatibility", ["company", "customer", "site", "model", "item"]),
            ("SHD Demand", ["work_order", "item", "warehouse"]),
        ]:
            frappe.db.add_unique(name, fields)
        old_indexes = frappe.db.sql("SHOW INDEX FROM `tabSHD Compatibility` WHERE Key_name='unique_company_model_item'")
        if old_indexes:
            frappe.db.sql_ddl("ALTER TABLE `tabSHD Compatibility` DROP INDEX `unique_company_model_item`")
        frappe.db.add_index("SHD Reservation", ["item", "warehouse", "status"], "shd_reservation_balance")
        constraint = frappe.db.sql("""SELECT CONSTRAINT_NAME FROM information_schema.TABLE_CONSTRAINTS
            WHERE TABLE_SCHEMA=DATABASE() AND TABLE_NAME='tabSHD Work Source' AND CONSTRAINT_NAME='shd_source_xor'""")
        if not constraint:
            frappe.db.sql_ddl("""ALTER TABLE `tabSHD Work Source` ADD CONSTRAINT shd_source_xor CHECK (
                (origin_kind='INCIDENT' AND incident IS NOT NULL AND incident<>'' AND COALESCE(request,'')='' AND COALESCE(pm_occurrence,'')='') OR
                (origin_kind='SERVICE_REQUEST' AND request IS NOT NULL AND request<>'' AND COALESCE(incident,'')='' AND COALESCE(pm_occurrence,'')='') OR
                (origin_kind='PM_OCCURRENCE' AND pm_occurrence IS NOT NULL AND pm_occurrence<>'' AND COALESCE(incident,'')='' AND COALESCE(request,'')=''))""")
        from frappe.custom.doctype.custom_field.custom_field import create_custom_fields
        create_custom_fields({
            "Stock Entry": [dict(field("custom_shd_work_order", "Link", "SHD Work Order"), read_only=1)],
            "Material Request": [dict(field("custom_shd_demand", "Link", "SHD Demand"), read_only=1)],
            "Purchase Order": [dict(field("custom_shd_demand", "Link", "SHD Demand"), read_only=1)],
            "Purchase Receipt": [dict(field("custom_shd_demand", "Link", "SHD Demand"), read_only=1)],
            "Sales Invoice": [dict(field("custom_shd_work_order", "Link", "SHD Work Order"), read_only=1)],
        })
        # Frappe skips doctype_js hooks for custom DocTypes. Install app-owned
        # Client Scripts from the same tracked source for Form and List views.
        from pathlib import Path
        script = (Path(__file__).parent / "public" / "js" / "operations.js").read_text(encoding="utf-8")
        for name in SCHEMAS:
            for view in ("Form", "List"):
                script_name = "SHD Operations · " + name + " · " + view
                client = frappe.get_doc("Client Script", script_name) if frappe.db.exists("Client Script", script_name) else frappe.new_doc("Client Script")
                client.update({"name": script_name, "dt": name, "view": view, "enabled": 1, "script": script})
                client.save(ignore_permissions=True)
        sync_workspace()
        frappe.clear_cache()
    finally:
        frappe.flags.shd_install = False


def sync_workspace():
    import json
    shortcuts = [
        ("M01 · Khách hàng & hợp đồng", "SHD Agreement"), ("M02 · Tiếp nhận & SLA", "SHD Request"),
        ("M03 · Điều phối & tác nghiệp", "SHD Work Order"), ("M04 · Thiết bị & bảo trì", "SHD PM Occurrence"),
        ("M05 · Kho & vật tư", "SHD Reservation"), ("M06 · Mua hàng", "SHD Demand"),
        ("M07 · Chi phí & hóa đơn", "SHD Charge"), ("M08 · Báo cáo & KPI", "SHD KPI Snapshot"),
        ("M09 · Tri thức kỹ thuật", "SHD Knowledge"), ("M10 · Quản trị & kiểm soát", "SHD Access Grant"),
    ]
    if frappe.db.exists("Workspace", "Smart Helpdesk"):
        return  # Preserve user layout customizations on upgrades.
    content = [{"id": "shd-header", "type": "header", "data": {"text": "Smart Helpdesk · Vận hành dịch vụ", "col": 12}}]
    content += [{"id": "shd-" + str(index), "type": "shortcut", "data": {"shortcut_name": label, "col": 4}}
                for index, (label, _) in enumerate(shortcuts)]
    frappe.get_doc({"doctype": "Workspace", "label": "Smart Helpdesk", "title": "Smart Helpdesk",
        "module": "Smart Helpdesk", "public": 1, "icon": "support", "type": "Workspace",
        "content": json.dumps(content, ensure_ascii=False),
        "shortcuts": [{"label": label, "type": "DocType", "link_to": target, "color": "Blue"} for label, target in shortcuts],
        "roles": [{"role": role} for role in ROLES if role != "AIS Customer Portal"]}).insert(ignore_permissions=True)
