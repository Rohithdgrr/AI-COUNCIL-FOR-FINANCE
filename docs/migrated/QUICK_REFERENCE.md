# 🚀 Quick Reference Card

## Start/Stop Commands

```bash
# Windows
start-all.bat    # Start everything
stop-all.bat     # Stop everything

# Linux/Mac
./start-all.sh   # Start everything
./stop-all.sh    # Stop everything
```

## Access URLs

- **Frontend**: http://localhost:3001
- **Backend API**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs
- **Neo4j**: http://localhost:7474 (neo4j/testpassword)
- **Redis**: localhost:6379
- **ChromaDB**: http://localhost:8001
- **Firecrawl**: http://localhost:3002

## Key Features

### AI Council
- 6 specialized agents (Risk, Supply, Logistics, Market, Finance, Brand)
- 3-round structured debate
- Real-time streaming
- Consensus building

### Astra ⭐ Swarm
- Multi-persona simulation
- Brand + Market intelligence
- Automatic parallel execution
- Predictive scenarios

### Data Integration
- 99+ MCP tools
- 27+ external APIs
- Hybrid RAG pipeline
- Real-time market data

## Quick Test

1. Open http://localhost:3001
2. Go to "Council Chat" or "Debate"
3. Enter: "Analyze semiconductor supply chain risks from Taiwan"
4. Watch the magic happen!

## Documentation

- `START_GUIDE.md` - Complete setup
- `SECURITY_FIXES.md` - Security improvements
- `UI_IMPROVEMENTS.md` - UI enhancements
- `FINAL_REPORT.md` - Complete overview

## Security

### API Keys (Secure)
```typescript
import { apiKeyManager } from '@/lib/secureStorage'

// Set
apiKeyManager.setApiKey('your-key')

// Get
const key = apiKeyManager.getApiKey()
```

### Input Validation
```typescript
import { validateQuery } from '@/lib/validation'

const { valid, error } = validateQuery(input)
if (!valid) {
  console.error(error)
  return
}
```

## Components

### Logo
```tsx
import Logo from '@/components/shared/Logo'

<Logo size="lg" showText={true} animated={true} />
```

### Enhanced Input
```tsx
import EnhancedInput from '@/components/shared/EnhancedInput'

<EnhancedInput
  value={query}
  onChange={setQuery}
  onSubmit={handleSubmit}
  disabled={loading}
/>
```

## Troubleshooting

### Backend not starting?
```bash
# Check if port 8000 is in use
netstat -ano | findstr :8000

# Check Python environment
venv\Scripts\python --version
```

### Frontend not starting?
```bash
# Check if port 3001 is in use
netstat -ano | findstr :3001

# Reinstall dependencies
cd frontend
npm install
```

### Docker services not running?
```bash
# Check Docker status
docker ps

# Restart services
docker compose down
docker compose up -d
```

## Status Check

```bash
# Backend health
curl http://localhost:8000/health

# Frontend (should return HTML)
curl http://localhost:3001

# Docker services
docker ps
```

## Common Issues

### "API key invalid"
- Set API key in Settings page
- Or use environment variables

### "Connection refused"
- Check if services are running
- Verify ports are not blocked

### "Module not found"
- Backend: `pip install -r backend/requirements.txt`
- Frontend: `cd frontend && npm install`

## Performance Tips

- Use Lite Mode for faster responses
- Enable Astra ⭐ for predictions
- Clear browser cache if slow
- Check Docker resource limits

## Support

- Check logs in terminal windows
- Review `FINAL_REPORT.md` for details
- See `SECURITY_FIXES.md` for security
- Read `UI_IMPROVEMENTS.md` for UI

---

**Version**: 2.0.0
**Status**: Production Ready ✅
