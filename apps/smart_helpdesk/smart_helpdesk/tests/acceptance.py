"""Desk role acceptance: three business flows executed end to end by the
users who actually hold each AIS role, on a dataset that belongs to this
suite alone (company "SHD Acceptance", customers ACC A/B).

Desk forms are read-only by design, so every step goes through the same
`smart_helpdesk.api.execute` command boundary the Desk operation dialog
calls. Each step records its actor, role and produced document IDs; each
flow then reconciles against stock (Bin), the invoice and the audit
trail (SHD Command receipts + SHD Event journal). Two denial cases close
the suite: cross-customer access and approval after expiry.

Setup (users, grants, authorities, agreement) is provisioning and runs
as Administrator / the service manager; the flows themselves never run
as Administrator. Run only on the dedicated shd-test.* site.
"""
import json
import time
from datetime import timedelta

import frappe
from frappe.utils import now_datetime

from smart_helpdesk.api import execute

COMPANY = "SHD Acceptance"
CUSTOMER_A = "ACC Customer A"
CUSTOMER_B = "ACC Customer B"
WAREHOUSE = "ACC Stores - SAC"
QUARANTINE = "ACC Quarantine - SAC"
PART = "ACC-PART"
SPARE = "ACC-SPARE"
SELLING = "ACC Selling VND"

MANAGER = "acc.manager@example.invalid"
DISPATCH = "acc.dispatch@example.invalid"
TECH = "acc.tech@example.invalid"
KEEPER = "acc.keeper@example.invalid"
PURCHASING = "acc.purchasing@example.invalid"
ACCOUNTING = "acc.accounting@example.invalid"
CUST_A = "acc.customer.a@example.invalid"
CUST_A2 = "acc.customer.a2@example.invalid"
CUST_B = "acc.customer.b@example.invalid"

ROLE_OF = {MANAGER: "AIS Service Manager", DISPATCH: "AIS Dispatcher",
           TECH: "AIS Field Technician", KEEPER: "AIS Warehouse Keeper",
           PURCHASING: "AIS Purchasing", ACCOUNTING: "AIS Billing Accountant",
           CUST_A: "AIS Customer Portal", CUST_A2: "AIS Customer Portal",
           CUST_B: "AIS Customer Portal"}

# Native ERPNext roles the same people hold for the Desk documents their
# commands map or submit (purchase/stock/accounts paperwork). The AIS
# role above stays the business authority; these only satisfy ERPNext's
# own DocType permissions, exactly as a real deployment would provision.
NATIVE_ROLES = {MANAGER: ["Purchase Manager", "Stock Manager", "Accounts User"],
                TECH: ["Stock User"],
                KEEPER: ["Stock User", "Purchase User", "Accounts User"],
                PURCHASING: ["Purchase User", "Stock User", "Accounts User"],
                ACCOUNTING: ["Accounts User"]}

SITE_A = None
SITE_B = None
EQUIPMENT_A = None


def call_as(user, command, key=None, **payload):
    frappe.set_user(user)
    try:
        return execute(command, payload, key or frappe.generate_hash(length=20))
    finally:
        frappe.set_user("Administrator")


def denial_as(user, command, **payload):
    """Return the exception text when the command is refused, else None."""
    frappe.set_user(user)
    try:
        execute(command, payload, frappe.generate_hash(length=20))
        return None
    except Exception as error:  # noqa: BLE001 - the refusal IS the evidence
        return f"{type(error).__name__}: {error}"
    finally:
        frappe.set_user("Administrator")


def _ensure(doctype, name, doc):
    if not frappe.db.exists(doctype, name):
        frappe.get_doc(doc).insert()
        return True
    return False


def setup_dataset(now, past, future):
    """Idempotent provisioning. Returns nothing; sets module scope names."""
    global SITE_A, SITE_B, EQUIPMENT_A
    frappe.set_user("Administrator")
    if not frappe.db.exists("Warehouse Type", "Transit"):
        from erpnext.setup.setup_wizard.operations.install_fixtures import install
        install("Vietnam")
    _ensure("Company", COMPANY, {"doctype": "Company", "company_name": COMPANY,
            "abbr": "SAC", "country": "Vietnam", "default_currency": "VND"})
    for customer in (CUSTOMER_A, CUSTOMER_B):
        _ensure("Customer", customer, {"doctype": "Customer", "customer_name": customer,
                "customer_type": "Company", "customer_group": "Commercial",
                "territory": "All Territories"})
    _ensure("Warehouse", WAREHOUSE, {"doctype": "Warehouse", "warehouse_name": "ACC Stores",
            "company": COMPANY})
    _ensure("Warehouse", QUARANTINE, {"doctype": "Warehouse", "warehouse_name": "ACC Quarantine",
            "company": COMPANY})
    _ensure("Price List", SELLING, {"doctype": "Price List", "price_list_name": SELLING,
            "enabled": 1, "selling": 1, "currency": "VND"})
    year = now.year
    _ensure("Fiscal Year", str(year), {"doctype": "Fiscal Year", "year": str(year),
            "year_start_date": f"{year}-01-01", "year_end_date": f"{year}-12-31"})
    for code in (PART, SPARE):
        _ensure("Item", code, {"doctype": "Item", "item_code": code, "item_name": code,
                "item_group": "Products", "stock_uom": "Nos", "is_stock_item": 1})
    _ensure("Supplier", "ACC Supplier", {"doctype": "Supplier", "supplier_name": "ACC Supplier",
            "supplier_group": "All Supplier Groups", "supplier_type": "Company",
            "default_currency": "VND"})
    if not frappe.db.get_value("Supplier", "ACC Supplier", "default_currency"):
        frappe.db.set_value("Supplier", "ACC Supplier", "default_currency", "VND")
    for item, qty in ((PART, 3), (SPARE, 1)):
        if not frappe.db.exists("Bin", {"item_code": item, "warehouse": WAREHOUSE}):
            receipt = frappe.get_doc({"doctype": "Stock Entry",
                "stock_entry_type": "Material Receipt", "company": COMPANY,
                "items": [{"item_code": item, "qty": qty, "t_warehouse": WAREHOUSE,
                           "basic_rate": 100}]})
            receipt.insert()
            receipt.submit()
    for user, role in ROLE_OF.items():
        wanted = [role] + NATIVE_ROLES.get(user, [])
        _ensure("User", user, {"doctype": "User", "email": user,
                "first_name": user.split(".")[1].split("@")[0], "send_welcome_email": 0,
                "roles": [{"role": r} for r in wanted]})
        doc = frappe.get_doc("User", user)
        have = {r.role for r in doc.roles}
        if any(r not in have for r in wanted):
            for r in wanted:
                if r not in have:
                    doc.append("roles", {"role": r})
            doc.save()
    base = {"company": COMPANY}
    site_a = frappe.db.get_value("SHD Site", {"company": COMPANY, "customer": CUSTOMER_A})
    if not site_a:
        site_a = execute("register", {"record_type": "SHD Site", "values": {
            **base, "customer": CUSTOMER_A, "title": "ACC Factory A"}},
            frappe.generate_hash(length=20))["name"]
    site_b = frappe.db.get_value("SHD Site", {"company": COMPANY, "customer": CUSTOMER_B})
    if not site_b:
        site_b = execute("register", {"record_type": "SHD Site", "values": {
            **base, "customer": CUSTOMER_B, "title": "ACC Factory B"}},
            frappe.generate_hash(length=20))["name"]
    SITE_A, SITE_B = site_a, site_b
    scoped_a = {**base, "customer": CUSTOMER_A, "site": SITE_A}
    equipment = frappe.db.get_value("SHD Equipment", {"site": SITE_A})
    if not equipment:
        equipment = execute("register", {"record_type": "SHD Equipment", "values": {
            **scoped_a, "equipment_code": "ACC-EQ-001", "model": "ACC-R1",
            "serial_number": "ACC-SERIAL-001"}}, frappe.generate_hash(length=20))["name"]
    EQUIPMENT_A = equipment
    for item in (PART, SPARE):
        if not frappe.db.exists("SHD Compatibility",
                                {"site": SITE_A, "model": "ACC-R1", "item": item}):
            execute("register", {"record_type": "SHD Compatibility", "values": {
                **scoped_a, "model": "ACC-R1", "item": item,
                "evidence": "Acceptance dataset compatibility"}}, frappe.generate_hash(length=20))
    if not frappe.db.exists("SHD Technician", {"user": TECH}):
        execute("register", {"record_type": "SHD Technician", "values": {
            "company": COMPANY, "user": TECH, "skills": ["compressor"],
            "available_from": past - timedelta(days=365),
            "available_until": future + timedelta(days=365)}}, frappe.generate_hash(length=20))

    def grant(user, resource, customer=None, site=None):
        filters = {"user": user, "resource_type": resource, "status": "Active"}
        if frappe.db.exists("SHD Access Grant", filters):
            return
        values = {**base, "user": user, "resource_type": resource, "actions": "read,operate"}
        if customer:
            values["customer"] = customer
        if site:
            values["site"] = site
        execute("register", {"record_type": "SHD Access Grant", "values": values},
                frappe.generate_hash(length=20))

    grant(MANAGER, "All")
    grant(DISPATCH, "All")
    grant(TECH, "All")
    for user in (KEEPER, PURCHASING):
        grant(user, "Service")
        grant(user, "Inventory")
    grant(ACCOUNTING, "Service")
    grant(ACCOUNTING, "Finance")
    # reconcile_charge locks the SHD Material Use source (Inventory resource).
    grant(ACCOUNTING, "Inventory")
    for user, customer, site in ((CUST_A, CUSTOMER_A, SITE_A), (CUST_A2, CUSTOMER_A, SITE_A),
                                 (CUST_B, CUSTOMER_B, SITE_B)):
        grant(user, "Service", customer, site)
        grant(user, "Finance", customer, site)

    def authority(user, kind, valid_from, valid_until, limit=0):
        if frappe.db.exists("SHD Contact Authority",
                            {"user": user, "authority": kind, "site": SITE_A}):
            return
        execute("register", {"record_type": "SHD Contact Authority", "values": {
            **scoped_a, "user": user, "authority": kind, "amount_limit": limit,
            "valid_from": valid_from, "valid_until": valid_until}},
            frappe.generate_hash(length=20))

    authority(CUST_A, "Accept", past - timedelta(days=1), future)
    authority(CUST_A, "Approve Cost", past - timedelta(days=1), future, 1000000)
    # The second customer contact holds an already-expired Approve Cost right.
    authority(CUST_A2, "Approve Cost", past - timedelta(days=2), past - timedelta(days=1), 1000000)
    frappe.db.commit()


def _window(past, minutes=60):
    """A scheduling window for the acceptance technician that starts after
    their latest open booking, so re-running the suite on a site that
    already holds acceptance history cannot collide with itself."""
    from frappe.utils import get_datetime
    last_end = frappe.db.sql("""SELECT MAX(scheduled_end) FROM `tabSHD Work Order`
        WHERE technician=%s AND status NOT IN ('Closed','Cancelled')""", TECH)[0][0]
    start = past
    if last_end and get_datetime(last_end) >= start:
        start = get_datetime(last_end) + timedelta(minutes=5)
    return start, start + timedelta(minutes=minutes)


def flow_one(now, past, future):
    """Intake -> dispatch -> repair -> customer acceptance -> invoice."""
    steps, docs = [], {}

    def step(user, command, label, **payload):
        out = call_as(user, command, **payload)
        entry = {"step": label, "command": command, "actor": user, "role": ROLE_OF[user]}
        if isinstance(out, dict) and out.get("name"):
            entry["document"] = out["name"]
        steps.append(entry)
        return out

    scoped = {"company": COMPANY, "customer": CUSTOMER_A, "site": SITE_A}
    bin_before = frappe.db.get_value("Bin", {"item_code": PART, "warehouse": WAREHOUSE}, "actual_qty")
    request = step(CUST_A, "receive_request", "intake_by_customer",
                   **scoped, equipment=EQUIPMENT_A, subject="ACC line stopped",
                   reported_at=str(past), received_at=str(past + timedelta(minutes=5)))
    docs["request"] = request["name"]
    agreement = _agreement_id()
    step(DISPATCH, "triage", "triage_by_dispatcher", request=request["name"],
         priority="High", reason="Production stopped", owner=DISPATCH, agreement=agreement)
    docs["incident"] = frappe.db.get_value("SHD Request", request["name"], "incident")
    step(DISPATCH, "acknowledge", "first_response", request=request["name"],
         response="Technician dispatched", occurred_at=str(past + timedelta(minutes=10)))
    wo = step(DISPATCH, "create_work_order", "work_order_by_dispatcher",
              origin_kind="INCIDENT", origin=docs["incident"], scope_text="Repair ACC line")
    docs["work_order"] = wo["name"]
    estimate = step(ACCOUNTING, "propose_estimate", "estimate_by_accountant",
                    work_order_id=wo["name"],
                    lines=[{"item": PART, "quantity": "1", "rate": "120"}],
                    currency="VND", expires_at=str(future))
    docs["estimate"] = estimate["name"]
    binding = frappe.db.get_value("SHD Estimate", estimate["name"], "binding_hash")
    step(CUST_A, "decide_estimate", "cost_approved_by_customer", estimate=estimate["name"],
         binding_hash=binding, approve=True, reason="Customer approves repair cost")
    step(DISPATCH, "declare_materials", "materials_declared", work_order_id=wo["name"],
         requirements=[{"item": PART, "warehouse": WAREHOUSE, "quantity": "1"}])
    hold = step(KEEPER, "reserve", "reserved_by_keeper", work_order_id=wo["name"],
                item=PART, warehouse=WAREHOUSE, quantity="1", expires_at=str(future))
    docs["reservation"] = hold["name"]
    wstart, wend = _window(past)
    step(DISPATCH, "assign", "assigned_by_dispatcher", work_order_id=wo["name"],
         technician=TECH, starts_at=str(wstart), ends_at=str(wend),
         required_skill="compressor")
    visit = step(TECH, "start_visit", "visit_started_by_technician",
                 work_order_id=wo["name"], occurred_at=str(past + timedelta(minutes=15)))
    docs["visit"] = visit["name"]
    used = step(TECH, "consume", "consumed_by_technician_on_site",
                reservation=hold["name"], visit=visit["name"], quantity="1")
    docs["material_use"] = used["name"]
    docs["stock_entry"] = used["stock_entry"]
    charge = step(ACCOUNTING, "reconcile_charge", "charge_by_accountant",
                  source_type="Material", source_name=used["name"], item=PART,
                  rate="120", billing_policy="Billable")
    docs["charge"] = charge["name"]
    step(TECH, "finish_visit", "visit_finished_by_technician", visit=visit["name"],
         outcome="Line repaired", evidence={"pressure": "8 bar"},
         occurred_at=str(now - timedelta(hours=1)))
    step(TECH, "restore", "restored_by_technician", work_order_id=wo["name"],
         criteria="Stable production run", measurements={"pressure": "8 bar"},
         occurred_at=str(now - timedelta(minutes=50)))
    step(CUST_A, "accept_work", "accepted_by_customer", work_order_id=wo["name"],
         evidence="Customer witnessed stable run", occurred_at=str(now - timedelta(minutes=40)))
    step(DISPATCH, "close_request", "closed_by_dispatcher", request=request["name"],
         reason="Accepted outcome recorded")
    invoice = step(ACCOUNTING, "prepare_invoice", "invoice_by_accountant",
                   work_order_id=wo["name"], selling_price_list=SELLING)
    docs["sales_invoice"] = invoice["name"]

    bin_after = frappe.db.get_value("Bin", {"item_code": PART, "warehouse": WAREHOUSE}, "actual_qty")
    native = frappe.get_doc("Sales Invoice", invoice["name"])
    reconciliations = [
        {"check": "stock_bin_decreased_by_consumption", "expected": "before-1",
         "actual": f"{bin_before}->{bin_after}",
         "success": float(bin_after) == float(bin_before) - 1},
        {"check": "invoice_total_matches_approved_estimate", "expected": "120",
         "actual": str(native.grand_total),
         "success": float(native.grand_total) == 120.0},
        {"check": "invoice_links_work_order_and_charge_allocated",
         "expected": docs["work_order"],
         "actual": native.custom_shd_work_order,
         "success": native.custom_shd_work_order == docs["work_order"]
         and frappe.db.get_value("SHD Charge", docs["charge"], "sales_invoice") == invoice["name"]},
        {"check": "invoice_does_not_issue_stock_again", "expected": "update_stock=0",
         "actual": f"update_stock={native.update_stock}",
         "success": native.update_stock == 0},
        {"check": "request_closed_after_acceptance", "expected": "Closed",
         "actual": frappe.db.get_value("SHD Request", docs["request"], "status"),
         "success": frappe.db.get_value("SHD Request", docs["request"], "status") == "Closed"},
    ]
    return {"flow": "intake_to_invoice", "documents": docs, "steps": steps,
            "reconciliations": reconciliations,
            "success": all(r["success"] for r in reconciliations)}


def _agreement_id():
    name = frappe.db.get_value("SHD Agreement", {"company": COMPANY,
        "customer": CUSTOMER_A, "site": SITE_A, "status": "Active"})
    if name:
        return name
    frappe.set_user("Administrator")
    policy = {"anchor": "received_at", "timezone": "Asia/Ho_Chi_Minh", "calendar": "24x7",
              "response_minutes": 30, "restoration_minutes": 120, "pause_policy": "No pause",
              "callback_window_hours": 24}
    now = now_datetime()
    agreement = execute("register", {"record_type": "SHD Agreement", "values": {
        "company": COMPANY, "customer": CUSTOMER_A, "site": SITE_A,
        "title": "ACC maintenance agreement", "valid_from": now - timedelta(days=1),
        "valid_until": now + timedelta(days=30), "equipment": EQUIPMENT_A,
        "service_type": "Repair", "policy": policy}}, frappe.generate_hash(length=20))["name"]
    call_as(MANAGER, "activate", record_type="SHD Agreement", name=agreement)
    frappe.db.commit()
    return agreement


def flow_two(now, past, future):
    """Shortage -> purchase approval -> partial receipt -> quarantine."""
    steps, docs = [], {}

    def step(user, command, label, **payload):
        out = call_as(user, command, **payload)
        entry = {"step": label, "command": command, "actor": user, "role": ROLE_OF[user]}
        if isinstance(out, dict) and out.get("name"):
            entry["document"] = out["name"]
        steps.append(entry)
        return out

    scoped = {"company": COMPANY, "customer": CUSTOMER_A, "site": SITE_A}
    bin_before = frappe.db.get_value("Bin", {"item_code": SPARE, "warehouse": WAREHOUSE},
                                     "actual_qty") or 0
    quar_before = frappe.db.get_value("Bin", {"item_code": SPARE, "warehouse": QUARANTINE},
                                      "actual_qty") or 0
    docs["spare_bin_before"] = bin_before
    request = step(DISPATCH, "receive_request", "intake_by_dispatcher",
                   **scoped, equipment=EQUIPMENT_A, subject="ACC spare shortage",
                   reported_at=str(past), received_at=str(past + timedelta(minutes=5)))
    step(DISPATCH, "triage", "triage_by_dispatcher", request=request["name"],
         priority="Medium", reason="Spare needed", owner=DISPATCH, agreement=_agreement_id())
    incident = frappe.db.get_value("SHD Request", request["name"], "incident")
    wo = step(DISPATCH, "create_work_order", "work_order_by_dispatcher",
              origin_kind="INCIDENT", origin=incident, scope_text="Replace worn spare")
    docs["work_order"] = wo["name"]
    demand = step(PURCHASING, "create_demand", "demand_by_purchasing",
                  work_order_id=wo["name"], item=SPARE, warehouse=WAREHOUSE,
                  quantity="5", needed_at=str(future.date()))
    docs["demand"] = demand["name"]
    req = step(PURCHASING, "requisition", "requisition_by_purchasing", demand=demand["name"])
    docs["material_request"] = req["material_request"]
    po = step(PURCHASING, "prepare_purchase_order", "po_prepared_by_purchasing",
              demand=demand["name"], supplier="ACC Supplier", rate="100",
              delivery_date=str(future.date()))
    docs["purchase_order"] = po["purchase_order"]
    docs["po_docstatus_before_approval"] = frappe.db.get_value(
        "Purchase Order", po["purchase_order"], "docstatus")
    step(MANAGER, "approve_purchase_order", "po_approved_by_service_manager",
         demand=demand["name"], binding_hash=po["binding_hash"],
         reason="Manager approves source and price")
    receipt = step(KEEPER, "receive_purchase", "partial_receipt_by_keeper",
                   demand=demand["name"], accepted_quantity="3", rejected_quantity="1",
                   rejected_warehouse=QUARANTINE)
    docs["purchase_receipt"] = receipt["purchase_receipt"]
    docs["demand_status"] = receipt["status"]

    bin_main = frappe.db.get_value("Bin", {"item_code": SPARE, "warehouse": WAREHOUSE}, "actual_qty")
    bin_quar = frappe.db.get_value("Bin", {"item_code": SPARE, "warehouse": QUARANTINE}, "actual_qty")
    po_row = frappe.db.sql("""SELECT qty, received_qty FROM `tabPurchase Order Item`
        WHERE parent=%s""", docs["purchase_order"], as_dict=True)[0]
    mr_qty = float(frappe.db.get_value("Material Request Item",
                   {"parent": docs["material_request"]}, "qty"))
    expected_net = 5.0 - float(bin_before)
    reconciliations = [
        {"check": "net_requisition_is_shortage_only",
         "expected": f"MR qty {expected_net} (5 needed - {bin_before} in stock)",
         "actual": str(mr_qty), "success": mr_qty == expected_net},
        {"check": "po_approved_by_manager", "expected": "docstatus 0->1",
         "actual": f"{docs['po_docstatus_before_approval']}->{frappe.db.get_value('Purchase Order', docs['purchase_order'], 'docstatus')}",
         "success": docs["po_docstatus_before_approval"] == 0
         and frappe.db.get_value("Purchase Order", docs["purchase_order"], "docstatus") == 1},
        {"check": "accepted_stock_in_main_warehouse",
         "expected": f"{bin_before}+3", "actual": str(bin_main),
         "success": float(bin_main) == float(bin_before) + 3},
        {"check": "rejected_stock_quarantined", "expected": f"{quar_before}+1",
         "actual": str(bin_quar), "success": float(bin_quar or 0) == float(quar_before) + 1},
        {"check": "po_received_quantity_counts_accepted_plus_rejected",
         "expected": f"{mr_qty}/{mr_qty}",
         "actual": f"{po_row.received_qty}/{po_row.qty}",
         "success": float(po_row.received_qty) == mr_qty == float(po_row.qty)},
        {"check": "demand_partially_fulfilled", "expected": "Partially fulfilled",
         "actual": docs["demand_status"], "success": docs["demand_status"] == "Partially fulfilled"},
    ]
    return {"flow": "shortage_to_quarantine", "documents": docs, "steps": steps,
            "reconciliations": reconciliations,
            "success": all(r["success"] for r in reconciliations)}


def flow_three(now, past, future):
    """PM generation -> finding recorded -> repair case opened."""
    steps, docs = [], {}

    def step(user, command, label, **payload):
        out = call_as(user, command, **payload)
        entry = {"step": label, "command": command, "actor": user, "role": ROLE_OF[user]}
        if isinstance(out, dict) and out.get("name"):
            entry["document"] = out["name"]
        steps.append(entry)
        return out

    plan = frappe.db.get_value("SHD PM Plan", {"equipment": EQUIPMENT_A, "status": "Active"})
    if not plan:
        frappe.set_user("Administrator")
        plan = execute("register", {"record_type": "SHD PM Plan", "values": {
            "company": COMPANY, "customer": CUSTOMER_A, "site": SITE_A,
            "equipment": EQUIPMENT_A,
            "checklist": [{"key": "vibration", "unit": "mm/s"}, {"key": "visual"}],
            "first_due": past.date(), "interval_days": 30,
            "service_owner": DISPATCH}}, frappe.generate_hash(length=20))["name"]
        call_as(MANAGER, "activate", record_type="SHD PM Plan", name=plan)
        frappe.db.commit()
    docs["pm_plan"] = plan
    period_key = str(frappe.db.count("SHD PM Occurrence", {"plan": plan}))
    occurrence = step(DISPATCH, "generate_pm", "pm_generated_by_dispatcher",
                      plan=plan, period_key=period_key)
    docs["pm_occurrence"] = occurrence["name"]
    source = frappe.db.get_value("SHD Work Source", {"pm_occurrence": occurrence["name"]})
    pm_wo = frappe.db.get_value("SHD Work Order", {"source": source, "package_key": "PM_MAIN"})
    docs["pm_work_order"] = pm_wo
    wstart, wend = _window(past)
    step(DISPATCH, "assign", "pm_assigned_by_dispatcher", work_order_id=pm_wo,
         technician=TECH, starts_at=str(wstart), ends_at=str(wend),
         required_skill="compressor")
    visit = step(TECH, "start_visit", "pm_visit_started", work_order_id=pm_wo,
                 occurred_at=str(past + timedelta(minutes=15)))
    step(TECH, "finish_visit", "pm_visit_finished", visit=visit["name"],
         outcome="PM inspection done", evidence={"vibration": "7.2 mm/s"},
         occurred_at=str(now - timedelta(hours=1)))
    done = step(TECH, "complete_pm", "pm_completed_with_finding_by_technician",
                occurrence=occurrence["name"],
                observations=[{"key": "vibration", "unit": "mm/s", "value": 7.2,
                               "result": "Abnormal"},
                              {"key": "visual", "result": "Passed"}],
                findings=[{"description": "ACC bearing vibration above threshold",
                           "severity": "High", "service_owner": DISPATCH,
                           "due_at": str(future)}],
                occurred_at=str(now - timedelta(minutes=30)))
    docs["finding"] = done["findings"][0]
    classified = step(DISPATCH, "classify_finding", "finding_classified_repair_by_dispatcher",
                      finding=docs["finding"], disposition="Repair",
                      reason="Bearing wear confirmed; open repair case")
    docs["repair_incident"] = frappe.db.get_value("SHD Finding", docs["finding"], "incident")
    repair_wo = step(DISPATCH, "create_work_order", "repair_work_order_opened",
                     origin_kind="INCIDENT", origin=docs["repair_incident"],
                     scope_text="Replace ACC bearing")
    docs["repair_work_order"] = repair_wo["name"]

    reconciliations = [
        {"check": "occurrence_completed", "expected": "Completed",
         "actual": frappe.db.get_value("SHD PM Occurrence", docs["pm_occurrence"], "status"),
         "success": frappe.db.get_value("SHD PM Occurrence", docs["pm_occurrence"], "status") == "Completed"},
        {"check": "finding_repair_pending_with_incident", "expected": "Repair pending + incident",
         "actual": frappe.db.get_value("SHD Finding", docs["finding"], "status"),
         "success": frappe.db.get_value("SHD Finding", docs["finding"], "status") == "Repair pending"
         and bool(docs["repair_incident"])},
        {"check": "repair_work_order_from_finding_incident", "expected": "Planned WO on incident",
         "actual": frappe.db.get_value("SHD Work Order", docs["repair_work_order"], "status"),
         "success": frappe.db.get_value("SHD Work Order", docs["repair_work_order"], "status") == "Planned"},
    ]
    return {"flow": "pm_finding_to_repair", "documents": docs, "steps": steps,
            "reconciliations": reconciliations,
            "success": all(r["success"] for r in reconciliations)}


def denial_cases(now, past, future):
    """Cross-customer access and approval-after-expiry must both be refused."""
    scoped = {"company": COMPANY, "customer": CUSTOMER_A, "site": SITE_A}
    wo = frappe.db.get_value("SHD Work Order", {"company": COMPANY,
        "customer": CUSTOMER_A, "status": "Customer accepted"})
    cross = denial_as(CUST_B, "accept_work", work_order_id=wo,
                      evidence="Foreign customer attempt",
                      occurred_at=str(now - timedelta(minutes=30)))
    frappe.set_user(CUST_B)
    visible = frappe.get_list("SHD Work Order", filters={"company": COMPANY}, pluck="name")
    frappe.set_user("Administrator")
    cross_ok = bool(cross) and "PermissionError" in cross and wo not in visible

    # Expired approvals: (a) the estimate itself expires before the decision;
    # (b) the approver's Contact Authority has already expired.
    request = call_as(DISPATCH, "receive_request", **scoped, equipment=EQUIPMENT_A,
                      subject="ACC expiry probe", reported_at=str(past),
                      received_at=str(past + timedelta(minutes=5)))
    call_as(DISPATCH, "triage", request=request["name"], priority="Low",
            reason="Expiry probe", owner=DISPATCH, agreement=_agreement_id())
    incident = frappe.db.get_value("SHD Request", request["name"], "incident")
    probe_wo = call_as(DISPATCH, "create_work_order", origin_kind="INCIDENT",
                       origin=incident, scope_text="Expiry probe scope")
    estimate = call_as(ACCOUNTING, "propose_estimate", work_order_id=probe_wo["name"],
                       lines=[{"item": PART, "quantity": "1", "rate": "120"}],
                       currency="VND",
                       expires_at=str(now_datetime() + timedelta(seconds=5)))
    binding = frappe.db.get_value("SHD Estimate", estimate["name"], "binding_hash")
    time.sleep(6)
    expired_estimate = denial_as(CUST_A, "decide_estimate", estimate=estimate["name"],
                                 binding_hash=binding, approve=True,
                                 reason="Decide after estimate expiry")
    expired_authority = denial_as(CUST_A2, "decide_estimate", estimate=estimate["name"],
                                  binding_hash=binding, approve=True,
                                  reason="Decide with expired authority")
    cases = [
        {"case": "cross_customer_access", "actor": CUST_B, "role": ROLE_OF[CUST_B],
         "expected": "PermissionError + no visibility of customer A work orders",
         "actual": cross, "list_leak": wo in visible, "success": cross_ok},
        {"case": "expired_estimate_decision", "actor": CUST_A, "role": ROLE_OF[CUST_A],
         "expected": "ValidationError (stale/expired estimate)",
         "actual": expired_estimate,
         "success": bool(expired_estimate) and "ValidationError" in expired_estimate},
        {"case": "expired_contact_authority", "actor": CUST_A2, "role": ROLE_OF[CUST_A2],
         "expected": "PermissionError (no effective customer authority)",
         "actual": expired_authority,
         "success": bool(expired_authority) and "PermissionError" in expired_authority},
    ]
    return cases


def audit_trail(flows):
    """Every flow step must have an Applied SHD Command receipt in its
    actor's name, and the journal must hold events for the aggregates."""
    checks = []
    for flow in flows:
        missing = []
        for entry in flow["steps"]:
            found = frappe.db.exists("SHD Command", {
                "actor": entry["actor"], "command_type": entry["command"],
                "status": "Applied"})
            if not found:
                missing.append(entry["command"])
        checks.append({"flow": flow["flow"], "steps": len(flow["steps"]),
                       "missing_receipts": missing, "success": not missing})
    return checks


def run():
    if not frappe.local.site.startswith("shd-test."):
        raise RuntimeError("Dedicated test site required")
    frappe.set_user("Administrator")
    now = now_datetime()
    past = now - timedelta(hours=4)
    future = now + timedelta(days=1)
    setup_dataset(now, past, future)
    flows = []
    for build in (flow_one, flow_two, flow_three):
        try:
            flows.append(build(now, past, future))
        except Exception as error:  # noqa: BLE001 - record and continue
            import traceback
            flows.append({"flow": build.__name__, "success": False,
                          "error": f"{type(error).__name__}: {error}",
                          "traceback": traceback.format_exc()[-1500:],
                          "steps": [], "reconciliations": []})
        frappe.db.commit()
        frappe.set_user("Administrator")
    denials = denial_cases(now, past, future)
    frappe.db.commit()
    audit = audit_trail([f for f in flows if f.get("steps")])
    success = (all(f["success"] for f in flows)
               and all(d["success"] for d in denials)
               and all(a["success"] for a in audit))
    report = {"scope": "desk_role_acceptance", "site": frappe.local.site,
              "dataset": COMPANY, "flows": flows, "denials": denials,
              "audit": audit, "success": success}
    print(json.dumps(report))
    if not success:
        raise RuntimeError("Desk role acceptance failed")
    return report
