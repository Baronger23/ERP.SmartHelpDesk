"""Exercise Gunicorn's authenticated HTTP boundary on the dedicated test site."""
import json
from urllib.request import Request, urlopen
from urllib.error import HTTPError
import frappe


def run():
    if not frappe.local.site.startswith("shd-test."):
        raise RuntimeError("Dedicated test site required")
    frappe.set_user("Administrator")
    user = frappe.get_doc("User", "Administrator")
    user.api_key = frappe.generate_hash(length=15)
    secret = frappe.generate_hash(length=24)
    user.api_secret = secret
    user.save()
    frappe.db.commit()
    headers = {"Host": frappe.local.site, "Authorization": "token " + user.api_key + ":" + secret,
               "Content-Type": "application/json"}
    def request(method, path, payload=None, authenticated=True):
        request_headers = dict(headers)
        if not authenticated:
            request_headers.pop("Authorization")
        req = Request("http://127.0.0.1:8000" + path, method=method, headers=request_headers,
                      data=json.dumps(payload).encode() if payload is not None else None)
        try:
            with urlopen(req, timeout=30) as response:
                return response.status, json.load(response)
        except HTTPError as error:
            return error.code, json.loads(error.read())
    path = "/api/method/smart_helpdesk.api.execute"
    key = frappe.generate_hash(length=24)
    payload = {"command": "register", "idempotency_key": key, "payload": {"record_type": "SHD Site", "values": {
        "company": "SHD Integration", "customer": "SHD Test Customer", "title": "HTTP boundary smoke"}}}
    status, first = request("POST", path, payload)
    retry_status, second = request("POST", path, payload)
    payload["payload"]["values"]["title"] = "Changed binding"
    conflict, _ = request("POST", path, payload)
    forbidden_method, _ = request("GET", path)
    guest, _ = request("GET", "/api/method/smart_helpdesk.api.catalog", authenticated=False)
    checks = {"authenticated_write": status == 200, "http_retry_same_id": retry_status == 200 and first.get("message") == second.get("message"),
              "changed_payload_conflict": conflict == 417, "get_cannot_mutate": forbidden_method in (403, 405),
              "guest_denied": guest in (401, 403)}
    report = {"scope": "live_authenticated_http", "site": frappe.local.site, "checks": checks, "success": all(checks.values())}
    print(json.dumps(report))
    if not report["success"]:
        raise RuntimeError("HTTP boundary checks failed")
    return report
