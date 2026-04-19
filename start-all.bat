@echo off
title SupplyChainGPT Council - Full Stack Launcher
echo ============================================================
echo   SupplyChainGPT Council - Starting All Services
echo ============================================================
echo.

REM ── 1. Start Docker services (Redis, Neo4j, ChromaDB) ──
echo [1/5] Starting Docker databases...
docker compose up -d redis neo4j chromadb 2>nul
if %errorlevel% neq 0 (
    echo   WARNING: Docker compose failed. Ensure Docker Desktop is running.
    echo   Run manually: docker compose up -d redis neo4j chromadb
) else (
    echo   OK: Redis, Neo4j, and ChromaDB are running
)
echo.

REM ── 2. Start Firecrawl (self-hosted, unlimited web scraping) ──
echo [2/5] Starting Firecrawl web scraping service...
pushd firecrawl
docker compose up -d 2>nul
if %errorlevel% neq 0 (
    echo   WARNING: Firecrawl failed to start. Run manually:
    echo   cd firecrawl ^&^& docker compose up -d
) else (
    echo   OK: Firecrawl API at http://localhost:3002
)
popd
echo.

REM ── 3. Start Backend (FastAPI + AI Agents + MCP + RAG) ──
echo [3/5] Starting Backend (FastAPI on port 8000)...
start "SupplyChainGPT Backend" cmd /k "venv\Scripts\python.exe -m uvicorn backend.main:app --host 0.0.0.0 --port 8000"
echo   OK: Backend starting at http://localhost:8000
echo   Wait ~10s for MCP initialization...
echo.

REM ── 4. Start Frontend (React + TypeScript) ──
echo [4/5] Starting Frontend (React on port 3000)...
cd frontend
start "SupplyChainGPT Frontend" cmd /k "npm run dev"
cd ..
echo   OK: Frontend starting at http://localhost:3000
echo.

REM ── 5. Health Check ──
echo [5/5] Waiting for services to initialize...
timeout /t 15 /nobreak >nul

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
    echo   [!!] Backend     - Not ready yet (may need more time)
)

REM Check Frontend
curl -s http://localhost:3000 >nul 2>&1
if %errorlevel% equ 0 (
    echo   [OK] Frontend    - http://localhost:3000
) else (
    echo   [!!] Frontend    - Not ready yet (may need more time)
)

REM Check Firecrawl
curl -s -X POST http://localhost:3002/v1/scrape -H "Content-Type: application/json" -d "{\"url\":\"https://example.com\",\"formats\":[\"markdown\"]}" >nul 2>&1
if %errorlevel% equ 0 (
    echo   [OK] Firecrawl   - http://localhost:3002 (unlimited web scraping)
) else (
    echo   [!!] Firecrawl   - Not ready yet
)

echo.
echo   Redis:      localhost:6379
echo   Neo4j:      http://localhost:7474
echo   ChromaDB:   http://localhost:8001
echo.
echo ============================================================
echo   All services launched! Press any key to exit this window.
echo   (Services will continue running in their own windows)
echo ============================================================
pause >nul
