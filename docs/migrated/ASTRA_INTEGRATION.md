# Astra ⭐ - Swarm Intelligence Integration

## Overview

**Astra** (formerly Mirofish) is now fully integrated with the SupplyChainGPT Council of Debate system. When you run a Council analysis, Astra automatically activates in parallel to provide predictive simulations and swarm intelligence.

## What Changed

### 1. Renamed Mirofish → Astra ⭐
- All `backend/mirofish/` files moved to `backend/astra/`
- All imports updated from `mirofish` to `astra`
- Star icon (⭐) added to represent Astra throughout the system
- Routes changed from `/simulation/*` to `/astra/*`

### 2. Automatic Council Integration

**When you run the Council of Debate, Astra now runs automatically in parallel!**

#### How It Works:
```
Council Query → Moderator → Dynamic Routing → RAG → MCP → ⭐ ASTRA (parallel) → Agents → Debate → Synthesis
```

The new `astra_parallel_node` in the graph:
- Triggers automatically after MCP escalation
- Runs brand + market simulations in parallel
- Completes before agent fan-out begins
- Results stored in `state.astra_results`

### 3. New API Endpoints

#### `/astra/run` - Run Single Simulation
```bash
POST /astra/run
{
  "query": "What happens if Taiwan chip supply is disrupted?",
  "agent_type": "brand",
  "horizon_days": 30,
  "num_personas": 50,
  "rounds": 3,
  "stream": true
}
```

#### `/astra/swarm` - Run Parallel Brand + Market Simulations
```bash
POST /astra/swarm
{
  "query": "Impact of new tariffs on supply chain",
  "horizon_days": 30,
  "num_personas": 50,
  "rounds": 3
}
```

#### `/astra/chat` - Chat with Simulation Results
```bash
POST /astra/chat
{
  "simulation_id": "brand_astra_abc123",
  "question": "What are the worst-case scenarios?"
}
```

#### `/astra/{simulation_id}` - Get Simulation State
```bash
GET /astra/abc123def456
```

### 4. Astra Results in Council Response

When you run a Council query, the response now includes:

```json
{
  "session_id": "...",
  "recommendation": "...",
  "confidence": 0.85,
  "agent_outputs": [...],
  "astra_results": {
    "enabled": true,
    "brand": {
      "agent": "brand",
      "simulation_id": "brand_astra_xyz",
      "status": "completed",
      "prediction": "Brand sentiment will decline 15% over 30 days...",
      "confidence": 0.78,
      "key_factors": ["social_media_backlash", "competitor_exploitation"],
      "risks": ["reputation_damage", "customer_churn"],
      "opportunities": ["crisis_comms_pivot", "transparency_campaign"],
      "recommendations": ["launch_proactive_pr", "monitor_sentiment_daily"],
      "scenarios": [
        {"name": "Best case", "probability": 0.2, "description": "..."},
        {"name": "Most likely", "probability": 0.6, "description": "..."},
        {"name": "Worst case", "probability": 0.2, "description": "..."}
      ],
      "entity_count": 12,
      "persona_count": 20,
      "rounds_completed": 2
    },
    "market": {
      "agent": "market",
      "simulation_id": "market_astra_abc",
      "status": "completed",
      "prediction": "Market prices will spike 25% in Q2...",
      "confidence": 0.82,
      "key_factors": ["supply_shortage", "demand_surge"],
      "risks": ["price_volatility", "supplier_consolidation"],
      "opportunities": ["forward_contracts", "alternative_sourcing"],
      "recommendations": ["hedge_commodity_exposure", "diversify_suppliers"],
      "entity_count": 15,
      "persona_count": 20,
      "rounds_completed": 2
    }
  }
}
```

## Features

### Automatic Parallel Execution
- Astra runs **simultaneously** with Council agents
- No additional latency added to Council response
- Brand and Market simulations run in parallel
- Results available when Council synthesis completes

### Swarm Intelligence
- 20-50 AI personas per simulation
- Multiple roles: competitors, customers, media, regulators, investors, analysts
- Each persona has unique traits, goals, and memory
- Personas interact over multiple rounds
- Emergent behavior from collective intelligence

### Predictive Scenarios
- Best case, most likely, worst case scenarios
- Probability-weighted outcomes
- 30/60/90-day forecasts
- Risk and opportunity identification
- Actionable recommendations

### Graph-Based Entity Extraction
- Automatically extracts entities from query
- Builds relationship graph
- Maps dependencies and influences
- Identifies key stakeholders

## Configuration

### Disable Astra for Specific Queries
```python
# In your Council request
{
  "query": "...",
  "context": {
    "disable_astra": true  # Astra won't run
  }
}
```

### Adjust Simulation Parameters
Edit `backend/graph_astra_integration.py`:
```python
config = SimulationConfig(
    name=sim_id,
    seed_query=query,
    horizon_days=30,        # Adjust forecast horizon
    num_personas=20,        # Adjust persona count (2-200)
    rounds=2,               # Adjust simulation rounds (1-10)
)
```

## Performance

### Optimizations for Parallel Execution
- **Fast mode graph building** - Reduced entity extraction time
- **Batched persona generation** - Single LLM call per role group
- **Reduced persona count** - 20 personas (vs 50 in standalone mode)
- **Fewer rounds** - 2 rounds (vs 3 in standalone mode)
- **Parallel brand + market** - Both run simultaneously

### Typical Execution Times
- Graph building: 2-3 seconds
- Persona generation: 3-5 seconds
- Simulation (2 rounds): 8-12 seconds
- Report generation: 2-3 seconds
- **Total: 15-23 seconds** (runs in parallel with Council)

## Icon Usage

The star icon (⭐) represents Astra throughout the system:
- API routes: `/astra/*`
- Logs: `⭐ Astra: Starting parallel simulations...`
- UI components: Use star icon for Astra-related features
- Documentation: Astra ⭐ branding

## Frontend Integration

### Display Astra Results
```typescript
// In your Council response handler
if (response.astra_results?.enabled) {
  const brandPrediction = response.astra_results.brand;
  const marketPrediction = response.astra_results.market;
  
  // Display predictions, scenarios, risks, opportunities
  // Show star icon (⭐) to indicate Astra intelligence
}
```

### Recommended UI Components
1. **Astra Panel** - Collapsible section showing predictions
2. **Scenario Cards** - Best/likely/worst case scenarios
3. **Risk/Opportunity Lists** - Color-coded indicators
4. **Confidence Meters** - Visual confidence scores
5. **Star Icon** - Use ⭐ to indicate Astra-powered insights

## Testing

### Test Astra Integration
```bash
# Run Council with Astra
curl -X POST http://localhost:8000/council/query \
  -H "Content-Type: application/json" \
  -d '{
    "query": "What if our main supplier in Taiwan fails?",
    "stream": false
  }'

# Check for astra_results in response
```

### Test Standalone Astra
```bash
# Run Astra simulation directly
curl -X POST http://localhost:8000/astra/run \
  -H "Content-Type: application/json" \
  -d '{
    "query": "Impact of port strike on supply chain",
    "agent_type": "brand",
    "stream": false
  }'
```

### Test Astra Swarm
```bash
# Run parallel brand + market simulations
curl -X POST http://localhost:8000/astra/swarm \
  -H "Content-Type: application/json" \
  -d '{
    "query": "New tariffs on electronics imports",
    "horizon_days": 60,
    "num_personas": 30,
    "rounds": 3
  }'
```

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    COUNCIL OF DEBATE                         │
│                                                              │
│  Query → Moderator → Routing → RAG → MCP → ⭐ ASTRA        │
│                                              ↓               │
│                                         [Parallel]           │
│                                              ↓               │
│                                    Brand Simulation          │
│                                    Market Simulation         │
│                                              ↓               │
│                                         [Results]            │
│                                              ↓               │
│  → Risk → Supply → Logistics → Market → Finance → Brand     │
│                                              ↓               │
│  → Predictions → Debate → Fallback → Synthesis              │
│                                              ↓               │
│  Final Response (includes Astra results)                    │
└─────────────────────────────────────────────────────────────┘
```

## Benefits

1. **Predictive Intelligence** - See future scenarios before they happen
2. **Swarm Wisdom** - Collective intelligence from multiple personas
3. **Parallel Execution** - No added latency to Council
4. **Comprehensive Analysis** - Council logic + Astra predictions
5. **Risk Identification** - Proactive risk detection
6. **Opportunity Discovery** - Uncover hidden opportunities
7. **Scenario Planning** - Multiple outcome pathways
8. **Confidence Scoring** - Transparent prediction confidence

## Next Steps

1. **Frontend Integration** - Add Astra results display to UI
2. **Icon Implementation** - Use ⭐ throughout frontend
3. **Scenario Visualization** - Create scenario comparison charts
4. **Persona Explorer** - Show persona interactions
5. **Sentiment Tracking** - Display sentiment trajectory
6. **Export Reports** - PDF export with Astra predictions

---

**Astra ⭐ - Swarm Intelligence for Supply Chain Predictions**

*Automatically runs alongside the Council of Debate to provide predictive simulations and scenario forecasting.*
