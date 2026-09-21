# Báo Cáo Evidence KPI — Smart HelpDesk & Maintenance
*Tự động sinh bởi `generate_evidence_report.py` lúc 2026-09-21 11:18:39*

---

## 1. SLA Compliance & Logging Latency

| Chỉ số | Giá trị |
| :--- | :---: |
| **SLA Compliance Rate** | **0%** |
| Total Resolved Issues | 0 |
| Avg Logging Latency | 12004.2 phút |
| FTFR (First-Time Fix Rate) | 100.0% |

## 2. Chi phí Bảo trì theo Tài sản (Cost per Asset)

| Asset | Tên | Tổng Chi phí (VND) | Số lượng Linh kiện | Tickets Liên quan |
| :--- | :--- | ---: | :---: | :--- |
| ACC-ASS-2026-00002 | May nen khi Hitachi 75kW (AST-CMP-02) - Bao bi Tan A | 1,300,000 | 2 | ISS-2026-00001 |

### Chuỗi Truy xuất Nguồn gốc (Issue → Stock Entry → Items)

**MAT-STE-2026-00002** → Issue: `ISS-2026-00001` | Asset: `ACC-ASS-2026-00002` | KTV: `an.nguyen@smarthelpdesk.local`
  - PART-FLT-OIL01 × 2.0 = 1,300,000 VND

## 3. Chỉ số Bảo trì (MTTR, PM Compliance, Root Cause)

| Chỉ số | Giá trị |
| :--- | :---: |
| **MTTR (Mean Time To Repair)** | **0 giờ** |
| **PM Compliance** | **0.0%** |
| Issues Analyzed | 0 |
| PM Logs Total | 4 |

### Phân bố Nguyên nhân Gốc (Root Cause)

| Nguyên nhân | Số lượng | Tỷ lệ |
| :--- | :---: | :---: |
| Hardware Failure | 6 | 100.0% |

---

*Dữ liệu được truy xuất trực tiếp từ ERPNext REST API, đảm bảo tính chính xác và khả kiểm chứng.*