"""Run isolated live ERP tests and save a scoped, reproducible evidence report."""
from datetime import datetime, timezone
import json
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[2]
SITE = "shd-test.localhost"


def bench(method):
    process = subprocess.run(["docker", "exec", "frappe_docker-backend-1", "bench", "--site", SITE,
        "execute", method], capture_output=True, text=True, encoding="utf-8", errors="replace")
    if process.returncode:
        print((process.stdout + process.stderr)[-10000:])
        raise SystemExit(process.returncode)
    if process.stderr:
        print(process.stderr.strip())
    for line in reversed(process.stdout.splitlines()):
        if line.startswith("{"):
            return json.loads(line)
    raise RuntimeError("No structured test result")


def main():
    # Schema migrations and cached Client Scripts must precede HTTP workers loading hooks.
    subprocess.run(["docker", "exec", "frappe_docker-backend-1", "bench", "--site", SITE,
                    "execute", "smart_helpdesk.install.sync"], check=True)
    subprocess.run(["docker", "restart", "frappe_docker-backend-1"], check=True, capture_output=True)
    checks = []
    for method in ("smart_helpdesk.tests.integration.run", "smart_helpdesk.tests.integration.run_concurrency",
                   "smart_helpdesk.tests.http_smoke.run"):
        report = bench(method)
        checks.append(report)
        print(json.dumps(report, ensure_ascii=False))
    calendar = subprocess.run(["docker", "exec", "frappe_docker-backend-1", "env/bin/python", "-m", "unittest",
        "smart_helpdesk.tests.test_calendar", "-v"], capture_output=True, text=True, encoding="utf-8", errors="replace")
    print(calendar.stderr)
    if calendar.returncode:
        raise SystemExit(calendar.returncode)
    checks.append({"scope": "deterministic_sla_calendar", "tests": 5, "success": True})
    output = ROOT / "data" / "business_validation.json"
    output.write_text(json.dumps({"checked_at": datetime.now(timezone.utc).isoformat(),
        "environment": {"site": SITE, "frappe": "16.33.1", "erpnext": "16.34.2", "database": "MariaDB 11.8"},
        "ai_runtime_included": False, "success": all(c["success"] for c in checks), "results": checks},
        indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print("Evidence:", output)


if __name__ == "__main__":
    main()
