#!/usr/bin/env python3
"""
RUN_PIPELINE.PY
Thin entry point for the local Docker environment: installs/updates the
smart_helpdesk app on the Docker site via docker/install_business_app.py
(backup first, then the standard bench install-app + migrate inside the
container).

Development does NOT go through this script - the primary environment is
the native bench in WSL (see README). The historical midterm demo scripts
were removed from the repo; they remain available in git history at tag
pre-bench-baseline.
"""

import argparse
import os
import subprocess
import sys

PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))


def main():
    parser = argparse.ArgumentParser(
        description="Install the business app on the local Docker site")
    parser.add_argument("--site", default="frontend",
                        help="Local Docker site for business app installation")
    args = parser.parse_args()
    installer = os.path.join(PROJECT_ROOT, "docker", "install_business_app.py")
    subprocess.run([sys.executable, installer, "--site", args.site], check=True)


if __name__ == "__main__":
    main()
