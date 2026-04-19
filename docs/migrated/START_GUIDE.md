# 🚀 SupplyChainGPT - Complete Startup Guide

## Quick Start (Automated)

### Windows
```bash
start-all.bat
```

### Linux/Mac
```bash
chmod +x start-all.sh
./start-all.sh
```

---

## Manual Setup (Step by Step)

### Prerequisites
- Python 3.12+
- Node.js 18+
- Docker & Docker Compose
- Git

### Step 1: Clone & Setup Environment

```bash
# Clone repository (if not already done)
git clone https://github.com/Rohithdgrr/cognizant-hackathon.git
cd cognizant-hackathon

# Copy environment file
cp .env.example .env
```

### Step 2: Configure Environment Variables

Edit `.env` file with your API keys:

**Required (Free Tier):**
```env
# At least one LLM provider (all free)
GROQ_API_KEY=gsk_your_key_here                    # Get from: https://console.groq.com
OPENROUTER_API_KEY=sk-or-v1-your_key_here         # Get from: https://openrouter.ai/keys
NVIDIA_API_KEY=nvapi-your_key_here                # Get from: https://build.nvidia.com

# Database (already configured for local Docker)
NEON_DATABASE_URL=postgresql://...                 # Get from: https://neon.tech (free)
REDIS_URL=redis://localhost:6379
NEO4J_URI=bolt://localhost:7687
NEO4J_PASSWORD=testpassword

# Observability (optional but recommended)
LANGCHAIN_TRACING_V2=true
LANGCHAIN_API_KEY=lsv2_your_key_here              # Get from: https://smith.langchain.com
LANGCHAIN_PROJECT=supplychaingpt-council
```

**Optional (Enhanced Features):**
```env
# External Data APIs (all free tier available)
NEWSAPI_KEY=your_key                               # Get from: https://newsapi.org
FINNHUB_API_KEY=your_key                          # Get from: https://finnhub.io
FRED_API_KEY=your_key                             # Get from: https://fred.stlouisfed.org
ALPHA_VANTAGE_API_KEY=your_key                    # Get from: https://www.alphavantage.co
POLYGON_API_KEY=your_key                          # Get from: https://polygon.io
```

### Step 3: Start Docker Services

```bash
# Start all Docker services (Redis, Neo4j, ChromaDB, Firecrawl)
docker-compose up -d

# Verify services are running
docker-compose ps

# Expected output:
# NAME                    STATUS
# redis                   Up
# neo4j                   Up
# chromadb                Up
# firecrawl-api           Up
# firecrawl-worker        Up
# lightpanda              Up
```

### Step 4: Start Backend (Python/FastAPI)

```bash
# Navigate to backend
cd backend

# Create virtual environment (if not exists)
python -m venv venv

# Activate virtual environment
# Windows:
venv\Scripts\activate
# Linux/Mac:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
# OR using uv (faster):
pip install uv
uv pip install -r requirements.txt

# Run database migrations
python -c "import asyncio; from backend.db.neon import init_db; asyncio.run(init_db())"

# Start backend server
uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000

# Backend will be available at: http://localhost:8000
# API Docs: http://localhost:8000/docs
```

### Step 5: Start Frontend (React/Vite)

Open a new terminal:

```bash
# Navigate to frontend
cd frontend

# Install dependencies (first time only)
npm install

# Start development server
npm run dev

# Frontend will be available at: http://localhost:5173
```

---

## 🎯 Access Points

Once everything is running:

| Service | URL | Description |
|---------|-----|-------------|
| **Frontend** | http://localhost:5173 | React UI |
| **Backend API** | http://localhost:8000 | FastAPI server |
| **API Docs** | http://localhost:8000/docs | Interactive API documentation |
| **Health Check** | http://localhost:8000/health | System health status |
| **Neo4j Browser** | http://localhost:7474 | Graph database UI (user: neo4j, pass: testpassword) |
| **Firecrawl** | http://localhost:3002 | Web scraping service |
| **ChromaDB** | http://localhost:8001 | Vector database |
| **Redis** | localhost:6379 | Cache (no UI) |

---

## 🧪 Test the System

### 1. Test Backend Health
```bash
curl http://localhost:8000/health
```

Expected response:
```json
{
  "success": true,
  "data": {
    "status": "ok",
    "version": "1.0.0",
    "checks": {
      "neon_postgres": "ok",
      "redis": "ok",
      "mcp_tools": "ok",
      "rag_embedder": "ok"
    }
  }
}
```

### 2. Test Council Query
```bash
curl -X POST http://localhost:8000/council/query \
  -H "Content-Type: application/json" \
  -d '{
    "query": "What is our risk if Taiwan chip supply is disrupted?",
    "stream": false
  }'
```

### 3. Test Astra ⭐ Simulation
```bash
curl -X POST http://localhost:8000/astra/run \
  -H "Content-Type: application/json" \
  -d '{
    "query": "Impact of port strike on supply chain",
    "agent_type": "brand",
    "stream": false
  }'
```

### 4. Test RAG Query
```bash
curl -X POST http://localhost:8000/rag/ask \
  -H "Content-Type: application/json" \
  -d '{
    "question": "What is our SOP for supplier disruptions?"
  }'
```

### 5. Test MCP Tools
```bash
curl http://localhost:8000/mcp/tools
```

---

## 🔧 Troubleshooting

### Backend won't start

**Error: "ModuleNotFoundError"**
```bash
# Reinstall dependencies
pip install -r backend/requirements.txt
```

**Error: "Database connection failed"**
```bash
# Check if Docker services are running
docker-compose ps

# Restart Docker services
docker-compose restart

# Check Neon database URL in .env
# Make sure NEON_DATABASE_URL is correct
```

**Error: "Redis connection refused"**
```bash
# Check Redis is running
docker-compose ps redis

# Restart Redis
docker-compose restart redis
```

### Frontend won't start

**Error: "EADDRINUSE: address already in use"**
```bash
# Port 5173 is already in use
# Kill the process or use a different port
npm run dev -- --port 5174
```

**Error: "Module not found"**
```bash
# Reinstall dependencies
rm -rf node_modules package-lock.json
npm install
```

### Docker services won't start

**Error: "port is already allocated"**
```bash
# Check what's using the port
# Windows:
netstat -ano | findstr :6379
# Linux/Mac:
lsof -i :6379

# Stop the conflicting service or change port in docker-compose.yml
```

**Error: "Cannot connect to Docker daemon"**
```bash
# Make sure Docker Desktop is running
# Windows: Start Docker Desktop
# Linux: sudo systemctl start docker
```

### Neo4j authentication failed

```bash
# Reset Neo4j password
docker-compose down
docker volume rm cognizant-hackathon_neo4j_data
docker-compose up -d neo4j

# Wait 30 seconds, then access http://localhost:7474
# Default credentials: neo4j / testpassword
```

### Firecrawl not working

```bash
# Check Firecrawl logs
docker-compose logs firecrawl-api

# Restart Firecrawl
docker-compose restart firecrawl-api firecrawl-worker lightpanda

# Test Firecrawl directly
curl http://localhost:3002/health
```

---

## 📊 System Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                         FRONTEND (React)                         │
│                     http://localhost:5173                        │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐       │
│  │Dashboard │  │  Chat    │  │ Debate   │  │  Brand   │       │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘       │
└────────────────────────────┬────────────────────────────────────┘
                             │ HTTP/WebSocket
┌────────────────────────────┴────────────────────────────────────┐
│                    BACKEND (FastAPI)                             │
│                  http://localhost:8000                           │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  Council of Debate (7 AI Agents + Moderator)             │  │
│  │  Risk │ Supply │ Logistics │ Market │ Finance │ Brand    │  │
│  └──────────────────────────────────────────────────────────┘  │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  Astra ⭐ (Swarm Intelligence - runs in parallel)        │  │
│  │  Brand Simulation │ Market Simulation                     │  │
│  └──────────────────────────────────────────────────────────┘  │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  RAG Pipeline (Hybrid: Vector + Graph + Reranking)       │  │
│  └──────────────────────────────────────────────────────────┘  │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  MCP Tools (99+ tools across 27+ APIs)                   │  │
│  └──────────────────────────────────────────────────────────┘  │
└────────────────────────────┬────────────────────────────────────┘
                             │
┌────────────────────────────┴────────────────────────────────────┐
│                    DOCKER SERVICES                               │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐       │
│  │  Redis   │  │  Neo4j   │  │ ChromaDB │  │Firecrawl │       │
│  │  :6379   │  │  :7474   │  │  :8001   │  │  :3002   │       │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘       │
└─────────────────────────────────────────────────────────────────┘
                             │
┌────────────────────────────┴────────────────────────────────────┐
│                    EXTERNAL SERVICES                             │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐       │
│  │  Groq    │  │  Neon    │  │LangSmith │  │ NewsAPI  │       │
│  │  (LLM)   │  │  (DB)    │  │ (Trace)  │  │ (Data)   │       │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘       │
└─────────────────────────────────────────────────────────────────┘
```

---

## 🎮 Usage Examples

### 1. Run Council Analysis
Navigate to http://localhost:5173 and enter a query:
```
"What is our exposure if Supplier X in Taiwan fails due to geopolitical tensions?"
```

The system will:
- ✅ Analyze with 7 specialized AI agents
- ⭐ Run Astra simulations in parallel
- 📊 Generate predictions and scenarios
- 🎯 Provide actionable recommendations
- 📈 Show risk scores and confidence levels

### 2. View Debate Timeline
Click on "Debate" tab to see:
- Round 1: Individual agent analysis
- Round 2: Challenge & counter phase
- Round 3: Synthesis & final recommendation
- ⭐ Astra predictions (brand + market)

### 3. Brand Crisis Management
Click on "Brand" tab to see:
- Real-time sentiment analysis
- Auto-generated crisis communications
- Competitor intelligence
- Advertising pivot recommendations

### 4. Export Reports
Click "Export PDF" to download:
- Full debate transcript
- Agent contributions
- Evidence and citations
- Astra predictions
- Recommendations

---

## 🛑 Shutdown

### Stop All Services
```bash
# Stop frontend (Ctrl+C in terminal)
# Stop backend (Ctrl+C in terminal)

# Stop Docker services
docker-compose down

# Stop and remove volumes (clean slate)
docker-compose down -v
```

### Restart Everything
```bash
# Start Docker services
docker-compose up -d

# Start backend (in backend terminal)
uvicorn backend.main:app --reload

# Start frontend (in frontend terminal)
npm run dev
```

---

## 📝 Development Tips

### Hot Reload
- **Backend**: Auto-reloads on file changes (--reload flag)
- **Frontend**: Auto-reloads on file changes (Vite HMR)

### View Logs
```bash
# Backend logs: visible in terminal
# Docker logs:
docker-compose logs -f redis
docker-compose logs -f neo4j
docker-compose logs -f firecrawl-api

# All Docker logs:
docker-compose logs -f
```

### Database Management
```bash
# Access Neo4j browser: http://localhost:7474
# Username: neo4j
# Password: testpassword

# Run Cypher queries:
MATCH (n) RETURN n LIMIT 25

# Clear all data:
MATCH (n) DETACH DELETE n
```

### Redis CLI
```bash
# Access Redis CLI
docker exec -it $(docker ps -qf "name=redis") redis-cli

# Common commands:
KEYS *
GET council_session:abc123
FLUSHALL  # Clear all cache
```

---

## 🚀 Production Deployment

See `docs/deployment.md` for production deployment guide including:
- AWS/GCP/Azure deployment
- Environment configuration
- SSL/TLS setup
- Load balancing
- Monitoring & logging
- Backup strategies

---

## 📚 Additional Resources

- **API Documentation**: http://localhost:8000/docs
- **Full Documentation**: `docs/README.md`
- **Astra Integration**: `ASTRA_INTEGRATION.md`
- **Testing Guide**: `docs/testing.md`
- **Architecture**: `docs/backend.md`

---

## ✅ Success Checklist

- [ ] Docker services running (6 containers)
- [ ] Backend API responding at :8000
- [ ] Frontend UI loading at :5173
- [ ] Health check returns "ok"
- [ ] Council query works
- [ ] Astra simulation works
- [ ] Neo4j browser accessible
- [ ] API docs accessible

---

**🎉 You're all set! The complete SupplyChainGPT system is now running with:**
- ✅ 7 AI Agents + Moderator
- ⭐ Astra Swarm Intelligence
- 🔍 RAG Pipeline
- 🛠️ 99+ MCP Tools
- 🐳 Docker Services
- 🌐 React Frontend

**Happy analyzing! 🚀**
