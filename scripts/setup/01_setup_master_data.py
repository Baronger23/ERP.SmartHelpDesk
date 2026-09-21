import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "core")))
import frappe_client as fc

print("=== STARTING 01_SETUP_MASTER_DATA.PY ===")

# 1. Check Company
company = fc.get_doc("Company", fc.COMPANY)
if not company:
    raise Exception(f"Fatal: Company {fc.COMPANY} not found!")
print(f"[OK] Company verified: {company.get('name')} ({fc.COMPANY_ABBR})")

# 2. Warehouses
warehouses = [
    {"name": f"Kho Linh kien Trung tam - {fc.COMPANY_ABBR}", "warehouse_name": "Kho Linh kien Trung tam"},
    {"name": f"Kho Xe Ky thuat Di dong - {fc.COMPANY_ABBR}", "warehouse_name": "Kho Xe Ky thuat Di dong"},
    {"name": f"Kho Xe - Nguyen Van An - {fc.COMPANY_ABBR}", "warehouse_name": "Kho Xe - Nguyen Van An"},
    {"name": f"Kho Xe - Tran Dinh Binh - {fc.COMPANY_ABBR}", "warehouse_name": "Kho Xe - Tran Dinh Binh"},
    {"name": f"Kho Xe - Le Hoang Cuong - {fc.COMPANY_ABBR}", "warehouse_name": "Kho Xe - Le Hoang Cuong"},
    {"name": f"Kho Thu hoi Linh kien Hong - {fc.COMPANY_ABBR}", "warehouse_name": "Kho Thu hoi Linh kien Hong"}
]
parent_wh = f"All Warehouses - {fc.COMPANY_ABBR}"
for wh in warehouses:
    wh_id = wh["name"]
    if not fc.exists_doc("Warehouse", wh_id):
        fc.create_doc("Warehouse", {
            "warehouse_name": wh["warehouse_name"],
            "parent_warehouse": parent_wh,
            "company": fc.COMPANY,
            "is_group": 0
        })
        print(f"[CREATED] Warehouse: {wh_id}")
    else:
        print(f"[EXISTS] Warehouse: {wh_id}")

# 3. Customers (3 B2B Customers)
customers = [
    {"customer_name": "Cong ty CP Bao bi Tan A", "customer_group": "Commercial", "territory": "All Territories"},
    {"customer_name": "Xi nghiep Duoc Hai Nam", "customer_group": "Commercial", "territory": "All Territories"},
    {"customer_name": "Cong ty Nhua & Co khi Song Long", "customer_group": "Commercial", "territory": "All Territories"}
]
for c in customers:
    c_name = c["customer_name"]
    if not fc.exists_doc("Customer", c_name):
        fc.create_doc("Customer", {
            "customer_name": c_name,
            "customer_type": "Company",
            "customer_group": c["customer_group"],
            "territory": c["territory"]
        })
        print(f"[CREATED] Customer: {c_name}")
    else:
        print(f"[EXISTS] Customer: {c_name}")

# 4. Suppliers (3 Suppliers)
suppliers = [
    {"supplier_name": "Cong ty TNHH Thiet bi Khi nen Kim Long", "supplier_group": "Distributor"},
    {"supplier_name": "Cong ty TNHH Thiet bi Dien Minh Phat", "supplier_group": "Distributor"},
    {"supplier_name": "Nha phan phoi Vat tu Ky thuat Tien Dat", "supplier_group": "Distributor"}
]
for s in suppliers:
    s_name = s["supplier_name"]
    if not fc.exists_doc("Supplier", s_name):
        fc.create_doc("Supplier", {
            "supplier_name": s_name,
            "supplier_type": "Company",
            "supplier_group": s["supplier_group"]
        })
        print(f"[CREATED] Supplier: {s_name}")
    else:
        print(f"[EXISTS] Supplier: {s_name}")

# 5. Item Group for Maintenance Parts
item_group_name = "Linh kien Sua chua - Bao tri"
if not fc.exists_doc("Item Group", item_group_name):
    fc.create_doc("Item Group", {
        "item_group_name": item_group_name,
        "parent_item_group": "All Item Groups",
        "is_group": 0
    })
    print(f"[CREATED] Item Group: {item_group_name}")
else:
    print(f"[EXISTS] Item Group: {item_group_name}")

# 6. 12 Maintenance Items & Reorder Levels
wh_main = f"Kho Linh kien Trung tam - {fc.COMPANY_ABBR}"
items_def = [
    {"code": "PART-FLT-OIL01", "name": "Loc dau may nen khi Hitachi", "uom": "Nos", "rate": 650000,
     "reorder": {"warehouse": wh_main, "warehouse_reorder_level": 3, "warehouse_reorder_qty": 5, "material_request_type": "Purchase"}},
    {"code": "PART-FLT-AIR01", "name": "Loc gio may nen khi truc vit 75kW", "uom": "Nos", "rate": 850000},
    {"code": "PART-OIL-COOL01", "name": "Dau lam mat tong hop New Alpha Screw (20L)", "uom": "Nos", "rate": 3200000,
     "reorder": {"warehouse": wh_main, "warehouse_reorder_level": 2, "warehouse_reorder_qty": 4, "material_request_type": "Purchase"}},
    {"code": "PART-NOZ-FLX01", "name": "Dau phun muc in cong nghiep Piezo 1020", "uom": "Nos", "rate": 8500000},
    {"code": "PART-BLT-TIM01", "name": "Day curoa rang truyen dong ban 50mm", "uom": "Nos", "rate": 420000},
    {"code": "PART-VAL-EXP01", "name": "Van tiet luu dien tu Chiller Danfoss ETS50", "uom": "Nos", "rate": 4600000},
    {"code": "PART-SEN-TEMP01", "name": "Cam bien nhiet do PT100 cong nghiep", "uom": "Nos", "rate": 380000},
    {"code": "PART-FLT-DSL01", "name": "Loc nhien lieu Diesel may phat dien Cummins", "uom": "Nos", "rate": 550000},
    {"code": "PART-AVR-CUM01", "name": "Bo mach dieu toc tu dong AVR Stamford SX460", "uom": "Nos", "rate": 2100000},
    {"code": "PART-CNT-150A", "name": "Khoi dong tu Contactor Schneider LC1D150", "uom": "Nos", "rate": 3800000,
     "reorder": {"warehouse": wh_main, "warehouse_reorder_level": 2, "warehouse_reorder_qty": 3, "material_request_type": "Purchase"}},
    {"code": "PART-RLY-THM01", "name": "Ro-le nhiet bao ve qua tai Schneider LRD3353", "uom": "Nos", "rate": 1150000},
    {"code": "PART-FUS-500A", "name": "Cau chi ha the gG 500A 690V", "uom": "Nos", "rate": 280000}
]

for it in items_def:
    code = it["code"]
    payload = {
        "item_code": code,
        "item_name": it["name"],
        "item_group": item_group_name,
        "stock_uom": it["uom"],
        "is_stock_item": 1,
        "valuation_rate": it["rate"]
    }
    if "reorder" in it:
        payload["reorder_levels"] = [it["reorder"]]
    
    if not fc.exists_doc("Item", code):
        fc.create_doc("Item", payload)
        print(f"[CREATED] Item: {code} (Reorder config: {'YES' if 'reorder' in it else 'NO'})")
    else:
        # Update reorder levels if needed
        if "reorder" in it:
            fc.update_doc("Item", code, {"reorder_levels": [it["reorder"]]})
        print(f"[EXISTS/UPDATED] Item: {code}")

# 7. Asset Categories
asset_cats = [
    "Compressor", "Industrial Printing", "HVAC & Cooling", "Generator", "Electrical Panel", "Calibration Equipment"
]
fixed_asset_acc = f"1750 - Plants and Machineries - {fc.COMPANY_ABBR}"
if not fc.exists_doc("Account", fixed_asset_acc):
    fixed_asset_acc = f"Plants and Machineries - {fc.COMPANY_ABBR}"
for cat in asset_cats:
    if not fc.exists_doc("Asset Category", cat):
        fc.create_doc("Asset Category", {
            "asset_category_name": cat,
            "non_depreciable_category": 1,
            "accounts": [{
                "company_name": fc.COMPANY,
                "fixed_asset_account": fixed_asset_acc
            }]
        })
        print(f"[CREATED] Asset Category: {cat}")
    else:
        print(f"[EXISTS] Asset Category: {cat}")

# 8. Locations & Assets (5 Customer Assets + 1 Internal Calibrated Tool Asset)
assets_def = [
    {
        "code": "AST-PRN-01",
        "name": "May in Flexo 6 mau (AST-PRN-01) - Bao bi Tan A",
        "cat": "Industrial Printing",
        "loc": "Xuong In 1 - Tan A",
        "customer": "Cong ty CP Bao bi Tan A",
        "serial": "FLX-2023-8891",
        "val": 450000000
    },
    {
        "code": "AST-CMP-02",
        "name": "May nen khi Hitachi 75kW (AST-CMP-02) - Bao bi Tan A",
        "cat": "Compressor",
        "loc": "Phong May Nen Khi - Tan A",
        "customer": "Cong ty CP Bao bi Tan A",
        "serial": "HTC-OSA-75-01",
        "val": 280000000
    },
    {
        "code": "AST-CHL-03",
        "name": "He thong Chiller Daikin 100RT (AST-CHL-03) - Duoc Hai Nam",
        "cat": "HVAC & Cooling",
        "loc": "Khu Ky Thuat Mai - Hai Nam",
        "customer": "Xi nghiep Duoc Hai Nam",
        "serial": "DK-CW-100-99",
        "val": 650000000
    },
    {
        "code": "AST-GEN-04",
        "name": "May phat dien Cummins 250kVA (AST-GEN-04) - Duoc Hai Nam",
        "cat": "Generator",
        "loc": "Nha Xe Tram Dien - Hai Nam",
        "customer": "Xi nghiep Duoc Hai Nam",
        "serial": "CUM-C250-772",
        "val": 350000000
    },
    {
        "code": "AST-PNL-05",
        "name": "Tu dien tong MSB 1200A (AST-PNL-05) - Song Long",
        "cat": "Electrical Panel",
        "loc": "Phong Dien Trung Tam - Song Long",
        "customer": "Cong ty Nhua & Co khi Song Long",
        "serial": "MSB-SL-1200A",
        "val": 180000000
    },
    {
        "code": "TOOL-VIB01",
        "name": "May do rung cong nghiep SKF CMAS 100-SL",
        "cat": "Calibration Equipment",
        "loc": "Kho Cong Cu Ky Thuat - AIS",
        "customer": None,
        "serial": "SKF-VIB-9921",
        "val": 35000000
    }
]

for a in assets_def:
    # Location
    loc = a["loc"]
    if not fc.exists_doc("Location", loc):
        fc.create_doc("Location", {"location_name": loc})
        print(f"[CREATED] Location: {loc}")
    
    # Fixed Asset Item
    item_asset_code = f"ITEM-{a['code']}"
    if not fc.exists_doc("Item", item_asset_code):
        fc.create_doc("Item", {
            "item_code": item_asset_code,
            "item_name": a["name"],
            "item_group": "All Item Groups",
            "is_fixed_asset": 1,
            "is_stock_item": 0,
            "asset_category": a["cat"],
            "stock_uom": "Nos"
        })
        print(f"[CREATED] Fixed Asset Item: {item_asset_code}")
    
    # Asset (Hạt sạn 1: Cách ly kế toán cho thiết bị của khách hàng & Hạt sạn 3: Tạo QR Code)
    existing_assets = fc.list_docs("Asset", filters=[["item_code", "=", item_asset_code], ["company", "=", fc.COMPANY]])
    
    is_cust_asset = 1 if a.get("customer") else 0
    
    asset_doc_name = existing_assets[0]["name"] if existing_assets else None
    
    # Generate Quick Issue Reporting URL for QR code (Hạt sạn 3)
    import urllib.parse
    qr_url = f"{fc.BASE_URL}/app/issue/new?custom_asset={asset_doc_name or ''}&customer={urllib.parse.quote(a.get('customer') or '')}"
    qr_html = (
        f'<div style="text-align: center; padding: 12px; background: #f8fafc; border: 2px dashed #cbd5e1; border-radius: 10px;">'
        f'<img src="https://api.qrserver.com/v1/create-qr-code/?size=150x150&data={urllib.parse.quote(qr_url)}" alt="QR Code" width="150" height="150" style="border-radius: 6px; box-shadow: 0 2px 4px rgba(0,0,0,0.1);" />'
        f'<br><div style="margin-top: 8px;"><b style="color: #1e293b; font-size: 13px;">QUÉT ĐỂ BÁO LỖI THIẾT BỊ NÀY</b></div>'
        f'<div style="color: #64748b; font-size: 11px; margin-top: 2px;">Mã: <b>{a["code"]}</b> | Số Serial: <b>{a["serial"]}</b></div>'
        f'</div>'
    )
    
    asset_payload = {
        "asset_name": a["name"],
        "item_code": item_asset_code,
        "company": fc.COMPANY,
        "location": loc,
        "purchase_date": "2025-01-10",
        "gross_purchase_amount": a["val"],
        "net_purchase_amount": a["val"],
        "is_existing_asset": 1,
        "calculate_depreciation": 0,
        "custom_customer": a.get("customer"),
        "custom_is_customer_equipment": is_cust_asset,
        "custom_qr_url": qr_url,
        "custom_qr_code_html": qr_html
    }
    
    if not existing_assets:
        doc = fc.create_doc("Asset", asset_payload)
        print(f"[CREATED] Asset: {a['code']} -> {doc.get('name')} (Customer: {a.get('customer')}, Isolated: {is_cust_asset})")
    else:
        doc_name = existing_assets[0]["name"]
        # Update QR URL with actual document name
        asset_payload["custom_qr_url"] = f"{fc.BASE_URL}/app/issue/new?custom_asset={doc_name}&customer={urllib.parse.quote(a.get('customer') or '')}"
        fc.update_doc("Asset", doc_name, asset_payload)
        print(f"[UPDATED] Asset: {a['code']} -> {doc_name} (Customer: {a.get('customer')}, Accounting Isolated: YES)")

# 9. Initial Stock Receipt (Material Receipt)
# Notice: For PART-FLT-OIL01 we set initial qty = 4. Later in scenario we issue 2, leaving 2 (< reorder_level 3).
existing_se = fc.list_docs("Stock Entry", filters=[["company", "=", fc.COMPANY], ["purpose", "=", "Material Receipt"]])
if not existing_se:
    stock_items = []
    for it in items_def:
        # For PART-FLT-OIL01 initial qty = 4, others 5-10
        qty = 4 if it["code"] == "PART-FLT-OIL01" else 5
        stock_items.append({
            "item_code": it["code"],
            "qty": qty,
            "uom": it["uom"],
            "stock_uom": it["uom"],
            "conversion_factor": 1,
            "t_warehouse": wh_main,
            "basic_rate": it["rate"]
        })
    se_doc = fc.create_doc("Stock Entry", {
        "stock_entry_type": "Material Receipt",
        "company": fc.COMPANY,
        "items": stock_items
    })
    se_name = se_doc.get("name")
    fc.submit_doc("Stock Entry", se_name)
    print(f"[CREATED & SUBMITTED] Initial Stock Receipt: {se_name}")
else:
    print(f"[EXISTS] Initial Stock Receipt already recorded ({existing_se[0]['name']})")

print("=== 01_SETUP_MASTER_DATA.PY COMPLETED SUCCESSFULLY ===")
