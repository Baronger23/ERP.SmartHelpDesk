"""POST-only, authenticated, transactional business command boundary."""
import inspect
import json
import frappe
from smart_helpdesk.core import data, digest, command_context


def handlers():
    from smart_helpdesk import operations, maintenance, inventory, commercial, reporting
    return {name: value for module in (operations, maintenance, inventory, commercial, reporting)
            for name, value in vars(module).items() if callable(value) and getattr(value, "business_command", False)}


def command(*allowed_roles):
    def decorate(function):
        function.business_command = True
        function.allowed_roles = set(allowed_roles) | {"AIS Service Manager"}
        return function
    return decorate


def normalize_dates(value):
    """Frappe stores naive site-local datetimes; honor explicit client UTC offsets."""
    from smart_helpdesk.schema import SCHEMAS, COMMON
    from frappe.utils import get_datetime, get_system_timezone
    from zoneinfo import ZoneInfo
    names = {f["fieldname"] for fields in SCHEMAS.values() for f in COMMON + fields if f["fieldtype"] == "Datetime"}
    names |= {"occurred_at", "starts_at", "ends_at", "period_start", "period_end"}
    def convert(obj):
        if isinstance(obj, list):
            return [convert(v) for v in obj]
        if not isinstance(obj, dict):
            return obj
        out = {}
        for key, item in obj.items():
            if key in names and item:
                try:
                    parsed = get_datetime(item)
                    if parsed.tzinfo:
                        parsed = parsed.astimezone(ZoneInfo(get_system_timezone())).replace(tzinfo=None)
                    out[key] = str(parsed)
                except (TypeError, ValueError):
                    frappe.throw("Invalid timestamp: " + key)
            else:
                out[key] = convert(item)
        return out
    return convert(value)


@frappe.whitelist(methods=["POST"])
def execute(command, payload, idempotency_key):
    handler = handlers().get(command)
    if not handler:
        frappe.throw("Unknown business command")
    if frappe.session.user != "Administrator" and not handler.allowed_roles.intersection(frappe.get_roles()):
        frappe.throw("Role does not permit this command", frappe.PermissionError)
    payload = data(payload)
    if not isinstance(payload, dict) or not isinstance(idempotency_key, str) or not 8 <= len(idempotency_key) <= 160:
        frappe.throw("Object payload and stable idempotency key (8–160 characters) required")
    try:
        inspect.signature(handler).bind(**payload)
    except TypeError:
        frappe.throw("Invalid or unexpected command arguments")
    binding = digest({"command": command, "payload": payload})
    name = digest({"actor": frappe.session.user, "command": command, "key": idempotency_key})
    savepoint = "shd_" + frappe.generate_hash(length=12)
    frappe.db.savepoint(savepoint)
    try:
        with command_context(name):
            frappe.flags.shd_command_type = command
            if frappe.session.user != "Administrator":
                actor = frappe.get_doc("User", frappe.session.user, for_update=True)
                if not actor.enabled:
                    frappe.throw("User account is disabled", frappe.PermissionError)
            # Insert first: the unique PK serializes concurrent retries, even before an aggregate exists.
            previous_messages = len(frappe.local.message_log or [])
            try:
                record = frappe.get_doc({"doctype": "SHD Command", "name": name,
                    "company": payload.get("company") or frappe.defaults.get_user_default("Company"),
                    "actor": frappe.session.user, "command_type": command, "binding_hash": binding,
                    "status": "Applying", "revision": 1})
                record.insert(ignore_permissions=True, set_name=name)
            except frappe.DuplicateEntryError:
                # A handled duplicate is a successful replay, not a UI error.
                frappe.local.message_log = (frappe.local.message_log or [])[:previous_messages]
                record = frappe.get_doc("SHD Command", name, for_update=True)
                if record.binding_hash != binding:
                    frappe.throw("IDEMPOTENCY_CONFLICT: key was used for different content")
                from smart_helpdesk.security import require
                for check in (data(record.details) or {}).get("access_checks", []):
                    require(frappe.get_doc(check["doctype"], check["name"]), check["action"])
                return data(record.result)
            frappe.flags.shd_access_checks = []
            value = handler(**normalize_dates(payload))
            # Receipt, domain changes and events share the HTTP transaction.
            record.result = value
            record.details = {"access_checks": frappe.flags.shd_access_checks}
            record.status = "Applied"
            record.save(ignore_permissions=True)
            return value
    except (frappe.QueryDeadlockError, frappe.QueryTimeoutError):
        # InnoDB can roll back the entire transaction on a deadlock; its old
        # savepoint no longer exists. Report a retryable conflict with no receipt.
        frappe.db.rollback()
        frappe.throw("CONCURRENCY_CONFLICT: transaction rolled back; retry with the same idempotency key")
    except Exception:
        frappe.db.rollback(save_point=savepoint)
        raise
    finally:
        frappe.flags.shd_access_checks = None
        frappe.flags.shd_command_type = None


@frappe.whitelist()
def catalog():
    user_roles = set(frappe.get_roles())
    return [{"command": name, "arguments": [
        {"name": p.name, "required": p.default is inspect.Parameter.empty,
         "default": None if p.default is inspect.Parameter.empty else p.default}
        for p in inspect.signature(handler).parameters.values()]}
        for name, handler in sorted(handlers().items())
        if frappe.session.user == "Administrator" or handler.allowed_roles & user_roles]


@frappe.whitelist()
def master_catalog():
    from smart_helpdesk.operations import MASTER_ROLES
    from smart_helpdesk.schema import SCHEMAS, COMMON
    user_roles = set(frappe.get_roles())
    result = {}
    for name, permitted_roles in MASTER_ROLES.items():
        if frappe.session.user == "Administrator" or user_roles & (permitted_roles | {"AIS Service Manager"}):
            result[name] = [f for f in COMMON[:3] + SCHEMAS[name] if not (name == "SHD Site" and f["fieldname"] == "site")]
    return result
