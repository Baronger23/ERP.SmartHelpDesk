"""Fail-closed scope checks shared by commands, lists, forms and file attachments."""
import frappe
from frappe.utils import get_datetime, now_datetime
from smart_helpdesk.schema import SCHEMAS, SENSITIVE, INTERNAL


def roles(user=None):
    return set(frappe.get_roles(user or frappe.session.user))


def grants(user=None):
    suffix = " FOR UPDATE" if frappe.flags.shd_command else ""
    return frappe.db.sql("SELECT company,customer,site,warehouse,resource_type,actions,valid_until FROM `tabSHD Access Grant` WHERE user=%s AND status='Active'" + suffix,
                         user or frappe.session.user, as_dict=True)


def resource_type(doctype):
    if doctype in INTERNAL:
        return "Administration" if doctype != "SHD Technician" else "Service"
    if doctype in ("SHD Reservation", "SHD Material Use", "SHD Demand", "SHD Compatibility"):
        return "Inventory"
    if doctype in ("SHD Charge", "SHD Estimate", "SHD KPI Snapshot"):
        return "Finance"
    if doctype == "SHD Knowledge":
        return "Knowledge"
    return "Service"


def permits(doc, action="read", user=None):
    user = user or frappe.session.user
    if user == "Administrator":
        return True
    if user == "Guest":
        return False
    user_roles = roles(user)
    if doc.doctype in SENSITIVE and not user_roles & {"AIS Service Manager", "AIS Billing Accountant"}:
        return False
    if doc.doctype in INTERNAL and "AIS Service Manager" not in user_roles and not (
            doc.doctype == "SHD Technician" and "AIS Dispatcher" in user_roles):
        return False
    for grant in grants(user):
        if grant.resource_type not in ("All", resource_type(doc.doctype)):
            continue
        if grant.valid_until and get_datetime(grant.valid_until) <= now_datetime():
            continue
        actions = {x.strip() for x in grant.actions.split(",")}
        if action not in actions:
            continue
        if grant.company != doc.get("company"):
            continue
        if any(grant.get(key) and grant.get(key) != (doc.name if key == "site" and doc.doctype == "SHD Site" else doc.get(key))
               for key in ("customer", "site", "warehouse")):
            continue
        if "AIS Field Technician" in user_roles and not user_roles & {"AIS Service Manager", "AIS Dispatcher"}:
            wo = doc.name if doc.doctype == "SHD Work Order" else doc.get("work_order")
            if wo and frappe.db.get_value("SHD Work Order", wo, "technician") != user:
                continue
        return True
    return False


def require(doc, action="read"):
    if not permits(doc, action):
        frappe.throw("Resource unavailable or outside your operational scope", frappe.PermissionError)
    if frappe.flags.shd_command and doc.get("name") and doc.doctype != "SHD Command":
        checks = frappe.flags.shd_access_checks
        if checks is not None:
            entry = {"doctype": doc.doctype, "name": doc.name, "action": action}
            if entry not in checks:
                checks.append(entry)


def has_permission(doc, user=None, permission_type=None, **kwargs):
    if permission_type not in (None, "read", "select"):
        return False
    return permits(doc, user=user)


def query_conditions(doctype, user=None):
    user = user or frappe.session.user
    if user == "Administrator":
        return ""
    if user == "Guest":
        return "1=0"
    user_roles = roles(user)
    if doctype in SENSITIVE and not user_roles & {"AIS Service Manager", "AIS Billing Accountant"}:
        return "1=0"
    if doctype in INTERNAL and "AIS Service Manager" not in user_roles and not (
            doctype == "SHD Technician" and "AIS Dispatcher" in user_roles):
        return "1=0"
    table = "`tab" + doctype + "`"
    meta = frappe.get_meta(doctype)
    alternatives = []
    for grant in grants(user):
        if grant.resource_type not in ("All", resource_type(doctype)):
            continue
        if "read" not in {a.strip() for a in grant.actions.split(",")} or grant.valid_until and get_datetime(grant.valid_until) <= now_datetime():
            continue
        conditions = [table + ".company=" + frappe.db.escape(grant.company)]
        for key in ("customer", "site", "warehouse"):
            if not grant.get(key):
                continue
            column = "name" if key == "site" and doctype == "SHD Site" else key
            conditions.append(table + ".`" + column + "`=" + frappe.db.escape(grant.get(key)) if column == "name" or meta.has_field(column) else "1=0")
        alternatives.append("(" + " AND ".join(conditions) + ")")
    condition = "(" + " OR ".join(alternatives) + ")" if alternatives else "1=0"
    if "AIS Field Technician" in user_roles and not user_roles & {"AIS Service Manager", "AIS Dispatcher"}:
        if doctype == "SHD Work Order":
            condition += " AND " + table + ".technician=" + frappe.db.escape(user)
        elif meta.has_field("work_order"):
            condition += " AND " + table + ".work_order IN (SELECT name FROM `tabSHD Work Order` WHERE technician=" + frappe.db.escape(user) + ")"
    return condition


def protect_file(doc, method=None):
    if doc.attached_to_doctype in SCHEMAS:
        parent = frappe.get_doc(doc.attached_to_doctype, doc.attached_to_name)
        require(parent, "read")
        if not doc.is_private:
            frappe.throw("Service files must be private and attached to an authorized record")


def guard_write(doc, method=None):
    if doc.doctype not in SCHEMAS:
        return
    if not (frappe.flags.shd_command or frappe.flags.shd_install):
        frappe.throw("Use Smart Helpdesk business commands; direct writes bypass workflow", frappe.PermissionError)
    for field in doc.meta.fields:
        if field.fieldtype == "JSON" and isinstance(doc.get(field.fieldname), (dict, list)):
            doc.set(field.fieldname, frappe.as_json(doc.get(field.fieldname)))


def guard_delete(doc, method=None):
    if doc.doctype in SCHEMAS and not frappe.flags.shd_install:
        frappe.throw("Operational history cannot be deleted", frappe.PermissionError)


def authority(doc, kind, amount=0):
    if frappe.session.user == "Administrator":
        # Bootstrap/admin still requires a configured named customer authority.
        pass
    rows = frappe.db.sql("""SELECT * FROM `tabSHD Contact Authority` WHERE user=%s AND company=%s AND customer=%s
        AND site=%s AND authority=%s AND status='Active' FOR UPDATE""",
        (frappe.session.user, doc.company, doc.customer, doc.site, kind), as_dict=True)
    if not any(get_datetime(r.valid_from) <= now_datetime() < get_datetime(r.valid_until) and
               (kind != "Approve Cost" or float(r.amount_limit or 0) >= float(amount)) for r in rows):
        frappe.throw("No effective customer authority for this decision", frappe.PermissionError)


def _make_query(doctype):
    def query(user=None):
        return query_conditions(doctype, user)
    return query


for _doctype in SCHEMAS:
    globals()["query_" + _doctype[4:].lower().replace(" ", "_")] = _make_query(_doctype)
