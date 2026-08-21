# SupplyChainGPT — Council of Debate AI Agents

**A Multi-Agent Intelligence Framework for Supply Chain Risk, Optimization & Brand Resilience**

> Imagine a boardroom of specialized AI experts — each with a unique role, perspective, and domain expertise — who debate, challenge, predict, and collectively decide the best course of action for any supply chain query or crisis.

Instead of a single AI giving one answer, the Council runs multiple specialized agents in parallel, each arguing their perspective, and a Moderator Agent synthesizes the final, balanced decision. This is powered by LangGraph multi-agent orchestration, where agents have memory, tools, and the ability to challenge each other's outputs before giving a final recommendation.

### Live Links

| Service | URL |
|---------|-----|
| **Frontend** | https://ai-council-for-finance.vercel.app |
| **Backend API** | https://supplychaingpt-backend.onrender.com |
| **Backend Docs** | https://supplychaingpt-backend.onrender.com/docs |

**Hackathon**: Cognizant Technoverse 2026  
**Team**: Rohith, Akhil, Poojitha, Aishwarya  
**Timeline**: 9 Days (April 12–20, 2026)

---

## Table of Contents

1. [The 7 AI Agents](#the-7-ai-agents)
2. [Council Debate Protocol](#council-debate-protocol)
3. [Predictions Engine](#predictions-engine)
4. [Fallback Options Engine](#fallback-options-engine)
5. [Brand Agent Crisis Scenarios](#brand-agent-crisis-scenarios)
6. [Technical Architecture](#technical-architecture)
7. [Tech Stack](#tech-stack)
8. [Risk Scoring Pipeline](#risk-scoring-pipeline)
9. [RAG Pipeline](#rag-genai-qa-pipeline)
10. [OR-Tools Optimization](#optimization-or-tools)
11. [API Overview](#api-overview)
12. [UI Overview](#ui-overview)
13. [Frontend Tech & Implementation](#frontend-tech--implementation)
14. [Demo Scenario](#demo-scenario)
15. [9-Day Execution Plan](#9-day-execution-plan)
16. [Team & Responsibility Chain](#team--responsibility-chain)
17. [Day 1–2 Detailed Plan](#day-1--2-detailed-plan)
18. [Day 8–9 Detailed Plan](#day-8--9-detailed-plan)
19. [Testing](#testing)
20. [Security & Responsible AI](#security--responsible-ai)
21. [Deployment](#deployment)
22. [Roadmap](#roadmap)
23. [Limitations / Non-goals](#limitations--non-goals)
24. [Contributing](#contributing)
25. [Hackathon Idea Submission Template](#hackathon-idea-submission-template)

---

## The 7 AI Agents

### Agent 1: Risk Sentinel Agent
> "I find threats before they find you"

| Aspect | Details |
|--------|---------|
| **Role** | Proactive Risk Detection & Scoring |
| **Data Sources** | GDELT global events database, NewsAPI (real-time feeds), Supplier financial health APIs, Geopolitical risk indices, Social media sentiment streams |
| **Capabilities** | Real-time supplier risk scoring (0–100), Geopolitical disruption prediction, Financial health monitoring, Natural disaster impact assessment, Multi-signal correlation engine |
| **AI Tools** | BERT fine-tuned on supply chain risk news, XGBoost risk scoring model, Time-series anomaly detection (LSTM) |

**Example Debate Contribution:**
> "Supplier X in Taiwan has a risk score of 87/100. Recent seismic activity + semiconductor tariff news from US + 40% drop in supplier stock price = HIGH PROBABILITY of disruption within 21 days. I recommend immediate escalation."

---

### Agent 2: Supply Optimizer Agent
> "I find you the best supplier, always"

| Aspect | Details |
|--------|---------|
| **Role** | Demand-Supply Matching + Alternate Sourcing |
| **Data Sources** | Supplier Database (Neo4j graph), Historical procurement data, Global supplier marketplaces (Alibaba, ThomasNet APIs), Contract terms database |
| **Capabilities** | Alternate supplier recommendation engine, Demand forecasting (seasonal + event-driven), Multi-tier supplier mapping (Tier 1, 2, 3 visibility), Safety stock optimization, Lead time comparison across suppliers |
| **AI Tools** | Graph Neural Networks (Neo4j supplier graph), Prophet + LSTM for demand forecasting, Cosine similarity for alternate supplier matching |

**Example Debate Contribution:**
> "If Supplier X fails, I've identified 3 alternate suppliers — Supplier A (India, 95% capability match, 12-day lead time), Supplier B (Vietnam, 88% match, 18 days), Supplier C (Mexico, 91% match, 15 days). Recommending Supplier A for speed."

---

### Agent 3: Logistics Navigator Agent
> "I find the fastest, cheapest route — always"

| Aspect | Details |
|--------|---------|
| **Role** | Route Optimization + Carrier Selection |
| **Data Sources** | Shipping APIs (FedEx, DHL, Maersk API), Port congestion data (Marine Traffic API), Fuel price APIs, Weather & geopolitical route risk data, Freight rate APIs (Freightos) |
| **Capabilities** | Multi-modal route optimization (sea/air/land), Real-time port congestion alerts, Carrier reliability scoring, Carbon footprint tracking per route, Customs clearance time estimation |
| **AI Tools** | Google OR-Tools (route optimization), Dijkstra's + A* algorithm for path finding, Regression model for freight rate prediction |

**Example Debate Contribution:**
> "The standard Shanghai→Rotterdam sea route has a 14-day port congestion delay right now. Alternative: Shanghai→Dubai→Hamburg air-sea combo — 9 days, 22% cost increase. OR rail via Trans-Siberian — 12 days, 8% cheaper. Given the time-sensitivity of this order, I vote air-sea."

---

### Agent 4: Market Intelligence Agent
> "I know what's coming before the market does"

| Aspect | Details |
|--------|---------|
| **Role** | Trend Analysis + Competitive Intelligence |
| **Data Sources** | Commodity price APIs (crude oil, metals, semiconductors), Trade data (UN Comtrade API), Competitor procurement signals, Industry analyst reports (scraped + indexed via RAG), Tariff & trade policy databases |
| **Capabilities** | Commodity price trend forecasting, Trade war / tariff impact modeling, Competitive supply chain benchmarking, Market demand shift prediction, "What-if" scenario modeling (10+ variables) |
| **AI Tools** | Prophet + ARIMA for price forecasting, Monte Carlo simulation for scenario modeling, Web scraping + NLP for competitor intelligence |

**Example Debate Contribution:**
> "Lithium prices are predicted to spike 34% in Q2 due to Chile's new export restrictions. If we don't pre-purchase now, our EV battery supply costs will increase by $2.3M/quarter. I recommend forward procurement of 6-month stock."

---

### Agent 5: Finance Guardian Agent
> "I protect every dollar and maximize every investment"

| Aspect | Details |
|--------|---------|
| **Role** | Financial Impact Analysis + ROI Optimization |
| **Data Sources** | ERP financial data (SAP/Oracle APIs), Currency exchange APIs, Insurance claim databases, Historical cost data, Budget & procurement spend analytics |
| **Capabilities** | Disruption cost estimation (direct + indirect), Mitigation ROI calculation, Currency risk assessment, Insurance claim automation, Budget impact forecasting |
| **AI Tools** | Z-score model for financial health, Monte Carlo for cost scenarios, Linear programming for budget optimization |

**Example Debate Contribution:**
> "Current exposure: $4.2M in outstanding POs tied to Supplier X. Mitigation cost (air freight + alternate sourcing): $85K immediate + $1.2M forward buy. Net savings vs. disruption: $2.95M. ROI: 3,400%. I strongly recommend immediate action."

---

### Agent 6: Brand Protector Agent
> "I protect the brand when supply chains break"

| Aspect | Details |
|--------|---------|
| **Role** | Brand Sentiment + Crisis Communication + Advertising Pivot |
| **Data Sources** | Social media APIs (Twitter, Reddit, YouTube), Brand sentiment tracking tools, Competitor ad monitoring (Semrush, SpyFu), Customer complaint databases, PR news wires |
| **Capabilities** | Real-time brand sentiment monitoring, Auto-generated crisis communications, Advertising pivot recommendations, Competitor exploitation detection, Customer notification drafting |
| **AI Tools** | BERT sentiment analysis (fine-tuned), GPT-4 for content generation, Social listening APIs + trend detection |

**Example Debate Contribution:**
> "Social sentiment around our brand has dropped 15% in the last 48 hours due to delivery delays. Competitor Y is running 'Always in Stock' ads targeting our customers. I recommend: (1) Pause current product ads immediately, (2) Launch 'We're committed to your trust' brand campaign, (3) Push substitution products to avoid revenue loss, (4) Draft press release within 2 hours. I'll generate all drafts now."

---

### Agent 7: Moderator / Orchestrator Agent
> "I run the debate and deliver the final verdict"

| Aspect | Details |
|--------|---------|
| **Role** | Route → Debate → Synthesize → Decide |
| **Responsibilities** | Receives user query / crisis event, Assigns query to relevant agents, Runs parallel agent processing, Identifies conflicts between agent recommendations, Forces debate when agents disagree, Weighs recommendations by confidence scores, Synthesizes final unified recommendation, Generates executive summary for decision-makers |
| **Debate Rules** | Each agent submits recommendation + confidence score, Agents can "challenge" other agents' recommendations, Maximum 3 debate rounds before forced synthesis, Majority confidence-weighted vote on final decision |
| **AI Tools** | LangGraph (multi-agent orchestration), Custom debate protocol (chain-of-thought prompting), Confidence-weighted ensemble decision making |

---

## Council Debate Protocol

### Step-by-Step Flow

**QUERY**: "What is our exposure if Supplier X (Taiwan) fails due to geopolitical tensions this quarter?"

#### Round 1: Individual Agent Analysis (Parallel Processing)

| Agent | Output |
|-------|--------|
| Risk Agent | "Risk Score: 87/100. Disruption likely in 21 days" |
| Supply Agent | "3 alternates found. Best: India supplier" |
| Logistics Agent | "Reroute adds 8 days. Air freight available" |
| Market Agent | "Chip prices spike 34% if Taiwan supply stops" |
| Finance Agent | "Exposure: $4.2M in outstanding POs" |
| Brand Agent | "Low social risk now. Pre-emptive comms ready" |

#### Round 2: Debate — Agents Challenge Each Other

- **Supply Agent challenges Logistics Agent**: "India supplier needs 12-day onboarding. Your 8-day reroute creates a 4-day production gap. How do we bridge this?"
- **Logistics Agent responds**: "Bridge via emergency air freight from Vietnam (Supplier C) for 4-day gap period. Cost: $85K one-time. Acceptable?"
- **Finance Agent responds**: "$85K bridge cost vs $4.2M exposure = 98% ROI. Approve."
- **Market Agent challenges Supply Agent**: "India supplier Tier 2 sources from same Taiwan chip fab. They will also be impacted. True independence unverified."
- **Supply Agent revises**: "Verified: India supplier uses Korean Tier 2 source. Safe."

#### Round 3: Final Synthesis by Moderator Agent

**FINAL COUNCIL RECOMMENDATION:**
1. Switch 60% volume to India supplier (Confidence: 94%)
2. 4-day gap bridged via Vietnam air freight ($85K)
3. Forward-buy 6-month chip stock (Market Agent forecast)
4. Financial hedge: Cover $4.2M PO exposure (Finance Agent)
5. Pre-draft brand communication — activate only if needed
6. Monitor Taiwan situation daily via Risk Agent

---

## Predictions Engine

### How Agents Forecast the Future

Each agent generates **30/60/90-day predictions** using ensemble ML models:

| Timeframe | Focus |
|-----------|-------|
| **30-day** | Immediate risk mitigation + short-term sourcing |
| **60-day** | Supply rebalancing + logistics optimization |
| **90-day** | Strategic shifts + brand recovery + financial hedging |

**Techniques**: Prophet + LSTM ensemble, Monte Carlo simulation (10,000 scenarios), Confidence-weighted ensemble across agents

---

## Fallback Options Engine

### Tier 1 — IMMEDIATE (0–48 Hours)
- Activate pre-qualified backup supplier (auto-PO generation)
- Emergency air freight routing (auto-booking via API)
- Pause product ads → Launch "Coming Soon" campaign
- Auto-notify affected customers (GenAI-drafted emails)

### Tier 2 — SHORT-TERM (2–4 Weeks)
- Multi-source procurement split across 2–3 suppliers
- Explore contract manufacturing options (Tier 3 fallback)
- Adjust product launch timeline → Marketing pivot
- Activate cargo insurance claim (auto-documented)

### Tier 3 — STRATEGIC (1–6 Months)
- Geographic diversification strategy (new country sourcing)
- Near-shoring/Friend-shoring recommendation
- Safety stock policy revision (AI-optimized buffer levels)
- Full brand narrative reset ("Supply Chain Excellence" story)

**Each fallback auto-includes**: Cost estimate, Time to implement, Risk score of the fallback itself

---

## Brand Agent Crisis Scenarios

### Scenario A: Product Shortage (Supply gap detected)
- STOP: Pause all product availability ads immediately
- LAUNCH: "We're working for you" brand sentiment campaign
- PUSH: Substitute/alternative products from same portfolio
- RUN: "Pre-order now" campaign to capture demand intent
- DRAFT: CEO/brand social posts about commitment (auto-generated)

### Scenario B: Price Increase (Cost disruption detected)
- PUSH: Value messaging — "Why our quality justifies premium"
- LAUNCH: Loyalty rewards campaign to reduce churn
- TARGET: High-LTV customers with exclusive pricing offers
- DRAFT: Transparent pricing communication to maintain trust

### Scenario C: Competitor Exploiting Your Disruption
- DETECT: Monitor competitor ad spend on your brand keywords
- COUNTER: Launch "Why Choose Us" differentiation campaigns
- CAPTURE: Retarget your customers who visited competitor pages
- ENGAGE: Accelerate social proof (reviews, testimonials) push

### Scenario D: Sustainability Disruption (Ethical SC issue)
- LAUNCH: Sustainability commitment campaign
- PUBLISH: Supplier audit results & corrective actions
- TARGET: ESG-conscious customer segment
- DRAFT: Stakeholder communication on ethical sourcing steps

---

## Technical Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│  FRONTEND (React.js)                                                │
│  ├── Council Chat Interface (multi-agent conversation UI)           │
│  ├── Risk Dashboard (real-time supplier risk heatmap)               │
│  ├── Debate Viewer (see each agent's argument live)                 │
│  ├── Brand Crisis Control Room                                      │
│  └── Fallback Options Panel (one-click activation)                  │
│                                                                      │
│  ORCHESTRATION LAYER                                                 │
│  ├── LangGraph (multi-agent state machine)                          │
│  ├── AWS Strand Agent Framework (agent tool management)             │
│  ├── LangChain (RAG + tool calling for each agent)                  │
│  └── Custom Debate Protocol (Python-based consensus engine)         │
│                                                                      │
│  AGENT TOOLS (each agent has domain-specific tools)                 │
│  ├── Risk Agent Tools: NewsAPI, GDELT, BERT classifier              │
│  ├── Supply Agent Tools: Neo4j graph query, supplier APIs           │
│  ├── Logistics Agent Tools: OR-Tools, Shipping APIs                 │
│  ├── Market Agent Tools: Commodity APIs, Monte Carlo engine         │
│  ├── Finance Agent Tools: ERP APIs, currency APIs, Z-score model    │
│  └── Brand Agent Tools: Social APIs, LLM content generator         │
│                                                                      │
│  AI/ML LAYER                                                         │
│  ├── LLM: GPT-4 / Gemini 1.5 Pro (GenAI reasoning)                 │
│  ├── Embedding: text-embedding-3-large (semantic search)            │
│  ├── NLP: BERT (fine-tuned, domain-specific)                        │
│  ├── Forecasting: LSTM + Prophet ensemble                           │
│  ├── Graph ML: PyTorch Geometric (GNN)                              │
│  └── Optimization: Google OR-Tools                                  │
│                                                                      │
│  DATA LAYER                                                          │
│  ├── PostgreSQL (structured data — POs, contracts, KPIs)            │
│  ├── Neo4j (supplier relationship graph — n-tier mapping)           │
│  ├── Pinecone (vector DB — document + news embeddings for RAG)      │
│  ├── InfluxDB (time-series — sensor, price, demand data)            │
│  └── Redis (real-time caching — risk scores, agent states)          │
│                                                                      │
│  BACKEND                                                             │
│  ├── FastAPI (Python — agent APIs, data pipelines)                  │
│  ├── Celery + Redis (async agent task queue)                        │
│  ├── WebSockets (real-time debate streaming to frontend)            │
│  └── Docker + Kubernetes (containerized agent microservices)        │
└─────────────────────────────────────────────────────────────────────┘
```

---

## Tech Stack

### Backend
- **Core**: Python 3.12, LangGraph 0.2+, LangChain 0.3+, FastAPI 0.115+
- **State Management**: LangGraph Checkpointer (PostgreSQL + Redis)
- **Observability**: LangSmith (tracing, cost, latency, debug)
- **Database**: PostgreSQL 16 (state persistence) + Redis 7 (cache) + Neo4j 5 (graph) + ChromaDB (vectors)
- **LLM**: NVIDIA NIM `meta/llama-3.1-8b-instruct` (primary) → OpenRouter `openai/gpt-oss-20b:free` → Mistral `mistral-large-latest` → Google `gemini-flash-latest` (fallback chain); also Groq, Cohere, SambaNova via same router (`backend/llm/router.py:27`)
- **MCP Tools**: 99 tools across 27+ live APIs (Finnhub, Polygon, Alpha Vantage, NOAA, NVD, etc.)
- **Web Scraping**: Firecrawl (self-hosted, unlimited) — 6 tools: scrape, crawl, search, extract, supplier, news
- **RAG**: LangChain + ChromaDB + Neo4j Graph RAG + Firecrawl URL loader
- **Tools**: uv (package manager), Docker, dotenv, pytest, GitHub Actions stub

### Frontend
- **Framework**: React 18 + Vite (fast build)
- **Language**: TypeScript
- **Routing**: React Router v6.4+
- **Styling**: Tailwind CSS + shadcn/ui (beautiful, accessible components)
- **Charts**: Recharts or Chart.js (for heatmaps, forecasts)
- **Graph Visualization**: React Flow (optional for supplier graph)
- **Data Fetching**: TanStack Query (from FastAPI)
- **Real-time**: Socket.io-client (real-time debate streaming)
- **State Management**: Zustand or Jotai (light state management)
- **Animations**: Framer Motion (for modals and agent status)

### Infrastructure
- **Containers**: Docker + docker-compose
- **Orchestration**: Kubernetes (optional), AWS ECS/Fargate
- **Monitoring**: Prometheus/Grafana stub, LangSmith

---

## Quick Start

```bash
# 1. Clone and install
git clone https://github.com/Rohithdgrr/cognizant-hackathon.git
cd project
python -m venv venv && venv\Scripts\activate  # Windows
pip install -r requirements.txt

# 2. Configure .env
cp .env.example .env  # Fill in API keys

# 3. Start everything (Windows)
start-all.bat

# Or start manually:
docker compose up -d redis neo4j chromadb   # Databases
cd firecrawl && docker compose up -d        # Firecrawl web scraping
venv\Scripts\python -m uvicorn backend.main:app --port 8000  # Backend
cd frontend && npm install && npm run dev    # Frontend
```

**Services**: Backend (8000) | Frontend (3000) | Firecrawl (3002) | Redis (6379) | Neo4j (7474) | ChromaDB (8001)

---

## Risk Scoring Pipeline

### Signal Ingestion
Collect risk signals from multiple sources: news events (GDELT, NewsAPI), shipment delays (carrier APIs), supplier financials (ERP), geopolitical indices, social sentiment.

### Signal Normalization
Convert signals into comparable numeric features.

### Score Aggregation
Combine features into a transparent score (weighted) or a model score (XGBoost).

### Evidence Attachment
Store why the score changed (event tags, lane delays, PO impact).

### Output
- **Risk score**: 0–100 (or Low/Medium/High)
- **Drivers**: top 3–5 factors
- **Impacted items**: list of affected components/POs
- **Suggested actions**: triggers Council analysis

---

## RAG (GenAI Q&A) Pipeline

### What RAG is Used For
RAG is used to answer questions using **your documents**, not guesswork:
- SOPs (what to do during a disruption)
- Contracts (SLAs, penalties, force majeure clauses — only where allowed)
- Past incident reports (what worked, what failed)
- Supplier onboarding checklists

### Typical Flow
1. Chunk documents → embed chunks → store vectors
2. On query: retrieve top-K chunks
3. LLM answers using only retrieved context + citations to internal doc IDs

### Example Queries
- "What is our SOP if a critical supplier lead time increases by 2 weeks?"
- "What steps are required to qualify an alternate supplier for Component C2?"
- "Summarize the last incident involving port congestion and what we changed."

---

## Optimization (OR-Tools)

SupplyChainGPT uses OR-Tools for actionable planning under constraints.

### Supported Optimization Patterns
| Pattern | Description |
|---------|-------------|
| **Routing** | Choose route/mode/carrier minimizing cost while meeting delivery deadline |
| **Allocation** | Split demand across suppliers based on capacity, MOQ, lead time, and risk |
| **Expedite tradeoffs** | Compare (reroute) vs (air freight) vs (safety stock usage) |

### Example Constraints
- Lead time ≤ target
- Budget ≤ limit
- Supplier capacity ≤ available
- MOQ constraints
- Service level targets

---

## API Overview

### Example Endpoints
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/health` | Health check |
| POST | `/ingest/erp` | Ingest POs, inventory |
| POST | `/signals/news` | Ingest a batch of news/events |
| GET | `/risk/suppliers/{supplier_id}` | Get supplier risk score |
| POST | `/council/analyze` | Run council on a query/incident |
| POST | `/optimize/routes` | Optimize routes |
| POST | `/rag/ask` | Ask RAG a question |

### Council Analysis Request
```json
{
  "query": "What is our exposure if Supplier S1 is delayed by 2 weeks?",
  "context": {
    "supplier_id": "S1",
    "plant_id": "PLANT-01",
    "time_window_days": 30
  }
}
```

### Council Analysis Response
```json
{
  "final_recommendation": {
    "summary": "Mitigate likely delay by splitting demand and rerouting urgent POs.",
    "actions": [
      {"type": "source_split", "details": "Allocate 60% to Supplier S2 (approved), 40% keep with S1"},
      {"type": "expedite", "details": "Air freight for PO-104 for 7 days to bridge gap"},
      {"type": "inventory_policy", "details": "Increase safety stock for C2 by +10 days until risk drops"}
    ],
    "fallbacks": [
      {"type": "customer_comms", "details": "Template for 7-day delivery slip"},
      {"type": "marketing_pivot", "details": "Pause 'fast delivery' ads; promote in-stock substitutes"}
    ],
    "confidence": 0.78
  },
  "agent_outputs": [
    {"agent": "risk", "confidence": 0.82, "key_points": ["Port strike signal", "Lane delays increasing"]},
    {"agent": "sourcing", "confidence": 0.74, "key_points": ["Two alternates found", "Qualification time 10–12 days"]},
    {"agent": "logistics", "confidence": 0.70, "key_points": ["Reroute adds 4 days", "Air option costly but fast"]}
  ],
  "evidence": [
    {"type": "news_event", "id": "EVT-991", "tag": "port_strike"},
    {"type": "shipment_delay", "lane": "REGION-A->PLANT-01", "days": 5}
  ]
}
```

---

## UI Overview

### 4-Page React SPA (React Router v6+)

#### Page 1: Dashboard Home (Route: `/` or `/dashboard`)
**Purpose**: First impression + quick overview (covers Risk Heatmap + Landing)

**Key Sections** (Layout: Sidebar + Main Content):
- **Top Navbar**: Logo "SupplyChainGPT", User (Supply Chain Manager), "New Query" button
- **Hero / Quick Stats**: Live Risk Score (0-100 gauge), Active Disruptions, Predicted Savings (₹ or $)
- **Interactive Risk Heatmap**: World map or supplier graph (Neo4j visualized with React Flow or Recharts) – clickable suppliers
- **Recent Queries**: Cards showing last 3 Council runs with confidence %
- **Quick Query Input**: Textarea + "Convene Council" button (triggers full analysis)
- **Footer**: "Powered by LangGraph + RAG + MCP"

#### Page 2: Council Chat Interface (Route: `/chat`)
**Purpose**: Core interaction page (main conversational UI)

**Key Sections**:
- **Left Sidebar**: Query History + Saved Scenarios (Taiwan Chip Crisis, etc.)
- **Central Chat Area**: Streaming messages from Moderator + Agent highlights
- **Right Panel**: Real-time Agent Status (7 avatars with live confidence bars: Risk, Supply, Logistics, etc.)
- **Bottom Input**: Query box + "Run Full Council" / "Run Specific Agent" dropdown
- **Features**: WebSocket streaming for live debate updates

#### Page 3: Live Debate & Predictions Viewer (Route: `/debate`)
**Purpose**: Showcase uniqueness – visual debate engine + predictions

**Key Sections**:
- **Top**: Query Summary + Overall Confidence
- **Main Area**: Horizontal or vertical timeline of Debate Rounds (Round 1: Individual Analysis → Round 2: Challenges → Round 3: Synthesis)
- **Each Agent Card**: Role, Contribution text, Confidence %, "View Full Reasoning" button (opens small modal)
- **Bottom Half**: Predictions Engine – Charts (Prophet/LSTM forecasts, Monte Carlo scenarios) using Recharts
- **Brand Sentiment Widget**: Real-time score + crisis alert

#### Page 4: Brand Crisis Control Room (Route: `/brand`)
**Purpose**: Highlight unique Brand Agent + Crisis features (ties into returns & social impact)

**Key Sections**:
- **Sentiment Dashboard**: Live Twitter/Reddit metrics + trend chart
- **Auto-Generated Comms**: Drafted press releases, social posts, ad copies (editable)
- **Competitor Intelligence**: Side-by-side comparison
- **Action Buttons**: "Launch Campaign", "Pause Ads", "Notify Stakeholders"

### Modals (Radix UI + shadcn/ui Dialog)

| Modal | Trigger | Content |
|-------|---------|---------|
| **Fallback & Action Plan** | "View Fallbacks" button on Chat/Debate | Tier 1-3 options with cost/risk/ROI calculator, one-click "Execute" (mocks ERP PO) |
| **Audit & Observability Log** | "View Audit Trail" icon on every page | Full debate history, LangSmith traces, confidence logs, export PDF/JSON. Searchable + filterable table |
| **Settings & Configuration** | Gear icon in Navbar | Tabs for MCP Tool Management, RAG Knowledge Base upload, Human-in-Loop toggles, LLM selection (Groq/Claude), Notification preferences |

### Shared Components (Used Across All Pages)
- Global Navbar (fixed)
- Toast notifications (for success/error – shadcn Toast)
- Loading skeletons during Council processing
- Dark/Light toggle + Responsive (mobile-friendly for demo)

---

## Frontend Tech & Implementation

### Folder Structure
```
frontend/
src/
├── pages/          → Dashboard.tsx, Chat.tsx, Debate.tsx, Brand.tsx, Settings.tsx, NotFound.tsx
├── components/
│   ├── layout/     → Navbar.tsx (server health indicator, settings link)
│   └── shared/     → ConfidenceBar.tsx, StatusBadge.tsx, LoadingSkeleton.tsx,
│                     Toast.tsx, ThemeToggle.tsx, MarkdownRenderer.tsx
├── lib/            → api.ts (axios + interceptors), socket.ts (native WebSocket)
├── store/          → councilStore.ts, settingsStore.ts (persisted), ragStore.ts, navStore.ts
├── hooks/          → useCouncilQuery.ts, useCouncilStream.ts, useWebSocket.ts,
│                     useRAGQuery.ts, useMCPTools.ts
├── types/          → council.ts, rag.ts, mcp.ts, api.ts, risk.ts
├── assets/         → icons, images
├── App.tsx         → Router (6 routes + 404) + QueryClientProvider + ToastContainer
└── index.css       → shadcn-compatible CSS variables, dark mode tokens
```

### Day-by-Day Frontend Build (Within 9-Day Plan)
- **Day 5 Afternoon** ✅: Vite + React 18 + TS scaffold. Tailwind config with brand colors + shadcn tokens. Type definitions, API client, WebSocket client, Zustand stores, custom hooks, Navbar, shared components, 5 page routes + 404, Vite proxy config. Production build passes with zero TS errors.
- **Day 7 Morning**: Implement Dashboard (heatmap + stats) + Chat page with streaming input
- **Day 7 Afternoon**: Debate page with timeline + charts + modals for Audit/Fallback
- **Day 8 Morning**: Brand page polish + Settings page + WebSocket integration
- **Day 8 Afternoon**: Polish (responsive, loading states, dark theme, export buttons) + connect to backend
- **Day 9**: Final polish, deployment, testing on AWS

### UI/UX Best Practices for Judges
- Minimalist dark theme (blue-purple accents matching Cognizant branding)
- Ample whitespace, subtle animations (framer-motion for modals)
- All actions have clear feedback (toasts + loading spinners)
- One-click flows: Query → Council → Debate → Fallbacks (all in < 10 seconds demo)

---

## Demo Scenario

Use this scenario in presentations and end-to-end demo:

**Assume a mid-size manufacturer:**
- 1 plant, 50 SKUs, ~40 active suppliers
- 3 critical components (C1, C2, C3) sourced from Tier-1 Supplier **S1**
- Supplier S1 depends on Tier-2 Supplier **T2** in another region

**Trigger**: News signal about **port strike** near Tier-2 region + rising shipment delays

**Expected Council behavior:**
1. Risk Agent raises risk score for affected lane/suppliers with evidence
2. Sourcing Agent suggests 2 alternates with lead times + qualification notes
3. Logistics Agent proposes reroute vs air freight tradeoff
4. Finance Agent estimates cost impact range (mitigation cost vs disruption exposure)
5. Brand Agent provides customer messaging template + advertising pivot suggestion

---

## 9-Day Execution Plan

| Day | Date | Focus | Owner | Deliverable |
|-----|------|-------|-------|-------------|
| 1 | Apr 12 | Foundation & Architecture | Rohith | GitHub repo, folder structure, basic LangGraph, FastAPI skeleton, architecture diagram, .env.example, initial PDF update |
| 2 | Apr 13 | Core LangGraph Council (7 Agents) | Rohith | Fully working 7-agent Council with parallel execution, checkpointer (Postgres + Redis), basic ReAct loops, LangSmith traces |
| 3 | Apr 14 | Agentic RAG Integration | Akhil | Agentic RAG + Graph RAG on Neo4j integrated into all 7 agents |
| 4 | Apr 15 | MCP Tool Integration | Akhil | MCP servers + secure tool calling in every agent |
| 5 | Apr 16 | Debate Engine + Predictions + Brand Agent + Frontend Foundation | Rohith + Akhil | ✅ Complete Debate Engine, Predictions, Brand Agent, Fallbacks, WebSocket, PDF Export, Firecrawl MCP, Frontend scaffold (Phase 6: 100%) |
| 6 | Apr 17 | Backend API + Observability + Real Data | Rohith + Akhil | ✅ 45 MCP tools (12 live APIs), Market API (4 endpoints), Streaming debate, Yahoo Finance fallback, API key security fix |
| 7 | Apr 18 | React Frontend Dashboard (4-Page SPA) | Aishwarya + Poojitha | Complete 4-page React SPA + all Radix modals + WebSocket integration |
| 8 | Apr 19 | Production Polish & Security | ALL 4 Members | Security hardening, cost optimization, UI polish, full integration, performance tuning, export features |
| 9 | Apr 20 | Testing, Deployment & Final Prep | ALL 4 Members | Fully Dockerized, AWS-deployed, tested MVP + polished PDF + demo video + README |

---

## Team & Responsibility Chain

```
Start → Rohith (Day 1 & 2) → creates foundation
  ↓
Rohith hands off to Akhil (Day 3 & 4) → adds intelligence (RAG + MCP)
  ↓
Akhil hands back to Rohith + Akhil (Day 5 & 6) → builds core logic & observability
  ↓
Rohith & Akhil hand off to Aishwarya + Poojitha (Day 7) → frontend layer
  ↓
Aishwarya & Poojitha hand off to All 4 (Day 8 & 9) → final polish, security, deployment & submission
```

### Working Structure
- **Git Workflow**: Daily PR → Review by at least one other member → Merge to `main` by 11:59 PM
- **Daily Stand-up**: 30-minute call at 9 PM (WhatsApp/Meet) – share progress + blockers + handoff notes
- **Code Sharing**: Use `main` branch as single source of truth
- **Documentation**: All members update README.md daily with screenshots and test results
- **Handoff Rule**: At the end of each day, the owner(s) must push code + write a short handoff note in the Git commit message + team group ("Ready for next person – latest on main")

---

## Day 1–2 Detailed Plan

### Day 1 (April 12) – Foundation & Architecture

**Total Time**: 8–10 hours (split Morning/Afternoon/Evening)

#### Morning (3 hours) – Project Setup & Git
1. Create GitHub repo: `supplychaingpt-council` (private, add all 4 team members)
2. Clone the 9 recommended repos into a `references/` folder for quick copy-paste
3. Initialize project: `uv init --python 3.12` → `uv add langgraph langchain langchain-groq fastapi uvicorn langsmith redis psycopg2-binary python-dotenv pytest`
4. Create folder structure:
   ```
   backend/
   ├── agents/
   ├── rag/
   ├── mcp/
   ├── tools/        → pdf_export.py, ...
   ├── ws/           → server.py, events.py
   ├── routes/       → council.py, risk.py, rag.py, ...
   ├── middleware/   → auth.py, rate_limit.py, error_handler.py
   ├── db/           → neon.py, redis_client.py, neo4j_client.py
   ├── config.py
   ├── graph.py
   ├── state.py
   ├── main.py
   frontend/
   ├── src/
   │   ├── pages/       → Dashboard, Chat, Debate, Brand, Settings, NotFound
   │   ├── components/  → layout/Navbar, shared/ (6 components)
   │   ├── lib/         → api.ts, socket.ts
   │   ├── store/       → 4 Zustand stores
   │   ├── hooks/       → 5 custom hooks
   │   ├── types/       → 5 type definition files
   │   └── App.tsx      → Router + QueryClient + Toast
   ├── tailwind.config.js
   ├── vite.config.ts
   └── package.json
   tests/
   ├── test_api.py
   └── test_websocket.py
   venv/
   docker-compose.yml
   .env.example
   ```
5. Copy `.env.example` → `.env` and fill all keys (use hackathon AWS credentials)

#### Afternoon (3 hours) – Architecture & Core State
1. Draw architecture diagram (use draw.io or Excalidraw): Council flow → Moderator → 7 Agents → Debate Engine → RAG + MCP. Export as PNG
2. Create `backend/state.py`: Define `CouncilState` TypedDict with fields: `query`, `messages`, `risk_score`, `recommendation`, `confidence`, `debate_history`, `fallback_options`
3. Create `backend/graph.py`: Basic `StateGraph` with Moderator node (use official LangGraph supervisor pattern)
4. Add LangSmith tracing: `langsmith_client = Client()` and enable in every run

#### Evening (2–3 hours) – FastAPI Skeleton + PDF Submission
1. Create `backend/api.py`: FastAPI app with endpoint `/council/query` (async) that runs the graph
2. Add health check `/health` and basic error middleware
3. Run locally: `uv run uvicorn backend.api:app --reload` → test with curl
4. Update Idea PDF:
   - Add architecture diagram (Technical Details section)
   - Add "9-Day Production Timeline" table
   - Add one-line statement: "Built as 4-page React SPA with Radix modals"
5. Submit PDF on Superset platform before midnight

**Production Feature**: Full LangSmith tracing enabled from Day 1 + Docker-ready `docker-compose.yml` stub (Postgres + Redis)

**Output by 11:59 PM**: Working FastAPI server + basic LangGraph graph running locally. Commit to `main` with message "Day 1 foundation complete"

---

### Day 2 (April 13) – Core LangGraph Council (7 Agents Skeleton)

**Total Time**: 8–10 hours

#### Morning (3 hours) – 7 Agent Nodes + Supervisor
1. In `backend/agents/` create 7 files: `risk_agent.py`, `supply_agent.py`, `logistics_agent.py`, `market_agent.py`, `finance_agent.py`, `brand_agent.py`, `moderator.py`
2. Use template from LangGraph and multi-agent repos: Each agent is a simple ReAct node with `tools=[]` (MCP will be added on Day 4)
3. Create `supervisor.py`: Use `create_supervisor` or custom StateGraph with conditional edges (parallel execution for first 6 agents)
4. Implement basic agent prompt templates (role-specific system prompts from the plan)

#### Afternoon (4 hours) – Checkpointer & Parallel Execution
1. Setup PostgreSQL + Redis via Docker (add to `docker-compose.yml`):
   ```yaml
   postgres:
     image: postgres:16
   redis:
     image: redis:7
   ```
2. Add `AsyncPostgresSaver` + `RedisCheckpointer` to the graph: `graph.compile(checkpointer=checkpointer)`
3. Enable parallel execution: Use `Send` or `parallel` node for Risk + Supply + Logistics + Market + Finance + Brand
4. Add structured output: Each agent returns Pydantic model with `confidence` (float 0-100) and `contribution`

#### Evening (2–3 hours) – Testing & Production Polish
1. Create `tests/test_council.py`: Run full Council with sample query "Taiwan chip crisis impact on our EV battery supply"
2. Add human-in-the-loop stub (`interrupt_before=["moderator"]`)
3. Enable LangSmith trace sharing (generate public link for demo)
4. Test: Single query → all 7 agents run in parallel → Moderator synthesizes → persisted state in Postgres

**Production Feature**: Persistent state across restarts + audit-ready `debate_history` list + confidence-weighted routing

**Output by 11:59 PM**: Fully working 7-agent Council that runs end-to-end with persistence. Commit to branch `feature/core-council` and merge to `main`

---

## Day 8–9 Detailed Plan

### Day 8 (April 19) – Production Polish & Security

**Total Time**: 8–10 hours

#### Morning (3–4 hours) – Security Hardening & Backend Polish
1. Add comprehensive security:
   - Prompt injection protection using LlamaGuard or custom guardrails in every agent
   - Rate limiting + CORS + API key authentication in FastAPI
   - PII redaction in Brand Agent outputs
   - MCP sandboxing with least-privilege scopes
2. Implement cost optimization:
   - Redis caching for RAG results and MCP responses (60%+ cost reduction)
   - LLM fallback (Groq → Claude on high latency)
   - Batch processing for multiple agent calls
3. Enhance observability:
   - Full LangSmith tracing with custom metadata (agent_name, confidence, mcp_calls)
   - Add Prometheus metrics endpoint for latency, token usage, error rate
   - Create simple Grafana dashboard JSON stub (for demo)

#### Afternoon (3–4 hours) – Frontend Integration & Polish
1. Complete integration of 4-page React SPA (from Day 7):
   - Dashboard, Chat, Debate, Brand pages fully connected to FastAPI via TanStack Query
   - Real-time debate streaming using Socket.io (show live agent contributions + confidence bars)
2. Add all Radix Dialogs/Modals:
   - Fallback & Action Plan (with ROI calculator + one-click "Execute" mock)
   - Audit & Observability Log (searchable table of debate_history + LangSmith public links)
   - Settings (MCP tools toggle, RAG upload, human-in-loop, LLM selector)
3. Polish UI/UX:
   - Minimalist dark theme with Cognizant blue-purple accents
   - Subtle animations (Framer Motion for modals and agent status)
   - Loading skeletons + toast notifications for every action
   - Responsive design (mobile-friendly for demo)

#### Evening (2 hours) – End-to-End Testing & Optimization
1. Run full integration tests on 8–10 disruption scenarios (Taiwan chip crisis, etc.)
2. Performance tuning: Ensure Council query completes in <8 seconds (target for live demo)
3. Add export features: Debate trail → PDF/JSON download
4. Record short screen recordings of key flows for your final presentation

**Output by 11:59 PM**: Fully integrated, secure, polished backend + frontend running locally. Commit to branch `feature/polish-security` and merge to `main`

---

### Day 9 (April 20) – Testing, Deployment & Submission Prep

**Total Time**: 8–10 hours

#### Morning (3 hours) – Dockerization & Deployment
1. Finalize `docker-compose.yml` (multi-container: FastAPI, React build, Redis, Postgres, Neo4j)
2. Create production Dockerfile for backend (multi-stage build) and frontend (Vite build served via nginx or FastAPI static)
3. Deploy locally with Docker: `docker compose up --build`
4. Prepare AWS deployment script (hackathon environment): ECS/Fargate ready commands + environment variable injection

#### Afternoon (3–4 hours) – Comprehensive Testing & Load Simulation
1. E2E testing: Use pytest + Playwright for all 4 pages + modals
2. Load testing: Simulate 50 concurrent queries and verify persistence + tracing
3. Edge-case testing: Low confidence → self-reflection, MCP failure → cached fallback, human-in-loop interrupt
4. Quantify ROI in UI: Add live calculator showing $ savings, time saved, risk reduction based on sample runs

#### Evening (2–3 hours) – Final Prep & Documentation
1. Create polished demo script (3–5 minute flow: New Query → Council → Live Debate → Fallback Execution → Audit Log)
2. Update Idea PDF / presentation with:
   - Latest screenshots
   - Architecture + 4-page frontend diagram
   - Production metrics (latency, cost, accuracy)
   - 9-day timeline + future roadmap
3. Generate public LangSmith trace links + short demo video
4. Final git push + README with setup instructions, one-click run commands, and judge Q&A notes (21 questions)

**Output by 11:59 PM**: Live local + Docker-deployed system, complete repo, all deliverables ready. Tag release `v1.0-mvp` and prepare for Agent Builder Challenge on April 23.

---

## Complete Feature Summary Table

| Feature | Agent Responsible | Technology Used | Business Value |
|---------|-------------------|-----------------|----------------|
| Real-time Supplier Risk Scoring | Risk Agent | BERT + LSTM + GDELT | Early crisis prevention |
| Alternate Supplier Recommendation | Supply Agent | GNN + Neo4j | Zero supply gaps |
| Intelligent Query Improvement | Moderator Agent | LLM intent classification | Better insights, faster |
| Debate & Consensus Engine | Moderator Agent | LangGraph state machine | Balanced decisions |
| 30/60/90-day Predictions | All Agents | Ensemble ML + Monte Carlo | Proactive planning |
| Multi-modal Route Optimization | Logistics Agent | OR-Tools + Shipping APIs | Fastest delivery recovery |
| Commodity Price Forecasting | Market Agent | Prophet + ARIMA | Cost avoidance |
| Financial Impact & ROI | Finance Agent | Z-score + Monte Carlo | Dollar-quantified decisions |
| Brand Crisis Auto-Response | Brand Agent | BERT + GPT-4 + Social APIs | Reputation protection |
| Tiered Fallback Options | All Agents | Constraint optimization | Never without a plan |
| RAG-powered Q&A | All Agents | LangChain + Pinecone | Grounded, cited answers |
| MCP Tool Integration | All Agents | MCP protocol | Real system actions |

---

## Testing

### Backend
- **Unit tests**: pytest + pytest-asyncio
- **API tests**: httpx against live server — **26/28 passed** (2 LLM-dependent skipped)
- **Live API tests**: All 12 real-data MCP tools verified LIVE (Finnhub, Frankfurter, Yahoo Finance, Open-Meteo, USGS, Wikipedia, Reddit, World Bank, GDACS, GDELT, SEC EDGAR, OpenCorporates)
- **Market API**: 4 endpoints tested — `/market/ticker`, `/market/company/{symbol}`, `/market/risk-dashboard`, `/market/brand-intel`
- **Streaming**: SSE debate engine verified — 4029 events streamed via Groq LLM
- **WebSocket tests**: `tests/test_websocket.py` — connect, subscribe, heartbeat
- **Static typing**: mypy (optional)
- **Linting**: ruff (or flake8)

```bash
# Using venv
& "project/venv/Scripts/python.exe" -m pytest tests/test_api.py -v
```

### Frontend
- **TypeScript**: Zero errors (`npx tsc --noEmit`)
- **Build**: Production build passes — 337KB JS, 18KB CSS, zero TS errors
- **Unit tests**: vitest / jest (to be added Day 7+)
- **Lint**: eslint

```bash
cd frontend
npm run build
```

### E2E
- **Framework**: pytest + Playwright
- **Coverage**: All 4 pages + modals

---

## Security & Responsible AI

- **Data minimization**: Ingest only fields needed for scoring and planning
- **Access control**: Role-based access (Procurement vs Finance vs Comms)
- **PII handling**: Avoid storing unnecessary personal data; mask where required
- **API key security**: All keys removed from `.env.example` (placeholders only), `google_api_key` and `gemini_api_key` removed from config, `extra = "ignore"` prevents crashes
- **Auth middleware**: `/market/*` endpoints are public, all other routes require API key
- **RAG grounding**: Answers should cite internal doc IDs; avoid free-form guessing
- **Auditability**: Store agent outputs and evidence references for review
- **Human-in-the-loop**: Suggestions should be reviewed before execution (especially supplier switches, customer communications, and financial actions)
- **Prompt injection hygiene**: Sanitize external content before adding to RAG context; isolate tools; restrict tool permissions per agent

---

## Deployment

### Production — Vercel (Frontend) + Render (Backend)

```
GitHub push to main
    ├─→ Vercel  — builds frontend/ (Vite → dist)  — https://ai-council-for-finance.vercel.app
    └─→ Render  — builds backend/ (Python)         — https://supplychaingpt-backend.onrender.com
```

**Frontend (Vercel)**:
- Root Directory: `frontend`
- Build Command: `npm run build`
- Output Directory: `dist`
- `frontend/vercel.json` handles API proxy rewrites to backend

**Backend (Render)**:
- Reads `render.yaml` from repo root
- Health check: `GET /health`
- CORS locked to `https://ai-council-for-finance.vercel.app`

### Docker / Compose (Local)

```bash
docker compose up -d --build
```

### AWS (Optional)

ECS/Fargate deployment with environment variable injection.

---

## Roadmap

- Add stronger **supplier qualification workflow** (checklists, approvals, evidence storage)
- Add **ESG/Sustainability agent** (certification tracking, ethical sourcing alerts)
- Improve forecasting and lane modeling with richer logistics data feeds
- Add "playbook automation" with approvals (generate PO drafts, carrier booking requests)
- Expand multi-language customer messaging templates (optional)

---

## Limitations / Non-goals

- This project does not aim to replace ERP/SCM systems; it complements them
- External data availability varies by region and vendor; some signals may be simulated in demos
- Risk scores are decision support, not guarantees
- Brand/advertising pivots are suggestions; final messaging should be reviewed by humans

---

## Contributing

1. Create a feature branch
2. Keep changes small and testable
3. Add or update tests for critical logic
4. Update docs if adding endpoints, agents, or data sources

---

## Hackathon Idea Submission Template

### Business Plan (1/2) — Explain the Problem & Solution

**Problem Description & Business Scenario**: Include relevant background information, data or context that helps to understand the problem significance and impact. Talk about the Industry and business trends, needs & scenario.

**Problem Scope**: Define the boundary and scope of the problem, specify any limitations or specific requirement.

**Target Users/Stakeholders**: Identify the target users or stakeholders who would benefit from the solution. Describe their needs, pain points that solution addresses. **WHY — Explain the Problem**

**Solution Overview**: Provide high level overview of the solution, explaining its core concepts and how it addresses the problem. Describe solution features, functionalities and main components of the solution.

**Technical Details**: Provide technical information around the solution, this may include underlying technologies, platforms, programming languages, frameworks, algorithms, libraries used. Explain the data sources and integration/interoperability considerations with systems.

**Innovation**: Highlight unique or innovative aspects of the solution, emphasize any novel technologies, methodology or strategies employed.

**Market Potential**: Provide approx. Market potential, bring in facts and figures from research & analyst reports (if possible).

**Why are the technologies you used appealing for the solution**: Explain why technologies used for the use case are relevant for the use case. **HOW — Explain the Solve**

**Value Proposition**:
- **Primary benefits**: Enumerate the primary benefits or advantages of the solution with specific metrics or data points
- **Efficiency and flexibility**
- **Time and cost saving**
- **Scalability**
- **Social Impact**

**WHAT — Value proposition**

### Business Plan (2/2) — Financials & Timelines

| Investments | Returns | Timelines |
|-------------|---------|-----------|
| What does it take & How much does it cost to solve? | Quantify the benefits & What if I don't solve? | Time to realize benefits |

Categories: Cloud, Process Re-engg, Modernization, AI  
ROI metrics: Revenue Growth, Happy Customer, Margin improvement, Employee Experience, Time to solve, Milestones, Tools

### Idea Evaluation Criteria
- Will the idea deliver business value?
- Is the idea unique?
- Is the idea implementable?
- Is the idea scalable?

---

## Environment Setup

```bash
# Environment variables (.env)
LANGCHAIN_TRACING_V2=true
LANGCHAIN_API_KEY=<your-key>
GROQ_API_KEY=<your-key>
POSTGRES_URI=postgresql://...
REDIS_URL=redis://...
```

**Important**: Never commit secrets. Use `.env.example` as template.

---

## Risk Mitigation & Best Practices

- Daily git push + PR review by one team member
- Use `uv sync` for reproducible environment
- Backup: Keep mock LLM responses in case API limits hit
- Environment variables only – never commit secrets
- Use mocks if any external API (NewsAPI, etc.) hits limits during testing
- Keep all secrets in `.env` and `.env.example`
- Backup: Full system snapshot before any major change

---

## Key Milestones After Day 9

- **April 21–22**: Buffer / dry-run for Agent Builder Challenge
- **April 23 (Agent Builder Challenge)**: Submit / demo the working Council (use your Day 9 deployment)
- **May 6 (Pune 24-hour MVP Hackathon)**: Arrive with 90%+ ready code → focus on minor tweaks, live AWS deployment, and stunning presentation

---

## Changelog — Aug 2026 Fixes

- **2026-08-21 — LLM Streaming Fix**: Fixed `All LLM streaming providers failed for agent supply`.
  - `backend/llm/router.py:27` — Routing now NVIDIA primary (`meta/llama-3.1-8b-instruct`) → OpenRouter `openai/gpt-oss-20b:free` → Mistral `mistral-large-latest` → Google `gemini-flash-latest`; previous OpenRouter `meta-llama/llama-3.3-70b-instruct:free` (404) and Google `gemini-2.0-flash` (deprecated) replaced.
  - `backend/llm/providers.py:29,45` — Google default `gemini-flash-latest`, added `get_mistral_client` via `https://api.mistral.ai/v1`.
  - `.env.example` — Added `MISTRAL_API_KEY`, `GOOGLE_API_KEY` placeholders; `NVIDIA_API_KEY` now required for primary.
- **2026-08-21 — Graph / Debate Fixes**:
  - `backend/graph.py:1,227,537` — Fan-out now uses `langgraph.constants.Send` (fixed `unhashable type: 'dict'`), renamed node `predictions` → `predictions_step` (fixed `"'predictions' is already being used as a state key"`).
  - `backend/debate_engine.py:513,551` — Coerce LLM-extracted `disagreements/consensus` dicts to JSON strings (fixed `DebateRound` validation).
  - `backend/graph.py:254,269` — Neo4j password now `testpassword` to match `docker-compose.yml`.
- **2026-08-21 — Requirements**: Relaxed pins to `>=` with `<0.4` caps for LangChain/LangGraph (`requirements.txt`) to avoid `langchain-cohere` / `strawberry-graphql` conflicts.

---

*License: Add a license appropriate for your hackathon submission (e.g., MIT for open demo, or "All rights reserved" for private).*
