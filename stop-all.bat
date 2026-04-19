@echo off
setlocal enabledelayedexpansion
title SupplyChainGPT Council - Shutdown
color 0C

echo.
echo ============================================================
echo   SupplyChainGPT Council - Stopping All Services
echo ============================================================
echo.

REM ── 1. Stop Backend (FastAPI) ──
echo [1/3] Stopping Backend (FastAPI)...
for /f "tokens=5" %%a in ('netstat -aon ^| findstr :8000 ^| findstr LISTENING') do (
    taskkill /F /PID %%a >nul 2>&1
    if !errorlevel! equ 0 (
        echo   [OK] Backend stopped (PID: %%a)
    )
)
echo.

REM ── 2. Stop Frontend (React) ──
echo [2/3] Stopping Frontend (React)...
for /f "tokens=5" %%a in ('netstat -aon ^| findstr :3000 ^| findstr LISTENING') do (
    taskkill /F /PID %%a >nul 2>&1
    if !errorlevel! equ 0 (
        echo   [OK] Frontend stopped (PID: %%a)
    )
)
echo.

REM ── 3. Stop Docker services ──
echo [3/3] Stopping Docker services...
echo   - Redis
echo   - Neo4j
echo   - ChromaDB
echo   - Firecrawl
echo.

docker compose down 2>nul
if %errorlevel% equ 0 (
    echo   [OK] Docker services stopped
) else (
    echo   [WARNING] Docker compose down failed
    echo   You may need to stop containers manually:
    echo   docker compose down
)
echo.

REM ── 4. Close terminal windows ──
echo [4/4] Closing service terminal windows...
taskkill /FI "WindowTitle eq SupplyChainGPT Backend*" /F >nul 2>&1
taskkill /FI "WindowTitle eq SupplyChainGPT Frontend*" /F >nul 2>&1
echo   [OK] Terminal windows closed
echo.

echo ============================================================
echo   All services stopped!
echo ============================================================
echo.
echo   To restart, run: start-all.bat
echo.
pause
