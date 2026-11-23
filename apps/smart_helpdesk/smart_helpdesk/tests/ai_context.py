"""Exercise the US-42 HTTP contract on the role-acceptance dataset."""
import json
from datetime import timedelta
from urllib.error import HTTPError
from urllib.request import Request, urlopen

import frappe
from frappe.utils import now_datetime

from smart_helpdesk.tests import acceptance

TECH_B = "acc.tech.b@example.invalid"
EQUIPMENT_CODE = "ACC-EQ-001"
QUESTION = "Máy ACC-R1 rung cao. SOP và lịch sử ca trước ghi nhận gì?"
METHOD = "/api/method/smart_helpdesk.ai_context.get_context"


def _scope(customer):
    company = acceptance.COMPANY
    site = frappe.db.get_value("SHD Site", {"company": company, "customer": customer})
    if not site:
        raise RuntimeError("Run the Desk role acceptance suite first")
    return {"company": company, "customer": customer, "site": site}


def _register(doctype, lookup, values):
    existing = frappe.db.get_value(doctype, lookup)
    if existing:
        return existing
    return acceptance.call_as("Administrator", "register", record_type=doctype, values=values)["name"]


def _knowledge(scoped, label, model, start, end, status):
    reference = f"SHD AI-1 synthetic SOP / {label} / section 1"
    name = _register("SHD Knowledge", {"source_reference": reference}, {
        **scoped, "model": model, "title": f"AI-1 vibration SOP ({label})",
        "document_version": "1.0", "effective_from": start, "effective_until": end,
        "source_reference": reference,
        "content": "<p>Đối chiếu số đo rung với lần kiểm tra trước. "
                   "Nếu số đo bất thường, ghi nhận và yêu cầu trưởng nhóm xác minh.</p>",
    })
    current = frappe.db.get_value("SHD Knowledge", name, "status")
    if current == "Draft" and status != "Draft":
        acceptance.call_as(acceptance.MANAGER, "activate", record_type="SHD Knowledge", name=name)
        current = "Published"
    if current == "Published" and status == "Revoked":
        acceptance.call_as(acceptance.MANAGER, "revoke", record_type="SHD Knowledge",
                           name=name, reason="Synthetic revocation test")
    return name


def _seed():
    a = _scope(acceptance.CUSTOMER_A)
    b = _scope(acceptance.CUSTOMER_B)
    now = now_datetime()
    past = now - timedelta(days=1)
    future = now + timedelta(days=365)
    acceptance._ensure("User", TECH_B, {"doctype": "User", "email": TECH_B,
        "first_name": "AI-1 technician B", "send_welcome_email": 0,
        "roles": [{"role": "AIS Field Technician"}]})
    _register("SHD Access Grant", {**b, "user": TECH_B, "resource_type": "Service"},
              {**b, "user": TECH_B, "resource_type": "Service", "actions": "read"})
    _register("SHD Equipment", {"equipment_code": "ACC-EQ-B-AI1"},
              {**b, "equipment_code": "ACC-EQ-B-AI1", "model": "ACC-R1", "serial_number": "ACC-AI1-B"})
    active = _knowledge(a, "approved", "ACC-R1", past, future, "Published")
    _knowledge(a, "draft", "ACC-R1", past, future, "Draft")
    _knowledge(a, "revoked", "ACC-R1", past, future, "Revoked")
    _knowledge(a, "expired", "ACC-R1", past - timedelta(days=1), past, "Published")
    _knowledge(a, "future", "ACC-R1", future, future + timedelta(days=1), "Published")
    _knowledge(a, "other-model", "ACC-WRONG", past, future, "Published")
    _knowledge(b, "other-customer", "ACC-R1", past, future, "Published")
    return active


def _token(user):
    account = frappe.get_doc("User", user)
    account.api_key = account.api_key or frappe.generate_hash(length=15)
    secret = frappe.generate_hash(length=24)
    account.api_secret = secret
    account.save()
    return f"token {account.api_key}:{secret}"


def _request(payload, token=None, method="POST"):
    headers = {"Host": frappe.local.site, "Content-Type": "application/json"}
    if token:
        headers["Authorization"] = token
    request = Request("http://127.0.0.1:8000" + METHOD, headers=headers, method=method,
                      data=json.dumps(payload).encode() if method == "POST" else None)
    try:
        with urlopen(request, timeout=30) as response:
            return response.status, json.load(response)
    except HTTPError as error:
        return error.code, json.load(error)


def run():
    if not frappe.local.site.startswith("shd-test."):
        raise RuntimeError("Dedicated test site required")
    frappe.set_user("Administrator")
    sop = _seed()
    tech_a_token = _token(acceptance.TECH)
    tech_b_token = _token(TECH_B)
    customer_token = _token(acceptance.CUST_A)
    frappe.db.commit()

    request = {"equipment_code": EQUIPMENT_CODE, "question": QUESTION}
    status, response = _request(request, tech_a_token)
    context = response.get("message") if status == 200 else {}
    equipment = context.get("equipment", {})
    orders = context.get("history", {}).get("work_orders", {}).get("items", [])
    findings = context.get("history", {}).get("findings", {}).get("items", [])
    knowledge = context.get("knowledge", {}).get("items", [])
    b_status, b_response = _request({**request, "equipment_code": "ACC-EQ-B-AI1"}, tech_b_token)
    denied = _request({**request, "customer": acceptance.CUSTOMER_A}, tech_b_token)
    unknown = _request({**request, "equipment_code": "ACC-NOT-FOUND"}, tech_b_token)
    checks = {
        "equipment_with_source_revision": (status == 200 and context.get("contract_version") == "1.0"
                                           and equipment.get("equipment_code") == EQUIPMENT_CODE
                                           and equipment.get("model") == "ACC-R1" and bool(equipment.get("revision"))),
        "repair_and_pm_history": (any(visit["outcome"] == "Line repaired" and visit["revision"]
                                      for order in orders for visit in order["visits"]["items"])
                                  and any("vibration" in finding["description"] and finding["revision"]
                                          for finding in findings)),
        "unassigned_orders_excluded": bool(orders) and all(
            frappe.db.get_value("SHD Work Order", order["name"], "technician") == acceptance.TECH for order in orders
        ),
        "only_eligible_sop_with_citation": ([item["name"] for item in knowledge] == [sop]
                                           and knowledge[0]["document_version"] == "1.0"
                                           and bool(knowledge[0]["source_reference"])
                                           and bool(knowledge[0]["content_text"])
                                           and "<p>" not in knowledge[0]["content_text"]),
        "scope_and_existence_protected": (denied[0] == unknown[0] == 403
                                          and denied[1].get("exception") == unknown[1].get("exception")
                                          and "message" not in denied[1]),
        "no_knowledge_grant_returns_empty": (b_status == 200
                                             and b_response["message"]["knowledge"] == {"items": [], "has_more": False}),
        "customer_role_denied": _request(request, customer_token)[0] == 403,
        "guest_denied": _request(request)[0] in (401, 403),
        "get_denied": _request(request, tech_a_token, "GET")[0] in (403, 405),
        "blank_question_rejected": _request({**request, "question": " "}, tech_a_token)[0] == 417,
    }
    report = {"scope": "live_ai1_erp_context", "site": frappe.local.site, "checks": checks,
              "success": all(checks.values())}
    print(json.dumps(report))
    return report
