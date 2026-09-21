import os
import urllib.request
import urllib.parse
import json
import time

# Auto-load .env file if present
_env_path = os.path.join(os.path.dirname(__file__), "..", ".env")
if os.path.exists(_env_path):
    with open(_env_path, "r", encoding="utf-8") as _f:
        for _line in _f:
            _line = _line.strip()
            if _line and not _line.startswith("#") and "=" in _line:
                _k, _v = _line.split("=", 1)
                os.environ.setdefault(_k.strip(), _v.strip())

BASE_URL = os.getenv("FRAPPE_BASE_URL", "https://smarthelpdesk23mainternace.s.frappe.cloud")
API_KEY = os.getenv("FRAPPE_API_KEY", "")
API_SECRET = os.getenv("FRAPPE_API_SECRET", "")
COMPANY = os.getenv("FRAPPE_COMPANY", "SmartHelpDeskBaro")
COMPANY_ABBR = os.getenv("FRAPPE_COMPANY_ABBR", "SBN")

HEADERS = {
    "Authorization": f"token {API_KEY}:{API_SECRET}",
    "Content-Type": "application/json",
    "Accept": "application/json"
}

def request(method, path, data=None):
    url = f"{BASE_URL}{path}"
    req = urllib.request.Request(url, headers=HEADERS, method=method)
    body = json.dumps(data).encode("utf-8") if data is not None else None
    try:
        with urllib.request.urlopen(req, data=body, timeout=30) as resp:
            content = resp.read().decode("utf-8")
            return json.loads(content) if content else {}
    except urllib.error.HTTPError as e:
        err_msg = e.read().decode("utf-8")
        try:
            err_json = json.loads(err_msg)
            return {"_error": True, "status": e.code, "message": err_json}
        except Exception:
            return {"_error": True, "status": e.code, "message": err_msg}
    except Exception as e:
        return {"_error": True, "status": 0, "message": str(e)}

def exists_doc(doctype, name):
    quoted_dt = urllib.parse.quote(doctype)
    quoted_name = urllib.parse.quote(name)
    res = request("GET", f"/api/resource/{quoted_dt}/{quoted_name}")
    if res.get("_error") and res.get("status") == 404:
        return False
    if "data" in res:
        return True
    return False

def get_doc(doctype, name):
    quoted_dt = urllib.parse.quote(doctype)
    quoted_name = urllib.parse.quote(name)
    res = request("GET", f"/api/resource/{quoted_dt}/{quoted_name}")
    if res.get("_error"):
        return None
    return res.get("data")

def create_doc(doctype, data, fail_on_exist=False):
    quoted_dt = urllib.parse.quote(doctype)
    res = request("POST", f"/api/resource/{quoted_dt}", data)
    if res.get("_error"):
        if res.get("status") == 409 or "Duplicate" in str(res.get("message")):
            if fail_on_exist:
                raise Exception(f"Duplicate {doctype}: {res}")
            print(f"[EXIST] {doctype} already exists.")
            return None
        raise Exception(f"Failed to create {doctype}: {res}")
    return res.get("data")

def update_doc(doctype, name, data):
    quoted_dt = urllib.parse.quote(doctype)
    quoted_name = urllib.parse.quote(name)
    res = request("PUT", f"/api/resource/{quoted_dt}/{quoted_name}", data)
    if res.get("_error"):
        raise Exception(f"Failed to update {doctype} {name}: {res}")
    return res.get("data")

def submit_doc(doctype, name):
    return update_doc(doctype, name, {"docstatus": 1})

def list_docs(doctype, filters=None, fields=None, limit=50):
    quoted_dt = urllib.parse.quote(doctype)
    params = [f"limit_page_length={limit}"]
    if filters:
        params.append(f"filters={urllib.parse.quote(json.dumps(filters))}")
    if fields:
        params.append(f"fields={urllib.parse.quote(json.dumps(fields))}")
    path = f"/api/resource/{quoted_dt}?" + "&".join(params)
    res = request("GET", path)
    if res.get("_error"):
        raise Exception(f"Failed to list {doctype}: {res}")
    return res.get("data", [])
