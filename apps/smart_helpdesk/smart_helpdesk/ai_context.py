"""Permission-aware ERP context for the read-only US-42 assistant."""
from datetime import UTC, datetime

import frappe
from frappe.utils import now_datetime, strip_html
from pypika import Criterion

from smart_helpdesk.core import scope
from smart_helpdesk.security import roles

LIMIT = 5
KNOWLEDGE_TEXT_LIMIT = 8000
ORIGINS = (
    ("SHD Incident", "incident"),
    ("SHD Request", "request"),
    ("SHD PM Occurrence", "pm_occurrence"),
)


def _query(doctype, fields, filters, *, order_by=None, limit=None):
    return frappe.qb.get_query(
        doctype, fields=fields, filters=filters, order_by=order_by, limit=limit,
        ignore_permissions=False,
    )


def _recent(query, doctype):
    rows = query.run(as_dict=True)
    entries = [{"doctype": doctype, **row} for row in rows[:LIMIT]]
    return {"items": entries, "has_more": len(rows) > LIMIT}


def _history(equipment):
    equipment_scope = scope(equipment)
    origins = [
        (field, _query(doctype, ["name"], {**equipment_scope, "equipment": equipment.name}))
        for doctype, field in ORIGINS
    ]
    source = frappe.qb.DocType("SHD Work Source")
    sources = _query("SHD Work Source", ["name"], equipment_scope).where(
        Criterion.any(source[field].isin(origin) for field, origin in origins)
    )
    order = frappe.qb.DocType("SHD Work Order")
    orders = _query(
        "SHD Work Order", ["name", "revision", "status", "scope", "restored_at", "accepted_at"],
        equipment_scope, order_by="creation desc, name desc", limit=LIMIT + 1,
    ).where(order.source.isin(sources))
    history = _recent(orders, "SHD Work Order")
    for entry in history["items"]:
        visits = _query(
            "SHD Visit", ["name", "revision", "status", "started_at", "ended_at", "outcome"],
            {**equipment_scope, "work_order": entry["name"]},
            order_by="started_at desc, name desc", limit=LIMIT + 1,
        )
        entry["visits"] = _recent(visits, "SHD Visit")

    findings = _query(
        "SHD Finding", ["name", "revision", "status", "description", "severity"],
        {**equipment_scope, "equipment": equipment.name},
        order_by="creation desc, name desc", limit=LIMIT + 1,
    )
    return {"work_orders": history, "findings": _recent(findings, "SHD Finding")}


def _knowledge(equipment):
    now = now_datetime()
    knowledge = frappe.qb.DocType("SHD Knowledge")
    published = _query(
        "SHD Knowledge",
        ["name", "revision", "title", "model", "document_version", "source_reference",
         "effective_from", "effective_until", "content"],
        {"company": equipment.company, "customer": equipment.customer, "model": equipment.model,
         "status": "Published", "effective_from": ["<=", now], "effective_until": [">", now]},
        order_by="effective_from desc, name desc", limit=LIMIT + 1,
    ).where(knowledge.site.isnull() | (knowledge.site == "") | (knowledge.site == equipment.site))
    catalog = _recent(published, "SHD Knowledge")
    for item in catalog["items"]:
        content = strip_html(item.pop("content") or "").strip()
        item["content_text"] = content[:KNOWLEDGE_TEXT_LIMIT]
        item["content_truncated"] = len(content) > KNOWLEDGE_TEXT_LIMIT
    return catalog


@frappe.whitelist(methods=["POST"])
def get_context(equipment_code: str, question: str):
    """Return a bounded evidence set for the signed-in field technician."""
    if frappe.session.user == "Administrator" or "AIS Field Technician" not in roles():
        frappe.throw("Field technician role required", frappe.PermissionError)
    if not isinstance(equipment_code, str) or not 1 <= len(equipment_code.strip()) <= 140:
        frappe.throw("Equipment code must contain 1–140 characters")
    if not isinstance(question, str) or not 1 <= len(question.strip()) <= 1000:
        frappe.throw("Question must contain 1–1000 characters")

    observed_at = datetime.now(UTC).isoformat()
    equipment_rows = _query(
        "SHD Equipment", ["name", "revision", "company", "customer", "site",
                          "equipment_code", "model", "serial_number"],
        {"equipment_code": equipment_code.strip(), "status": "Active"}, limit=1,
    ).run(as_dict=True)
    if not equipment_rows or not all(scope(equipment_rows[0]).values()):
        frappe.throw("Resource unavailable or outside your operational scope", frappe.PermissionError)
    equipment = equipment_rows[0]
    return {
        "contract_version": "1.0",
        "observed_at": observed_at,
        "question": question.strip(),
        "equipment": {"doctype": "SHD Equipment", **equipment},
        "history": _history(equipment),
        "knowledge": _knowledge(equipment),
    }
