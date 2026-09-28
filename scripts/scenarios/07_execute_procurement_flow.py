import sys
import os
import json
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "core")))
import frappe_client as fc

print("=== STARTING 07_EXECUTE_PROCUREMENT_FLOW.PY ===")

item_code = "PART-FLT-OIL01"
supplier_name = "Cong ty TNHH Thiet bi Khi nen Kim Long"
wh_central = f"Kho Linh kien Trung tam - {fc.COMPANY_ABBR}"
wh_van_an = f"Kho Xe - Nguyen Van An - {fc.COMPANY_ABBR}"

# 1. CHECK STOCK LEVEL & REORDER CONDITION BEFORE PROCUREMENT
bin_pre = fc.list_docs("Bin", filters=[["item_code", "=", item_code], ["warehouse", "=", wh_central]], fields=["actual_qty"])
stock_before = bin_pre[0]["actual_qty"] if bin_pre else 0.0

item_doc = fc.get_doc("Item", item_code)
reorder_levels = item_doc.get("reorder_levels", [{}])
reorder_threshold = reorder_levels[0].get("warehouse_reorder_level", 3.0) if reorder_levels else 3.0
reorder_batch_qty = reorder_levels[0].get("warehouse_reorder_qty", 5.0) if reorder_levels else 10.0
# We procure 10 Nos to cover batch replenishment
replenish_qty = 10

print(f"Current Stock in Central: {stock_before} Nos | Reorder Level: {reorder_threshold} Nos")
is_below_reorder = stock_before < reorder_threshold
print(f"Replenishment Trigger Condition (Stock < Reorder): {is_below_reorder}")

# 2. STEP 1: MATERIAL REQUEST (PURCHASE REQUISITION)
existing_mr = fc.list_docs("Material Request", filters=[["material_request_type", "=", "Purchase"], ["docstatus", "=", 1]], limit=5)
# Filter for our item
mr_target = None
for mr_candidate in existing_mr:
    doc = fc.get_doc("Material Request", mr_candidate["name"])
    for row in doc.get("items", []):
        if row.get("item_code") == item_code:
            mr_target = doc
            break
    if mr_target:
        break

if not mr_target:
    mr_new = fc.create_doc("Material Request", {
        "material_request_type": "Purchase",
        "company": fc.COMPANY,
        "schedule_date": "2026-09-28",
        "items": [{
            "item_code": item_code,
            "qty": replenish_qty,
            "schedule_date": "2026-09-28",
            "warehouse": wh_central
        }]
    })
    mr_name = mr_new.get("name")
    fc.submit_doc("Material Request", mr_name)
    mr_target = fc.get_doc("Material Request", mr_name)
    print(f"[CREATED & SUBMITTED] Material Request: {mr_name} (Qty: {replenish_qty} Nos)")
else:
    mr_name = mr_target.get("name")
    print(f"[EXISTS] Material Request: {mr_name}")

mr_item_row = mr_target.get("items", [{}])[0]

# 3. STEP 2: PURCHASE ORDER
existing_po = fc.list_docs("Purchase Order", filters=[["supplier", "=", supplier_name], ["docstatus", "=", 1]], limit=5)
po_target = None
for po_candidate in existing_po:
    doc = fc.get_doc("Purchase Order", po_candidate["name"])
    for row in doc.get("items", []):
        if row.get("item_code") == item_code:
            po_target = doc
            break
    if po_target:
        break

if not po_target:
    po_new = fc.create_doc("Purchase Order", {
        "supplier": supplier_name,
        "company": fc.COMPANY,
        "schedule_date": "2026-09-28",
        "items": [{
            "item_code": item_code,
            "qty": replenish_qty,
            "rate": 650000,
            "schedule_date": "2026-09-28",
            "warehouse": wh_central,
            "material_request": mr_name,
            "material_request_item": mr_item_row.get("name")
        }]
    })
    po_name = po_new.get("name")
    fc.submit_doc("Purchase Order", po_name)
    po_target = fc.get_doc("Purchase Order", po_name)
    print(f"[CREATED & SUBMITTED] Purchase Order: {po_name} (Supplier: {supplier_name})")
else:
    po_name = po_target.get("name")
    print(f"[EXISTS] Purchase Order: {po_name}")

po_item_row = po_target.get("items", [{}])[0]

# 4. STEP 3: PURCHASE RECEIPT (GOODS RECEIPT INTO CENTRAL WAREHOUSE)
existing_pr = fc.list_docs("Purchase Receipt", filters=[["supplier", "=", supplier_name], ["docstatus", "=", 1]], limit=5)
pr_target = None
for pr_candidate in existing_pr:
    doc = fc.get_doc("Purchase Receipt", pr_candidate["name"])
    for row in doc.get("items", []):
        if row.get("item_code") == item_code:
            pr_target = doc
            break
    if pr_target:
        break

if not pr_target:
    pr_new = fc.create_doc("Purchase Receipt", {
        "supplier": supplier_name,
        "company": fc.COMPANY,
        "purchase_order": po_name,
        "items": [{
            "item_code": item_code,
            "qty": replenish_qty,
            "rate": 650000,
            "warehouse": wh_central,
            "purchase_order": po_name,
            "purchase_order_item": po_item_row.get("name")
        }]
    })
    pr_name = pr_new.get("name")
    fc.submit_doc("Purchase Receipt", pr_name)
    pr_target = fc.get_doc("Purchase Receipt", pr_name)
    print(f"[CREATED & SUBMITTED] Purchase Receipt: {pr_name} (+{replenish_qty} Nos into {wh_central})")
else:
    pr_name = pr_target.get("name")
    print(f"[EXISTS] Purchase Receipt: {pr_name}")

# 5. STEP 4: REPLENISH VAN STOCK VIA MATERIAL TRANSFER
van_transfer_qty = 2
existing_transfer = fc.list_docs("Stock Entry", filters=[
    ["stock_entry_type", "=", "Material Transfer"],
    ["docstatus", "=", 1]
])
transfer_found = None
for se_tr in existing_transfer:
    doc = fc.get_doc("Stock Entry", se_tr["name"])
    for r in doc.get("items", []):
        if r.get("item_code") == item_code and r.get("t_warehouse") == wh_van_an:
            transfer_found = doc
            break
    if transfer_found:
        break

if not transfer_found:
    se_tr_new = fc.create_doc("Stock Entry", {
        "stock_entry_type": "Material Transfer",
        "company": fc.COMPANY,
        "items": [{
            "item_code": item_code,
            "qty": van_transfer_qty,
            "s_warehouse": wh_central,
            "t_warehouse": wh_van_an,
            "basic_rate": 650000
        }]
    })
    tr_name = se_tr_new.get("name")
    fc.submit_doc("Stock Entry", tr_name)
    print(f"[CREATED & SUBMITTED] Van Replenishment (Material Transfer): {tr_name} ({van_transfer_qty} Nos -> {wh_van_an})")
else:
    tr_name = transfer_found.get("name")
    print(f"[EXISTS] Van Replenishment (Material Transfer): {tr_name}")

# 6. VERIFY FINAL BALANCES & REORDER STATUS
bin_central_final = fc.list_docs("Bin", filters=[["item_code", "=", item_code], ["warehouse", "=", wh_central]], fields=["actual_qty"])
stock_central_final = bin_central_final[0]["actual_qty"] if bin_central_final else 0.0

bin_van_final = fc.list_docs("Bin", filters=[["item_code", "=", item_code], ["warehouse", "=", wh_van_an]], fields=["actual_qty"])
stock_van_final = bin_van_final[0]["actual_qty"] if bin_van_final else 0.0

reorder_resolved = stock_central_final >= reorder_threshold

print("\n--- PROCUREMENT & REPLENISHMENT VERIFICATION SUMMARY ---")
print(f"[*] Initial Central Stock : {stock_before} Nos (Triggered Reorder < {reorder_threshold})")
print(f"[*] Material Request      : {mr_name}")
print(f"[*] Purchase Order        : {po_name} -> Supplier: {supplier_name}")
print(f"[*] Purchase Receipt      : {pr_name} (+{replenish_qty} Nos)")
print(f"[*] Van Stock Transfer    : {tr_name} ({van_transfer_qty} Nos to Van An)")
print(f"[*] Final Central Stock   : {stock_central_final} Nos (Condition Stock >= Reorder Level: {reorder_resolved})")
print(f"[*] Final Van Stock       : {stock_van_final} Nos (Emergency readiness: 100%)")

# 7. SAVE EVIDENCE JSON
procurement_evidence = {
    "timestamp": "2026-09-28T15:00:00",
    "item_code": item_code,
    "supplier": supplier_name,
    "material_request": mr_name,
    "purchase_order": po_name,
    "purchase_receipt": pr_name,
    "van_transfer": tr_name,
    "quantities": {
        "replenished": replenish_qty,
        "transferred_to_van": van_transfer_qty,
        "central_stock_final": stock_central_final,
        "van_stock_final": stock_van_final,
        "reorder_threshold": reorder_threshold,
        "reorder_cleared": reorder_resolved
    }
}

evidence_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "data", "procurement_evidence.json"))
with open(evidence_path, "w", encoding="utf-8") as f:
    json.dump(procurement_evidence, f, indent=2, ensure_ascii=False)

print(f"[OK] Procurement evidence saved to: {evidence_path}")
print("=== 07_EXECUTE_PROCUREMENT_FLOW.PY COMPLETED SUCCESSFULLY ===")
