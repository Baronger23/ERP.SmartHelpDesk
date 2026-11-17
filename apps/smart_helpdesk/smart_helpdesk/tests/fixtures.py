"""Pre-web fixtures for the dedicated bench test site.

The integration suites historically created their own master data inside
``setUpClass`` — after the web processes had already loaded. This module
moves that preparation into an explicit, idempotent step that the bench
test runner executes BEFORE the web server starts, so fixtures, the
buying price / currency setup and the HTTP token all exist before the
first HTTP worker serves a request. Every record mirrors the names and
values the suites look for, and every creation is guarded by an
existence check, so seeding early never conflicts with the suites' own
``setUpClass`` guards.
"""
import json
from datetime import timedelta

import frappe
from frappe.utils import now_datetime

from smart_helpdesk.api import execute

COMPANY = "SHD Integration"
CUSTOMER = "SHD Test Customer"
WAREHOUSE = "Stores - SHT"
PART = "SHD-TEST-PART"
LABOR = "SHD-TEST-LABOR"
SELLING_PRICE_LIST = "SHD Selling VND"
BUYING_PRICE_LIST = "SHD Buying VND"
BUYING_RATE = 100  # matches the rate the purchase test passes and the opening receipt


def _require_test_site():
    if not frappe.local.site.startswith("shd-test."):
        raise RuntimeError("Fixtures require a dedicated shd-test.* site")


def seed():
    _require_test_site()
    frappe.set_user("Administrator")
    created = []

    def ensure(doctype, name, doc):
        if not frappe.db.exists(doctype, name):
            frappe.get_doc(doc).insert()
            created.append(f"{doctype}:{name}")

    if not frappe.db.exists("Warehouse Type", "Transit"):
        from erpnext.setup.setup_wizard.operations.install_fixtures import install
        install("Vietnam")
        created.append("erpnext_fixtures:Vietnam")

    # Currency fixture: the whole test economy runs in VND.
    if frappe.db.exists("Currency", "VND") and not frappe.db.get_value("Currency", "VND", "enabled"):
        frappe.db.set_value("Currency", "VND", "enabled", 1)
        created.append("Currency:VND(enabled)")

    ensure("Company", COMPANY, {"doctype": "Company", "company_name": COMPANY, "abbr": "SHT",
                                "country": "Vietnam", "default_currency": "VND"})
    ensure("Customer", CUSTOMER, {"doctype": "Customer", "customer_name": CUSTOMER,
                                  "customer_type": "Company", "customer_group": "Commercial",
                                  "territory": "All Territories"})
    ensure("Warehouse", WAREHOUSE, {"doctype": "Warehouse", "warehouse_name": "Stores",
                                    "company": COMPANY})
    ensure("Price List", SELLING_PRICE_LIST, {"doctype": "Price List",
                                              "price_list_name": SELLING_PRICE_LIST, "enabled": 1,
                                              "selling": 1, "currency": "VND"})
    # Buying price fixture: purchase price list + the part's buying Item Price.
    ensure("Price List", BUYING_PRICE_LIST, {"doctype": "Price List",
                                             "price_list_name": BUYING_PRICE_LIST, "enabled": 1,
                                             "buying": 1, "currency": "VND"})
    year = now_datetime().year
    ensure("Fiscal Year", str(year), {"doctype": "Fiscal Year", "year": str(year),
                                      "year_start_date": f"{year}-01-01",
                                      "year_end_date": f"{year}-12-31"})
    for code, stock in ((PART, 1), (LABOR, 0)):
        ensure("Item", code, {"doctype": "Item", "item_code": code, "item_name": code,
                              "item_group": "Products", "stock_uom": "Nos",
                              "is_stock_item": stock})
    if not frappe.db.exists("Item Price", {"item_code": PART, "price_list": BUYING_PRICE_LIST}):
        frappe.get_doc({"doctype": "Item Price", "item_code": PART,
                        "price_list": BUYING_PRICE_LIST, "price_list_rate": BUYING_RATE,
                        "currency": "VND", "buying": 1}).insert()
        created.append(f"Item Price:{PART}@{BUYING_PRICE_LIST}={BUYING_RATE} VND")
    if not frappe.db.exists("Bin", {"item_code": PART, "warehouse": WAREHOUSE}):
        receipt = frappe.get_doc({"doctype": "Stock Entry", "stock_entry_type": "Material Receipt",
                                  "company": COMPANY,
                                  "items": [{"item_code": PART, "qty": 2,
                                             "t_warehouse": WAREHOUSE,
                                             "basic_rate": BUYING_RATE}]})
        receipt.insert()
        receipt.submit()
        created.append("Stock Entry:opening 2 x " + PART)
    for user, role in (("shd.tech@example.invalid", "AIS Field Technician"),
                       ("shd.customer@example.invalid", "AIS Customer Portal"),
                       ("shd.dispatch@example.invalid", "AIS Dispatcher"),
                       ("shd.accounting@example.invalid", "AIS Billing Accountant")):
        ensure("User", user, {"doctype": "User", "email": user,
                              "first_name": user.split(".")[1].split("@")[0],
                              "send_welcome_email": 0, "roles": [{"role": role}]})
    tech = "shd.tech@example.invalid"
    if not frappe.db.exists("SHD Technician", {"user": tech}):
        execute("register", {"record_type": "SHD Technician",
                             "values": {"company": COMPANY, "user": tech,
                                        "skills": ["compressor"],
                                        "available_from": now_datetime() - timedelta(days=365),
                                        "available_until": now_datetime() + timedelta(days=365)}},
                frappe.generate_hash(length=20))
        created.append("SHD Technician:" + tech)
    frappe.db.commit()
    report = {"scope": "pre_web_fixtures", "site": frappe.local.site, "created": created,
              "buying_price": {"item": PART, "price_list": BUYING_PRICE_LIST,
                               "rate": BUYING_RATE, "currency": "VND"},
              "success": True}
    print(json.dumps(report))
    return report


def prepare_http_token():
    """Provision the Administrator API token in the database before the web
    server starts, so authenticated HTTP checks never depend on a token
    created lazily after workers are already serving."""
    _require_test_site()
    frappe.set_user("Administrator")
    user = frappe.get_doc("User", "Administrator")
    user.api_key = frappe.generate_hash(length=15)
    user.api_secret = frappe.generate_hash(length=24)
    user.save()
    frappe.db.commit()
    report = {"scope": "pre_web_http_token", "site": frappe.local.site,
              "ready": True, "success": True}
    print(json.dumps(report))
    return report
