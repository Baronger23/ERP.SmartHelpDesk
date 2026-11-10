"""Reproducible event-time snapshots; never hard-code successful KPIs."""
from datetime import timedelta
from decimal import Decimal
import frappe
from frappe.utils import get_datetime, now_datetime
from smart_helpdesk.api import command
from smart_helpdesk.core import create, read, result, data, scope


def ratio(numerator, denominator, missing=0):
    return {"numerator": numerator, "denominator": denominator,
            "rate": numerator / denominator if denominator else None, "missing": missing}


def facts_at(events, as_of):
    """Latest authoritative version per aggregate, at recorded-time cut-off."""
    facts = {}
    for evt in sorted(events, key=lambda e: (e.aggregate_type, e.aggregate_id, int(e.aggregate_version))):
        if get_datetime(evt.recorded_at) <= as_of:
            facts[(evt.aggregate_type, evt.aggregate_id)] = data(evt.payload)
    return facts


@command("AIS Billing Accountant")
def snapshot_kpis(company, period_start, period_end, customer=None, site=None, as_of=None, supersedes=None, auto_revision=False):
    start, end = get_datetime(period_start), get_datetime(period_end)
    cut = get_datetime(as_of) if as_of else now_datetime()
    if end <= start or cut > now_datetime():
        frappe.throw("Valid reporting window and non-future as_of required")
    # Grant filtering happens before any payload is read into this reporting process.
    filters = {"company": company, "recorded_at": ["<=", cut]}
    if customer:
        filters["customer"] = customer
    if site:
        filters["site"] = site
    # Event records are not generally readable by billing; scope uses a report proxy.
    from smart_helpdesk.security import require
    context = frappe._dict(doctype="SHD KPI Snapshot", company=company, customer=customer, site=site)
    require(context, "operate")
    events = frappe.get_all("SHD Event", filters=filters, fields=["*"])
    # Recheck every source: a company-level report does not authorize all customers.
    from smart_helpdesk.security import permits
    events = [e for e in events if permits(frappe._dict(doctype="SHD KPI Snapshot", **scope(e)), "read")]
    facts = facts_at(events, cut)
    requests, visits, incidents, occurrences, charges = [], [], [], [], []
    for (kind, _), fact in facts.items():
        {"SHD Request": requests, "SHD Visit": visits, "SHD Incident": incidents,
         "SHD PM Occurrence": occurrences, "SHD Charge": charges}.get(kind, []).append(fact)
    cohort = [r for r in requests if start <= get_datetime(r["received_at"]) < end and r.get("status") not in ("Duplicate", "Cancelled", "Rejected")]
    metrics = {}
    for name, due_field, fulfilled in (("response_sla", "response_due", "acknowledged_at"),
                                        ("restoration_sla", "restoration_due", "restored_at")):
        eligible, met, missing = 0, 0, 0
        for req in cohort:
            if not req.get(due_field):
                missing += 1
                continue
            due = get_datetime(req[due_field])
            done = get_datetime(req[fulfilled]) if req.get(fulfilled) else None
            if due <= cut or done and done <= cut:
                eligible += 1
                met += int(bool(done and done <= due))
        metrics[name] = ratio(met, eligible, missing)
    due_pm = [p for p in occurrences if start.date() <= get_datetime(p["due_original"]).date() < end.date()]
    metrics["pm_original"] = ratio(sum(bool(p.get("completed_at") and get_datetime(p["completed_at"]).date() <= get_datetime(p["due_original"]).date()) for p in due_pm), len(due_pm))
    ft_eligible, fixed, pending, missing = 0, 0, 0, 0
    orders = {name: f for (kind, name), f in facts.items() if kind == "SHD Work Order"}
    sources = {name: f for (kind, name), f in facts.items() if kind == "SHD Work Source"}
    for inc in incidents:
        restored = get_datetime(inc["restored_at"]) if inc.get("restored_at") else None
        if not restored or not start <= restored < end:
            continue
        window = inc.get("callback_window_hours")
        if window is None or float(window) <= 0:
            missing += 1
            continue
        if restored + timedelta(hours=float(window)) > cut:
            pending += 1
            continue
        ft_eligible += 1
        wo_ids = {name for name, wo in orders.items() if sources.get(wo.get("source"), {}).get("incident") == inc["name"]}
        service_visits = sorted((v for v in visits if v.get("work_order") in wo_ids and v.get("started_at")), key=lambda v: v["started_at"])
        callbacks = [c for c in incidents if c.get("callback_of") == inc["name"] and c.get("callback_classification") == "Callback"]
        fixed += int(len(service_visits) == 1 and service_visits[0].get("status") == "Completed" and not callbacks)
    metrics["first_time_fix"] = {**ratio(fixed, ft_eligible, missing), "pending_observation": pending}
    cohort_incidents = {r.get("incident") for r in cohort if r.get("incident")}
    cohort_requests = {r["name"] for r in cohort}
    cohort_orders = {name for name, wo in orders.items() if
        sources.get(wo.get("source"), {}).get("incident") in cohort_incidents or
        sources.get(wo.get("source"), {}).get("request") in cohort_requests}
    materials = [f for (kind, _), f in facts.items() if kind == "SHD Material Use" and f.get("work_order") in cohort_orders]
    time_logs = [f for (kind, _), f in facts.items() if kind == "SHD Time Log" and f.get("work_order") in cohort_orders]
    invoices = [f for (kind, _), f in facts.items() if kind == "Sales Invoice" and f.get("custom_shd_work_order") in cohort_orders and f.get("docstatus") == 1]
    material_cost = sum((Decimal(str(m["quantity"])) * Decimal(str(m["unit_cost"])) for m in materials), Decimal(0))
    confirmed_labor = [t for t in time_logs if (data(t.get("details")) or {}).get("cost_basis")]
    labor_cost = sum((Decimal(str(t["hours"])) * Decimal(str(t["cost_rate"])) for t in confirmed_labor), Decimal(0))
    revenue = sum((Decimal(str(i["net_total"])) for i in invoices), Decimal(0))
    metrics["service_cohort_finance"] = {"currency": frappe.db.get_value("Company", company, "default_currency"),
        "known_material_cost": str(material_cost), "known_labor_cost": str(labor_cost),
        "missing_labor_valuations": len(time_logs) - len(confirmed_labor), "submitted_net_revenue": str(revenue),
        "provisional_contribution": str(revenue - material_cost - labor_cost) if len(confirmed_labor) == len(time_logs) else None,
        "material_sources": [m["name"] for m in materials], "time_sources": [t["name"] for t in time_logs],
        "invoice_sources": [i["name"] for i in invoices]}
    metrics["request_sources"] = [r["name"] for r in cohort]
    metrics["operational_exceptions"] = [{"name": r["name"], "owner": r.get("service_owner"), "status": r.get("status")}
        for r in cohort if not r.get("service_owner") or (r.get("restoration_due") and not r.get("restored_at") and get_datetime(r["restoration_due"]) < cut)]
    if auto_revision:
        if supersedes:
            frappe.throw("Choose automatic revision or an explicit previous snapshot")
        previous_rows = frappe.get_list("SHD KPI Snapshot", filters={"company": company, "customer": customer,
            "site": site, "period_start": start, "period_end": end}, fields=["name"], order_by="creation desc", limit_page_length=1)
        supersedes = previous_rows[0].name if previous_rows else None
    previous = read("SHD KPI Snapshot", supersedes) if supersedes else None
    if previous and (previous.company != company or previous.customer != customer or previous.site != site or
        get_datetime(previous.period_start) != start or get_datetime(previous.period_end) != end):
        frappe.throw("Revision must supersede the same reporting scope and window")
    snapshot = create("SHD KPI Snapshot", {"company": company, "customer": customer, "site": site,
        "period_start": start, "period_end": end, "as_of": cut, "formula_version": "ais-p1-v1",
        "watermark": max((e.recorded_at for e in events), default=None), "metrics": metrics,
        "source_events": [e.name for e in events], "supersedes": supersedes,
        "details": {"label": "Provisional", "reason": "Late events produce a new immutable snapshot"}}, "Provisional")
    return {**result(snapshot), "metrics": metrics}
