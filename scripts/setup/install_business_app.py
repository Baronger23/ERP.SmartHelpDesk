"""Install the business app into local Docker only, with a pre-install backup.

Uses argument arrays; never loads .env credentials or connects to Frappe Cloud.
"""
import argparse
import os
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[2]


def run(*arguments, env=None):
    subprocess.run(list(arguments), check=True, cwd=ROOT, env=env)


def fix_local_realtime_origin():
    # Validate the browser's actual origin at the edge, then use the resolvable
    # Docker frontend host for Frappe realtime's internal authentication fetch.
    script = "\n".join([
        "from pathlib import Path",
        "import re",
        "p = Path('/etc/nginx/conf.d/frappe.conf')",
        "before = p.read_text()",
        "source = re.sub(r'map \\$http_origin \\$shd_socket_origin \\{.*?\\}\\n\\n', '', before, flags=re.S)",
        "lines = []; inside = False",
        "for line in source.splitlines():",
        "    if line.strip().startswith('location /socket.io'):",
        "        inside = True; lines.append(line)",
        "        if 'if ($shd_bad_socket_origin)' not in source: lines.append('\\t\\tif ($shd_bad_socket_origin) { return 403; }')",
        "        continue",
        "    if inside and line.strip().startswith('proxy_set_header Origin '): line = '\\t\\tproxy_set_header Origin http://frontend:8080;'",
        "    if inside and line.strip().startswith('proxy_set_header Host '): line = '\\t\\tproxy_set_header Host frontend:8080;'",
        "    lines.append(line)",
        "    if inside and line.strip() == '}': inside = False",
        "after = '\\n'.join(lines) + '\\n'",
        "if 'map \"$http_origin|$http_host\" $shd_bad_socket_origin' not in after:",
        "    after = 'map \"$http_origin|$http_host\" $shd_bad_socket_origin {\\n\\tdefault 1;\\n\\t~^[|] 0;\\n\\t~^https?://([^/]+)[|]\\\\1$ 0;\\n}\\n\\n' + after",
        "backup = p.with_name('frappe.conf.before-smart-helpdesk')",
        "if before != after:",
        "    if not backup.exists(): backup.write_text(before)",
        "    p.write_text(after)",
    ])
    run("docker", "exec", "--user", "root", "frappe_docker-frontend-1", "env/bin/python", "-c", script)
    run("docker", "exec", "--user", "root", "frappe_docker-frontend-1", "nginx", "-t")
    run("docker", "exec", "--user", "root", "frappe_docker-frontend-1", "nginx", "-s", "reload")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--site", default="frontend")
    parser.add_argument("--compose", type=Path, default=ROOT.parent / "frappe_docker" / "pwd.yml")
    args = parser.parse_args()
    if not args.compose.is_file():
        parser.error("Local ERPNext compose file not found")
    env = dict(os.environ, SHD_APP_PATH=(ROOT / "apps" / "smart_helpdesk").as_posix())
    run("docker", "exec", "frappe_docker-backend-1", "bench", "--site", args.site, "backup", "--with-files")
    run("docker", "compose", "-p", "frappe_docker", "-f", str(args.compose), "-f",
        str(ROOT / "docker" / "compose.business.yml"), "up", "-d", "--no-deps",
        "backend", "queue-short", "queue-long", "scheduler", env=env)
    run("docker", "exec", "frappe_docker-backend-1", "env/bin/pip", "install", "--no-deps", "-e", "apps/smart_helpdesk")
    script = (
        "from pathlib import Path; p=Path('sites/apps.txt'); "
        "names=p.read_text().splitlines(); "
        "p.write_text('\\n'.join(dict.fromkeys(names+['smart_helpdesk']))+'\\n')"
    )
    run("docker", "exec", "frappe_docker-backend-1", "env/bin/python", "-c", script)
    run("docker", "exec", "frappe_docker-backend-1", "bench", "--site", args.site, "install-app", "smart_helpdesk")
    run("docker", "exec", "frappe_docker-backend-1", "bench", "--site", args.site, "migrate")
    run("docker", "restart", "frappe_docker-backend-1", "frappe_docker-queue-short-1",
        "frappe_docker-queue-long-1", "frappe_docker-scheduler-1")
    fix_local_realtime_origin()


if __name__ == "__main__":
    main()
