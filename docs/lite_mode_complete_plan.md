# SupplyChainGPT Lite Mode

## Purpose

Lite Mode is a faster council-debate experience that keeps one primary agent as the final decision maker and uses five support subagents to gather evidence from all available sources.

The goal is to keep the answer grounded in real data while reducing the overhead of the full 6-agent, 3-round debate.

Lite Mode should:
- Accept one selected primary agent.
- Launch five support subagents in evidence-gathering mode.
- Collect context from RAG, APIs, web scraping, MCP tools, and graph/database lookups.
- Merge the evidence into one final answer from the primary agent.
- Skip the heavy debate rounds and moderator/supervisor choreography unless explicitly enabled.

---

## Core Idea

Current council mode is designed for depth and debate.
Lite Mode is designed for speed and focus.

### Full Council

```text
User Query
   |
   v
Moderator Parse
   |
   v
Dynamic Routing
   |
   v
RAG Prefetch + MCP Escalation
   |
   v
6 Domain Agents
   |
   v
Debate Round 1 -> Round 2 -> Round 3
   |
   v
Fallbacks + Brand Enhancement + Synthesis
```

### Lite Mode

```text
User Query
   |
   v
Lite Mode Gate
   |
   v
Primary Agent Selected
   |
   +-------------------------------+
   |       Evidence Subagents      |
   |  RAG | APIs | Web | MCP | DB  |
   +-------------------------------+
   |
   v
Evidence Merge
   |
   v
Primary Agent Final Answer
   |
   v
Compact Confidence + Sources
```

---

## What Lite Mode Means

Lite Mode is not a separate product.
It is a streamlined orchestration profile inside the existing council system.

### In Lite Mode
- One agent owns the answer.
- Five support subagents collect supporting evidence.
- All source paths stay active: APIs, web scraping, MCP, RAG, and graph/database lookups.
- The UI shows a compact pipeline instead of a full multi-round debate.
- The response remains citation-aware and source-backed.

### Not In Lite Mode
- Full 6-agent debate.
- Multiple debate rounds.
- Moderator scoring board.
- Supervisor synthesis page.

---

## Step-by-Step Process

### Step 1. User selects Lite Mode

The user opens Settings or the Council page and enables Lite Mode.

They also choose a primary agent, for example:
- Risk Sentinel
- Supply Optimizer
- Logistics Navigator
- Market Intelligence
- Finance Guardian
- Brand Protector

### Step 2. Query is submitted

The frontend sends a request that includes:
- `query`
- `lite: true`
- `primary_agent`
- optional `support_agent_policy`

### Step 3. Backend enters Lite Mode gate

The council route inspects the request and chooses the lite pipeline instead of the full debate pipeline.

### Step 4. Source gathering begins

The system gathers evidence from multiple layers:
- RAG context
- DuckDuckGo search
- Firecrawl web scraping
- MCP tools
- Domain APIs such as news, weather, finance, forex, geopolitics, logistics
- Neo4j graph queries when useful
- Neon/PostgreSQL audit and session state
- Redis cache for speed

### Step 5. Five support subagents run

Instead of all six agents debating, Lite Mode launches:
- 1 primary agent
- 5 support subagents

The support subagents should not try to dominate the answer.
They should return compact evidence summaries such as:
- key facts
- source URLs
- confidence hints
- contradictions
- alerts
- relevant numeric values

### Step 6. Evidence is merged

All support outputs are merged into one evidence bundle.
The primary agent receives:
- source snippets
- citation map
- data quality summary
- conflicts or gaps
- source counts

### Step 7. Primary agent writes the final answer

The primary agent produces the final response using:
- the query
- the merged evidence bundle
- the selected domain framing
- source citations

### Step 8. UI renders result

The frontend shows:
- primary agent response
- support agent evidence cards
- compact source pipeline
- clickable citations
- confidence badge
- optional follow-up actions

### Step 9. Session is stored

The result is persisted to the existing session/cache system so it can be re-opened or audited later.

---

## Proposed Backend Flow

```text
POST /council/query
   |
   v
Request Schema
   |
   +--> lite = false  -> existing full council flow
   |
   +--> lite = true   -> lite pipeline
                          |
                          v
                  Select primary agent
                          |
                          v
                  Spawn 5 support subagents
                          |
                          v
          Gather RAG + APIs + Web + MCP + Graph/DB
                          |
                          v
                Merge evidence bundle + citations
                          |
                          v
               Primary agent generates final answer
                          |
                          v
                Store session + render to frontend
```

---

## Backend Connections

### 1. Route Layer

Files involved:
- [backend/routes/council.py](../backend/routes/council.py)
- [backend/routes/council_v2.py](../backend/routes/council_v2.py)

Role:
- Accept lite-mode request fields.
- Route the request to lite or full orchestration.
- Preserve current full council behavior.

### 2. Graph Orchestration

Files involved:
- [backend/graph.py](../backend/graph.py)
- [backend/agents/dynamic_routing.py](../backend/agents/dynamic_routing.py)

Role:
- Decide which agent is primary.
- Choose the five support subagents.
- Keep explicit routing support through `context.active_agents`.
- Preserve current RAG prefetch and MCP escalation patterns.

### 3. RAG Layer

Files involved:
- [backend/rag/agent_rag_integration.py](../backend/rag/agent_rag_integration.py)
- [backend/rag/api.py](../backend/rag/api.py)
- [backend/rag/vectorstore.py](../backend/rag/vectorstore.py)
- [backend/rag/graph_rag.py](../backend/rag/graph_rag.py)

Role:
- Retrieve internal knowledge base context.
- Use ChromaDB as the local vector store and Pinecone as fallback.
- Optionally query Neo4j graph context.
- Return citation-rich context chunks.

### 4. MCP Layer

Files involved:
- [backend/mcp/agent_mcp_integration.py](../backend/mcp/agent_mcp_integration.py)
- [backend/mcp/server.py](../backend/mcp/server.py)
- [backend/mcp/registry.py](../backend/mcp/registry.py)
- [backend/mcp/audit.py](../backend/mcp/audit.py)
- [backend/mcp/cache.py](../backend/mcp/cache.py)

Role:
- Invoke tools for news, weather, shipping, finance, supplier search, and other real-time data.
- Respect sandbox, caching, and audit logging.
- Keep the same security and tool ownership model.

### 5. Database Layer

Files involved:
- [backend/db/neon.py](../backend/db/neon.py)
- [backend/db/redis_client.py](../backend/db/redis_client.py)
- [backend/db/neo4j_client.py](../backend/db/neo4j_client.py)

Role:
- Neon stores session and audit records.
- Redis stores sessions and cache entries.
- Neo4j stores supplier and relationship graphs.

---

## Suggested Lite Mode Orchestration Design

A practical way to implement Lite Mode is to divide the work into one primary writer and five evidence workers.

### Example Roles

```text
Primary Agent
- Final answer owner
- Produces the actual response
- Interprets merged evidence

Support Agent 1
- RAG retrieval and historical context

Support Agent 2
- API and market/news lookup

Support Agent 3
- MCP tool execution and verification

Support Agent 4
- Web scraping and external evidence

Support Agent 5
- Graph/database lookup and dependency mapping
```

### Example Evidence Contract

Each support subagent should return a small structured payload:

```json
{
  "agent": "risk",
  "role": "support",
  "summary": "Key findings in 3-5 bullets",
  "sources": ["[1]", "[2]", "[3]"],
  "confidence": 82,
  "flags": ["contradiction", "needs_verification"],
  "links": ["https://...", "https://..."]
}
```

The primary agent then consumes these and writes the final answer.

---

## UI/UX Goals

Lite Mode should feel:
- fast
- focused
- evidence-rich
- calmer than the full council debate
- easier to scan on desktop and mobile

### Visual principles
- One dominant primary agent panel.
- Five compact support cards.
- A narrow source pipeline strip.
- Citation chips that remain clickable.
- Less visual noise than the full council mode.

---

## UI Flow

```text
[Settings / Chat Header]
        |
        v
[Lite Mode Toggle]
        |
        v
[Primary Agent Picker]
        |
        v
[Query Box]
        |
        v
[Submit]
        |
        v
[Source Pipeline Appears]
        |
        v
[Primary Agent Card]
        |
        v
[Five Support Evidence Cards]
        |
        v
[Final Answer + Citations + Confidence]
```

---

## Wireframe

### Lite Mode Chat Page

```text
┌──────────────────────────────────────────────────────────────────────┐
│ SupplyChainGPT Council                                                │
├──────────────────────────────────────────────────────────────────────┤
│ Mode: [ Lite Mode ON ]   Primary Agent: [ Risk Sentinel v ]          │
│                                                                      │
│ Query: [ What is our exposure if Supplier X fails?               ]   │
│ [Run Lite Council]                                                   │
├──────────────────────────────────────────────────────────────────────┤
│ Pipeline                                                              │
│ [RAG] -> [APIs] -> [Web Scraping] -> [MCP] -> [Graph/DB]              │
├──────────────────────────────────────────────────────────────────────┤
│ Primary Agent                                                         │
│ ┌──────────────────────────────────────────────────────────────────┐ │
│ │ Risk Sentinel                                                    │ │
│ │ Final answer text with citations [1][2][3]                       │ │
│ │ Confidence: 87/100                                              │ │
│ └──────────────────────────────────────────────────────────────────┘ │
├──────────────────────────────────────────────────────────────────────┤
│ Support Evidence                                                      │
│ ┌──────────────┐ ┌──────────────┐ ┌──────────────┐                   │
│ │ Support #1   │ │ Support #2   │ │ Support #3   │                   │
│ │ summary      │ │ summary      │ │ summary      │                   │
│ └──────────────┘ └──────────────┘ └──────────────┘                   │
│ ┌──────────────┐ ┌──────────────┐                                      │
│ │ Support #4   │ │ Support #5   │                                      │
│ │ summary      │ │ summary      │                                      │
│ └──────────────┘ └──────────────┘                                      │
├──────────────────────────────────────────────────────────────────────┤
│ Sources & References                                                  │
│ [1] [2] [3] [4] [5] [6] [7] [8]                                      │
└──────────────────────────────────────────────────────────────────────┘
```

### Lite Mode Settings Panel

```text
┌───────────────────────────────┐
│ Council Mode                  │
├───────────────────────────────┤
│ [x] Lite Mode                 │
│                               │
│ Primary Agent                 │
│ [ Risk Sentinel v ]           │
│                               │
│ Support Subagents             │
│ [x] RAG                       │
│ [x] API / Market              │
│ [x] MCP Tools                 │
│ [x] Web Scraping              │
│ [x] Graph / DB                │
└───────────────────────────────┘
```

---

## UX Behavior

### When Lite Mode is ON
- Show only one main decision path.
- Collapse the moderator and supervisor sections.
- Replace the debate timeline with a short evidence pipeline.
- Show support agents as compact cards or side chips.
- Keep citations visible and clickable.

### When Lite Mode is OFF
- Use the existing full council debate UI.
- Show all agent tabs.
- Show moderator summary.
- Show supervisor verdict.

---

## Frontend Connections

### 1. Settings Store

Files involved:
- [frontend/src/store/settingsStore.ts](../frontend/src/store/settingsStore.ts)
- [frontend/src/pages/Settings.tsx](../frontend/src/pages/Settings.tsx)

Add:
- `lite_mode: boolean`
- `primary_agent: string | null`
- optional support-agent policy fields

### 2. Stream Hook

Files involved:
- [frontend/src/hooks/useCouncilV2Stream.ts](../frontend/src/hooks/useCouncilV2Stream.ts)

Role:
- Send lite-mode request body.
- Include selected primary agent.
- Pass optional support-agent selection.
- Parse SSE events.

### 3. Council State Store

Files involved:
- [frontend/src/store/councilV2Store.ts](../frontend/src/store/councilV2Store.ts)

Role:
- Track primary agent state.
- Track support evidence outputs.
- Track pipeline stages.
- Store citation maps.
- Collapse moderator/supervisor when lite mode is active.

### 4. Chat and Debate Pages

Files involved:
- [frontend/src/pages/Chat.tsx](../frontend/src/pages/Chat.tsx)
- [frontend/src/pages/Debate.tsx](../frontend/src/pages/Debate.tsx)

Role:
- Render the lite-mode main answer panel.
- Show support evidence cards.
- Show compact source pipeline.
- Keep the full debate UI for normal mode.

### 5. Citation Renderer

Files involved:
- [frontend/src/components/shared/CitedMarkdownRenderer.tsx](../frontend/src/components/shared/CitedMarkdownRenderer.tsx)

Role:
- Keep citations clickable.
- Render `[N]` source markers.
- Preserve source URL mapping from the backend.

---

## Tech Stack

### Backend
- FastAPI
- LangGraph
- LangChain
- Python async I/O
- Redis
- Neon PostgreSQL
- Neo4j
- ChromaDB
- Pinecone fallback
- MCP tool server
- Firecrawl
- DuckDuckGo search

### Frontend
- React
- TypeScript
- Vite
- Zustand
- Tailwind CSS
- Framer Motion
- SSE streaming
- Markdown rendering

### Source Systems
- RAG for internal knowledge
- APIs for real-time market and risk data
- Web scraping for live web evidence
- MCP for sandboxed tool execution
- Graph/database lookup for relationships and supplier networks

---

## Data and Event Flow

```text
1. User enters query
2. UI sends lite request + primary agent
3. Backend sets lite mode context
4. Dynamic routing resolves primary and support agents
5. RAG prefetch runs
6. MCP escalation runs when needed
7. APIs and web scraping fetch current evidence
8. Support subagents summarize evidence
9. Primary agent writes final answer
10. Citations map is returned
11. Frontend renders answer and references
12. Session is cached and auditable
```

---

## Step-by-Step Build Plan

### Phase 1. Backend contract
- Add lite request fields.
- Add primary-agent selection.
- Add support-agent policy fields.

### Phase 2. Lite pipeline branch
- Add lite orchestration before the full debate branch.
- Keep the existing full debate untouched.
- Route evidence tasks through the existing integrations.

### Phase 3. Evidence packaging
- Define a compact evidence schema.
- Merge RAG, API, web, MCP, and graph results.
- Add citation mapping.

### Phase 4. Frontend state
- Store lite mode preferences.
- Store selected primary agent.
- Track support outputs.

### Phase 5. UI
- Add toggle in Settings.
- Add primary-agent selector.
- Render a lite pipeline and compact support cards.

### Phase 6. Testing
- Verify lite mode request/response.
- Verify citations.
- Verify full council still works.

---

## Acceptance Criteria

Lite Mode is complete when:
- A user can enable lite mode.
- A user can choose exactly one primary agent.
- Five support subagents gather evidence.
- RAG, APIs, web scraping, MCP, and graph/database sources are used.
- The frontend shows a compact, understandable UI.
- Citations are preserved and clickable.
- Full council mode still behaves exactly as before.

---

## Suggested File Map

Backend:
- [backend/routes/council.py](../backend/routes/council.py)
- [backend/graph.py](../backend/graph.py)
- [backend/debate_engine.py](../backend/debate_engine.py)
- [backend/agents/dynamic_routing.py](../backend/agents/dynamic_routing.py)
- [backend/rag/agent_rag_integration.py](../backend/rag/agent_rag_integration.py)
- [backend/mcp/agent_mcp_integration.py](../backend/mcp/agent_mcp_integration.py)
- [backend/config.py](../backend/config.py)
- [backend/state.py](../backend/state.py)

Frontend:
- [frontend/src/pages/Chat.tsx](../frontend/src/pages/Chat.tsx)
- [frontend/src/pages/Debate.tsx](../frontend/src/pages/Debate.tsx)
- [frontend/src/pages/Settings.tsx](../frontend/src/pages/Settings.tsx)
- [frontend/src/store/settingsStore.ts](../frontend/src/store/settingsStore.ts)
- [frontend/src/store/councilV2Store.ts](../frontend/src/store/councilV2Store.ts)
- [frontend/src/hooks/useCouncilV2Stream.ts](../frontend/src/hooks/useCouncilV2Stream.ts)
- [frontend/src/types/council.ts](../frontend/src/types/council.ts)

---

## Final Note

The best implementation path is to preserve the existing full council as the default and add Lite Mode as a new, clearly labeled path.

That gives the user a fast option when they want a single decisive answer, while still leveraging the platform’s strongest capability: gathering and grounding evidence from many systems at once.
