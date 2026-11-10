import frappe

from smart_helpdesk.schema import ROLES, field


def sync():
    """Additive, repeatable migration; never imports demo data or broadens native roles.

    Since the bench-standard refactor, the 28 SHD DocTypes are defined as
    standard DocType JSON in smart_helpdesk/doctype/ (generated from
    schema.py by gen_doctypes.py) and are synced by Frappe itself on
    install/migrate. This hook only keeps what DocType JSON cannot express:
    roles, composite unique constraints, the XOR check constraint, the
    reservation balance index, Custom Fields on native DocTypes and the
    workspace bootstrap.
    """
    frappe.flags.shd_install = True
    try:
        for role in ROLES:
            if not frappe.db.exists("Role", role):
                frappe.get_doc({"doctype": "Role", "role_name": role,
                                "desk_access": int(role != "AIS Customer Portal")}).insert(ignore_permissions=True)
        if not frappe.db.exists("Module Def", "Smart Helpdesk"):
            frappe.get_doc({"doctype": "Module Def", "module_name": "Smart Helpdesk", "app_name": "smart_helpdesk"}).insert(ignore_permissions=True)
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
        # Client Scripts are no longer created here: the SHD DocTypes are now
        # standard (non-custom) DocTypes, so the doctype_js / doctype_list_js
        # hooks in hooks.py load public/js/operations.js directly. (The old
        # programmatic Client Scripts existed only because Frappe skips
        # doctype_js hooks for custom DocTypes.) Verified on the WSL bench
        # install; see the migration plan in docs/.
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
