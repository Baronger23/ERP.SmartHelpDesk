#!/usr/bin/env python3
"""
RUN_PIPELINE.PY
Unified Execution Pipeline for ERP Smart HelpDesk & Maintenance Management.
Executes Master Data Setup, Technicians & Routing, Custom Fields, SLA & Plans,
and End-to-End Scenarios in sequential order.
"""

import os
import sys
import time
import subprocess

PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(PROJECT_ROOT, "scripts", "core"))

import frappe_client as fc

STEPS = [
    {
        "step": "01",
        "title": "Master Data & Configuration (Company, Warehouses, Items, Assets)",
        "script": os.path.join(PROJECT_ROOT, "scripts", "setup", "01_setup_master_data.py")
    },
    {
        "step": "02",
        "title": "Technicians, Teams & Round Robin Assignment Rules",
        "script": os.path.join(PROJECT_ROOT, "scripts", "setup", "02_setup_technicians.py")
    },
    {
        "step": "03",
        "title": "DocType Custom Fields (FSM, SLA & Maintenance Links)",
        "script": os.path.join(PROJECT_ROOT, "scripts", "setup", "03_setup_custom_fields.py")
    },
    {
        "step": "04",
        "title": "SLA Policies, Priorities, Calendars & Maintenance Plans",
        "script": os.path.join(PROJECT_ROOT, "scripts", "setup", "04_setup_sla_and_plans.py")
    },
    {
        "step": "05",
        "title": "End-to-End Operational Scenarios & Evidence Collection",
        "script": os.path.join(PROJECT_ROOT, "scripts", "scenarios", "05_execute_scenarios.py")
    }
]

def print_banner():
    print("=" * 78)
    print("   ERP SMART HELPDESK & MAINTENANCE - AUTOMATED SETUP PIPELINE")
    print("=" * 78)
    print(f"[*] Target ERPNext URL : {fc.BASE_URL}")
    print(f"[*] Company Abbr       : {fc.COMPANY} ({fc.COMPANY_ABBR})")
    print(f"[*] Environment Mode   : {'LOCAL DOCKER' if 'localhost' in fc.BASE_URL or '127.0.0.1' in fc.BASE_URL else 'FRAPPE CLOUD'}")
    print("=" * 78)

def check_connectivity():
    print("[+] Checking connection to ERPNext server...", end=" ", flush=True)
    res = fc.request("GET", "/api/method/frappe.auth.get_logged_user")
    if res.get("_error"):
        print(f"FAILED!\n[!] Error: {res.get('message')}")
        print("[!] Please check your .env configuration and ensure the ERPNext instance is running.")
        sys.exit(1)
    user = res.get("message")
    print(f"SUCCESS! Connected as [{user}]")

def run_step(step_info):
    step_num = step_info["step"]
    title = step_info["title"]
    script_path = step_info["script"]

    print(f"\n>>>>> STEP {step_num}: {title} <<<<<")
    start_time = time.time()
    
    result = subprocess.run([sys.executable, script_path], cwd=PROJECT_ROOT)
    duration = time.time() - start_time
    
    if result.returncode != 0:
        print(f"\n[X] Step {step_num} FAILED with exit code {result.returncode} (took {duration:.2f}s)")
        sys.exit(result.returncode)
    else:
        print(f"[V] Step {step_num} completed successfully in {duration:.2f}s")

def main():
    print_banner()
    check_connectivity()
    
    pipeline_start = time.time()
    for s in STEPS:
        run_step(s)
        
    total_duration = time.time() - pipeline_start
    print("\n" + "=" * 78)
    print(f"   ALL 5 STEPS COMPLETED SUCCESSFULLY IN {total_duration:.2f}s")
    print("=" * 78)
    print(f"[*] Evidence data: data/verification_evidence.json")
    print(f"[*] System is fully operational and ready for use.")
    print("=" * 78)

if __name__ == "__main__":
    main()
