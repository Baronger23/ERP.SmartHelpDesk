@echo off
echo ===================================================
echo Starting Local ERPNext Docker Environment...
echo ===================================================
set DOCKER_DIR=%~dp0..\..\frappe_docker
if not exist "%DOCKER_DIR%\pwd.yml" (
    echo [ERROR] frappe_docker directory not found at: %DOCKER_DIR%
    pause
    exit /b 1
)
cd /d "%DOCKER_DIR%"
docker compose -f pwd.yml start
echo ===================================================
echo ERPNext is running at: http://localhost:8080
echo ===================================================
pause
