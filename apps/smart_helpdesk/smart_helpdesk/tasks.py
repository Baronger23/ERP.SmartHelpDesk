"""Opt-in scheduler jobs run as explicitly configured, scoped service identities."""
from datetime import timedelta

import frappe
from frappe.utils import getdate

from smart_helpdesk.api import execute


def service_user(setting):
    user = frappe.conf.get(setting)
    if not user:
        return None
    if user in ("Administrator", "Guest") or not frappe.db.exists("User", {"name": user, "enabled": 1}):
        frappe.throw("Scheduler requires a named, enabled service user with explicit grants")
    return user


def generate_due_pm():
    user = service_user("shd_scheduler_user")
    if not user:
        return {"enabled": False, "created": 0}
    original = frappe.session.user
    count = 0
    try:
        frappe.set_user(user)
        # get_list applies the same row permissions as Desk; no administrator-wide scan.
        plans = frappe.get_list("SHD PM Plan", filters={"status": "Active"}, fields=["name", "revision", "first_due", "interval_days"], limit_page_length=0)
        for plan in plans:
            latest = (getdate() - getdate(plan.first_due)).days // int(plan.interval_days)
            if latest < 0:
                continue
            existing = set(frappe.get_list("SHD PM Occurrence", filters={"plan": plan.name, "plan_version": plan.revision}, pluck="period_key", limit_page_length=0))
            for ordinal in range(latest + 1):
                if str(ordinal) in existing:
                    continue
                execute("generate_pm", {"plan": plan.name, "period_key": str(ordinal)},
                        f"scheduled-pm:{plan.name}:{plan.revision}:{ordinal}")
                count += 1
                if count >= 50:
                    return {"enabled": True, "created": count, "catchup_may_remain": True}
        return {"enabled": True, "created": count, "catchup_may_remain": False}
    finally:
        frappe.set_user(original)


def build_daily_reports():
    user = service_user("shd_report_user")
    if not user:
        return {"enabled": False, "snapshots": 0}
    lookback = int(frappe.conf.get("shd_report_lookback_days") or 0)
    if not 1 <= lookback <= 31:
        frappe.throw("Set an explicit report revision lookback between 1 and 31 days")
    original = frappe.session.user
    count = 0
    try:
        frappe.set_user(user)
        sites = frappe.get_list("SHD Site", filters={"status": "Active"}, fields=["name", "company", "customer"], limit_page_length=0)
        for site in sites:
            for days in range(1, lookback + 1):
                start = str(getdate() - timedelta(days=days)) + " 00:00:00"
                end = str(getdate() - timedelta(days=days - 1)) + " 00:00:00"
                execute("snapshot_kpis", {"company": site.company, "customer": site.customer, "site": site.name,
                    "period_start": start, "period_end": end, "auto_revision": True},
                    f"daily-report:{site.name}:{getdate()}:{days}")
                count += 1
        return {"enabled": True, "snapshots": count}
    finally:
        frappe.set_user(original)
