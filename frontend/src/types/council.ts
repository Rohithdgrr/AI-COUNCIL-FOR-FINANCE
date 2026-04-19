export interface AgentOutput {
  agent: string
  output: string
  confidence: number
  evidence: string[]
}

export interface DebateRound {
  round_number: number
  agent_positions: Record<string, string>
  disagreements: string[]
  resolutions: string[]
}

export interface CouncilSession {
  session_id: string
  query: string
  recommendation: string | null
  confidence: number | null
  agent_outputs: AgentOutput[]
  evidence: string[]
  debate_history: DebateRound[]
  round_number: number
  status: 'pending' | 'streaming' | 'complete' | 'error'
  latency_ms: number
  context?: Record<string, unknown>
}

export interface CouncilRequest {
  query: string
  context?: Record<string, unknown>
  ws_session_id?: string
}

export type AgentStatus = 'idle' | 'thinking' | 'done' | 'error'

export interface AgentInfo {
  key: string
  label: string
  color: string
  bgColor: string
  borderColor: string
  textColor: string
  dotColor: string
  hexColor: string
}

export interface AgentRoundState {
  status: AgentStatus
  output: string
  confidence: number
}

export interface ModeratorResult {
  scores: Record<string, number>
  consensus: number
  summary: string
}

export interface SupervisorResult {
  output: string
  confidence: number
}

export interface CouncilV2StreamEvent {
  type: 'start' | 'round_start' | 'agent_start' | 'token' | 'agent_done' | 'agent_error' | 'moderator_start' | 'moderator_done' | 'supervisor_done' | 'complete' | 'pipeline_stage' | 'citations_ready' | 'citations_map' | 'source_discovered' | 'support_evidence' | 'evidence_bundle' | 'subagent_start' | 'subagent_evidence' | 'mirofish_start' | 'mirofish_agent_progress' | 'mirofish_agent_complete' | 'mirofish_agent_error' | 'mirofish_complete'
  session_id?: string
  query?: string
  lite_mode?: boolean
  mirofish_enabled?: boolean
  primary_agent?: string
  support_agents?: string[]
  support_agent_policy?: SupportAgentPolicy
  round?: number
  phase?: string
  agent?: string
  agents?: string[]
  content?: string
  error?: string
  confidence?: number
  scores?: Record<string, number>
  consensus?: number
  summary?: string
  recommendation?: string
  output_preview?: string
  stage?: string
  detail?: string
  count?: number
  urls?: Record<string, string>
  sources?: Array<{num: number, title: string, url: string}>
  evidence?: SupportEvidence
  bundle?: EvidenceBundle
  subagent_key?: string
  parent_agent?: string
  data_channel?: string
  label?: string
  subagent_evidence?: SubagentEvidence[]
  // MiroFish fields
  simulation_id?: string
  entities?: string[]
  entity_count?: number
  personas?: string[]
  persona_count?: number
  result?: SimulationResult & { simulation_id?: string; status?: string; entities?: string[]; personas?: string[]; report_summary?: string }
}

export interface CouncilStreamEvent {
  type: 'start' | 'agent_start' | 'token' | 'agent_done' | 'agent_error' | 'complete'
  agent?: string
  content?: string
  error?: string
  session_id?: string
  recommendation?: string
}

export interface Recommendation {
  text: string
  confidence: number
  supporting_agents: string[]
  risk_level: 'low' | 'medium' | 'high' | 'critical'
}

// ---------------------------------------------------------------------------
// Full graph pipeline types (from LangGraph council)
// ---------------------------------------------------------------------------

export interface Prediction {
  type: 'price' | 'disruption' | 'lead_time'
  label: string
  value: number
  unit: string
  confidence: number
  horizon: string
}

export interface TieredFallback {
  type: 'tier1_immediate' | 'tier2_shortterm' | 'tier3_strategic'
  details: string
  cost_estimate: number
  time_to_implement: string
}

export interface BrandSentiment {
  overall_sentiment: string
  sentiment_score: number
  crisis_detected: boolean
  crisis_comms?: string
  ad_pivot?: string
  competitor_analysis?: Record<string, unknown>
}

export interface CouncilGraphResult {
  session_id: string
  query: string
  recommendation: string
  confidence: number
  risk_score: number
  debate_rounds: DebateRound[]
  agent_outputs: AgentOutput[]
  predictions: Prediction[]
  tiered_fallbacks: TieredFallback[]
  brand_sentiment: BrandSentiment | null
  debate_history: { round: number; phase: string; confidence: number }[]
}

/** WebSocket event from /observability/ws/debate full graph pipeline */
export interface CouncilWSEvent {
  type: 'agent_done' | 'debate_round' | 'complete' | 'human_review_needed' | 'heartbeat'
  data: {
    session_id?: string
    agent?: string
    confidence?: number
    contribution?: string
    debate_rounds?: DebateRound[]
    recommendation?: string
    risk_score?: number
  }
}

// ---------------------------------------------------------------------------
// Lite Mode types
// ---------------------------------------------------------------------------

export interface SupportEvidence {
  agent: string
  role: string
  summary: string
  sources: string[]
  confidence: number
  flags: string[]
  links: string[]
}

export interface EvidenceBundle {
  support_evidence: SupportEvidence[]
  citation_map: Record<string, string>
  data_quality_summary: string
  conflicts: string[]
  source_counts: Record<string, number>
}

export interface SubagentEvidence {
  subagent_key: string
  parent_agent: string
  data_channel: string
  domain_hint: string
  summary: string
  sources: string[]
  confidence: number
  flags: string[]
  links: string[]
}

export interface SubagentDef {
  key: string
  label: string
  data_channel: string
  domain_hint: string
}

export interface LiteModeResult {
  primary_agent: string
  evidence_bundle: EvidenceBundle
  final_answer: string
  confidence: number
}

export interface SupportAgentPolicy {
  rag: boolean
  api: boolean
  mcp: boolean
  web: boolean
  graph: boolean
}

export const DEFAULT_SUPPORT_AGENT_POLICY: SupportAgentPolicy = {
  rag: true,
  api: true,
  mcp: true,
  web: true,
  graph: true,
}

// Channel metadata for subagent UI rendering
export const SUBAGENT_CHANNELS = ['rag', 'api', 'web', 'mcp', 'graph'] as const
export type SubagentChannel = typeof SUBAGENT_CHANNELS[number]

export const SUBAGENT_CHANNEL_META: Record<SubagentChannel, { icon: string; shortLabel: string; color: string }> = {
  rag:   { icon: 'database',    shortLabel: 'RAG',   color: '#6366F1' },
  api:   { icon: 'globe',       shortLabel: 'API',   color: '#3B82F6' },
  web:   { icon: 'search',      shortLabel: 'Web',   color: '#8B5CF6' },
  mcp:   { icon: 'cpu',         shortLabel: 'MCP',   color: '#F59E0B' },
  graph: { icon: 'git-branch',  shortLabel: 'Graph', color: '#10B981' },
}

export const COUNCIL_AGENTS: AgentInfo[] = [
  { key: 'risk', label: 'Risk Sentinel', color: 'bg-red-500', bgColor: 'bg-red-50', borderColor: 'border-red-200', textColor: 'text-red-700', dotColor: 'bg-red-500', hexColor: '#EF4444' },
  { key: 'supply', label: 'Supply Optimizer', color: 'bg-violet-500', bgColor: 'bg-violet-50', borderColor: 'border-violet-200', textColor: 'text-violet-700', dotColor: 'bg-violet-500', hexColor: '#7C3AED' },
  { key: 'logistics', label: 'Logistics Navigator', color: 'bg-cyan-500', bgColor: 'bg-cyan-50', borderColor: 'border-cyan-200', textColor: 'text-cyan-700', dotColor: 'bg-cyan-500', hexColor: '#06B6D4' },
  { key: 'market', label: 'Market Intelligence', color: 'bg-amber-500', bgColor: 'bg-amber-50', borderColor: 'border-amber-200', textColor: 'text-amber-700', dotColor: 'bg-amber-500', hexColor: '#F97316' },
  { key: 'finance', label: 'Finance Guardian', color: 'bg-emerald-500', bgColor: 'bg-emerald-50', borderColor: 'border-emerald-200', textColor: 'text-emerald-700', dotColor: 'bg-emerald-500', hexColor: '#059669' },
  { key: 'brand', label: 'Brand Protector', color: 'bg-pink-500', bgColor: 'bg-pink-50', borderColor: 'border-pink-200', textColor: 'text-pink-700', dotColor: 'bg-pink-500', hexColor: '#EC4899' },
]

// Build SUBAGENT_DEFS for each main agent (5 subagents per agent)
const _parentLabels: Record<string, string> = {
  risk: 'Risk', supply: 'Supply', logistics: 'Logistics',
  market: 'Market', finance: 'Finance', brand: 'Brand',
}

export const SUBAGENT_DEFS: Record<string, SubagentDef[]> = Object.fromEntries(
  COUNCIL_AGENTS.map(agent => [
    agent.key,
    SUBAGENT_CHANNELS.map(channel => ({
      key: `${agent.key}_${channel}`,
      label: `${SUBAGENT_CHANNEL_META[channel].shortLabel} ${_parentLabels[agent.key]} Analyst`,
      data_channel: channel,
      domain_hint: '',
    })),
  ])
)

/** @deprecated Use COUNCIL_AGENTS instead */
export const SEVEN_AGENTS = COUNCIL_AGENTS

// ── MiroFish Simulation Types ──────────────────────────────────────────────────

export interface SimulationConfig {
  name: string
  seed_query: string
  horizon_days: number
  num_personas: number
  rounds: number
  focus_areas: string[]
}

export interface SimulationResult {
  prediction: string
  confidence: number
  key_factors: string[]
  scenarios: Record<string, unknown>[]
  risks: string[]
  opportunities: string[]
  recommendations: string[]
}

export interface SimulationRound {
  round_number: number
  events: string[]
  sentiment_shift: Record<string, number>
}

export interface SimulationState {
  id: string
  config: SimulationConfig
  status: 'pending' | 'running' | 'completed' | 'failed'
  entities: { id: string; name: string; type: string; importance: number }[]
  relationships: { source_id: string; target_id: string; type: string; weight: number }[]
  personas: { id: string; name: string; role: string; traits: string[] }[]
  rounds: SimulationRound[]
  result: SimulationResult | null
  agent_type: string
}

export interface ReviewCritique {
  reviewer: string
  role: string
  severity: string
  category: string
  finding: string
  suggestion: string
}

export interface ReviewResult {
  overall_score: number
  critiques: ReviewCritique[]
  validated_facts: string[]
  unverified_claims: string[]
  improvements: string[]
  passed: boolean
}
