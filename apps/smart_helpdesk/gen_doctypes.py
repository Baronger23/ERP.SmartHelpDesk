#!/usr/bin/env python3
"""Generate standard Frappe DocType JSON tree from schema.py (single source).

Replicates exactly the mutations smart_helpdesk.install.sync applied when it
created the DocTypes programmatically, so the generated JSON definitions are
behavior-identical:
- module "Smart Helpdesk", autoname "hash" ("prompt" for SHD Command),
  track_changes=1, allow_rename=0, sort by modified DESC
- fields = COMMON + schema fields (minus the self-link 'site' on SHD Site;
  SHD Command.company not required)
- every field read_only=1; cost_rate/unit_cost permlevel=1;
  status/customer/company/title/subject in_list_view=1
- permissions: read-only for all ROLES; permlevel-1 read for Service Manager
  and Billing Accountant when the DocType has a permlevel-1 field.
Output: <app>/smart_helpdesk/smart_helpdesk/doctype/<slug>/<slug>.json + <slug>.py stub.
"""
import json
import sys
from pathlib import Path

APP_DIR = Path(__file__).resolve().parent / "smart_helpdesk"
sys.path.insert(0, str(Path(__file__).resolve().parent))
from smart_helpdesk.schema import COMMON, ROLES, SCHEMAS  # noqa: E402


def slug(name: str) -> str:
    return name.lower().replace(" ", "_")


def build_doctype(name: str, extra: list) -> dict:
    fields = [dict(f) for f in COMMON + extra
              if not (name == "SHD Site" and f["fieldname"] == "site")]
    for f in fields:
        if name == "SHD Command" and f["fieldname"] == "company":
            f["reqd"] = 0
        f["read_only"] = 1
        if f["fieldname"] in ("cost_rate", "unit_cost"):
            f["permlevel"] = 1
        if f["fieldname"] in ("status", "customer", "company", "title", "subject"):
            f["in_list_view"] = 1
    permissions = [{"role": role, "read": 1, "export": 0, "print": 0} for role in ROLES]
    if any(f.get("permlevel") == 1 for f in fields):
        permissions += [{"role": role, "permlevel": 1, "read": 1}
                        for role in ("AIS Service Manager", "AIS Billing Accountant")]
    return {
        "actions": [],
        "allow_rename": 0,
        "autoname": "prompt" if name == "SHD Command" else "hash",
        "creation": "2026-10-15 00:00:00.000000",
        "doctype": "DocType",
        "engine": "InnoDB",
        "field_order": [f["fieldname"] for f in fields],
        "fields": fields,
        "grid_page_length": 50,
        "index_web_pages_for_search": 1,
        "links": [],
        "modified": "2026-10-15 00:00:00.000000",
        "modified_by": "Administrator",
        "module": "Smart Helpdesk",
        "name": name,
        "owner": "Administrator",
        "permissions": permissions,
        "row_format": "Dynamic",
        "sort_field": "modified",
        "sort_order": "DESC",
        "states": [],
        "track_changes": 1,
    }


CONTROLLER = '''# Copyright (c) 2026, AIS and contributors
# For license information, please see license.txt

from frappe.model.document import Document


class {cls}(Document):
    pass
'''


def main() -> None:
    base = APP_DIR / "smart_helpdesk" / "doctype"
    for name, extra in SCHEMAS.items():
        s = slug(name)
        folder = base / s
        folder.mkdir(parents=True, exist_ok=True)
        (folder / "__init__.py").write_text("", encoding="utf-8")
        doc = build_doctype(name, extra)
        (folder / f"{s}.json").write_text(
            json.dumps(doc, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
        cls = name.replace(" ", "").replace("-", "")
        (folder / f"{s}.py").write_text(CONTROLLER.format(cls=cls), encoding="utf-8")
        print(f"{name}: {len(doc['fields'])} fields, {len(doc['permissions'])} perms")
    print(f"TOTAL: {len(SCHEMAS)} doctypes -> {base}")


if __name__ == "__main__":
    main()
