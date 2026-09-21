"""
KPI Report: Maintenance Metrics (MTTR, PM Compliance)
=====================================================
Truy vấn ERPNext API tính:
- MTTR (Mean Time To Repair): Thời gian trung bình xử lý Issue
- PM Compliance: Tỷ lệ hoàn thành bảo trì đúng hạn
- Issue phân loại theo Root Cause
"""
import sys
import os
import json
from datetime import datetime

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "core")))
import frappe_client as fc

OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "data", "evidence")
os.makedirs(OUTPUT_DIR, exist_ok=True)


def parse_datetime(dt_str):
    """Parse ERPNext datetime string."""
    if not dt_str:
        return None
    for fmt in ("%Y-%m-%d %H:%M:%S.%f", "%Y-%m-%d %H:%M:%S", "%Y-%m-%dT%H:%M:%S.%f", "%Y-%m-%dT%H:%M:%S"):
        try:
            return datetime.strptime(dt_str, fmt)
        except ValueError:
            continue
    return None


def calculate_maintenance_metrics():
    """Calculate MTTR, PM Compliance, and Root Cause distribution."""
    print("\n" + "=" * 60)
    print("  KPI REPORT: MTTR, PM COMPLIANCE & ROOT CAUSE ANALYSIS")
    print("=" * 60)

    # --- 1. MTTR (Mean Time To Repair) ---
    print("\n--- MTTR (Mean Time To Repair) ---")

    # Fetch Issue names first (minimal fields)
    issue_list = fc.list_docs(
        "Issue",
        filters=[["status", "in", ["Resolved", "Closed"]]],
        fields=["name"],
        limit=100
    )

    # Fetch full details per Issue
    issues = []
    for item in issue_list:
        doc = fc.get_doc("Issue", item["name"])
        if doc:
            issues.append(doc)

    mttr_data = []
    for issue in issues:
        creation = parse_datetime(issue.get("creation"))
        resolution = parse_datetime(issue.get("resolution_date"))
        if creation and resolution:
            delta_hours = (resolution - creation).total_seconds() / 3600
            mttr_data.append({
                "issue": issue["name"],
                "customer": issue.get("customer", "N/A"),
                "priority": issue.get("priority", "N/A"),
                "asset": issue.get("custom_asset", "N/A"),
                "creation": str(creation),
                "resolution": str(resolution),
                "resolution_hours": round(delta_hours, 2)
            })
            print(f"  {issue['name']}: {delta_hours:.2f}h ({issue.get('priority', 'N/A')})")

    avg_mttr = sum(d["resolution_hours"] for d in mttr_data) / len(mttr_data) if mttr_data else 0
    print(f"\n  Overall MTTR: {avg_mttr:.2f} hours")

    # MTTR by Priority
    print("\n--- MTTR by Priority ---")
    priority_mttr = {}
    for d in mttr_data:
        p = d["priority"]
        if p not in priority_mttr:
            priority_mttr[p] = []
        priority_mttr[p].append(d["resolution_hours"])

    mttr_by_priority = []
    for priority, hours_list in priority_mttr.items():
        avg = sum(hours_list) / len(hours_list)
        mttr_by_priority.append({
            "priority": priority,
            "avg_mttr_hours": round(avg, 2),
            "count": len(hours_list)
        })
        print(f"  {priority}: {avg:.2f}h ({len(hours_list)} issues)")

    # MTTR by Asset
    print("\n--- MTTR by Asset ---")
    asset_mttr = {}
    for d in mttr_data:
        a = d["asset"] or "Unlinked"
        if a not in asset_mttr:
            asset_mttr[a] = []
        asset_mttr[a].append(d["resolution_hours"])

    mttr_by_asset = []
    for asset, hours_list in asset_mttr.items():
        avg = sum(hours_list) / len(hours_list)
        asset_name = asset
        if asset != "Unlinked":
            doc = fc.get_doc("Asset", asset)
            if doc:
                asset_name = doc.get("asset_name", asset)
        mttr_by_asset.append({
            "asset": asset,
            "asset_name": asset_name,
            "avg_mttr_hours": round(avg, 2),
            "count": len(hours_list)
        })
        print(f"  {asset_name}: {avg:.2f}h ({len(hours_list)} issues)")

    # --- 2. PM Compliance ---
    print("\n--- PM Compliance (Preventive Maintenance) ---")

    # Fetch Asset Maintenance Logs
    pm_logs = fc.list_docs(
        "Asset Maintenance Log",
        fields=["name", "asset_maintenance", "task", "due_date",
                "completion_date", "has_certificate", "actions_performed"],
        limit=100
    )

    pm_total = len(pm_logs)
    pm_on_time = 0
    pm_late = 0
    pm_details = []

    for log in pm_logs:
        due = parse_datetime(log.get("due_date"))
        completed = parse_datetime(log.get("completion_date"))

        if due and completed:
            on_time = completed <= due
        elif completed:
            on_time = True  # No due date set, consider on time
        else:
            on_time = False  # Not completed

        if on_time:
            pm_on_time += 1
        else:
            pm_late += 1

        pm_details.append({
            "log": log["name"],
            "maintenance": log.get("asset_maintenance", "N/A"),
            "task": log.get("task", "N/A"),
            "due_date": str(due) if due else "N/A",
            "completion_date": str(completed) if completed else "N/A",
            "on_time": on_time
        })

    pm_compliance = (pm_on_time / pm_total * 100) if pm_total > 0 else 0

    print(f"  Total PM Logs:     {pm_total}")
    print(f"  Completed On Time: {pm_on_time}")
    print(f"  Late/Incomplete:   {pm_late}")
    print(f"  PM Compliance:     {pm_compliance:.1f}%")

    # --- 3. Root Cause Distribution ---
    print("\n--- Root Cause Distribution ---")

    all_issue_names = fc.list_docs(
        "Issue",
        fields=["name"],
        limit=100
    )

    all_issues = []
    for item in all_issue_names:
        doc = fc.get_doc("Issue", item["name"])
        if doc:
            all_issues.append(doc)

    root_cause_counts = {}
    for issue in all_issues:
        rc = issue.get("custom_root_cause") or "Not Classified"
        root_cause_counts[rc] = root_cause_counts.get(rc, 0) + 1

    root_cause_dist = []
    for rc, count in sorted(root_cause_counts.items(), key=lambda x: -x[1]):
        pct = count / len(all_issues) * 100 if all_issues else 0
        root_cause_dist.append({
            "root_cause": rc,
            "count": count,
            "percentage": round(pct, 1)
        })
        print(f"  {rc}: {count} ({pct:.1f}%)")

    # --- Build result ---
    result = {
        "report_name": "Maintenance Metrics (MTTR, PM Compliance, Root Cause)",
        "generated_at": datetime.now().isoformat(),
        "summary": {
            "overall_mttr_hours": round(avg_mttr, 2),
            "pm_compliance_percent": round(pm_compliance, 1),
            "total_issues_analyzed": len(mttr_data),
            "total_pm_logs": pm_total
        },
        "mttr_details": mttr_data,
        "mttr_by_priority": mttr_by_priority,
        "mttr_by_asset": mttr_by_asset,
        "pm_compliance_details": pm_details,
        "root_cause_distribution": root_cause_dist
    }

    output_path = os.path.join(OUTPUT_DIR, "kpi_maintenance_metrics.json")
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2, ensure_ascii=False, default=str)
    print(f"\n[SAVED] {output_path}")

    return result


if __name__ == "__main__":
    calculate_maintenance_metrics()
