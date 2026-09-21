"""
06_SERVER_SCRIPT_PROTOTYPES.PY
Tài liệu mã nguồn nguyên mẫu (Prototypes) cho các giải pháp Fit-Gap nâng cao:
1. Skill-based Routing (Phân bổ theo Chuyên môn Kỹ thuật).
2. Proactive Technician Absence Filter (Lọc KTV nghỉ phép đầu ca qua Leave Application).
3. Reactive SLA Escalation Alert (Cảnh báo leo thang tiền vi phạm SLA cho Dispatcher).

Các đoạn mã này được thiết kế theo đúng chuẩn cú pháp Frappe Server Script / Scheduled Script (Python Sandbox).
"""

# ==============================================================================
# PROTOTYPE 1: SKILL-BASED ROUTING HOOK (DocType Event: Issue -> before_insert)
# ==============================================================================
PROTOTYPE_SKILL_BASED_ROUTING = """
# Frappe Server Script Type: DocType Event
# Reference DocType: Issue
# Event: before_insert

if doc.custom_asset:
    # 1. Bóc tách Asset Category từ Asset
    asset_doc = frappe.get_doc("Asset", doc.custom_asset)
    cat = asset_doc.asset_category

    # 2. Ma trận Kỹ năng (Skill Matrix: Asset Category -> Qualified Technicians)
    skill_matrix = {
        "AST-CAT-CMP": ["an.nguyen@smarthelpdesk.local"],                    # Khí nén: Nguyễn Văn An
        "AST-CAT-PRN": ["an.nguyen@smarthelpdesk.local"],                    # Cơ khí in: Nguyễn Văn An
        "AST-CAT-PNL": ["binh.tran@smarthelpdesk.local"],                    # Điện hạ thế: Trần Đình Bình
        "AST-CAT-CHL": ["cuong.le@smarthelpdesk.local"],                     # Nhiệt lạnh HVAC: Lê Hoàng Cường
        "AST-CAT-GEN": ["cuong.le@smarthelpdesk.local", "binh.tran@smarthelpdesk.local"] # Máy phát: Cường / Bình
    }

    qualified_techs = skill_matrix.get(cat, [])
    if qualified_techs:
        # Chọn KTV đầu tiên hoặc xoay vòng nội bộ nhóm đủ năng lực
        selected_tech = qualified_techs[0]
        # Lưu vết gán việc
        doc._assign = frappe.as_json([selected_tech])
        frappe.msgprint(f"He thong tu dong dinh tuyen theo chuyen mon ({cat}) toi KTV: {selected_tech}")
"""

# ==============================================================================
# PROTOTYPE 2: PROACTIVE TECHNICIAN ABSENCE FILTER (Scheduler Event: Daily 07:45)
# ==============================================================================
PROTOTYPE_PROACTIVE_LEAVE_FILTER = """
# Frappe Server Script Type: Scheduler Event
# Frequency: Daily (Cấu hình cron chạy lúc 07:45 sáng)

import frappe
from frappe.utils import today

current_date = today()

# 1. Tìm các đơn xin nghỉ phép đã được phê duyệt trong ngày hôm nay
approved_leaves = frappe.get_all(
    "Leave Application",
    filters=[
        ["status", "=", "Approved"],
        ["docstatus", "=", 1],
        ["from_date", "<=", current_date],
        ["to_date", ">=", current_date]
    ],
    fields=["employee", "employee_name"]
)

absent_users = []
for leave in approved_leaves:
    # Truy vấn User ID từ Employee DocType
    emp = frappe.get_doc("Employee", leave.employee)
    if emp.user_id:
        absent_users.append(emp.user_id)

# 2. Cập nhật bảng con users của Assignment Rule
rule_name = "Round Robin Assignment for Issues"
if frappe.db.exists("Assignment Rule", rule_name):
    rule = frappe.get_doc("Assignment Rule", rule_name)
    
    # Danh sách toàn bộ KTV của công ty
    master_tech_pool = [
        "an.nguyen@smarthelpdesk.local",
        "binh.tran@smarthelpdesk.local",
        "cuong.le@smarthelpdesk.local"
    ]
    
    # Lọc ra những KTV ĐANG ĐI LÀM (không có đơn nghỉ phép hôm nay)
    active_techs = [u for u in master_tech_pool if u not in absent_users]
    
    # Cập nhật lại child table users của rule
    rule.users = []
    for u in active_techs:
        rule.append("users", {"user": u})
        
    rule.save(ignore_permissions=True)
    frappe.logger().info(f"[ABSENCE FILTER] Cap nhat pool KTV truc ngay {current_date}: {active_techs} (Vang: {absent_users})")
"""

# ==============================================================================
# PROTOTYPE 3: REACTIVE SLA ESCALATION ALERT (Scheduler Event: Hourly / Every 15m)
# ==============================================================================
PROTOTYPE_REACTIVE_SLA_ALERT = """
# Frappe Server Script Type: Scheduler Event
# Frequency: Every 15 minutes

import frappe
from frappe.utils import now_datetime, get_datetime

current_time = now_datetime()

# Lấy các Issue đang mở chưa được phản hồi
open_issues = frappe.get_all(
    "Issue",
    filters=[
        ["status", "=", "Open"],
        ["first_responded_on", "is", "not set"],
        ["response_by", "is", "set"]
    ],
    fields=["name", "subject", "creation", "response_by", "_assign"]
)

for iss in open_issues:
    creation_time = get_datetime(iss.creation)
    deadline = get_datetime(iss.response_by)
    
    total_window = (deadline - creation_time).total_seconds()
    elapsed = (current_time - creation_time).total_seconds()
    
    # Nếu đã trôi qua hơn 50% thời hạn phản hồi mà KTV vẫn chưa xử lý
    if elapsed > (total_window * 0.5) and elapsed < total_window:
        # Bắn thông báo cảnh báo leo thang tới Dispatcher Desk
        msg = f"[CANH BAO TIEN VI PHAM SLA] Issue {iss.name} ({iss.subject}) da qua 50% thoi gian phan hoi! KTV duoc gan: {iss._assign}"
        frappe.publish_realtime("msgprint", {"message": msg, "alert": True, "indicator": "red"})
"""

# ==============================================================================
# PROTOTYPE 4: AUTOMATIC CALLBACK FLAG SYNCHRONIZATION (DocType Event: Issue -> after_insert)
# ==============================================================================
PROTOTYPE_AUTO_CALLBACK_FLAG = """
# Frappe Server Script Type: DocType Event
# Reference DocType: Issue
# Event: after_insert

if doc.custom_related_issue and doc.issue_type == "Callback / Recall":
    # Tu dong cap nhat co custom_has_callback tren Issue goc
    frappe.db.set_value("Issue", doc.custom_related_issue, "custom_has_callback", 1)
    frappe.msgprint(f"Da danh dau [Co Callback] tren Issue goc {doc.custom_related_issue} phuc vu tinh KPI FTFR.")
"""

if __name__ == "__main__":
    print("=== TAP LENH NGUYEN MAU SERVER SCRIPTS CHO FRAPPE / ERPNEXT ===")
    print("1. PROTOTYPE_SKILL_BASED_ROUTING (San sang)")
    print("2. PROTOTYPE_PROACTIVE_LEAVE_FILTER (San sang)")
    print("3. PROTOTYPE_REACTIVE_SLA_ALERT (San sang)")
    print("4. PROTOTYPE_AUTO_CALLBACK_FLAG (San sang)")
    print("\nCac script nay co the copy vao Module Server Script cua Frappe Desk khi nang cap pha cuoi ky.")
