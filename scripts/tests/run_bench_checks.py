"""One-command bench verification for Smart HelpDesk.

Builds the dedicated test site from blank on a native Frappe bench,
seeds the pre-web fixtures (buying price / currency) and the HTTP token,
starts the web server, then runs every suite — SLA calendar, live
ERPNext/MariaDB integration, stock-reservation concurrency, the
authenticated HTTP boundary and the Desk role acceptance (three
business flows executed as the AIS role holders on their own dataset,
plus cross-customer and expired-approval denial cases) — writes
data/business_validation.json and exits non-zero if anything fails,
so CI can gate on it.

Prerequisites: a bench with frappe + erpnext apps (see README), MariaDB
and Redis reachable, and the MariaDB root password available via
--db-root-password, $SHD_DB_ROOT_PASSWORD or a password file
(default ~/.dbpass when present).

Usage:
    python scripts/tests/run_bench_checks.py [--bench ~/frappe-bench]
        [--site shd-test.localhost] [--keep-site]
"""
import argparse
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import shutil
import socket
import subprocess
import sys
import time
from urllib.parse import urlparse
from urllib.error import URLError
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parents[2]
APP_DIR = ROOT / "apps" / "smart_helpdesk"
SUITES = ("smart_helpdesk.tests.integration.run",
          "smart_helpdesk.tests.integration.run_concurrency",
          "smart_helpdesk.tests.http_smoke.run",
          "smart_helpdesk.tests.acceptance.run")


def fail(message, process=None):
    print("ERROR:", message)
    if process is not None:
        print(((process.stdout or "") + (process.stderr or ""))[-8000:])
    raise SystemExit(1)


def run(arguments, cwd, check=True, env=None):
    shown = [str(a) for a in arguments]
    for index, value in enumerate(shown[:-1]):
        if value == "--db-root-password":
            shown[index + 1] = "********"
    print("+", " ".join(shown), flush=True)
    process = subprocess.run([str(a) for a in arguments], cwd=cwd, env=env,
                             stdin=subprocess.DEVNULL,
                             capture_output=True, text=True, encoding="utf-8",
                             errors="replace")
    if check and process.returncode:
        fail(f"command failed ({process.returncode})", process)
    return process


def bench_execute(bench, bench_dir, site, method):
    process = run([bench, "--site", site, "execute", method], cwd=bench_dir,
                  check=False)
    if process.returncode:
        print(((process.stdout or "") + (process.stderr or ""))[-8000:])
        return {"scope": method, "success": False,
                "error": f"exit {process.returncode}"}
    for line in reversed(process.stdout.splitlines()):
        if line.startswith("{"):
            return json.loads(line)
    return {"scope": method, "success": False, "error": "no JSON report"}


def tcp_open(port):
    try:
        with socket.create_connection(("127.0.0.1", port), timeout=2):
            return True
    except OSError:
        return False


def ensure_redis(bench_dir):
    """Frappe expects the bench Redis instances (cache/queue/socketio) to
    answer on the ports in common_site_config.json; a bare CI bench has
    none running and the ERPNext install dies on the first cache write.
    Spawn a plain redis-server for every configured port that is closed
    and return the processes so the caller can stop them afterwards."""
    config = {}
    config_path = bench_dir / "sites" / "common_site_config.json"
    if config_path.is_file():
        config = json.loads(config_path.read_text(encoding="utf-8"))
    spawned = []
    for key, default in (("redis_cache", 11000), ("redis_queue", 12000),
                         ("redis_socketio", 13000)):
        port = urlparse(config.get(key, "")).port or default
        if tcp_open(port):
            continue
        if not shutil.which("redis-server"):
            fail(f"port {port} ({key}) is closed and redis-server is not on PATH")
        print(f"Starting redis-server on :{port} ({key})")
        spawned.append(subprocess.Popen(
            ["redis-server", "--port", str(port), "--save", "",
             "--appendonly", "no", "--protected-mode", "no"],
            stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL))
        for _ in range(25):
            if tcp_open(port):
                break
            time.sleep(0.2)
    return spawned


def wait_for_web(site, port, timeout=120):
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            request = Request(f"http://127.0.0.1:{port}/",
                              headers={"Host": site})
            with urlopen(request, timeout=5) as response:
                if response.status in (200, 302):
                    return True
        except URLError:
            pass
        except Exception:
            pass
        time.sleep(2)
    return False


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--bench", type=Path, default=None,
                        help="bench directory (default: $BENCH_DIR, ~/frappe-bench, or cwd)")
    parser.add_argument("--site", default="shd-test.localhost")
    parser.add_argument("--admin-password", default="admin")
    parser.add_argument("--db-root-password", default=os.environ.get("SHD_DB_ROOT_PASSWORD"))
    parser.add_argument("--db-root-password-file", type=Path, default=None)
    parser.add_argument("--port", type=int, default=8000)
    parser.add_argument("--keep-site", action="store_true",
                        help="do not drop an existing test site first (still rebuilds nothing)")
    args = parser.parse_args()

    bench_dir = args.bench or (Path(os.environ["BENCH_DIR"]) if os.environ.get("BENCH_DIR")
                               else Path.home() / "frappe-bench")
    if not (bench_dir / "sites").is_dir():
        if (Path.cwd() / "sites").is_dir():
            bench_dir = Path.cwd()
        else:
            fail(f"bench directory not found: {bench_dir}")
    bench = shutil.which("bench") or str(bench_dir / "env" / "bin" / "bench")
    password = args.db_root_password
    if not password:
        password_file = args.db_root_password_file or Path.home() / ".dbpass"
        if password_file.is_file():
            password = password_file.read_text(encoding="utf-8").strip()
    if not password:
        fail("MariaDB root password required (--db-root-password, "
             "$SHD_DB_ROOT_PASSWORD or --db-root-password-file)")

    # 1. Make sure THIS repo's app is the one the bench runs.
    bench_app = bench_dir / "apps" / "smart_helpdesk"
    if not bench_app.exists():
        print(f"Linking {bench_app} -> {APP_DIR}")
        os.symlink(APP_DIR, bench_app)
        run([bench_dir / "env" / "bin" / "pip", "install", "-e", "apps/smart_helpdesk"],
            cwd=bench_dir)
    elif Path(os.path.realpath(bench_app)) != Path(os.path.realpath(APP_DIR)):
        print(f"WARNING: bench app is {os.path.realpath(bench_app)}, "
              f"not this repo's {APP_DIR}; testing the bench copy.")
    apps_txt = bench_dir / "sites" / "apps.txt"
    names = apps_txt.read_text(encoding="utf-8").split() if apps_txt.exists() else []
    if "smart_helpdesk" not in names:
        apps_txt.write_text("\n".join([*names, "smart_helpdesk"]) + "\n",
                            encoding="utf-8")

    site = args.site
    if not site.startswith("shd-test."):
        fail("test site name must start with shd-test. (suite guard)")

    # 1b. The bench Redis instances must answer before any site work:
    #     the ERPNext install writes through the cache layer and dies
    #     with ConnectionError on port 11000 when redis_cache is down.
    redis_procs = ensure_redis(bench_dir)
    try:
        _run_all(args, bench, bench_dir, site, password, redis_procs)
    finally:
        for proc in redis_procs:
            proc.terminate()


def _run_all(args, bench, bench_dir, site, password, redis_procs):
    # 2. Blank test site: drop any previous one, create fresh, install apps.
    if not args.keep_site:
        run([bench, "drop-site", site, "--force", "--no-backup",
             "--db-root-username", "root", "--db-root-password", password],
            cwd=bench_dir, check=False)
    if not (bench_dir / "sites" / site).exists():
        # --db-root-username must be explicit: without it frappe prompts
        # "Enter mysql super user [root]:" and blocks forever on a TTY.
        run([bench, "new-site", site, "--db-root-username", "root",
             "--db-root-password", password,
             "--admin-password", args.admin_password, "--install-app", "erpnext"],
            cwd=bench_dir)
    run([bench, "--site", site, "install-app", "smart_helpdesk"], cwd=bench_dir,
        check=False)
    run([bench, "--site", site, "migrate"], cwd=bench_dir)
    run([bench, "--site", site, "set-config", "allow_tests", "true"], cwd=bench_dir)

    checks = []
    web = None
    log_path = ROOT / "data" / "bench_web.log"
    try:
        # 3. Fixtures (buying price / currency / master data) and the HTTP
        #    token are prepared BEFORE the web server starts.
        checks.append(bench_execute(bench, bench_dir, site,
                                    "smart_helpdesk.tests.fixtures.seed"))
        checks.append(bench_execute(bench, bench_dir, site,
                                    "smart_helpdesk.tests.fixtures.prepare_http_token"))

        # 4. Web up, then the live suites.
        log_path.parent.mkdir(parents=True, exist_ok=True)
        with open(log_path, "w", encoding="utf-8") as log:
            web = subprocess.Popen([bench, "--site", site, "serve",
                                    "--port", str(args.port)],
                                   cwd=bench_dir, stdin=subprocess.DEVNULL,
                                   stdout=log, stderr=log)
        if not wait_for_web(site, args.port):
            fail(f"web server did not answer on port {args.port}; see {log_path}")
        print(f"Web serving {site} on :{args.port}")
        for method in SUITES:
            checks.append(bench_execute(bench, bench_dir, site, method))
    finally:
        if web is not None:
            web.terminate()
            try:
                web.wait(timeout=15)
            except subprocess.TimeoutExpired:
                web.kill()

    # 5. Deterministic SLA calendar suite (pure Python, no site needed).
    calendar = run([bench_dir / "env" / "bin" / "python", "-m", "unittest",
                    "smart_helpdesk.tests.test_calendar", "-v"],
                   cwd=bench_dir, check=False)
    print(calendar.stderr)
    checks.append({"scope": "deterministic_sla_calendar", "tests": 5,
                   "success": calendar.returncode == 0})

    success = all(c.get("success") for c in checks)
    output = ROOT / "data" / "business_validation.json"
    output.write_text(json.dumps({
        "checked_at": datetime.now(timezone.utc).isoformat(),
        "environment": {"runner": "bench", "site": site, "frappe": "16.33.1",
                        "erpnext": "16.34.2", "database": "MariaDB 11.8"},
        "ai_runtime_included": False, "success": success, "results": checks},
        indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    for check in checks:
        print(("PASS " if check.get("success") else "FAIL "), check.get("scope"))
    print("Evidence:", output)
    raise SystemExit(0 if success else 1)


if __name__ == "__main__":
    main()
