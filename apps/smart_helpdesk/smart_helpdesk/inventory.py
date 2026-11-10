from decimal import Decimal

import frappe
from frappe.utils import get_datetime, getdate, now_datetime

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
from smart_helpdesk.security import require


def bin_balance(item, warehouse, company):
    wh = frappe.get_doc("Warehouse", warehouse)
    if wh.company != company or wh.is_group or wh.disabled:
        frappe.throw("Warehouse must be active, a leaf and in the same company")
    # Bin is ERPNext's stock balance; reservations do not maintain a second ledger.
    from erpnext.stock.utils import get_or_make_bin
    name = get_or_make_bin(item, warehouse)
    row = frappe.db.sql("SELECT actual_qty, valuation_rate FROM `tabBin` WHERE name=%s FOR UPDATE", name, as_dict=True)[0]
    return row


def held(item, warehouse):
    # Expiration is explicit: an elapsed timestamp alone never releases a committed hold.
    # Locking/current read is essential under MariaDB REPEATABLE READ. A snapshot
    # established before waiting for Bin must not hide the previous holder's commit.
    rows = frappe.db.sql("SELECT remaining_qty FROM `tabSHD Reservation` WHERE item=%s AND warehouse=%s AND status IN ('Held','Partially consumed') FOR UPDATE",
                         (item, warehouse), as_dict=True)
    return sum((Decimal(str(r.remaining_qty)) for r in rows), Decimal(0))


def warehouse_scope(wo, warehouse):
    pseudo = frappe._dict(doctype="SHD Reservation", **scope(wo), warehouse=warehouse, work_order=wo.name)
    require(pseudo, "operate")


def check_compatibility(wo, item):
    source = read("SHD Work Source", wo.source)
    origin = read("SHD Incident", source.incident) if source.incident else read("SHD Request", source.request) if source.request else read("SHD PM Occurrence", source.pm_occurrence)
    if not origin.equipment:
        frappe.throw("Equipment must be resolved before preparing material")
    equipment = read("SHD Equipment", origin.equipment)
    match = frappe.db.get_value("SHD Compatibility", {"company": wo.company, "customer": wo.customer,
        "site": wo.site, "model": equipment.model, "item": item, "status": "Active"})
    if not match:
        frappe.throw("No approved item/model compatibility")


@command("AIS Dispatcher")
def declare_materials(work_order_id, requirements):
    wo = work_order(work_order_id)
    if wo.status != "Planned":
        frappe.throw("Declare material needs before scheduling work")
    entries = data(requirements)
    if not isinstance(entries, list):
        frappe.throw("Material requirements must be an array")
    keys = set()
    for row in entries:
        if set(row) != {"item", "warehouse", "quantity"} or (row["item"], row["warehouse"]) in keys:
            frappe.throw("Unique item, warehouse, quantity rows required")
        keys.add((row["item"], row["warehouse"]))
        row["quantity"] = str(number(row["quantity"]))
        warehouse_scope(wo, row["warehouse"])
        check_compatibility(wo, row["item"])
    change(wo, "MaterialRequirementsDeclared", {"material_requirements": entries})
    return result(wo)


def check_material_readiness(wo, needed_at):
    for row in data(wo.material_requirements) or []:
        bin_balance(row["item"], row["warehouse"], wo.company)
        held_rows = frappe.db.sql("""SELECT remaining_qty,expires_at FROM `tabSHD Reservation`
            WHERE work_order=%s AND item=%s AND warehouse=%s AND status IN ('Held','Partially consumed') FOR UPDATE""",
            (wo.name, row["item"], row["warehouse"]), as_dict=True)
        available = sum((Decimal(str(r.remaining_qty)) for r in held_rows if get_datetime(r.expires_at) > get_datetime(needed_at)), Decimal(0))
        if available < Decimal(row["quantity"]):
            frappe.throw("Required material is not reserved through the planned visit; resolve supply before scheduling")


@command("AIS Warehouse Keeper", "AIS Dispatcher", "AIS Field Technician")
def available_stock(work_order_id, item, warehouse):
    wo = work_order(work_order_id)
    warehouse_scope(wo, warehouse)
    balance = bin_balance(item, warehouse, wo.company)
    reserved = held(item, warehouse)
    return {"actual_qty": str(balance.actual_qty), "held_qty": str(reserved),
            "available_qty": str(Decimal(str(balance.actual_qty)) - reserved),
            "uom": frappe.db.get_value("Item", item, "stock_uom"), "observed_at": str(now_datetime())}


@command("AIS Warehouse Keeper", "AIS Dispatcher")
def reserve(work_order_id, item, warehouse, quantity, expires_at):
    wo = work_order(work_order_id)
    warehouse_scope(wo, warehouse)
    qty = number(quantity)
    if get_datetime(expires_at) <= now_datetime():
        frappe.throw("Reservation expiry must be in the future")
    check_compatibility(wo, item)
    item_doc = frappe.get_doc("Item", item)
    if item_doc.disabled or item_doc.has_serial_no or item_doc.has_batch_no:
        frappe.throw("P1 supports enabled untracked stock items; serial/batch custody needs a dedicated workflow")
    if frappe.db.get_value("UOM", item_doc.stock_uom, "must_be_whole_number") and qty != qty.to_integral_value():
        frappe.throw("Stock unit requires a whole-number quantity")
    balance = bin_balance(item, warehouse, wo.company)
    if Decimal(str(balance.actual_qty)) - held(item, warehouse) < qty:
        frappe.throw("INSUFFICIENT_STOCK: another work order may have reserved this stock")
    return result(create("SHD Reservation", {**scope(wo), "work_order": wo.name, "item": item,
        "warehouse": warehouse, "quantity": qty, "remaining_qty": qty, "expires_at": expires_at}, "Held"))


@command("AIS Warehouse Keeper", "AIS Dispatcher")
def release_reservation(reservation, reason):
    initial = read("SHD Reservation", reservation)
    bin_balance(initial.item, initial.warehouse, initial.company)
    doc = locked("SHD Reservation", reservation)
    if doc.status not in ("Held", "Partially consumed") or not reason.strip():
        frappe.throw("Open reservation and release reason required")
    change(doc, "ReservationReleased", {"remaining_qty": 0, "status": "Released", "details": {"reason": reason}})
    return result(doc)


@command("AIS Warehouse Keeper", "AIS Field Technician")
def consume(reservation, visit, quantity):
    initial = read("SHD Reservation", reservation)
    wo = work_order(initial.work_order)
    warehouse_scope(wo, initial.warehouse)
    bin_balance(initial.item, initial.warehouse, initial.company)
    doc = locked("SHD Reservation", reservation)
    v = locked("SHD Visit", visit)
    if v.work_order != doc.work_order or v.status != "Started":
        frappe.throw("Material use must belong to an active visit for this work order")
    if wo.estimate:
        from smart_helpdesk.commercial import valid_approval
        valid_approval(wo)
    qty = number(quantity)
    if doc.status not in ("Held", "Partially consumed") or number(doc.remaining_qty) < qty or get_datetime(doc.expires_at) <= now_datetime():
        frappe.throw("Reservation not available or expired")
    check_compatibility(wo, doc.item)
    remaining = Decimal(str(doc.remaining_qty)) - qty
    change(doc, "ReservationConsumed", {"remaining_qty": remaining, "status": "Consumed" if remaining == 0 else "Partially consumed"})
    stock = frappe.get_doc({"doctype": "Stock Entry", "stock_entry_type": "Material Issue", "company": doc.company,
        "custom_shd_work_order": wo.name, "items": [{"item_code": doc.item, "s_warehouse": doc.warehouse, "qty": float(qty)}]})
    stock.insert(ignore_permissions=True)
    stock.submit()
    detail = stock.items[0]
    use = create("SHD Material Use", {**scope(doc), "work_order": wo.name, "visit": v.name, "reservation": doc.name,
        "item": doc.item, "warehouse": doc.warehouse, "quantity": qty, "unit_cost": abs(detail.basic_rate),
        "stock_entry": stock.name}, "Consumed")
    return {**result(use), "stock_entry": stock.name}


@command("AIS Warehouse Keeper")
def transfer_reserved(reservation, target_warehouse, quantity):
    initial = read("SHD Reservation", reservation)
    wo = work_order(initial.work_order)
    warehouse_scope(wo, target_warehouse)
    warehouse_scope(wo, initial.warehouse)
    for warehouse in sorted({initial.warehouse, target_warehouse}):
        bin_balance(initial.item, warehouse, initial.company)
    doc = locked("SHD Reservation", reservation)
    qty = number(quantity)
    if target_warehouse == doc.warehouse or doc.status not in ("Held", "Partially consumed") or qty > number(doc.remaining_qty):
        frappe.throw("Invalid reservation transfer")
    change(doc, "ReservationTransferred", {"remaining_qty": Decimal(str(doc.remaining_qty)) - qty,
        "status": "Transferred" if qty == Decimal(str(doc.remaining_qty)) else "Partially consumed"})
    entry = frappe.get_doc({"doctype": "Stock Entry", "stock_entry_type": "Material Transfer", "company": doc.company,
        "custom_shd_work_order": wo.name, "items": [{"item_code": doc.item, "qty": float(qty),
        "s_warehouse": doc.warehouse, "t_warehouse": target_warehouse}]})
    entry.insert(ignore_permissions=True)
    entry.submit()
    target = create("SHD Reservation", {**scope(doc), "work_order": wo.name, "item": doc.item,
        "warehouse": target_warehouse, "quantity": qty, "remaining_qty": qty, "expires_at": doc.expires_at,
        "details": {"transfer": entry.name, "source_reservation": doc.name, "received_by": frappe.session.user}}, "Held")
    return {**result(target), "stock_entry": entry.name}


def protect_holds(doc, method=None):
    """Native Desk/API Stock Entries must respect the same holds as custom commands."""
    delta = {}
    for item in doc.items:
        qty = Decimal(str(item.transfer_qty or item.qty))
        for warehouse, sign in ((item.s_warehouse, -1), (item.t_warehouse, 1)):
            if warehouse:
                key = (item.item_code, warehouse)
                delta[key] = delta.get(key, Decimal(0)) + sign * qty * (-1 if method == "before_cancel" else 1)
    for (item, warehouse), movement in sorted(delta.items()):
        if movement < 0:
            balance = bin_balance(item, warehouse, doc.company)
            if Decimal(str(balance.actual_qty)) + movement < held(item, warehouse):
                frappe.throw("Stock movement would consume inventory reserved for service work")
    if method == "before_cancel" and frappe.db.exists("SHD Material Use", {"stock_entry": doc.name}):
        frappe.throw("Confirmed service consumption requires a traced return; direct cancellation is blocked")


def protect_ledger(doc, method=None):
    """Also covers native delivery, invoice, receipt cancellation and reconciliation paths."""
    if not frappe.db.exists("DocType", "SHD Reservation") or float(doc.actual_qty or 0) >= 0:
        return
    balance = bin_balance(doc.item_code, doc.warehouse, doc.company)
    reserved = held(doc.item_code, doc.warehouse)
    if not reserved:
        return
    if Decimal(str(balance.actual_qty)) + Decimal(str(doc.actual_qty)) < reserved:
        frappe.throw("Stock ledger movement would violate active service reservations")


@command("AIS Purchasing", "AIS Dispatcher")
def create_demand(work_order_id, item, warehouse, quantity, needed_at):
    wo = work_order(work_order_id)
    warehouse_scope(wo, warehouse)
    check_compatibility(wo, item)
    qty = number(quantity)
    existing = frappe.db.get_value("SHD Demand", {"work_order": wo.name, "item": item, "warehouse": warehouse,
        "status": ["not in", ["Cancelled", "Fulfilled"]]})
    if existing:
        frappe.throw("An open demand already exists; review its supply before buying again")
    return result(create("SHD Demand", {**scope(wo), "work_order": wo.name, "item": item,
        "warehouse": warehouse, "quantity": qty, "needed_at": getdate(needed_at)}, "Open"))


@command("AIS Purchasing")
def requisition(demand):
    doc = locked("SHD Demand", demand)
    if doc.material_request:
        return {**result(doc), "material_request": doc.material_request}
    balance = bin_balance(doc.item, doc.warehouse, doc.company)
    available = max(Decimal(0), Decimal(str(balance.actual_qty)) - held(doc.item, doc.warehouse))
    # Query authoritative native open PO rows for the item/warehouse; draft orders are not supply.
    supply = frappe.db.sql("""SELECT COALESCE(SUM(GREATEST(0, pi.qty - pi.received_qty)), 0)
        FROM `tabPurchase Order Item` pi JOIN `tabPurchase Order` po ON po.name=pi.parent
        WHERE po.docstatus=1 AND po.status NOT IN ('Closed','Cancelled') AND po.company=%s
        AND pi.item_code=%s AND pi.warehouse=%s AND po.custom_shd_demand=%s""", (doc.company, doc.item, doc.warehouse, doc.name))[0][0]
    net = max(Decimal(0), Decimal(str(doc.quantity)) - available - Decimal(str(supply)))
    if not net:
        change(doc, "DemandCovered", {"details": {"available": str(available), "open_supply": str(supply)}})
        return {**result(doc), "material_request": None, "reason": "Existing stock or open purchase supply covers demand"}
    mr = frappe.get_doc({"doctype": "Material Request", "company": doc.company, "material_request_type": "Purchase",
        "custom_shd_demand": doc.name, "schedule_date": doc.needed_at,
        "items": [{"item_code": doc.item, "qty": float(net), "warehouse": doc.warehouse, "schedule_date": doc.needed_at}]})
    mr.insert(ignore_permissions=True)
    change(doc, "RequisitionPrepared", {"material_request": mr.name, "details": {"net_quantity": str(net)}})
    return {**result(doc), "material_request": mr.name, "docstatus": 0}


@command("AIS Purchasing")
def prepare_purchase_order(demand, supplier, rate, delivery_date):
    doc = locked("SHD Demand", demand)
    if not doc.material_request or doc.purchase_order:
        frappe.throw("An unallocated material request is required")
    mr = frappe.get_doc("Material Request", doc.material_request)
    if mr.docstatus == 0:
        mr.flags.ignore_permissions = True
        mr.submit()
    if mr.docstatus != 1:
        frappe.throw("Material request must be submitted")
    from erpnext.stock.doctype.material_request.material_request import (
        make_purchase_order,
    )
    po = make_purchase_order(mr.name)
    po.supplier = supplier
    po.custom_shd_demand = doc.name
    po.schedule_date = getdate(delivery_date)
    price = number(rate, False)
    for row in po.items:
        row.rate = float(price)
        row.schedule_date = getdate(delivery_date)
    po.insert(ignore_permissions=True)
    binding = purchase_binding(po)
    change(doc, "PurchaseOrderPrepared", {"purchase_order": po.name, "eta": getdate(delivery_date),
        "details": {**(data(doc.details) or {}), "purchase_binding_hash": digest(binding)}})
    return {**result(doc), "purchase_order": po.name, "binding_hash": digest(binding), "docstatus": 0}


def purchase_binding(po):
    return {"company": po.company, "supplier": po.supplier, "currency": po.currency,
            "items": [{"item": i.item_code, "qty": str(i.qty), "rate": str(i.rate), "warehouse": i.warehouse,
                       "schedule_date": str(i.schedule_date)} for i in po.items],
            "grand_total": str(po.grand_total), "taxes": [{"account": t.account_head, "amount": str(t.tax_amount)} for t in po.taxes]}


@command()
def approve_purchase_order(demand, binding_hash, reason):
    doc = locked("SHD Demand", demand)
    if not doc.purchase_order or not reason.strip():
        frappe.throw("Purchase order and approval justification required")
    po = frappe.get_doc("Purchase Order", doc.purchase_order)
    if po.docstatus != 0 or digest(purchase_binding(po)) != binding_hash or (data(doc.details) or {}).get("purchase_binding_hash") != binding_hash:
        frappe.throw("STALE_APPROVAL: purchase order changed; prepare a new purchase decision")
    po.flags.ignore_permissions = True
    po.submit()
    change(doc, "PurchaseOrderApproved", {"status": "Ordered", "details": {**(data(doc.details) or {}),
        "approved_by": frappe.session.user, "approved_hash": binding_hash, "approval_reason": reason}})
    return {**result(doc), "purchase_order": po.name, "docstatus": po.docstatus}


def protect_purchase_order(doc, method=None):
    if doc.get("custom_shd_demand") and frappe.flags.shd_command_type != "approve_purchase_order":
        frappe.throw("Service purchases require the exact-content service manager approval command")


@command("AIS Warehouse Keeper")
def receive_purchase(demand, accepted_quantity, rejected_quantity="0", rejected_warehouse=None):
    doc = locked("SHD Demand", demand)
    warehouse_scope(read("SHD Work Order", doc.work_order), doc.warehouse)
    if not doc.purchase_order:
        frappe.throw("Approved purchase order required")
    po = frappe.get_doc("Purchase Order", doc.purchase_order)
    if po.docstatus != 1:
        frappe.throw("Purchase order is not approved")
    accepted, rejected = number(accepted_quantity, False), number(rejected_quantity, False)
    if accepted + rejected <= 0:
        frappe.throw("Positive received quantity required")
    if rejected:
        if not rejected_warehouse or rejected_warehouse == doc.warehouse:
            frappe.throw("Rejected stock must go to a separate quarantine warehouse")
        warehouse_scope(read("SHD Work Order", doc.work_order), rejected_warehouse)
        wh = frappe.get_doc("Warehouse", rejected_warehouse)
        if wh.company != doc.company:
            frappe.throw("Quarantine warehouse belongs to another company")
    from erpnext.buying.doctype.purchase_order.purchase_order import (
        make_purchase_receipt,
    )
    receipt = make_purchase_receipt(po.name)
    if len(receipt.items) != 1:
        frappe.throw("P1 purchase receipt supports one demand/item per purchase order")
    row = receipt.items[0]
    if accepted + rejected > Decimal(str(row.qty)):
        frappe.throw("Cannot receive more than the remaining purchase quantity")
    row.qty = float(accepted)
    row.received_qty = float(accepted + rejected)
    row.rejected_qty = float(rejected)
    row.rejected_warehouse = rejected_warehouse
    receipt.custom_shd_demand = doc.name
    receipt.insert(ignore_permissions=True)
    receipt.flags.ignore_permissions = True
    receipt.submit()
    accepted_total = frappe.db.sql("""SELECT COALESCE(SUM(i.qty),0) FROM `tabPurchase Receipt Item` i
        JOIN `tabPurchase Receipt` r ON r.name=i.parent WHERE r.docstatus=1 AND r.custom_shd_demand=%s""", doc.name)[0][0]
    target = Decimal(str((data(doc.details) or {}).get("net_quantity", doc.quantity)))
    change(doc, "SupplyReceived", {"status": "Fulfilled" if Decimal(str(accepted_total)) >= target else "Partially fulfilled",
        "details": {**(data(doc.details) or {}), "accepted_total": str(accepted_total), "last_receipt": receipt.name,
                    "last_rejected_quantity": str(rejected)}})
    return {**result(doc), "purchase_receipt": receipt.name, "accepted_quantity": str(accepted), "rejected_quantity": str(rejected)}
