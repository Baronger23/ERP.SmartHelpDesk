from decimal import Decimal

import frappe
from frappe.utils import get_datetime, now_datetime

from smart_helpdesk.api import command
from smart_helpdesk.core import (
    change,
    create,
    data,
    digest,
    locked,
    number,
    read,
    result,
    scope,
    work_order,
)
from smart_helpdesk.security import authority, roles


def estimate_binding(wo, lines, currency, expires_at):
    return {**scope(wo), "work_order": wo.name, "scope": wo.scope, "generation_version": wo.generation_version,
            "lines": lines, "currency": currency, "expires_at": str(get_datetime(expires_at))}


def valid_approval(wo):
    estimate = locked("SHD Estimate", wo.estimate)
    binding = estimate_binding(wo, data(estimate.lines), estimate.currency, estimate.expires_at)
    if estimate.status != "Approved" or estimate.binding_hash != digest(binding) or get_datetime(estimate.expires_at) <= now_datetime():
        frappe.throw("STALE_APPROVAL: approve the current exact scope, prices and quantities")
    # Re-evaluate current authority; a revoked customer representative cannot authorize future work.
    people = frappe.db.sql("""SELECT amount_limit,valid_from,valid_until FROM `tabSHD Contact Authority`
        WHERE company=%s AND customer=%s AND site=%s AND user=%s AND authority='Approve Cost' AND status='Active' FOR UPDATE""",
        (wo.company, wo.customer, wo.site, estimate.approved_by), as_dict=True)
    if not any(get_datetime(a.valid_from) <= now_datetime() < get_datetime(a.valid_until) and
               Decimal(str(a.amount_limit)) >= Decimal(str(estimate.amount)) for a in people):
        frappe.throw("Approver no longer has current authority", frappe.PermissionError)
    return estimate


@command("AIS Billing Accountant", "AIS Dispatcher")
def propose_estimate(work_order_id, lines, currency, expires_at):
    wo = work_order(work_order_id)
    if wo.status in ("Technically complete", "Customer accepted") or get_datetime(expires_at) <= now_datetime():
        frappe.throw("Open scope and future approval expiry required")
    entries = data(lines)
    if not isinstance(entries, list) or not entries:
        frappe.throw("Estimate lines required")
    total = Decimal(0)
    seen = set()
    for line in entries:
        if set(line) != {"item", "quantity", "rate"} or line["item"] in seen:
            frappe.throw("One exact item, quantity and rate per estimate line required")
        seen.add(line["item"])
        if not frappe.db.exists("Item", {"name": line["item"], "disabled": 0}):
            frappe.throw("Enabled ERP item required")
        line["quantity"] = str(number(line["quantity"]))
        line["rate"] = str(number(line["rate"], False))
        total += Decimal(line["quantity"]) * Decimal(line["rate"])
    estimate = create("SHD Estimate", {**scope(wo), "work_order": wo.name, "lines": entries,
        "currency": currency, "amount": total, "expires_at": get_datetime(expires_at),
        "binding_hash": digest(estimate_binding(wo, entries, currency, expires_at))}, "Awaiting approval")
    if wo.estimate:
        old = locked("SHD Estimate", wo.estimate)
        change(old, "EstimateSuperseded", {"status": "Superseded"})
    change(wo, "EstimateProposed", {"estimate": estimate.name})
    return result(estimate)


@command("AIS Customer Portal")
def decide_estimate(estimate, binding_hash, approve, reason):
    doc = locked("SHD Estimate", estimate)
    wo = work_order(doc.work_order)
    authority(doc, "Approve Cost", doc.amount)
    if wo.estimate != doc.name or doc.status != "Awaiting approval" or doc.binding_hash != binding_hash or get_datetime(doc.expires_at) <= now_datetime():
        frappe.throw("Estimate is stale, changed or expired")
    if not isinstance(approve, bool) or not reason.strip():
        frappe.throw("Explicit decision and reason required")
    change(doc, "EstimateApproved" if approve else "EstimateRejected", {"status": "Approved" if approve else "Rejected",
        "approved_by": frappe.session.user if approve else None, "approved_at": now_datetime() if approve else None,
        "details": {"decision_reason": reason}})
    return result(doc)


@command("AIS Billing Accountant")
def reconcile_charge(source_type, source_name, item, rate, billing_policy, labor_cost_rate=None, reason=None):
    if source_type not in ("Material", "Time") or billing_policy not in ("Warranty", "Billable", "Goodwill"):
        frappe.throw("Invalid charge source or billing policy")
    source = locked("SHD Material Use" if source_type == "Material" else "SHD Time Log", source_name)
    wo = work_order(source.work_order)
    if frappe.db.exists("SHD Charge", {"source_key": source_type + ":" + source_name}):
        frappe.throw("Source has already been reconciled; use an adjustment rather than a second charge")
    qty = Decimal(str(source.quantity if source_type == "Material" else source.billable_hours))
    if qty <= 0:
        frappe.throw("Zero billable quantity is not an invoice charge")
    if source_type == "Material" and source.item != item:
        frappe.throw("Charge item must match consumed material")
    if source_type == "Time":
        if labor_cost_rate is None or not reason:
            frappe.throw("Confirmed labor cost rate and allocation basis required")
        cost = number(source.hours) * number(labor_cost_rate, False)
        change(source, "LaborCostConfirmed", {"cost_rate": number(labor_cost_rate, False), "details": {"cost_basis": reason}})
    else:
        cost = Decimal(str(source.unit_cost)) * Decimal(str(source.quantity))
    price = number(rate, False)
    if billing_policy != "Billable" and (price != 0 or not reason):
        frappe.throw("Warranty/goodwill charges require zero price and a policy justification")
    if billing_policy == "Goodwill" and frappe.session.user != "Administrator" and "AIS Service Manager" not in roles():
        frappe.throw("Goodwill requires service manager authority", frappe.PermissionError)
    if billing_policy == "Warranty":
        source_ref = read("SHD Work Source", wo.source)
        filters = {"incident": source_ref.incident} if source_ref.incident else {"name": source_ref.request}
        entitlement = frappe.db.get_value("SHD Request", filters, "entitlement") if any(filters.values()) else None
        policy = data(read("SHD Entitlement", entitlement).policy) if entitlement else {}
        if item not in policy.get("included_items", []):
            frappe.throw("Warranty item is not included in the request entitlement snapshot")
    estimate = None
    if billing_policy == "Billable":
        if not wo.estimate:
            frappe.throw("Billable work requires an approved estimate")
        estimate = valid_approval(wo)
        line = next((r for r in data(estimate.lines) if r["item"] == item), None)
        charged = frappe.get_all("SHD Charge", filters={"work_order": wo.name, "item": item, "billing_policy": "Billable"}, pluck="quantity")
        if not line or Decimal(line["rate"]) != price or sum((Decimal(str(q)) for q in charged), Decimal(0)) + qty > Decimal(line["quantity"]):
            frappe.throw("Actual charge exceeds the approved item, quantity or price")
    charge = create("SHD Charge", {**scope(wo), "work_order": wo.name, "source_type": source_type,
        "source_name": source_name, "source_key": source_type + ":" + source_name, "item": item,
        "quantity": qty, "cost": cost, "rate": price, "billing_policy": billing_policy,
        "estimate": estimate.name if estimate else None, "details": {"policy_reason": reason}}, "Reconciled")
    return result(charge)


@command("AIS Billing Accountant")
def prepare_invoice(work_order_id, selling_price_list=None):
    wo = work_order(work_order_id)
    if wo.status != "Customer accepted":
        frappe.throw("Customer acceptance required before invoicing")
    estimate = valid_approval(wo)
    if frappe.db.get_value("Company", wo.company, "default_currency") != estimate.currency:
        frappe.throw("P1 invoices require the company currency; configure an explicit FX policy before billing other currencies")
    if not selling_price_list:
        selling_price_list = frappe.db.get_value("Customer", wo.customer, "default_price_list") or frappe.db.get_single_value("Selling Settings", "selling_price_list")
    if not selling_price_list or not frappe.db.exists("Price List", {"name": selling_price_list,
            "enabled": 1, "selling": 1, "currency": estimate.currency}):
        frappe.throw("Select an enabled selling price list in the approved currency")
    charges = frappe.get_all("SHD Charge", filters={"work_order": wo.name, "status": "Reconciled", "billing_policy": "Billable"}, fields=["*"])
    if not charges:
        frappe.throw("No reconciled billable charges")
    if any(c.sales_invoice for c in charges):
        frappe.throw("Charge already allocated to an invoice")
    invoice = frappe.get_doc({"doctype": "Sales Invoice", "company": wo.company, "customer": wo.customer,
        "currency": estimate.currency, "update_stock": 0, "custom_shd_work_order": wo.name,
        "selling_price_list": selling_price_list, "price_list_currency": estimate.currency,
        "conversion_rate": 1, "plc_conversion_rate": 1, "ignore_pricing_rule": 1,
        "items": [{"item_code": c.item, "qty": c.quantity, "rate": c.rate} for c in charges]})
    invoice.insert(ignore_permissions=True)
    for charge in charges:
        doc = locked("SHD Charge", charge.name)
        change(doc, "ChargeAllocated", {"sales_invoice": invoice.name, "status": "Allocated"})
    return {"doctype": "Sales Invoice", "name": invoice.name, "docstatus": invoice.docstatus,
            "charges": [c.name for c in charges], "update_stock": 0}


def validate_invoice(doc, method=None):
    previous = doc.get_doc_before_save()
    if previous and previous.get("custom_shd_work_order") and previous.custom_shd_work_order != doc.get("custom_shd_work_order"):
        frappe.throw("Service invoice origin cannot be removed or changed")
    if not doc.get("custom_shd_work_order"):
        return
    if doc.update_stock:
        frappe.throw("Service material was already issued; invoice must not issue stock again")
    if method != "before_submit":
        return
    wo = locked("SHD Work Order", doc.custom_shd_work_order, "read")
    if doc.company != wo.company or doc.customer != wo.customer or wo.status != "Customer accepted":
        frappe.throw("Invoice scope and customer acceptance do not match")
    estimate = valid_approval(wo)
    if doc.currency != estimate.currency:
        frappe.throw("Invoice currency differs from approval")
    charges = frappe.get_all("SHD Charge", filters={"sales_invoice": doc.name}, fields=["item", "quantity", "rate"])
    expected = sorted((c.item, Decimal(str(c.quantity)), Decimal(str(c.rate))) for c in charges)
    actual = sorted((i.item_code, Decimal(str(i.qty)), Decimal(str(i.rate))) for i in doc.items)
    if not expected or expected != actual or doc.discount_amount or doc.additional_discount_percentage:
        frappe.throw("Invoice lines must match reconciled approved charges; adjustments require separate review")


def invoice_event(doc, method=None):
    if not doc.get("custom_shd_work_order"):
        return
    from smart_helpdesk.core import command_context, event
    with command_context(frappe.flags.shd_command or "native-invoice:" + doc.name + ":" + method):
        wo = read("SHD Work Order", doc.custom_shd_work_order)
        for key, value in scope(wo).items():
            doc.set(key, value)
        previous = frappe.db.sql("SELECT COALESCE(MAX(aggregate_version),0) FROM `tabSHD Event` WHERE aggregate_type='Sales Invoice' AND aggregate_id=%s", doc.name)[0][0]
        doc.revision = int(previous) + 1
        event(doc, "InvoiceSubmitted" if method == "on_submit" else "InvoiceCancelled")


def protect_invoice_cancel(doc, method=None):
    if doc.get("custom_shd_work_order") and frappe.flags.shd_command_type != "cancel_service_invoice":
        frappe.throw("Service invoice cancellation requires service manager review through the business command")


@command()
def cancel_service_invoice(invoice, reason):
    if not reason.strip():
        frappe.throw("Cancellation justification required")
    doc = frappe.get_doc("Sales Invoice", invoice, for_update=True)
    if not doc.get("custom_shd_work_order") or doc.docstatus != 1:
        frappe.throw("Submitted service invoice required")
    read("SHD Work Order", doc.custom_shd_work_order, "operate")
    doc.flags.ignore_permissions = True
    doc.cancel()
    for name in frappe.get_all("SHD Charge", filters={"sales_invoice": invoice}, pluck="name"):
        charge = locked("SHD Charge", name)
        change(charge, "InvoiceAllocationCancelled", {"sales_invoice": None, "status": "Reconciled",
            "details": {**(data(charge.details) or {}), "cancelled_invoice": invoice, "cancellation_reason": reason}})
    return {"doctype": "Sales Invoice", "name": doc.name, "docstatus": 2}
