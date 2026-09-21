@echo off
echo ===================================================
echo Stopping Local ERPNext Docker Environment...
echo ===================================================
set DOCKER_DIR=%~dp0..\..\frappe_docker
if not exist "%DOCKER_DIR%\pwd.yml" (
    echo [ERROR] frappe_docker directory not found at: %DOCKER_DIR%
    pause
    exit /b 1
)
cd /d "%DOCKER_DIR%"
docker compose -f pwd.yml stop
echo ===================================================
echo ERPNext containers stopped successfully to save RAM.
echo ===================================================
pause
