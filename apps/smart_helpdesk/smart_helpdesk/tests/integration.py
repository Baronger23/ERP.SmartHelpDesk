"""Real ERPNext/MariaDB integration tests. Run only on the isolated shd-test site."""
import json
import threading
import unittest
from concurrent.futures import ThreadPoolExecutor
from datetime import timedelta
import frappe
from frappe.utils import now_datetime
from smart_helpdesk.api import execute
from smart_helpdesk.core import data


def call(command, key=None, **payload):
    return execute(command, payload, key or frappe.generate_hash(length=20))


class BusinessIntegration(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if not frappe.local.site.startswith("shd-test."):
            raise RuntimeError("Tests require a dedicated shd-test.* site")
        frappe.set_user("Administrator")
        if not frappe.db.exists("Warehouse Type", "Transit"):
            from erpnext.setup.setup_wizard.operations.install_fixtures import install
            install("Vietnam")
        cls.company = "SHD Integration"
        if not frappe.db.exists("Company", cls.company):
            frappe.get_doc({"doctype": "Company", "company_name": cls.company, "abbr": "SHT",
                           "country": "Vietnam", "default_currency": "VND"}).insert()
        if not frappe.db.exists("Customer", "SHD Test Customer"):
            frappe.get_doc({"doctype": "Customer", "customer_name": "SHD Test Customer", "customer_type": "Company",
                           "customer_group": "Commercial", "territory": "All Territories"}).insert()
        cls.customer = "SHD Test Customer"
        cls.warehouse = "Stores - SHT"
        if not frappe.db.exists("Warehouse", cls.warehouse):
            frappe.get_doc({"doctype": "Warehouse", "warehouse_name": "Stores", "company": cls.company}).insert()
        cls.part = "SHD-TEST-PART"
        if not frappe.db.exists("Price List", "SHD Selling VND"):
            frappe.get_doc({"doctype": "Price List", "price_list_name": "SHD Selling VND", "enabled": 1,
                           "selling": 1, "currency": "VND"}).insert()
        year = now_datetime().year
        if not frappe.db.exists("Fiscal Year", str(year)):
            frappe.get_doc({"doctype": "Fiscal Year", "year": str(year),
                "year_start_date": f"{year}-01-01", "year_end_date": f"{year}-12-31"}).insert()
        for code, stock in ((cls.part, 1), ("SHD-TEST-LABOR", 0)):
            if not frappe.db.exists("Item", code):
                frappe.get_doc({"doctype": "Item", "item_code": code, "item_name": code,
                    "item_group": "Products", "stock_uom": "Nos", "is_stock_item": stock}).insert()
        if not frappe.db.exists("Bin", {"item_code": cls.part, "warehouse": cls.warehouse}):
            receipt = frappe.get_doc({"doctype": "Stock Entry", "stock_entry_type": "Material Receipt", "company": cls.company,
                "items": [{"item_code": cls.part, "qty": 2, "t_warehouse": cls.warehouse, "basic_rate": 100}]})
            receipt.insert()
            receipt.submit()
        for user, role in (("shd.tech@example.invalid", "AIS Field Technician"),
                           ("shd.customer@example.invalid", "AIS Customer Portal"),
                           ("shd.dispatch@example.invalid", "AIS Dispatcher"),
                           ("shd.accounting@example.invalid", "AIS Billing Accountant")):
            if not frappe.db.exists("User", user):
                frappe.get_doc({"doctype": "User", "email": user, "first_name": user.split(".")[1].split("@")[0],
                    "send_welcome_email": 0, "roles": [{"role": role}]}).insert()
        cls.tech = "shd.tech@example.invalid"
        if not frappe.db.exists("SHD Technician", {"user": cls.tech}):
            call("register", record_type="SHD Technician", values={"company": cls.company, "user": cls.tech,
                "skills": ["compressor"], "available_from": now_datetime() - timedelta(days=365),
                "available_until": now_datetime() + timedelta(days=365)})
        frappe.db.commit()

    def setUp(self):
        frappe.set_user("Administrator")
        frappe.db.savepoint("business_case")
        self.addCleanup(self.cleanup_case)
        self.base = {"company": self.company, "customer": self.customer}
        self.site = call("register", record_type="SHD Site", values={**self.base, "title": "Factory A"})["name"]
        self.scoped = {**self.base, "site": self.site}
        self.equipment = call("register", record_type="SHD Equipment", values={**self.scoped,
            "equipment_code": frappe.generate_hash(length=12), "model": "TEST-R1", "serial_number": "TEST-SERIAL"})["name"]
        call("register", record_type="SHD Compatibility", values={**self.scoped, "model": "TEST-R1", "item": self.part,
            "evidence": "Synthetic test manufacturer compatibility"})
        self.now = now_datetime()
        self.past = self.now - timedelta(hours=4)
        self.future = self.now + timedelta(days=1)
        self.policy = {"anchor": "received_at", "timezone": "Asia/Ho_Chi_Minh", "calendar": "24x7",
            "response_minutes": 30, "restoration_minutes": 120, "pause_policy": "No pause", "callback_window_hours": 24}
        self.agreement = call("register", record_type="SHD Agreement", values={**self.scoped,
            "title": "Maintenance agreement", "valid_from": self.past - timedelta(days=1),
            "valid_until": self.future, "equipment": self.equipment, "service_type": "Repair", "policy": self.policy})["name"]
        call("activate", record_type="SHD Agreement", name=self.agreement)
        for kind in ("Accept", "Approve Cost"):
            call("register", record_type="SHD Contact Authority", values={**self.scoped, "user": "Administrator",
                "authority": kind, "amount_limit": 1000000, "valid_from": self.past, "valid_until": self.future})

    def cleanup_case(self):
        frappe.set_user("Administrator")
        frappe.db.rollback(save_point="business_case")

    def request(self, incident=None):
        req = call("receive_request", **self.scoped, equipment=self.equipment, subject="Compressor stopped",
            reported_at=str(self.past), received_at=str(self.past + timedelta(minutes=5)))["name"]
        call("triage", request=req, priority="High", reason="Production stopped", owner="Administrator",
            agreement=self.agreement, incident=incident)
        return frappe.get_doc("SHD Request", req)

    def work(self, req=None, package="MAIN"):
        req = req or self.request()
        wo = call("create_work_order", origin_kind="INCIDENT", origin=req.incident, scope_text="Restore compressor", package_key=package)
        return frappe.get_doc("SHD Work Order", wo["name"])

    def visit(self, wo):
        call("assign", work_order_id=wo.name, technician=self.tech, starts_at=str(self.past),
             ends_at=str(self.now - timedelta(hours=1)), required_skill="compressor")
        return call("start_visit", work_order_id=wo.name, occurred_at=str(self.past + timedelta(minutes=10)))["name"]

    def restore(self, wo):
        visit = self.visit(wo)
        call("finish_visit", visit=visit, outcome="Machine tested", evidence={"pressure": "8 bar"}, occurred_at=str(self.now - timedelta(hours=1)))
        call("restore", work_order_id=wo.name, criteria="Stable test run", measurements={"pressure": "8 bar"},
             occurred_at=str(self.now - timedelta(minutes=50)))
        return visit

    def test_01_receipt_retry_and_conflict(self):
        payload = dict(**self.scoped, subject="Unknown equipment", reported_at=str(self.past), received_at=str(self.past))
        first = call("receive_request", key="stable-intake-1", **payload)
        self.assertEqual(first, call("receive_request", key="stable-intake-1", **payload))
        with self.assertRaises(frappe.ValidationError):
            call("receive_request", key="stable-intake-1", **{**payload, "subject": "Changed"})

    def test_02_shared_incident_no_duplicate_work(self):
        req = self.request()
        other = self.request(req.incident)
        one, two = self.work(req), self.work(other)
        self.assertEqual(one.name, two.name)
        self.assertEqual(1, frappe.db.count("SHD Work Source", {"incident": req.incident}))

    def test_03_restoration_waits_for_all_packages(self):
        req = self.request()
        first = self.work(req)
        self.work(req, package="FOLLOWUP")
        self.restore(first)
        req.reload()
        self.assertIsNone(req.restored_at)
        self.assertEqual(req.status, "Active")

    def test_04_separate_restoration_acceptance_invoice(self):
        req = self.request()
        wo = self.work(req)
        self.restore(wo)
        req.reload()
        self.assertEqual(req.status, "Restored")
        self.assertIsNone(req.accepted_at)
        with self.assertRaises(frappe.ValidationError):
            call("close_request", request=req.name, reason="Try closing too early")
        call("accept_work", work_order_id=wo.name, evidence="Customer witnessed test", occurred_at=str(self.now - timedelta(minutes=40)))
        call("close_request", request=req.name, reason="Accepted outcome recorded")
        self.assertEqual(frappe.db.get_value("SHD Request", req.name, "status"), "Closed")
        self.assertEqual(0, frappe.db.count("Sales Invoice", {"custom_shd_work_order": wo.name}))

    def test_05_reservation_native_stock_guard(self):
        wo = self.work()
        call("reserve", work_order_id=wo.name, item=self.part, warehouse=self.warehouse, quantity="2", expires_at=str(self.future))
        with self.assertRaises(frappe.ValidationError):
            call("reserve", work_order_id=wo.name, item=self.part, warehouse=self.warehouse, quantity="1", expires_at=str(self.future))
        stock = frappe.get_doc({"doctype": "Stock Entry", "stock_entry_type": "Material Issue", "company": self.company,
            "items": [{"item_code": self.part, "s_warehouse": self.warehouse, "qty": 1}]})
        stock.insert()
        with self.assertRaises(frappe.ValidationError):
            stock.submit()

    def test_06_consumption_is_real_ledger_and_one_effect(self):
        wo = self.work()
        visit = self.visit(wo)
        hold = call("reserve", work_order_id=wo.name, item=self.part, warehouse=self.warehouse, quantity="2", expires_at=str(self.future))["name"]
        first = call("consume", key="consume-stable-1", reservation=hold, visit=visit, quantity="1")
        self.assertEqual(first, call("consume", key="consume-stable-1", reservation=hold, visit=visit, quantity="1"))
        self.assertEqual(1, frappe.db.get_value("Stock Entry", first["stock_entry"], "docstatus"))
        self.assertEqual(1, frappe.db.get_value("Bin", {"item_code": self.part, "warehouse": self.warehouse}, "actual_qty"))
        self.assertEqual(1, frappe.db.get_value("SHD Reservation", hold, "remaining_qty"))

    def test_07_changed_estimate_requires_new_decision(self):
        wo = self.work()
        def propose(qty):
            return call("propose_estimate", work_order_id=wo.name, lines=[{"item": self.part, "quantity": qty, "rate": "120"}],
                        currency="VND", expires_at=str(self.future))["name"]
        first = propose("1")
        approval = frappe.get_doc("SHD Estimate", first)
        call("decide_estimate", estimate=first, binding_hash=approval.binding_hash, approve=True, reason="Customer approves one")
        second = propose("2")
        self.assertNotEqual(first, second)
        with self.assertRaises(frappe.ValidationError):
            self.visit(wo)
        self.assertEqual("Superseded", frappe.db.get_value("SHD Estimate", first, "status"))

    def test_08_pm_period_and_finding_lifecycle(self):
        plan = call("register", record_type="SHD PM Plan", values={**self.scoped, "equipment": self.equipment,
            "checklist": [{"key": "vibration", "unit": "mm/s"}], "first_due": self.past.date(),
            "interval_days": 30, "service_owner": "Administrator"})["name"]
        call("activate", record_type="SHD PM Plan", name=plan)
        period = call("generate_pm", plan=plan, period_key="0")
        self.assertEqual(period["name"], call("generate_pm", plan=plan, period_key="0")["name"])
        source = frappe.db.get_value("SHD Work Source", {"pm_occurrence": period["name"]})
        wo = frappe.get_doc("SHD Work Order", {"source": source})
        self.visit(wo)
        done = call("complete_pm", occurrence=period["name"], observations=[{"key": "vibration", "unit": "mm/s", "value": 0, "result": "Abnormal"}],
            findings=[{"description": "Synthetic abnormality", "severity": "Review", "service_owner": "Administrator", "due_at": str(self.future)}],
            occurred_at=str(self.now - timedelta(minutes=30)))
        self.assertEqual("Open", frappe.db.get_value("SHD Finding", done["findings"][0], "status"))

    def test_09_scope_api_list_file_and_direct_mutation(self):
        user = "shd.customer@example.invalid"
        call("register", record_type="SHD Access Grant", values={**self.scoped, "user": user, "actions": "read,operate"})
        req = self.request()
        other = call("register", record_type="SHD Site", values={**self.base, "title": "Private Factory"})["name"]
        frappe.set_user(user)
        from smart_helpdesk.security import permits
        self.assertTrue(permits(frappe.get_doc("SHD Request", req.name)))
        self.assertFalse(permits(frappe.get_doc("SHD Site", other)))
        self.assertEqual([self.site], frappe.get_list("SHD Site", pluck="name"))
        with self.assertRaises(frappe.PermissionError):
            frappe.get_doc("SHD Request", req.name).update({"status": "Closed"}).save(ignore_permissions=True)
        with self.assertRaises(frappe.ValidationError):
            frappe.get_doc({"doctype": "File", "file_name": "unsafe.txt", "content": "test", "is_private": 0,
                "attached_to_doctype": "SHD Request", "attached_to_name": req.name}).insert(ignore_permissions=True)

    def test_10_correction_preserves_event_and_updates_projection(self):
        req = self.request()
        wo = self.work(req)
        self.restore(wo)
        evt = frappe.db.get_value("SHD Event", {"aggregate_id": wo.name, "event_type": "WorkOrderRestored"})
        call("correct_restoration", work_order_id=wo.name, source_event=evt, reason="Test result was misrecorded")
        self.assertIsNone(frappe.db.get_value("SHD Request", req.name, "restored_at"))
        self.assertTrue(frappe.db.exists("SHD Event", evt))
        self.assertEqual(1, frappe.db.count("SHD Event", {"supersedes_event": evt}))

    def test_11_report_revision_and_missing_data(self):
        self.request()
        call("receive_request", **self.scoped, subject="Still untriaged", reported_at=str(self.past), received_at=str(self.past))
        payload = dict(company=self.company, customer=self.customer, site=self.site,
            period_start=str(self.past - timedelta(hours=1)), period_end=str(self.future))
        first = call("snapshot_kpis", **payload)
        sla = first["metrics"]["response_sla"]
        self.assertEqual((0, 1, 1), (sla["numerator"], sla["denominator"], sla["missing"]))
        second = call("snapshot_kpis", **payload, supersedes=first["name"])
        self.assertNotEqual(first["name"], second["name"])
        self.assertTrue(frappe.db.exists("SHD KPI Snapshot", first["name"]))

    def test_12_unexpected_identity_arguments_rejected(self):
        with self.assertRaises(frappe.ValidationError):
            call("receive_request", **self.scoped, subject="injection", reported_at=str(self.past), received_at=str(self.past),
                ignore_permissions=True)

    def test_13_real_invoice_sources_and_no_double_stock(self):
        wo = self.work()
        estimate = call("propose_estimate", work_order_id=wo.name,
            lines=[{"item": self.part, "quantity": "1", "rate": "120"}], currency="VND", expires_at=str(self.future))["name"]
        call("decide_estimate", estimate=estimate, binding_hash=frappe.db.get_value("SHD Estimate", estimate, "binding_hash"),
             approve=True, reason="Customer approves material")
        visit = self.visit(wo)
        hold = call("reserve", work_order_id=wo.name, item=self.part, warehouse=self.warehouse, quantity="1", expires_at=str(self.future))["name"]
        used = call("consume", reservation=hold, visit=visit, quantity="1")["name"]
        charge = call("reconcile_charge", source_type="Material", source_name=used, item=self.part,
            rate="120", billing_policy="Billable")["name"]
        with self.assertRaises(frappe.ValidationError):
            call("reconcile_charge", source_type="Material", source_name=used, item=self.part,
                 rate="0", billing_policy="Warranty", reason="Duplicate attempt")
        call("finish_visit", visit=visit, outcome="Successful", evidence={"pressure": "8 bar"}, occurred_at=str(self.now - timedelta(hours=1)))
        call("restore", work_order_id=wo.name, criteria="Run test", measurements={"pressure": "8 bar"}, occurred_at=str(self.now - timedelta(minutes=50)))
        call("accept_work", work_order_id=wo.name, evidence="Signed acceptance", occurred_at=str(self.now - timedelta(minutes=40)))
        invoice = call("prepare_invoice", key="invoice-stable-1", work_order_id=wo.name, selling_price_list="SHD Selling VND")
        self.assertEqual(invoice, call("prepare_invoice", key="invoice-stable-1", work_order_id=wo.name, selling_price_list="SHD Selling VND"))
        self.assertEqual(invoice["name"], frappe.db.get_value("SHD Charge", charge, "sales_invoice"))
        native = frappe.get_doc("Sales Invoice", invoice["name"])
        native.submit()
        self.assertEqual(native.docstatus, 1)
        self.assertEqual(1, frappe.db.get_value("Bin", {"item_code": self.part, "warehouse": self.warehouse}, "actual_qty"))
        self.assertEqual(1, frappe.db.count("SHD Event", {"aggregate_id": native.name, "event_type": "InvoiceSubmitted"}))
        report = call("snapshot_kpis", **self.scoped, period_start=str(self.past - timedelta(hours=1)), period_end=str(self.future))
        self.assertEqual("120.0", report["metrics"]["service_cohort_finance"]["submitted_net_revenue"])
        with self.assertRaises(frappe.ValidationError):
            native.cancel()
        cancelled = call("cancel_service_invoice", invoice=native.name, reason="Manager reviewed disputed amount")
        self.assertEqual(2, cancelled["docstatus"])
        self.assertIsNone(frappe.db.get_value("SHD Charge", charge, "sales_invoice"))

    def test_14_purchase_partial_receipt_reject_and_retry(self):
        wo = self.work()
        demand = call("create_demand", work_order_id=wo.name, item=self.part, warehouse=self.warehouse,
                      quantity="10", needed_at=str(self.future.date()))["name"]
        req = call("requisition", demand=demand)
        self.assertEqual(req["material_request"], call("requisition", demand=demand)["material_request"])
        supplier = frappe.get_doc({"doctype": "Supplier", "supplier_name": "SHD Test Supplier",
            "supplier_group": "All Supplier Groups", "supplier_type": "Company"}).insert()
        quarantine = frappe.get_doc({"doctype": "Warehouse", "warehouse_name": "SHD Quarantine", "company": self.company}).insert()
        po = call("prepare_purchase_order", demand=demand, supplier=supplier.name, rate="100", delivery_date=str(self.future.date()))
        call("approve_purchase_order", demand=demand, binding_hash=po["binding_hash"], reason="Approve source and price")
        receipt = call("receive_purchase", key="receipt-stable-1", demand=demand, accepted_quantity="4",
            rejected_quantity="2", rejected_warehouse=quarantine.name)
        self.assertEqual(receipt, call("receive_purchase", key="receipt-stable-1", demand=demand, accepted_quantity="4",
            rejected_quantity="2", rejected_warehouse=quarantine.name))
        self.assertEqual("Partially fulfilled", receipt["status"])
        self.assertEqual(6, frappe.db.get_value("Bin", {"item_code": self.part, "warehouse": self.warehouse}, "actual_qty"))

    def test_15_technician_scope_and_revoked_receipt(self):
        wo = self.work()
        self.visit(wo)
        grant = call("register", record_type="SHD Access Grant", values={**self.scoped, "user": self.tech, "resource_type": "All", "actions": "read,operate"})["name"]
        frappe.set_user(self.tech)
        from smart_helpdesk.security import permits
        self.assertTrue(permits(frappe.get_doc("SHD Work Order", wo.name)))
        stock = dict(work_order_id=wo.name, item=self.part, warehouse=self.warehouse)
        call("available_stock", key="scoped-stock-read", **stock)
        frappe.set_user("Administrator")
        call("revoke", record_type="SHD Access Grant", name=grant, reason="User transferred teams")
        frappe.set_user(self.tech)
        with self.assertRaises(frappe.PermissionError):
            call("available_stock", key="scoped-stock-read", **stock)

    def test_16_knowledge_review_and_live_revocation(self):
        knowledge = call("register", record_type="SHD Knowledge", values={**self.scoped, "title": "E17 procedure",
            "model": "TEST-R1", "document_version": "r1", "effective_from": self.past, "effective_until": self.future,
            "content": "Synthetic E17 procedure", "source_reference": "manual/test/page-4"})["name"]
        query = dict(**self.scoped, model="TEST-R1", query="E17")
        self.assertEqual(0, call("search_knowledge", **query)["total"])
        call("activate", record_type="SHD Knowledge", name=knowledge)
        self.assertEqual(1, call("search_knowledge", **query)["total"])
        call("revoke", record_type="SHD Knowledge", name=knowledge, reason="Manual superseded")
        self.assertEqual(0, call("search_knowledge", **query)["total"])

    def test_17_materials_required_before_scheduling(self):
        wo = self.work()
        call("declare_materials", work_order_id=wo.name, requirements=[{"item": self.part, "warehouse": self.warehouse, "quantity": "1"}])
        with self.assertRaises(frappe.ValidationError):
            self.visit(wo)
        call("reserve", work_order_id=wo.name, item=self.part, warehouse=self.warehouse, quantity="1", expires_at=str(self.future))
        self.assertTrue(self.visit(wo))

    def test_18_service_grant_does_not_grant_inventory(self):
        wo = self.work()
        self.visit(wo)
        call("register", record_type="SHD Access Grant", values={**self.scoped, "user": self.tech, "resource_type": "Service", "actions": "read,operate"})
        frappe.set_user(self.tech)
        with self.assertRaises(frappe.PermissionError):
            call("available_stock", work_order_id=wo.name, item=self.part, warehouse=self.warehouse)

    def test_19_scheduler_uses_scoped_identity_and_is_repeatable(self):
        dispatcher = "shd.dispatch@example.invalid"
        call("register", record_type="SHD Access Grant", values={**self.scoped, "user": dispatcher,
             "resource_type": "Service", "actions": "read,operate"})
        plan = call("register", record_type="SHD PM Plan", values={**self.scoped, "equipment": self.equipment,
            "checklist": [{"key": "pressure", "unit": "bar"}], "first_due": self.past.date(),
            "interval_days": 30, "service_owner": dispatcher})["name"]
        call("activate", record_type="SHD PM Plan", name=plan)
        old = frappe.conf.get("shd_scheduler_user")
        frappe.conf.shd_scheduler_user = dispatcher
        try:
            from smart_helpdesk.tasks import generate_due_pm
            first = generate_due_pm()
            second = generate_due_pm()
            self.assertEqual((1, 0), (first["created"], second["created"]))
            self.assertEqual(1, frappe.db.count("SHD PM Occurrence", {"plan": plan}))
            actor = frappe.db.get_value("SHD Event", {"aggregate_type": "SHD PM Occurrence", "event_type": "Created", "site": self.site}, "actor")
            self.assertEqual(dispatcher, actor)
        finally:
            frappe.conf.shd_scheduler_user = old

    def test_20_report_scheduler_replays_without_new_snapshot(self):
        user = "shd.accounting@example.invalid"
        for resource, actions in (("Service", "read"), ("Finance", "read,operate")):
            call("register", record_type="SHD Access Grant", values={**self.scoped, "user": user,
                 "resource_type": resource, "actions": actions})
        old_user, old_days = frappe.conf.get("shd_report_user"), frappe.conf.get("shd_report_lookback_days")
        frappe.conf.shd_report_user, frappe.conf.shd_report_lookback_days = user, 1
        try:
            from smart_helpdesk.tasks import build_daily_reports
            build_daily_reports()
            build_daily_reports()
            self.assertEqual(1, frappe.db.count("SHD KPI Snapshot", {"site": self.site}))
        finally:
            frappe.conf.shd_report_user, frappe.conf.shd_report_lookback_days = old_user, old_days

    def test_21_technician_can_read_use_without_internal_cost(self):
        wo = self.work()
        visit = self.visit(wo)
        hold = call("reserve", work_order_id=wo.name, item=self.part, warehouse=self.warehouse, quantity="1", expires_at=str(self.future))["name"]
        use = call("consume", reservation=hold, visit=visit, quantity="1")["name"]
        self.assertGreater(frappe.db.get_value("SHD Material Use", use, "unit_cost"), 0)
        call("register", record_type="SHD Access Grant", values={**self.scoped, "user": self.tech, "resource_type": "All", "actions": "read,operate"})
        frappe.set_user(self.tech)
        from frappe.client import get
        visible = get("SHD Material Use", use)
        self.assertEqual(1, visible["quantity"])
        # Frappe's as_dict converts an excluded numeric field to zero.
        self.assertIn(visible.get("unit_cost"), (None, 0))


def run():
    suite = unittest.defaultTestLoader.loadTestsFromTestCase(BusinessIntegration)
    outcome = unittest.TextTestRunner(verbosity=2).run(suite)
    frappe.db.rollback()
    report = {"scope": "live_erpnext_mariadb_integration", "site": frappe.local.site, "tests": outcome.testsRun,
              "failures": len(outcome.failures), "errors": len(outcome.errors), "success": outcome.wasSuccessful()}
    print(json.dumps(report))
    if not outcome.wasSuccessful():
        raise RuntimeError("Business integration tests failed")
    return report


def run_concurrency():
    """Two independent DB connections contend for the same real Bin balance."""
    if not frappe.local.site.startswith("shd-test."):
        raise RuntimeError("Dedicated test site required")
    BusinessIntegration.setUpClass()
    case = BusinessIntegration()
    case.setUp()
    first = case.work()
    second = case.work(package="SECOND")
    part = "SHD-RACE-" + frappe.generate_hash(length=8)
    frappe.get_doc({"doctype": "Item", "item_code": part, "item_group": "Products", "stock_uom": "Nos"}).insert()
    call("register", record_type="SHD Compatibility", values={**case.scoped, "model": "TEST-R1", "item": part,
        "evidence": "Synthetic concurrency test"})
    receipt = frappe.get_doc({"doctype": "Stock Entry", "stock_entry_type": "Material Receipt", "company": case.company,
        "items": [{"item_code": part, "t_warehouse": case.warehouse, "qty": 2, "basic_rate": 100}]})
    receipt.insert()
    receipt.submit()
    frappe.db.commit()
    site, sites_path = frappe.local.site, frappe.local.sites_path
    barrier = threading.Barrier(2)
    def contender(wo):
        frappe.init(site=site, sites_path=sites_path)
        frappe.connect()
        frappe.set_user("Administrator")
        try:
            barrier.wait(timeout=15)
            value = call("reserve", work_order_id=wo, item=part, warehouse=case.warehouse,
                         quantity="2", expires_at=str(case.future))
            frappe.db.commit()
            return {"outcome": "Held", "name": value["name"]}
        except frappe.ValidationError as error:
            frappe.db.rollback()
            return {"outcome": "Rejected", "reason": str(error)}
        finally:
            frappe.destroy()
    with ThreadPoolExecutor(max_workers=2) as pool:
        outcomes = list(pool.map(contender, [first.name, second.name]))
    from smart_helpdesk.inventory import held
    total = held(part, case.warehouse)
    success = sorted(o["outcome"] for o in outcomes) == ["Held", "Rejected"] and total == 2
    report = {"scope": "live_mariadb_concurrency", "success": success, "total_held": str(total), "outcomes": outcomes}
    print(json.dumps(report))
    if not success:
        raise RuntimeError("Atomic reservation failed")
    return report
