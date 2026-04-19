# SupplyChainGPT Council

An AI-powered supply chain intelligence platform with multi-agent debate system, real-time risk monitoring, and brand intelligence.

![Version](https://img.shields.io/badge/version-2.0.0-blue)
![License](https://img.shields.io/badge/license-MIT-green)
![Tests](https://img.shields.io/badge/tests-50%20passing-brightgreen)

## Quick Links

- [Full Documentation](./docs/README.md)
- [UI/UX Enhancements](./docs/ui-ux-enhancements.md)
- [Backend Architecture](./docs/backend.md)
- [Frontend Guide](./docs/frontend.md)
- [Agent System](./docs/agents.md)
- [API Reference](./docs/routing.md)

## Features

### 🤖 AI Council System
- 6 specialized AI agents (Risk, Supply, Logistics, Market, Finance, Brand)
- Multi-round debate with supervisor oversight
- Real-time streaming responses
- Confidence scoring and consensus building

### 📊 Intelligence Dashboard
- Live market data (stocks, forex, commodities)
- Risk heatmaps and disaster alerts
- Supplier directory with risk scoring
- Supply chain health score gauge

### 🔍 Brand Intelligence
- Social sentiment analysis (Reddit)
- Competitor tracking and comparison
- Brand health monitoring
- Real-time alert system

### ⚙️ Advanced Settings
- 20+ customizable preferences
- Response verbosity control
- Typography and theme options
- Data source prioritization

## Tech Stack

### Backend
- **Framework**: FastAPI (Python)
- **AI**: LangChain, LangGraph
- **Database**: Neon PostgreSQL, Redis, Neo4j
- **MCP Tools**: Firecrawl, Finnhub, FRED, etc.

### Frontend
- **Framework**: React + TypeScript
- **Styling**: Tailwind CSS
- **State**: Zustand
- **Animation**: Framer Motion
- **Testing**: Vitest + React Testing Library

## Quick Start

### Prerequisites
- Python 3.11+
- Node.js 18+
- Docker & Docker Compose

### 1. Clone and Setup
```bash
git clone https://github.com/Rohithdgrr/cognizant-hackathon.git
cd cognizant-hackathon
```

### 2. Environment Variables
```bash
cp .env.example .env
# Edit .env with your API keys
```

### 3. Start Services
```bash
# Using batch script (Windows)
start-all.bat

# Or manually
docker-compose up -d  # Redis, Neo4j, ChromaDB
cd backend && uvicorn main:app --reload
cd frontend && npm run dev
```

### 4. Access Application
- Frontend: http://localhost:5173
- API Docs: http://localhost:8000/docs
- Health Check: http://localhost:8000/health

## Recent Updates

### UI/UX Enhancements (2026-04-17)
- ✅ Sources & References panel with expandable citations
- ✅ Enhanced AI response readability with visual callouts
- ✅ New Settings page with 6 tabbed sections
- ✅ Dashboard health score and quick actions
- ✅ Brand Intelligence alerts and competitor comparison
- ✅ 50 passing unit tests

See [ui-ux-enhancements.md](./docs/ui-ux-enhancements.md) for details.

## Documentation

| Document | Description |
|----------|-------------|
| [README.md](./docs/README.md) | Complete project documentation |
| [ui-ux-enhancements.md](./docs/ui-ux-enhancements.md) | UI/UX improvements guide |
| [backend.md](./docs/backend.md) | Backend services architecture |
| [frontend.md](./docs/frontend.md) | Frontend development guide |
| [agents.md](./docs/agents.md) | Multi-agent system details |
| [mcp.md](./docs/mcp.md) | MCP tools integration |
| [rag.md](./docs/rag.md) | RAG implementation |
| [routing.md](./docs/routing.md) | API routing reference |
| [testing.md](./docs/testing.md) | Testing strategy |
| [deployment.md](./docs/deployment.md) | Deployment guide |

## Project Structure

```
cognizant-hackathon/
├── backend/              # FastAPI application
│   ├── agents/          # AI agent implementations
│   ├── mcp/             # MCP tool definitions
│   ├── routes/          # API endpoints
│   └── main.py          # Application entry
├── frontend/            # React application
│   ├── src/
│   │   ├── components/  # Shared UI components
│   │   ├── pages/       # Route pages
│   │   ├── store/       # Zustand stores
│   │   └── hooks/       # Custom hooks
│   └── package.json
├── docs/                # Documentation
├── tests/               # Integration tests
└── docker-compose.yml   # Infrastructure services
```

## Testing

```bash
# Frontend tests
cd frontend
npm test

# Backend tests
cd backend
pytest

# All tests
npm run test:all
```

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

[MIT](./LICENSE)

## Acknowledgments

- Built for Cognizant Hackathon 2026
- Powered by LangChain, FastAPI, and React
- MCP integration for external data sources
