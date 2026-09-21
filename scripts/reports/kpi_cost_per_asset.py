"""
KPI Report: Cost per Asset & Inventory Traceability
====================================================
Truy vấn ERPNext API tính:
- Tổng chi phí linh kiện từ Stock Entry theo custom_asset
- Số lượng vật tư tiêu hao theo Asset
- Truy xuất nguồn gốc: Issue → Stock Entry → Item
"""
import sys
import os
import json
from datetime import datetime

# Fix Windows console encoding
if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "core")))
import frappe_client as fc

OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "data", "evidence")
os.makedirs(OUTPUT_DIR, exist_ok=True)


def calculate_cost_per_asset():
    """Query Stock Entries and calculate maintenance cost per asset."""
    print("\n" + "=" * 60)
    print("  KPI REPORT: COST PER ASSET & INVENTORY TRACEABILITY")
    print("=" * 60)

    # Fetch all submitted Stock Entries (Material Issue type)
    stock_entries = fc.list_docs(
        "Stock Entry",
        filters=[["docstatus", "=", 1], ["stock_entry_type", "=", "Material Issue"]],
        fields=[
            "name", "posting_date", "total_amount",
            "custom_issue", "custom_asset", "custom_technician"
        ],
        limit=100
    )

    if not stock_entries:
        print("[WARN] No submitted Stock Entries found.")
        return None

    print(f"\n[OK] Found {len(stock_entries)} Material Issue entries\n")

    # Fetch Stock Entry Details for each entry
    all_items = []
    for se in stock_entries:
        details = fc.list_docs(
            "Stock Entry Detail",
            filters=[["parent", "=", se["name"]]],
            fields=["name"],
            limit=50
        )
        for d_ref in details:
            d = fc.get_doc("Stock Entry Detail", d_ref["name"])
            if not d:
                continue
            d["stock_entry"] = se["name"]
            d["custom_asset"] = se.get("custom_asset", "N/A")
            d["custom_issue"] = se.get("custom_issue", "N/A")
            d["custom_technician"] = se.get("custom_technician", "N/A")
            all_items.append(d)

    # --- 1. Cost per Asset ---
    asset_costs = {}
    for item in all_items:
        asset = item.get("custom_asset") or "Unlinked"
        if asset not in asset_costs:
            asset_costs[asset] = {"total_cost": 0, "total_qty": 0, "items": [], "issues": set()}
        asset_costs[asset]["total_cost"] += float(item.get("amount", 0) or 0)
        asset_costs[asset]["total_qty"] += float(item.get("qty", 0) or 0)
        asset_costs[asset]["items"].append(item.get("item_code", "N/A"))
        issue_ref = item.get("custom_issue")
        if issue_ref:
            asset_costs[asset]["issues"].add(issue_ref)

    print("--- Cost per Asset ---")
    cost_summary = []
    for asset, data in asset_costs.items():
        # Fetch asset name
        asset_doc = fc.get_doc("Asset", asset) if asset != "Unlinked" else None
        asset_name = asset_doc.get("asset_name", asset) if asset_doc else asset

        entry = {
            "asset_id": asset,
            "asset_name": asset_name,
            "total_cost_vnd": data["total_cost"],
            "total_parts_qty": data["total_qty"],
            "unique_issues": list(data["issues"]),
            "parts_used": list(set(data["items"]))
        }
        cost_summary.append(entry)
        print(f"  {asset_name} ({asset}):")
        print(f"    Cost: {data['total_cost']:,.0f} VND | Parts: {data['total_qty']:.0f} units")
        print(f"    Linked Issues: {', '.join(data['issues']) if data['issues'] else 'None'}")

    # --- 2. Warehouse Stock Check ---
    print("\n--- Current Stock Levels (Items with Reorder) ---")
    items_with_reorder = fc.list_docs(
        "Item",
        filters=[["is_stock_item", "=", 1]],
        fields=["name", "item_name", "item_group"],
        limit=50
    )

    stock_levels = []
    for item in items_with_reorder:
        bins = fc.list_docs(
            "Bin",
            filters=[["item_code", "=", item["name"]]],
            fields=["warehouse", "actual_qty", "projected_qty", "reserved_qty"],
            limit=20
        )
        for b in bins:
            if float(b.get("actual_qty", 0)) > 0 or True:  # Show all
                entry = {
                    "item_code": item["name"],
                    "item_name": item.get("item_name", ""),
                    "warehouse": b.get("warehouse", ""),
                    "actual_qty": float(b.get("actual_qty", 0)),
                    "projected_qty": float(b.get("projected_qty", 0)),
                    "reserved_qty": float(b.get("reserved_qty", 0))
                }
                stock_levels.append(entry)
                print(f"  {item['name']} @ {b.get('warehouse', 'N/A')}: "
                      f"Actual={b.get('actual_qty', 0)} | "
                      f"Projected={b.get('projected_qty', 0)}")

    # --- 3. Traceability: Issue → Stock Entry → Items ---
    print("\n--- Full Traceability Chain ---")
    traceability = []
    for se in stock_entries:
        se_details = [i for i in all_items if i["stock_entry"] == se["name"]]
        chain = {
            "stock_entry": se["name"],
            "issue": se.get("custom_issue", "N/A"),
            "asset": se.get("custom_asset", "N/A"),
            "technician": se.get("custom_technician", "N/A"),
            "items": [{"item": d["item_code"], "qty": d["qty"], "cost": d.get("amount", 0)}
                      for d in se_details]
        }
        traceability.append(chain)
        print(f"  {se['name']}: Issue={se.get('custom_issue', '-')} | "
              f"Asset={se.get('custom_asset', '-')} | "
              f"KTV={se.get('custom_technician', '-')}")
        for d in se_details:
            print(f"    └─ {d['item_code']} x{d['qty']} = {d.get('amount', 0):,.0f} VND")

    # --- Build result ---
    result = {
        "report_name": "Cost per Asset & Inventory Traceability",
        "generated_at": datetime.now().isoformat(),
        "cost_per_asset": cost_summary,
        "stock_levels": stock_levels,
        "traceability_chains": traceability
    }

    output_path = os.path.join(OUTPUT_DIR, "kpi_cost_per_asset.json")
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2, ensure_ascii=False, default=str)
    print(f"\n[SAVED] {output_path}")

    return result


if __name__ == "__main__":
    calculate_cost_per_asset()
