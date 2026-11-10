from datetime import timedelta

import frappe
from frappe.utils import getdate, now_datetime

from smart_helpdesk.api import command
from smart_helpdesk.core import (
    change,
    create,
    data,
    locked,
    read,
    result,
    scope,
    timestamp,
)


@command("AIS Dispatcher")
def generate_pm(plan, period_key):
    doc = locked("SHD PM Plan", plan)
    if doc.status != "Active":
        frappe.throw("Active PM plan required")
    # Period is an ordinal, not a caller-supplied arbitrary due date.
    try:
        ordinal = int(period_key)
    except (TypeError, ValueError):
        frappe.throw("Period key must be a non-negative ordinal")
    if ordinal < 0 or str(ordinal) != str(period_key):
        frappe.throw("Period key must use canonical non-negative integer format")
    filters = {"plan": plan, "plan_version": doc.revision, "equipment": doc.equipment, "period_key": str(ordinal)}
    existing = frappe.db.get_value("SHD PM Occurrence", filters, for_update=True)
    if existing:
        return result(read("SHD PM Occurrence", existing))
    due = getdate(doc.first_due) + timedelta(days=ordinal * doc.interval_days)
    occurrence = create("SHD PM Occurrence", {**scope(doc), **filters, "due_original": due,
        "checklist": data(doc.checklist)}, "Scheduled")
    from smart_helpdesk.operations import create_work_order
    create_work_order("PM_OCCURRENCE", occurrence.name, "PM checklist " + doc.name, "PM_MAIN")
    return result(occurrence)


@command("AIS Dispatcher")
def postpone_pm(occurrence, new_due, reason):
    doc = locked("SHD PM Occurrence", occurrence)
    if doc.status == "Completed" or not reason.strip() or getdate(new_due) < getdate(doc.due_original):
        frappe.throw("Open occurrence, valid postponement date and reason required")
    change(doc, "PMPostponed", {"due_adjusted": getdate(new_due), "details": {"postponement_reason": reason,
        "approved_by": frappe.session.user}})
    return result(doc)


@command("AIS Field Technician", "AIS Dispatcher")
def complete_pm(occurrence, observations, findings, occurred_at):
    doc = locked("SHD PM Occurrence", occurrence)
    if doc.status != "Scheduled":
        frappe.throw("PM occurrence is not scheduled")
    source = frappe.db.get_value("SHD Work Source", {"pm_occurrence": doc.name})
    wo_name = frappe.db.get_value("SHD Work Order", {"source": source, "package_key": "PM_MAIN"})
    wo = locked("SHD Work Order", wo_name)
    if wo.status not in ("In progress", "Technically complete", "Customer accepted"):
        frappe.throw("PM work must be performed through the assigned work order")
    observed = data(observations)
    template = data(doc.checklist)
    if not isinstance(observed, list) or not isinstance(template, list):
        frappe.throw("Checklist and observations must be arrays")
    expected = {step["key"]: step for step in template}
    if len(expected) != len(template) or len(observed) != len(expected) or {o["key"] for o in observed} != set(expected):
        frappe.throw("Every checklist step must be represented exactly once")
    for observation in observed:
        step = expected[observation["key"]]
        if observation.get("result") not in ("Passed", "Abnormal", "Not applicable", "Not performed"):
            frappe.throw("Invalid checklist result")
        if observation["result"] in ("Not applicable", "Not performed") and not observation.get("reason"):
            frappe.throw("Skipped checks require a reason")
        if step.get("unit") and observation["result"] in ("Passed", "Abnormal") and (observation.get("value") is None or observation.get("unit") != step["unit"]):
            frappe.throw("Measured value and matching unit required; zero is a valid measurement")
    finding_ids = []
    for finding in data(findings):
        if set(finding) - {"description", "severity", "service_owner", "due_at"}:
            frappe.throw("Unexpected finding fields")
        item = create("SHD Finding", {**scope(doc), **finding, "pm_occurrence": doc.name, "equipment": doc.equipment}, "Open")
        finding_ids.append(item.name)
    if any(o["result"] == "Abnormal" for o in observed) and not finding_ids:
        frappe.throw("Abnormal observations require findings with an owner and due date")
    change(doc, "PMOccurrenceCompleted", {"status": "Completed", "completed_at": timestamp(occurred_at), "observations": observed}, timestamp(occurred_at))
    return {**result(doc), "findings": finding_ids}


@command("AIS Dispatcher")
def classify_finding(finding, disposition, reason):
    doc = locked("SHD Finding", finding)
    if doc.status != "Open" or disposition not in ("Monitor", "Repair", "No fault") or not reason.strip():
        frappe.throw("Open finding and justified disposition required")
    values = {"status": "Monitoring" if disposition == "Monitor" else "Repair pending" if disposition == "Repair" else "Reviewed",
              "details": {"classification_reason": reason}}
    if disposition == "Repair":
        occurrence = read("SHD PM Occurrence", doc.pm_occurrence)
        inc = create("SHD Incident", {**scope(doc), "equipment": doc.equipment, "subject": doc.description,
            "detected_at": occurrence.completed_at}, "Active")
        values["incident"] = inc.name
    change(doc, "FindingClassified", values)
    return result(doc)


@command("AIS Knowledge Reviewer", "AIS Field Technician", "AIS Dispatcher")
def search_knowledge(company, model, query, customer=None, site=None):
    now = now_datetime()
    matches = []
    # Permission-aware list first; all pages, bounded response. No embeddings or AI calls.
    rows = frappe.get_list("SHD Knowledge", filters={"company": company, "model": model,
        "status": "Published", "effective_from": ["<=", now], "effective_until": [">", now]},
        fields=["name", "title", "content", "document_version", "source_reference", "customer", "site"], limit_page_length=0)
    for row in rows:
        if customer and row.customer != customer or site and row.site != site:
            continue
        if query.casefold() in (row.title + " " + row.content).casefold():
            matches.append(row)
    return {"results": matches[:50], "total": len(matches), "search_mode": "approved_catalog_keyword"}
