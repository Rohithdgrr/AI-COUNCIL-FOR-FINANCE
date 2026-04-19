@echo off
setlocal enabledelayedexpansion
title SupplyChainGPT Council - Full Stack Launcher
color 0A

echo.
echo ============================================================
echo   SupplyChainGPT Council - Starting All Services
echo ============================================================
echo.

REM Check if .env exists
if not exist ".env" (
    echo [WARNING] .env file not found!
    echo Please copy .env.example to .env and configure your API keys.
    echo.
    echo Run: copy .env.example .env
    echo.
    pause
    exit /b 1
)

REM ── 1. Start Docker services (Redis, Neo4j, ChromaDB, Firecrawl) ──
echo [1/4] Starting Docker services...
echo   - Redis (cache + sessions)
echo   - Neo4j (knowledge graph)
echo   - ChromaDB (vector store)
echo   - Firecrawl (web scraping)
echo.

docker compose up -d 2>nul
if %errorlevel% neq 0 (
    echo   [ERROR] Docker compose failed!
    echo   Make sure Docker Desktop is running.
    echo.
    echo   Then run: docker compose up -d
    echo.
    pause
    exit /b 1
)

echo   [OK] Docker services starting...
echo.

REM ── 2. Wait for Docker services to be ready ──
echo [2/4] Waiting for Docker services to initialize (15s)...
timeout /t 15 /nobreak >nul
echo   [OK] Docker services should be ready
echo.

REM ── 3. Start Backend (FastAPI + AI Agents + MCP + RAG) ──
echo [3/4] Starting Backend (FastAPI on port 8000)...
echo   - AI Agents: Risk, Supply, Logistics, Market, Finance, Brand
echo   - Astra Simulations (Swarm Intelligence)
echo   - RAG Pipeline (Hybrid Retrieval)
echo   - MCP Tools (99+ external APIs)
echo.

REM Check if virtual environment exists
if not exist "venv\Scripts\python.exe" (
    echo   [WARNING] Virtual environment not found!
    echo   Please create it first: python -m venv venv
    echo   Then install dependencies: venv\Scripts\pip install -r backend\requirements.txt
    echo.
    pause
    exit /b 1
)

start "SupplyChainGPT Backend" cmd /k "cd /d %CD% && venv\Scripts\python.exe -m uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload"
echo   [OK] Backend starting at http://localhost:8000
echo   Wait ~10-15s for MCP initialization...
echo.

REM ── 4. Start Frontend (React + TypeScript) ──
echo [4/4] Starting Frontend (React on port 3000)...
echo.

REM Check if node_modules exists
if not exist "frontend\node_modules" (
    echo   [WARNING] Frontend dependencies not installed!
    echo   Please run: cd frontend ^&^& npm install
    echo.
    pause
    exit /b 1
)

start "SupplyChainGPT Frontend" cmd /k "cd /d %CD%\frontend && npm run dev"
echo   [OK] Frontend starting at http://localhost:3000
echo.

REM ── 5. Health Check ──
echo ============================================================
echo   Waiting for services to initialize (20s)...
echo ============================================================
timeout /t 20 /nobreak >nul

echo.
echo ============================================================
echo   Service Status:
echo ============================================================
echo.

REM Check Backend
curl -s http://localhost:8000/health >nul 2>&1
if %errorlevel% equ 0 (
    echo   [OK] Backend     - http://localhost:8000
) else (
    echo   [..] Backend     - Still initializing (check backend window)
)

REM Check Frontend
curl -s http://localhost:3000 >nul 2>&1
if %errorlevel% equ 0 (
    echo   [OK] Frontend    - http://localhost:3000
) else (
    echo   [..] Frontend    - Still initializing (check frontend window)
)

REM Check Firecrawl
curl -s http://localhost:3002 >nul 2>&1
if %errorlevel% equ 0 (
    echo   [OK] Firecrawl   - http://localhost:3002
) else (
    echo   [..] Firecrawl   - Still initializing
)

echo.
echo   Redis:      localhost:6379
echo   Neo4j:      http://localhost:7474 (user: neo4j, pass: testpassword)
echo   ChromaDB:   http://localhost:8001
echo.
echo ============================================================
echo   All services launched!
echo ============================================================
echo.
echo   Open your browser: http://localhost:3000
echo.
echo   To stop all services, run: stop-all.bat
echo.
echo   Press any key to exit this window.
echo   (Services will continue running in their own windows)
echo ============================================================
pause >nul
