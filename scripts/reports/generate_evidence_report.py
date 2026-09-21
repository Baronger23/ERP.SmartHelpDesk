"""
Master Evidence Generator
=========================
Chạy tất cả các script báo cáo KPI và tổng hợp kết quả
thành một file JSON tổng hợp + file markdown evidence report.
"""
import sys
import os
import json
from datetime import datetime

# Ensure scripts directory is importable
sys.path.insert(0, os.path.dirname(__file__))

OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "data", "evidence")
REPORT_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "docs", "reports", "evidence")
os.makedirs(OUTPUT_DIR, exist_ok=True)
os.makedirs(REPORT_DIR, exist_ok=True)


def run_all_reports():
    """Run all KPI reports and generate combined evidence."""
    print("=" * 70)
    print("  SMART HELPDESK & MAINTENANCE — EVIDENCE GENERATOR")
    print(f"  Generated at: {datetime.now().isoformat()}")
    print("=" * 70)

    results = {}

    # 1. SLA Compliance
    try:
        from kpi_sla_compliance import calculate_sla_compliance
        results["sla_compliance"] = calculate_sla_compliance()
    except Exception as e:
        print(f"[ERROR] SLA Compliance report failed: {e}")
        results["sla_compliance"] = {"error": str(e)}

    # 2. Cost per Asset
    try:
        from kpi_cost_per_asset import calculate_cost_per_asset
        results["cost_per_asset"] = calculate_cost_per_asset()
    except Exception as e:
        print(f"[ERROR] Cost per Asset report failed: {e}")
        results["cost_per_asset"] = {"error": str(e)}

    # 3. Maintenance Metrics
    try:
        from kpi_maintenance_metrics import calculate_maintenance_metrics
        results["maintenance_metrics"] = calculate_maintenance_metrics()
    except Exception as e:
        print(f"[ERROR] Maintenance Metrics report failed: {e}")
        results["maintenance_metrics"] = {"error": str(e)}

    # Save combined JSON
    combined_path = os.path.join(OUTPUT_DIR, "combined_evidence.json")
    with open(combined_path, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False, default=str)
    print(f"\n[SAVED] Combined JSON: {combined_path}")

    # Generate Markdown Evidence Report
    generate_markdown_report(results)

    return results


def generate_markdown_report(results):
    """Generate a markdown evidence report from KPI results."""
    md_lines = []
    md_lines.append("# Báo Cáo Evidence KPI — Smart HelpDesk & Maintenance")
    md_lines.append(f"*Tự động sinh bởi `generate_evidence_report.py` lúc {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*\n")
    md_lines.append("---\n")

    # --- SLA Compliance Section ---
    sla = results.get("sla_compliance")
    if sla and "summary" in sla:
        s = sla["summary"]
        md_lines.append("## 1. SLA Compliance & Logging Latency\n")
        md_lines.append("| Chỉ số | Giá trị |")
        md_lines.append("| :--- | :---: |")
        md_lines.append(f"| **SLA Compliance Rate** | **{s['sla_compliance_rate']}%** |")
        md_lines.append(f"| Total Resolved Issues | {s['total_resolved']} |")
        md_lines.append(f"| Avg Logging Latency | {s['avg_logging_latency_minutes']} phút |")
        md_lines.append(f"| FTFR (First-Time Fix Rate) | {s['ftfr_percent']}% |")
        md_lines.append("")

        # By Tier
        if sla.get("by_tier"):
            md_lines.append("### SLA Compliance theo Phân hạng Khách hàng\n")
            md_lines.append("| SLA Tier | Total | Met | Breached | Rate |")
            md_lines.append("| :--- | :---: | :---: | :---: | :---: |")
            for tier in sla["by_tier"]:
                md_lines.append(f"| {tier['sla_tier']} | {tier['total']} | {tier['met']} | "
                                f"{tier['breached']} | **{tier['compliance_rate']}%** |")
            md_lines.append("")

        # Detail table
        if sla.get("sla_details"):
            md_lines.append("### Chi tiết SLA từng Issue\n")
            md_lines.append("| Issue | Customer | Priority | SLA Compliant |")
            md_lines.append("| :--- | :--- | :---: | :---: |")
            for d in sla["sla_details"]:
                status = "✅" if d["sla_compliant"] else "❌"
                md_lines.append(f"| {d['issue']} | {d['customer']} | {d['priority']} | {status} |")
            md_lines.append("")

    # --- Cost per Asset Section ---
    cost = results.get("cost_per_asset")
    if cost and cost.get("cost_per_asset"):
        md_lines.append("## 2. Chi phí Bảo trì theo Tài sản (Cost per Asset)\n")
        md_lines.append("| Asset | Tên | Tổng Chi phí (VND) | Số lượng Linh kiện | Tickets Liên quan |")
        md_lines.append("| :--- | :--- | ---: | :---: | :--- |")
        for a in cost["cost_per_asset"]:
            issues_str = ", ".join(a["unique_issues"]) if a["unique_issues"] else "—"
            md_lines.append(f"| {a['asset_id']} | {a['asset_name']} | "
                            f"{a['total_cost_vnd']:,.0f} | {a['total_parts_qty']:.0f} | {issues_str} |")
        md_lines.append("")

        # Traceability
        if cost.get("traceability_chains"):
            md_lines.append("### Chuỗi Truy xuất Nguồn gốc (Issue → Stock Entry → Items)\n")
            for chain in cost["traceability_chains"]:
                md_lines.append(f"**{chain['stock_entry']}** → Issue: `{chain['issue']}` | "
                                f"Asset: `{chain['asset']}` | KTV: `{chain['technician']}`")
                for item in chain["items"]:
                    md_lines.append(f"  - {item['item']} × {item['qty']} = {item.get('cost', 0):,.0f} VND")
                md_lines.append("")

    # --- Maintenance Metrics Section ---
    maint = results.get("maintenance_metrics")
    if maint and "summary" in maint:
        s = maint["summary"]
        md_lines.append("## 3. Chỉ số Bảo trì (MTTR, PM Compliance, Root Cause)\n")
        md_lines.append("| Chỉ số | Giá trị |")
        md_lines.append("| :--- | :---: |")
        md_lines.append(f"| **MTTR (Mean Time To Repair)** | **{s['overall_mttr_hours']} giờ** |")
        md_lines.append(f"| **PM Compliance** | **{s['pm_compliance_percent']}%** |")
        md_lines.append(f"| Issues Analyzed | {s['total_issues_analyzed']} |")
        md_lines.append(f"| PM Logs Total | {s['total_pm_logs']} |")
        md_lines.append("")

        # MTTR by Priority
        if maint.get("mttr_by_priority"):
            md_lines.append("### MTTR theo Mức độ Ưu tiên\n")
            md_lines.append("| Priority | Avg MTTR (giờ) | Số Issues |")
            md_lines.append("| :--- | :---: | :---: |")
            for p in maint["mttr_by_priority"]:
                md_lines.append(f"| {p['priority']} | {p['avg_mttr_hours']} | {p['count']} |")
            md_lines.append("")

        # Root Cause
        if maint.get("root_cause_distribution"):
            md_lines.append("### Phân bố Nguyên nhân Gốc (Root Cause)\n")
            md_lines.append("| Nguyên nhân | Số lượng | Tỷ lệ |")
            md_lines.append("| :--- | :---: | :---: |")
            for rc in maint["root_cause_distribution"]:
                md_lines.append(f"| {rc['root_cause']} | {rc['count']} | {rc['percentage']}% |")
            md_lines.append("")

    md_lines.append("---\n")
    md_lines.append("*Dữ liệu được truy xuất trực tiếp từ ERPNext REST API, "
                    "đảm bảo tính chính xác và khả kiểm chứng.*")

    # Save markdown
    md_path = os.path.join(REPORT_DIR, "kpi_evidence_report.md")
    with open(md_path, "w", encoding="utf-8") as f:
        f.write("\n".join(md_lines))
    print(f"[SAVED] Markdown Report: {md_path}")


if __name__ == "__main__":
    run_all_reports()
