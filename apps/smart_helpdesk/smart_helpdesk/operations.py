import json
from datetime import timedelta
import frappe
from frappe.utils import get_datetime, now_datetime, get_system_timezone
from zoneinfo import ZoneInfo
from smart_helpdesk.api import command
from smart_helpdesk.core import create, change, read, locked, scope, same_scope, result, data, timestamp, work_order, number
from smart_helpdesk.security import require, roles, authority
from smart_helpdesk.schema import SCHEMAS
from smart_helpdesk.sla import deadline, validate_policy


MASTER_ROLES = {
    "SHD Site": {"AIS Dispatcher"}, "SHD Equipment": {"AIS Dispatcher"},
    "SHD Agreement": set(), "SHD Access Grant": set(), "SHD Contact Authority": set(),
    "SHD Technician": {"AIS Dispatcher"}, "SHD Compatibility": {"AIS Knowledge Reviewer"},
    "SHD PM Plan": {"AIS Dispatcher"}, "SHD Knowledge": {"AIS Field Technician", "AIS Knowledge Reviewer"},
}


@command("AIS Dispatcher", "AIS Field Technician", "AIS Knowledge Reviewer")
def register(record_type, values):
    if record_type not in MASTER_ROLES:
        frappe.throw("This record must be created through its business workflow")
    if frappe.session.user != "Administrator" and not (roles() & (MASTER_ROLES[record_type] | {"AIS Service Manager"})):
        frappe.throw("Master data requires designated authority", frappe.PermissionError)
    values = data(values)
    allowed = {f["fieldname"] for f in SCHEMAS[record_type]} | {"company", "customer", "site"}
    if not isinstance(values, dict) or set(values) - allowed:
        frappe.throw("Unknown or protected master fields")
    if record_type not in ("SHD Access Grant", "SHD Technician") and not values.get("customer"):
        frappe.throw("Customer scope is required")
    if record_type in ("SHD Equipment", "SHD Agreement", "SHD Contact Authority", "SHD PM Plan") and not values.get("site"):
        frappe.throw("This operational master requires a specific customer site")
    if values.get("site"):
        site = read("SHD Site", values["site"], "operate")
        if (site.company, site.customer) != (values.get("company"), values.get("customer")):
            frappe.throw("Site does not belong to customer/company")
    if values.get("equipment"):
        equipment = read("SHD Equipment", values["equipment"], "operate")
        same_scope(equipment, frappe._dict(values))
    if record_type in ("SHD Agreement", "SHD Contact Authority"):
        if get_datetime(values["valid_until"]) <= get_datetime(values["valid_from"]):
            frappe.throw("Invalid effective dates")
    if record_type == "SHD Access Grant":
        values.setdefault("resource_type", "Service")
        if set(x.strip() for x in values["actions"].split(",")) - {"read", "operate"}:
            frappe.throw("Only read and operate grants are supported")
    if record_type == "SHD Agreement":
        values["policy"] = data(values["policy"])
        try:
            validate_policy(values["policy"])
        except (ValueError, KeyError, TypeError) as error:
            frappe.throw(str(error))
    if record_type == "SHD PM Plan":
        if int(values["interval_days"]) <= 0 or not data(values["checklist"]):
            frappe.throw("Positive interval and versioned checklist required")
    if record_type == "SHD Technician":
        if get_datetime(values["available_until"]) <= get_datetime(values["available_from"]):
            frappe.throw("Invalid availability window")
    if record_type == "SHD Knowledge":
        if get_datetime(values["effective_until"]) <= get_datetime(values["effective_from"]):
            frappe.throw("Invalid knowledge effective dates")
    status = "Draft" if record_type in ("SHD Agreement", "SHD PM Plan", "SHD Knowledge") else "Active"
    return result(create(record_type, values, status))


@command("AIS Knowledge Reviewer")
def activate(record_type, name):
    if record_type not in ("SHD Agreement", "SHD PM Plan", "SHD Knowledge"):
        frappe.throw("Unsupported publication type")
    if record_type != "SHD Knowledge" and frappe.session.user != "Administrator" and "AIS Service Manager" not in roles():
        frappe.throw("Service manager required", frappe.PermissionError)
    doc = locked(record_type, name)
    if doc.status != "Draft":
        frappe.throw("Published versions are immutable; create a new version")
    values = {"status": "Published" if record_type == "SHD Knowledge" else "Active"}
    if record_type == "SHD Knowledge":
        values["reviewed_by"] = frappe.session.user
    change(doc, "Published", values)
    return result(doc)


@command()
def revoke(record_type, name, reason):
    if record_type not in MASTER_ROLES or not reason.strip():
        frappe.throw("Master record and reason required")
    doc = locked(record_type, name)
    change(doc, "Revoked", {"status": "Revoked", "details": {"reason": reason}})
    return result(doc)


@command("AIS Dispatcher", "AIS Customer Portal")
def receive_request(company, customer, site, subject, reported_at, received_at, service_type="Repair", equipment=None):
    site_doc = read("SHD Site", site, "operate")
    if (site_doc.company, site_doc.customer) != (company, customer):
        frappe.throw("Invalid customer/site")
    reported, received = timestamp(reported_at), timestamp(received_at)
    if received < reported:
        frappe.throw("Receipt cannot precede report")
    values = dict(company=company, customer=customer, site=site, subject=subject,
                  service_type=service_type, reported_at=reported, received_at=received,
                  recorded_at=now_datetime(), equipment=equipment)
    if equipment:
        same_scope(frappe._dict(values), read("SHD Equipment", equipment))
    return result(create("SHD Request", values, "Received"))


@command("AIS Dispatcher")
def triage(request, priority, reason, owner, agreement=None, incident=None):
    doc = locked("SHD Request", request)
    if doc.status not in ("Received", "Triage") or not reason.strip():
        frappe.throw("Untriaged request and a priority reason required")
    if priority not in ("Low", "Medium", "High", "Urgent"):
        frappe.throw("Unsupported priority")
    if not doc.equipment and doc.service_type == "Repair":
        frappe.throw("Resolve equipment before creating a repair incident")
    if not frappe.db.exists("User", {"name": owner, "enabled": 1}):
        frappe.throw("Enabled service owner required")
    updates = {"priority": priority, "service_owner": owner, "status": "Ready", "details": {"triage_reason": reason}}
    if agreement:
        contract = locked("SHD Agreement", agreement, "read")
        same_scope(doc, contract)
        if contract.status != "Active" or contract.service_type != doc.service_type or (contract.equipment and contract.equipment != doc.equipment):
            frappe.throw("Agreement does not cover request")
        anchor_policy = data(contract.policy)
        anchor = get_datetime(doc.get(anchor_policy["anchor"]))
        if not get_datetime(contract.valid_from) <= anchor < get_datetime(contract.valid_until):
            frappe.throw("No entitlement at request anchor")
        overlapping = frappe.get_all("SHD Agreement", filters={"company": doc.company, "customer": doc.customer,
             "site": doc.site, "status": "Active", "service_type": doc.service_type}, fields=["name", "equipment", "valid_from", "valid_until"])
        if sum(1 for c in overlapping if (not c.equipment or c.equipment == doc.equipment) and
               get_datetime(c.valid_from) <= anchor < get_datetime(c.valid_until)) > 1:
            frappe.throw("Overlapping entitlements require an explicit policy resolution")
        snapshot = create("SHD Entitlement", {**scope(doc), "agreement": contract.name,
            "agreement_revision": contract.revision, "applied_at": anchor, "policy": anchor_policy}, "Applied")
        updates["entitlement"] = snapshot.name
        for field, minutes_key in (("response_due", "response_minutes"), ("restoration_due", "restoration_minutes")):
            updates[field] = deadline(anchor.replace(tzinfo=ZoneInfo(get_system_timezone())), float(anchor_policy[minutes_key]), anchor_policy).astimezone(
                ZoneInfo(get_system_timezone())).replace(tzinfo=None)
    else:
        frappe.throw("Confirmed entitlement required for P1 triage; out-of-contract policy must be configured")
    if doc.service_type == "Repair":
        if incident:
            inc = locked("SHD Incident", incident)
            same_scope(doc, inc)
            if inc.equipment != doc.equipment or inc.status in ("Closed", "Cancelled"):
                frappe.throw("Incident equipment or lifecycle does not match")
        else:
            inc = create("SHD Incident", {**scope(doc), "equipment": doc.equipment, "subject": doc.subject,
                "detected_at": doc.reported_at,
                "callback_window_hours": data(contract.policy).get("callback_window_hours")}, "Active")
        updates["incident"] = inc.name
    elif incident:
        frappe.throw("Consultation/PM cannot use a repair incident")
    change(doc, "RequestTriaged", updates)
    return result(doc)


@command("AIS Dispatcher")
def acknowledge(request, response, occurred_at):
    doc = locked("SHD Request", request)
    at = timestamp(occurred_at)
    if not response.strip() or at < get_datetime(doc.received_at) or doc.acknowledged_at:
        frappe.throw("A first customer response after receipt is required")
    change(doc, "RequestAcknowledged", {"acknowledged_at": at,
           "details": {**(data(doc.details) or {}), "first_response": response}}, at)
    return result(doc)


@command("AIS Dispatcher")
def create_work_order(origin_kind, origin, scope_text, package_key="MAIN", required_for_restoration=True):
    if not isinstance(required_for_restoration, bool) or not scope_text.strip():
        frappe.throw("Explicit required-for-restoration flag and nonempty scope required")
    kinds = {"INCIDENT": ("SHD Incident", "incident"), "SERVICE_REQUEST": ("SHD Request", "request"),
             "PM_OCCURRENCE": ("SHD PM Occurrence", "pm_occurrence")}
    if origin_kind not in kinds:
        frappe.throw("Invalid WorkSource kind")
    doctype, field = kinds[origin_kind]
    parent = locked(doctype, origin)
    if origin_kind == "SERVICE_REQUEST" and (parent.incident or parent.status != "Ready"):
        frappe.throw("Use the incident source for incident-linked requests; triage is required")
    if origin_kind == "PM_OCCURRENCE":
        package_key = "PM_MAIN"
    source_name = frappe.db.get_value("SHD Work Source", {field: origin}, for_update=True)
    source = read("SHD Work Source", source_name) if source_name else create("SHD Work Source", {
        **scope(parent), "origin_kind": origin_kind, field: origin, "source_version": parent.revision}, "Active")
    existing = frappe.db.get_value("SHD Work Order", {"source": source.name, "package_key": package_key, "generation_version": 1}, for_update=True)
    if existing:
        doc = read("SHD Work Order", existing)
        if doc.scope != scope_text or bool(doc.required_for_restoration) != bool(required_for_restoration):
            frappe.throw("Package already exists with different approved scope")
        return result(doc)
    doc = create("SHD Work Order", {**scope(parent), "source": source.name, "package_key": package_key,
        "generation_version": 1, "scope": scope_text, "required_for_restoration": int(required_for_restoration)}, "Planned")
    if origin_kind == "INCIDENT":
        # Adding a required package invalidates any earlier aggregate restoration.
        project_incident(parent.name)
    return result(doc)


@command("AIS Dispatcher")
def assign(work_order_id, technician, starts_at, ends_at, required_skill):
    wo = work_order(work_order_id)
    if wo.status not in ("Planned", "Assigned"):
        frappe.throw("Assignment changes require a planned work order")
    profile_name = frappe.db.get_value("SHD Technician", {"user": technician, "company": wo.company, "status": "Active"})
    if not profile_name:
        frappe.throw("No active technician profile")
    profile = locked("SHD Technician", profile_name)
    start, end = get_datetime(starts_at), get_datetime(ends_at)
    if end <= start or not get_datetime(profile.available_from) <= start < end <= get_datetime(profile.available_until):
        frappe.throw("Technician is unavailable")
    if required_skill not in data(profile.skills):
        frappe.throw("Technician lacks required skill")
    conflicts = frappe.db.sql("""SELECT name FROM `tabSHD Work Order` WHERE technician=%s AND status NOT IN ('Closed','Cancelled')
        AND scheduled_start < %s AND scheduled_end > %s FOR UPDATE""", (technician, end, start), as_dict=True)
    if any(row.name != wo.name for row in conflicts):
        frappe.throw("Technician is already booked")
    from smart_helpdesk.inventory import check_material_readiness
    check_material_readiness(wo, end)
    change(wo, "WorkOrderAssigned", {"technician": technician, "required_skill": required_skill,
                                    "scheduled_start": start, "scheduled_end": end, "status": "Assigned"})
    return result(wo)


@command("AIS Field Technician", "AIS Dispatcher")
def start_visit(work_order_id, occurred_at):
    wo = work_order(work_order_id)
    if wo.status not in ("Assigned", "In progress") or not wo.technician:
        frappe.throw("An assigned work order is required")
    if frappe.session.user != "Administrator" and frappe.session.user != wo.technician and "AIS Service Manager" not in roles():
        frappe.throw("Assigned technician must start the visit", frappe.PermissionError)
    if frappe.db.exists("SHD Visit", {"work_order": wo.name, "status": "Started"}):
        frappe.throw("A visit is already in progress")
    if wo.estimate:
        from smart_helpdesk.commercial import valid_approval
        valid_approval(wo)
    from smart_helpdesk.inventory import check_material_readiness
    check_material_readiness(wo, now_datetime())
    at = timestamp(occurred_at)
    visit = create("SHD Visit", {**scope(wo), "work_order": wo.name, "technician": wo.technician, "started_at": at}, "Started")
    change(wo, "VisitStarted", {"status": "In progress"}, at)
    return result(visit)


@command("AIS Field Technician")
def finish_visit(visit, outcome, evidence, occurred_at, completed=True):
    if not isinstance(completed, bool):
        frappe.throw("Completion outcome must be a boolean")
    doc = locked("SHD Visit", visit)
    wo = work_order(doc.work_order)
    at = timestamp(occurred_at)
    if doc.status != "Started" or at < get_datetime(doc.started_at) or not outcome.strip() or not evidence:
        frappe.throw("Started visit, outcome and evidence required")
    change(doc, "VisitCompleted", {"ended_at": at, "outcome": outcome, "evidence": data(evidence),
                                   "status": "Completed" if completed else "Incomplete"}, at)
    return result(doc)


@command("AIS Field Technician")
def log_time(visit, hours, billable_hours, work_kind):
    doc = locked("SHD Visit", visit)
    work_order(doc.work_order)
    actual, billable = number(hours), number(billable_hours, False)
    if doc.status not in ("Completed", "Incomplete") or billable > actual:
        frappe.throw("Completed visit and billable hours no greater than actual required")
    if actual > (get_datetime(doc.ended_at) - get_datetime(doc.started_at)).total_seconds() / 3600:
        frappe.throw("Time log exceeds visit duration")
    existing = frappe.get_all("SHD Time Log", filters={"visit": visit}, pluck="hours")
    if sum(float(h) for h in existing) + float(actual) > (get_datetime(doc.ended_at) - get_datetime(doc.started_at)).total_seconds() / 3600:
        frappe.throw("Combined time logs exceed visit duration")
    return result(create("SHD Time Log", {**scope(doc), "work_order": doc.work_order, "visit": doc.name,
        "technician": doc.technician, "hours": actual, "billable_hours": billable, "work_kind": work_kind}, "Confirmed"))


@command("AIS Field Technician")
def restore(work_order_id, criteria, measurements, occurred_at):
    wo = work_order(work_order_id)
    if wo.status != "In progress" or not criteria.strip() or not data(measurements):
        frappe.throw("In-progress work, test criteria and measured evidence required")
    if frappe.db.exists("SHD Visit", {"work_order": wo.name, "status": "Started"}) or not frappe.db.exists(
            "SHD Visit", {"work_order": wo.name, "status": "Completed"}):
        frappe.throw("Finish technical testing visit before recording restoration")
    at = timestamp(occurred_at)
    visits = frappe.get_all("SHD Visit", filters={"work_order": wo.name}, fields=["ended_at"])
    if any(v.ended_at and get_datetime(v.ended_at) > at for v in visits):
        frappe.throw("Restoration cannot precede visit completion")
    if wo.estimate:
        from smart_helpdesk.commercial import valid_approval
        valid_approval(wo)
    change(wo, "WorkOrderRestored", {"restored_at": at, "status": "Technically complete",
        "restoration_evidence": {"criteria": criteria, "measurements": data(measurements)}}, at)
    source = read("SHD Work Source", wo.source)
    if source.incident:
        project_incident(source.incident)
    else:
        project_source(source)
    return result(wo)


@command("AIS Customer Portal", "AIS Dispatcher")
def accept_work(work_order_id, evidence, occurred_at):
    wo = work_order(work_order_id)
    authority(wo, "Accept")
    at = timestamp(occurred_at)
    if wo.status != "Technically complete" or at < get_datetime(wo.restored_at) or not evidence.strip():
        frappe.throw("Restoration and customer acceptance evidence required")
    create("SHD Acceptance", {**scope(wo), "work_order": wo.name, "accepted_by": frappe.session.user,
        "accepted_at": at, "evidence": evidence}, "Accepted")
    change(wo, "CustomerAcceptanceRecorded", {"accepted_at": at, "status": "Customer accepted"}, at)
    source = read("SHD Work Source", wo.source)
    project_incident(source.incident) if source.incident else project_source(source)
    return result(wo)


def source_orders(source):
    return frappe.get_all("SHD Work Order", filters={"source": source.name, "required_for_restoration": 1,
         "status": ["!=", "Cancelled"]}, fields=["name", "restored_at", "accepted_at"])


def project_source(source):
    orders = source_orders(source)
    restored = max(get_datetime(o.restored_at) for o in orders) if orders and all(o.restored_at for o in orders) else None
    accepted = max(get_datetime(o.accepted_at) for o in orders) if orders and all(o.accepted_at for o in orders) else None
    filters = {"incident": source.incident} if source.incident else {"name": source.request} if source.request else None
    if filters:
        event_ids = frappe.get_all("SHD Event", filters={"aggregate_type": "SHD Work Order",
            "aggregate_id": ["in", [o.name for o in orders]]}, pluck="name") if orders else []
        for name in frappe.get_all("SHD Request", filters=filters, pluck="name"):
            req = locked("SHD Request", name)
            if req.status not in ("Closed", "Cancelled", "Duplicate"):
                change(req, "IncidentRestorationProjected", {"restored_at": restored, "accepted_at": accepted,
                    "status": "Accepted" if accepted else "Restored" if restored else "Active", "projection_events": event_ids})
    return restored, accepted


def project_incident(incident):
    inc = locked("SHD Incident", incident)
    source = frappe.db.get_value("SHD Work Source", {"incident": inc.name})
    if source:
        restored, accepted = project_source(read("SHD Work Source", source))
        change(inc, "IncidentRestorationProjected", {"restored_at": restored, "accepted_at": accepted,
            "status": "Accepted" if accepted else "Restored" if restored else "Active"})


@command("AIS Dispatcher")
def close_request(request, reason):
    doc = locked("SHD Request", request)
    if doc.status != "Accepted" or not reason.strip():
        frappe.throw("All required work must be restored and accepted")
    if frappe.db.exists("SHD Wait Interval", {"request": request, "status": "Waiting"}):
        frappe.throw("Resolve open waiting intervals first")
    change(doc, "ServiceRequestClosed", {"status": "Closed", "closed_at": now_datetime()})
    return result(doc)


@command("AIS Dispatcher")
def wait(request, reason, owner, eta):
    req = locked("SHD Request", request)
    if req.status in ("Closed", "Cancelled", "Duplicate"):
        frappe.throw("Terminal request cannot enter waiting")
    return result(create("SHD Wait Interval", {**scope(req), "request": request, "reason": reason,
        "service_owner": owner, "eta": eta, "started_at": now_datetime()}, "Waiting"))


@command("AIS Dispatcher")
def end_wait(interval):
    doc = locked("SHD Wait Interval", interval)
    if doc.status != "Waiting":
        frappe.throw("Interval already ended")
    change(doc, "WaitEnded", {"status": "Ended", "ended_at": now_datetime()})
    return result(doc)


@command("AIS Dispatcher")
def classify_callback(incident, original_incident, classification, reason):
    new = locked("SHD Incident", incident)
    original = locked("SHD Incident", original_incident)
    same_scope(new, original)
    if new.name == original.name or new.equipment != original.equipment or classification not in ("Callback", "Related", "New") or not reason.strip():
        frappe.throw("Distinct incidents, same equipment and justified classification required")
    if not original.restored_at:
        frappe.throw("Original incident has not been restored")
    if classification == "Callback":
        window = float(original.callback_window_hours or 0)
        if window <= 0 or not new.detected_at or not get_datetime(original.restored_at) <= get_datetime(new.detected_at) <= get_datetime(original.restored_at) + timedelta(hours=window):
            frappe.throw("Callback must be reported within the original incident's configured observation window")
    change(new, "CallbackClassified", {"callback_of": original.name, "callback_classification": classification,
                                      "details": {"classification_reason": reason}})
    return result(new)


@command("AIS Dispatcher")
def correct_restoration(work_order_id, source_event, reason, occurred_at=None):
    wo = work_order(work_order_id)
    # The work-order scope above authorizes this narrow event lookup, not the audit catalog.
    original = frappe.get_doc("SHD Event", source_event)
    if original.aggregate_id != wo.name or original.event_type != "WorkOrderRestored" or not reason.strip():
        frappe.throw("Restoration event and correction reason required")
    if frappe.db.exists("SHD Event", {"supersedes_event": source_event}):
        frappe.throw("This event has already been superseded")
    if wo.accepted_at:
        frappe.throw("Accepted work needs a customer quality review before reopening")
    at = timestamp(occurred_at) if occurred_at else None
    change(wo, "RestorationCorrected", {"restored_at": at, "status": "Technically complete" if at else "In progress",
           "details": {"correction_reason": reason}}, supersedes=source_event)
    source = read("SHD Work Source", wo.source)
    project_incident(source.incident) if source.incident else project_source(source)
    return result(wo)
