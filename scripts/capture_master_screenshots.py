"""
Master Screenshot Capture Script for Smart HelpDesk & Maintenance
Captures authentic, high-resolution screenshots from local Docker ERPNext (http://localhost:8080)
matching the current codebase, master data, custom fields, SLA matrix, and skill-based assignments.
"""

import os
import glob
import time
import requests
from playwright.sync_api import sync_playwright

BASE_URL = os.getenv("FRAPPE_BASE_URL", "http://localhost:8080")
USERNAME = os.getenv("FRAPPE_USERNAME", "an.nguyen@smarthelpdesk.local")
PASSWORD = os.getenv("FRAPPE_PASSWORD", "AlphaTech@2026!")

OUTPUT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "docs", "assets", "screenshots"))
os.makedirs(OUTPUT_DIR, exist_ok=True)

print(f"Connecting to {BASE_URL} as {USERNAME}...")
session = requests.Session()
login_res = session.post(f"{BASE_URL}/api/method/login", data={"usr": USERNAME, "pwd": PASSWORD})
if login_res.status_code != 200:
    print(f"Login failed: {login_res.status_code} - {login_res.text}")
    exit(1)

sid = session.cookies.get("sid")
print(f"Logged in successfully. Session ID: {sid[:10]}...")

def clean_page(page):
    page.evaluate("""() => {
        // Remove onboarding modals, dialogs, backdrops, and tours
        const selectors = [
            '.user-onboarding', '.onb-panel', '.modal-backdrop',
            '.onboarding-widget-box', '[data-doctype="Onboarding Step"]',
            '.tour-popover', '.desk-alert', '.modal-dialog',
            '.onboarding-sidebar', '.body-sidebar-bottom'
        ];
        selectors.forEach(sel => {
            document.querySelectorAll(sel).forEach(el => el.remove());
        });
    }""")

def clear_list_filters(page):
    page.evaluate("""() => {
        if (window.cur_list && window.cur_list.filter_area) {
            window.cur_list.filter_area.clear();
        }
    }""")

with sync_playwright() as p:
    browser = p.chromium.launch(
        executable_path=r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
        headless=True
    )
    context = browser.new_context(viewport={"width": 1600, "height": 1000})
    context.add_cookies([{"name": "sid", "value": sid, "domain": "localhost", "path": "/"}])
    page = context.new_page()

    # 1. 01_issue_list.png
    print("\n[1/8] Capturing 01_issue_list.png...")
    page.goto(f"{BASE_URL}/app/issue")
    page.wait_for_timeout(3000)
    clean_page(page)
    clear_list_filters(page)
    page.wait_for_timeout(2000)
    clean_page(page)
    p01 = os.path.join(OUTPUT_DIR, "01_issue_list.png")
    page.screenshot(path=p01)
    print(f"  -> Saved: {p01}")

    # 2. 02_issue_detail_sla.png
    print("\n[2/8] Capturing 02_issue_detail_sla.png...")
    page.goto(f"{BASE_URL}/app/issue/ISS-2026-00001")
    page.wait_for_timeout(3500)
    clean_page(page)
    p02 = os.path.join(OUTPUT_DIR, "02_issue_detail_sla.png")
    page.screenshot(path=p02)
    print(f"  -> Saved: {p02}")

    # 3. 03_stock_entry_repair.png
    print("\n[3/8] Capturing 03_stock_entry_repair.png...")
    page.goto(f"{BASE_URL}/app/stock-entry/MAT-STE-2026-00002")
    page.wait_for_timeout(3500)
    clean_page(page)
    p03 = os.path.join(OUTPUT_DIR, "03_stock_entry_repair.png")
    page.screenshot(path=p03)
    print(f"  -> Saved: {p03}")

    # 4. 04_asset_maintenance_log.png
    print("\n[4/8] Capturing 04_asset_maintenance_log.png...")
    page.goto(f"{BASE_URL}/app/asset-maintenance-log/ACC-AML-2026-00004")
    page.wait_for_timeout(3500)
    clean_page(page)
    p04 = os.path.join(OUTPUT_DIR, "04_asset_maintenance_log.png")
    page.screenshot(path=p04)
    print(f"  -> Saved: {p04}")

    # 5. 05_asset_list.png
    print("\n[5/8] Capturing 05_asset_list.png...")
    page.goto(f"{BASE_URL}/app/asset")
    page.wait_for_timeout(3000)
    clean_page(page)
    clear_list_filters(page)
    page.wait_for_timeout(2000)
    clean_page(page)
    p05 = os.path.join(OUTPUT_DIR, "05_asset_list.png")
    page.screenshot(path=p05)
    print(f"  -> Saved: {p05}")

    # 6. 06_item_reorder.png
    print("\n[6/8] Capturing 06_item_reorder.png...")
    page.goto(f"{BASE_URL}/app/item/PART-FLT-OIL01")
    page.wait_for_timeout(3000)
    clean_page(page)
    # Switch to Inventory tab
    page.evaluate("""() => {
        const tabs = Array.from(document.querySelectorAll('.form-tabs .nav-link'));
        const invTab = tabs.find(t => t.textContent.trim().toLowerCase() === 'inventory');
        if (invTab) invTab.click();
    }""")
    page.wait_for_timeout(1000)
    # Click to expand Auto re-order section
    page.click("text=Auto re-order")
    page.wait_for_timeout(1500)
    clean_page(page)
    p06 = os.path.join(OUTPUT_DIR, "06_item_reorder.png")
    page.screenshot(path=p06)
    print(f"  -> Saved: {p06}")

    # 7. 07_sla_vip_detail.png
    print("\n[7/8] Capturing 07_sla_vip_detail.png...")
    page.goto(f"{BASE_URL}/app/service-level-agreement/SLA-Issue-SLA%20Khach%20hang%20VIP")
    page.wait_for_timeout(3000)
    clean_page(page)
    p07 = os.path.join(OUTPUT_DIR, "07_sla_vip_detail.png")
    page.screenshot(path=p07)
    print(f"  -> Saved: {p07}")

    # 8. 08_asset_maintenance_list.png
    print("\n[8/8] Capturing 08_asset_maintenance_list.png...")
    page.goto(f"{BASE_URL}/app/asset-maintenance")
    page.wait_for_timeout(3000)
    clean_page(page)
    clear_list_filters(page)
    page.wait_for_timeout(2000)
    clean_page(page)
    p08 = os.path.join(OUTPUT_DIR, "08_asset_maintenance_list.png")
    page.screenshot(path=p08)
    print(f"  -> Saved: {p08}")

    browser.close()

# Cleanup any temporary test screenshots
test_files = glob.glob(os.path.join(OUTPUT_DIR, "test_*.png"))
for tf in test_files:
    try:
        os.remove(tf)
        print(f"Removed temporary file: {os.path.basename(tf)}")
    except Exception:
        pass

print("\n=== ALL 8 MASTER SCREENSHOTS CAPTURED AND UPDATED SUCCESSFULLY ===")
