"""
KPI Report: SLA Compliance & Logging Latency
=============================================
Truy vấn ERPNext API tính:
- SLA Compliance Rate theo Customer tier
- Logging Latency trung bình (creation - custom_incident_time)
- Phân tích chi tiết từng Issue
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


def parse_datetime(dt_str):
    """Parse ERPNext datetime string to Python datetime."""
    if not dt_str:
        return None
    for fmt in ("%Y-%m-%d %H:%M:%S.%f", "%Y-%m-%d %H:%M:%S", "%Y-%m-%dT%H:%M:%S.%f", "%Y-%m-%dT%H:%M:%S"):
        try:
            return datetime.strptime(dt_str, fmt)
        except ValueError:
            continue
    return None


def calculate_sla_compliance():
    """Query all Issues and calculate SLA metrics."""
    print("\n" + "=" * 60)
    print("  KPI REPORT: SLA COMPLIANCE & LOGGING LATENCY")
    print("=" * 60)

    # Fetch Issue names first (minimal fields to avoid permission errors)
    issue_list = fc.list_docs(
        "Issue",
        fields=["name"],
        limit=100
    )

    if not issue_list:
        print("[WARN] No issues found on the system.")
        return None

    print(f"\n[OK] Found {len(issue_list)} Issues on ERPNext. Fetching details...\n")

    # Fetch full details for each Issue individually
    issues = []
    for item in issue_list:
        doc = fc.get_doc("Issue", item["name"])
        if doc:
            issues.append(doc)

    # --- 1. SLA Compliance ---
    resolved_issues = [i for i in issues if i.get("status") in ("Resolved", "Closed")]
    sla_met = 0
    sla_breached = 0
    sla_details = []

    for issue in resolved_issues:
        resolution_date = parse_datetime(issue.get("resolution_date"))
        resolution_by = parse_datetime(issue.get("resolution_by"))

        if resolution_date and resolution_by:
            compliant = resolution_date <= resolution_by
            if compliant:
                sla_met += 1
            else:
                sla_breached += 1

            sla_details.append({
                "issue": issue["name"],
                "customer": issue.get("customer", "N/A"),
                "priority": issue.get("priority", "N/A"),
                "sla": issue.get("service_level_agreement", "N/A"),
                "resolution_date": str(resolution_date) if resolution_date else "N/A",
                "resolution_by": str(resolution_by) if resolution_by else "N/A",
                "sla_compliant": compliant
            })

    total_resolved = sla_met + sla_breached
    compliance_rate = (sla_met / total_resolved * 100) if total_resolved > 0 else 0

    print("--- SLA Compliance Summary ---")
    print(f"  Total Resolved Issues:  {total_resolved}")
    print(f"  SLA Met:                {sla_met}")
    print(f"  SLA Breached:           {sla_breached}")
    print(f"  SLA Compliance Rate:    {compliance_rate:.1f}%")

    # --- 2. SLA by Customer Tier ---
    tier_stats = {}
    for detail in sla_details:
        sla_name = detail["sla"]
        if sla_name not in tier_stats:
            tier_stats[sla_name] = {"met": 0, "breached": 0}
        if detail["sla_compliant"]:
            tier_stats[sla_name]["met"] += 1
        else:
            tier_stats[sla_name]["breached"] += 1

    print("\n--- SLA Compliance by Customer Tier ---")
    tier_summary = []
    for sla_name, stats in tier_stats.items():
        total = stats["met"] + stats["breached"]
        rate = (stats["met"] / total * 100) if total > 0 else 0
        tier_summary.append({
            "sla_tier": sla_name,
            "total": total,
            "met": stats["met"],
            "breached": stats["breached"],
            "compliance_rate": round(rate, 1)
        })
        print(f"  {sla_name}: {rate:.1f}% ({stats['met']}/{total})")

    # --- 3. Logging Latency ---
    print("\n--- Logging Latency (ΔT = creation - custom_incident_time) ---")
    latencies = []
    for issue in issues:
        creation = parse_datetime(issue.get("creation"))
        incident_time = parse_datetime(issue.get("custom_incident_time"))
        if creation and incident_time:
            delta_seconds = (creation - incident_time).total_seconds()
            delta_minutes = delta_seconds / 60
            latencies.append({
                "issue": issue["name"],
                "customer": issue.get("customer", "N/A"),
                "creation": str(creation),
                "incident_time": str(incident_time),
                "latency_minutes": round(delta_minutes, 1)
            })
            print(f"  {issue['name']}: ΔT = {delta_minutes:.1f} min")

    avg_latency = sum(l["latency_minutes"] for l in latencies) / len(latencies) if latencies else 0
    print(f"\n  Average Logging Latency: {avg_latency:.1f} minutes")

    # --- 4. FTFR (First-Time Fix Rate) ---
    corrective_closed = [i for i in issues
                         if i.get("status") in ("Resolved", "Closed")
                         and i.get("custom_root_cause") not in (None, "")]
    no_callback = [i for i in corrective_closed if not i.get("custom_has_callback")]
    ftfr = (len(no_callback) / len(corrective_closed) * 100) if corrective_closed else 0

    print(f"\n--- First-Time Fix Rate (FTFR) ---")
    print(f"  Corrective Issues Closed: {len(corrective_closed)}")
    print(f"  Without Callback:         {len(no_callback)}")
    print(f"  FTFR:                     {ftfr:.1f}%")

    # --- Build result ---
    result = {
        "report_name": "SLA Compliance & Logging Latency",
        "generated_at": datetime.now().isoformat(),
        "summary": {
            "total_issues": len(issues),
            "total_resolved": total_resolved,
            "sla_compliance_rate": round(compliance_rate, 1),
            "avg_logging_latency_minutes": round(avg_latency, 1),
            "ftfr_percent": round(ftfr, 1)
        },
        "by_tier": tier_summary,
        "sla_details": sla_details,
        "latency_details": latencies
    }

    # Save JSON
    output_path = os.path.join(OUTPUT_DIR, "kpi_sla_compliance.json")
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2, ensure_ascii=False)
    print(f"\n[SAVED] {output_path}")

    return result


if __name__ == "__main__":
    calculate_sla_compliance()
