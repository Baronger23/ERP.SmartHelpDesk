import hashlib
import json
from decimal import Decimal, InvalidOperation
from contextlib import contextmanager
import frappe
from frappe.utils import get_datetime, now_datetime
from smart_helpdesk.security import require


def data(value):
    return json.loads(value) if isinstance(value, str) else value


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":"), default=str,
                                     allow_nan=False).encode()).hexdigest()


def number(value, positive=True):
    try:
        result = Decimal(str(value))
    except (InvalidOperation, ValueError):
        frappe.throw("Invalid decimal quantity")
    if not result.is_finite() or result < 0 or (positive and result == 0):
        frappe.throw("Quantity must be finite and " + ("positive" if positive else "non-negative"))
    return result


def timestamp(value):
    result = get_datetime(value)
    if result > now_datetime():
        frappe.throw("Business event cannot be in the future")
    return result


def locked(doctype, name, action="operate"):
    # Table name comes only from compiled command handlers, never user input.
    doc = frappe.get_doc(doctype, name, for_update=True)
    require(doc, action)
    return doc


def read(doctype, name, action="read"):
    doc = frappe.get_doc(doctype, name)
    require(doc, action)
    return doc


def same_scope(parent, child):
    for key in ("company", "customer", "site"):
        if parent.get(key) != child.get(key):
            frappe.throw("Linked documents must have the same company, customer and site")


def scope(doc):
    return {k: doc.get(k) for k in ("company", "customer", "site")}


def create(doctype, values, status="Draft"):
    doc = frappe.get_doc({"doctype": doctype, "status": status, "revision": 1, **values})
    require(doc, "operate")
    doc.insert(ignore_permissions=True)
    require(doc, "operate")
    event(doc, "Created")
    return doc


def change(doc, event_type, values, occurred_at=None, supersedes=None):
    doc.update(values)
    doc.revision = int(doc.revision or 0) + 1
    doc.save(ignore_permissions=True)
    return event(doc, event_type, occurred_at, supersedes)


def event(doc, kind, occurred_at=None, supersedes=None):
    if doc.doctype in ("SHD Command", "SHD Event"):
        return None
    evt = frappe.get_doc({"doctype": "SHD Event", **scope(doc), "status": "Recorded", "revision": 1,
                          "event_type": kind, "aggregate_type": doc.doctype, "aggregate_id": doc.name,
                          "aggregate_version": doc.revision, "occurred_at": occurred_at or now_datetime(),
                          "recorded_at": now_datetime(), "actor": frappe.session.user,
                          "command_id": frappe.flags.shd_command, "supersedes_event": supersedes,
                          "payload": frappe.as_json(doc.as_dict())})
    evt.insert(ignore_permissions=True)
    return evt.name


def result(doc):
    return {"doctype": doc.doctype, "name": doc.name, "status": doc.status, "revision": doc.revision}


def work_order(name):
    doc = locked("SHD Work Order", name)
    if doc.status in ("Closed", "Cancelled"):
        frappe.throw("Work order is terminal")
    return doc


@contextmanager
def command_context(command_id):
    previous = frappe.flags.shd_command
    frappe.flags.shd_command = command_id
    try:
        yield
    finally:
        frappe.flags.shd_command = previous
