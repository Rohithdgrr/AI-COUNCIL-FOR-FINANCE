import { create } from 'zustand'
import type { AgentRoundState, ModeratorResult, SupervisorResult, CouncilV2StreamEvent, SupportEvidence, EvidenceBundle, SupportAgentPolicy, SubagentEvidence, SimulationResult } from '@/types/council'

const AGENT_KEYS = ['risk', 'supply', 'logistics', 'market', 'finance', 'brand'] as const
type AgentKey = typeof AGENT_KEYS[number]

interface AgentState {
  round1: AgentRoundState
  round2: AgentRoundState
}

export type PipelineStageKey = 'rag_fetching' | 'api_called' | 'mcp_fetched' | 'sources_ready'
export interface PipelineStageState {
  status: 'idle' | 'active' | 'done'
  detail: string
  count: number
}

interface CouncilV2State {
  sessionId: string | null
  query: string
  currentRound: number
  currentPhase: 'idle' | 'analysis' | 'debate' | 'supervisor' | 'synthesis'
  isStreaming: boolean
  liteMode: boolean
  liteSupportAgents: string[]
  agents: Record<string, AgentState>
  moderatorR1: ModeratorResult | null
  moderatorR2: ModeratorResult | null
  supervisorResult: SupervisorResult | null
  selectedAgent: string | null
  viewMode: 'agent' | 'moderator' | 'supervisor'
  streamError: string | null
  citationMaps: Record<string, Record<string, string>>
  pipelineStages: Record<PipelineStageKey, PipelineStageState>
  discoveredSources: Record<string, {num: number, title: string, url: string}[]>
  supportEvidence: Record<string, SupportEvidence>
  evidenceBundle: EvidenceBundle | null
  supportAgentPolicy: SupportAgentPolicy
  subagentEvidence: Record<string, SubagentEvidence>
  activeSubagents: string[]
  streamingSubagents: string[] // Track which subagents are currently receiving streaming updates
  // MiroFish swarm state
  mirofishPhase: 'idle' | 'graph_building' | 'persona_generation' | 'simulation_running' | 'report_generation' | 'completed' | 'failed'
  mirofishBrandResult: (SimulationResult & { simulation_id?: string; status?: string; entities?: string[]; personas?: string[]; report_summary?: string }) | null
  mirofishMarketResult: (SimulationResult & { simulation_id?: string; status?: string; entities?: string[]; personas?: string[]; report_summary?: string }) | null
  mirofishBrandEntities: string[]
  mirofishMarketEntities: string[]
  mirofishBrandPersonas: string[]
  mirofishMarketPersonas: string[]
  mirofishBrandPhase: string
  mirofishMarketPhase: string
  handleV2Event: (event: CouncilV2StreamEvent) => void
  setSelectedAgent: (agent: string | null) => void
  setViewMode: (mode: 'agent' | 'moderator' | 'supervisor') => void
  reset: () => void
  setStreaming: (streaming: boolean) => void
  setStreamError: (error: string | null) => void
}

function makeInitialAgents(): Record<string, AgentState> {
  const agents: Record<string, AgentState> = {}
  for (const key of AGENT_KEYS) {
    agents[key] = {
      round1: { status: 'idle', output: '', confidence: 0 },
      round2: { status: 'idle', output: '', confidence: 0 },
    }
  }
  return agents
}

const STAGE_KEYS: PipelineStageKey[] = ['rag_fetching', 'api_called', 'mcp_fetched', 'sources_ready']
function makeInitialStages(): Record<PipelineStageKey, PipelineStageState> {
  return Object.fromEntries(
    STAGE_KEYS.map((k) => [k, { status: 'idle', detail: '', count: 0 }])
  ) as Record<PipelineStageKey, PipelineStageState>
}

function isValidAgent(key: string): key is AgentKey {
  return (AGENT_KEYS as readonly string[]).includes(key)
}

function updateAgentRound(
  agents: Record<string, AgentState>,
  agentKey: string,
  roundKey: 'round1' | 'round2',
  update: Partial<AgentRoundState>
): Record<string, AgentState> {
  const current = agents[agentKey]
  if (!current) return agents
  const currentRound = current[roundKey]
  return {
    ...agents,
    [agentKey]: {
      ...current,
      [roundKey]: { ...currentRound, ...update },
    },
  }
}

export const useCouncilV2Store = create<CouncilV2State>((set) => ({
  sessionId: null,
  query: '',
  currentRound: 0,
  currentPhase: 'idle',
  isStreaming: false,
  liteMode: false,
  liteSupportAgents: [],
  agents: makeInitialAgents(),
  moderatorR1: null,
  moderatorR2: null,
  supervisorResult: null,
  selectedAgent: null,
  viewMode: 'agent',
  streamError: null,
  citationMaps: {},
  pipelineStages: makeInitialStages(),
  discoveredSources: {},
  supportEvidence: {},
  evidenceBundle: null,
  supportAgentPolicy: { rag: true, api: true, mcp: true, web: true, graph: true },
  subagentEvidence: {},
  activeSubagents: [],
  streamingSubagents: [],
  // MiroFish swarm state
  mirofishPhase: 'idle',
  mirofishBrandResult: null,
  mirofishMarketResult: null,
  mirofishBrandEntities: [],
  mirofishMarketEntities: [],
  mirofishBrandPersonas: [],
  mirofishMarketPersonas: [],
  mirofishBrandPhase: '',
  mirofishMarketPhase: '',

  handleV2Event: (event) => {
    switch (event.type) {
      case 'start':
        set({
          isStreaming: true,
          streamError: null,
          sessionId: event.session_id || null,
          query: event.query || '',
          currentRound: 0,
          currentPhase: 'idle',
          liteMode: Boolean((event as any).lite_mode),
          liteSupportAgents: (event as any).support_agents || [],
          subagentEvidence: {},
          activeSubagents: [],
          streamingSubagents: [],
          supportAgentPolicy: (event as any).support_agent_policy || { rag: true, api: true, mcp: true, web: true, graph: true },
          agents: makeInitialAgents(),
          moderatorR1: null,
          moderatorR2: null,
          supervisorResult: null,
          selectedAgent: (event as any).primary_agent || 'risk',
          viewMode: 'agent',
          citationMaps: {},
          pipelineStages: makeInitialStages(),
          supportEvidence: {},
          evidenceBundle: null,
        })
        break

      case 'pipeline_stage': {
        const stageKey = (event as any).stage as PipelineStageKey | undefined
        if (stageKey && STAGE_KEYS.includes(stageKey)) {
          set((state) => {
            // Mark previous stages as done, current as active
            const newStages = { ...state.pipelineStages }
            const idx = STAGE_KEYS.indexOf(stageKey)
            STAGE_KEYS.forEach((k, i) => {
              if (i < idx) newStages[k] = { ...newStages[k], status: 'done' }
              else if (i === idx) newStages[k] = {
                status: 'active',
                detail: (event as any).detail || '',
                count: (event as any).count || 0,
              }
            })
            return { pipelineStages: newStages }
          })
        }
        break
      }

      case 'citations_ready':
        // Mark all stages done
        set(() => ({
          pipelineStages: Object.fromEntries(
            STAGE_KEYS.map((k) => [k, { status: 'done', detail: '', count: 0 }])
          ) as Record<PipelineStageKey, PipelineStageState>,
        }))
        break

      case 'round_start':
        set((state) => ({
          currentRound: event.round || 1,
          currentPhase: (event.phase as 'analysis' | 'debate' | 'supervisor' | 'synthesis') || (state.liteMode ? 'synthesis' : 'analysis'),
        }))
        break

      case 'agent_start': {
        const agentKey = event.agent || ''
        const roundKey: 'round1' | 'round2' = (event.round || 1) === 1 ? 'round1' : 'round2'
        if (isValidAgent(agentKey)) {
          set((state) => {
            const updates: Partial<CouncilV2State> = {
              agents: updateAgentRound(state.agents, agentKey, roundKey, { status: 'thinking', output: '', confidence: 0 }),
            }
            // Only auto-select if no agent is selected yet (first agent to start)
            if (!state.selectedAgent) {
              updates.selectedAgent = agentKey
              updates.viewMode = 'agent'
            }
            return updates
          })
        } else if (agentKey === 'supervisor') {
          set({ viewMode: 'supervisor', selectedAgent: 'supervisor' })
        }
        break
      }

      case 'token': {
        const agentKey = event.agent || ''
        const roundKey: 'round1' | 'round2' = (event.round || 1) === 1 ? 'round1' : 'round2'
        const content = event.content || ''

        if (agentKey === 'supervisor') {
          set((state) => ({
            supervisorResult: state.supervisorResult
              ? { ...state.supervisorResult, output: state.supervisorResult.output + content }
              : { output: content, confidence: 0 },
          }))
        } else if (isValidAgent(agentKey)) {
          set((state) => ({
            agents: updateAgentRound(state.agents, agentKey, roundKey, {
              output: (state.agents[agentKey]?.[roundKey]?.output || '') + content,
            }),
          }))
        }
        break
      }

      case 'agent_done': {
        const agentKey = event.agent || ''
        const roundKey: 'round1' | 'round2' = (event.round || 1) === 1 ? 'round1' : 'round2'
        const confidence = event.confidence || 0

        if (isValidAgent(agentKey)) {
          set((state) => ({
            agents: updateAgentRound(state.agents, agentKey, roundKey, { status: 'done', confidence }),
          }))
        }
        break
      }

      case 'agent_error': {
        const agentKey = event.agent || ''
        const roundKey: 'round1' | 'round2' = (event.round || 1) === 1 ? 'round1' : 'round2'
        const error = event.error || 'Unknown error'

        if (isValidAgent(agentKey)) {
          set((state) => ({
            agents: updateAgentRound(state.agents, agentKey, roundKey, {
              status: 'error',
              output: `Error: ${error}`,
              confidence: 0,
            }),
          }))
        }
        break
      }

      case 'moderator_start':
        set({ viewMode: 'moderator' })
        break

      case 'moderator_done': {
        const round = event.round || 1
        const modResult: ModeratorResult = {
          scores: event.scores || {},
          consensus: event.consensus || 0,
          summary: event.summary || '',
        }
        if (round === 1) {
          set({ moderatorR1: modResult })
        } else {
          set({ moderatorR2: modResult })
        }
        break
      }

      case 'supervisor_done': {
        set((state) => ({
          supervisorResult: {
            output: state.supervisorResult?.output || '',
            confidence: event.confidence || 0,
          },
          viewMode: 'supervisor',
        }))
        break
      }

      case 'citations_map': {
        const agentKey = (event as any).agent || ''
        const urls = (event as any).urls || {}
        if (agentKey) {
          set((state) => ({
            citationMaps: {
              ...state.citationMaps,
              [agentKey]: urls,
            },
          }))
        }
        break
      }

      case 'source_discovered': {
        const agentKey = (event as any).agent || ''
        const sources = (event as any).sources || []
        const count = (event as any).count || 0
        // Store discovered sources immediately and show in pipeline
        set((state) => ({
          discoveredSources: {
            ...state.discoveredSources,
            [agentKey]: sources
          },
          pipelineStages: {
            ...state.pipelineStages,
            mcp_fetched: { 
              status: 'active', 
              detail: `${agentKey}: ${count} sources found`, 
              count 
            }
          }
        }))
        break
      }

      case 'support_evidence': {
        const agentKey = (event as any).agent || ''
        const evidence = (event as any).evidence as SupportEvidence | undefined
        if (agentKey && evidence) {
          set((state) => ({
            supportEvidence: {
              ...state.supportEvidence,
              [agentKey]: evidence,
            },
          }))
        }
        break
      }

      case 'evidence_bundle': {
        const bundle = (event as any).bundle as EvidenceBundle | undefined
        if (bundle) {
          set({ evidenceBundle: bundle })
        }
        // Also store subagent_evidence if present
        const subagentEv = (event as any).subagent_evidence as SubagentEvidence[] | undefined
        if (subagentEv) {
          set((state) => {
            const map: Record<string, SubagentEvidence> = { ...state.subagentEvidence }
            for (const se of subagentEv) {
              map[se.subagent_key] = se
            }
            return { subagentEvidence: map }
          })
        }
        break
      }

      case 'subagent_start': {
        const subagentKey = (event as any).subagent_key as string | undefined
        if (subagentKey) {
          set((state) => ({
            activeSubagents: [...state.activeSubagents, subagentKey],
          }))
        }
        break
      }

      case 'subagent_evidence': {
        const seData = (event as any).evidence as SubagentEvidence | undefined
        const sKey = (event as any).subagent_key as string | undefined
        if (seData && sKey) {
          set((state) => ({
            subagentEvidence: {
              ...state.subagentEvidence,
              [sKey]: seData,
            },
            // Mark as no longer streaming when evidence arrives
            streamingSubagents: state.streamingSubagents.filter((k) => k !== sKey),
          }))
        }
        break
      }

      case 'mirofish_start':
        set({
          mirofishPhase: 'graph_building',
          mirofishBrandResult: null,
          mirofishMarketResult: null,
          mirofishBrandEntities: [],
          mirofishMarketEntities: [],
          mirofishBrandPersonas: [],
          mirofishMarketPersonas: [],
          mirofishBrandPhase: 'graph_building',
          mirofishMarketPhase: 'graph_building',
        })
        break

      case 'mirofish_agent_progress': {
        const mfAgent = (event as any).agent as string
        const mfPhase = (event as any).phase as string
        const mfEntities = (event as any).entities as string[] | undefined
        const mfPersonas = (event as any).personas as string[] | undefined

        const updates: Partial<CouncilV2State> = {}
        if (mfAgent === 'brand') {
          updates.mirofishBrandPhase = mfPhase
          if (mfEntities) updates.mirofishBrandEntities = mfEntities
          if (mfPersonas) updates.mirofishBrandPersonas = mfPersonas
        } else if (mfAgent === 'market') {
          updates.mirofishMarketPhase = mfPhase
          if (mfEntities) updates.mirofishMarketEntities = mfEntities
          if (mfPersonas) updates.mirofishMarketPersonas = mfPersonas
        }

        // Update overall phase based on the most advanced agent
        const phaseMap: Record<string, CouncilV2State['mirofishPhase']> = {
          graph_building: 'graph_building',
          graph_ready: 'persona_generation',
          persona_generation: 'persona_generation',
          personas_ready: 'simulation_running',
          simulation_running: 'simulation_running',
          report_generation: 'report_generation',
        }
        if (phaseMap[mfPhase]) {
          updates.mirofishPhase = phaseMap[mfPhase]
        }

        set(updates)
        break
      }

      case 'mirofish_agent_complete': {
        const mfAgent = (event as any).agent as string
        const mfResult = (event as any).result as (SimulationResult & { simulation_id?: string; status?: string; entities?: string[]; personas?: string[]; report_summary?: string }) | undefined
        if (mfAgent === 'brand' && mfResult) {
          set({ mirofishBrandResult: mfResult, mirofishBrandPhase: 'completed' })
        } else if (mfAgent === 'market' && mfResult) {
          set({ mirofishMarketResult: mfResult, mirofishMarketPhase: 'completed' })
        }
        break
      }

      case 'mirofish_agent_error': {
        const mfAgent = (event as any).agent as string
        if (mfAgent === 'brand') {
          set({ mirofishBrandPhase: 'failed' })
        } else if (mfAgent === 'market') {
          set({ mirofishMarketPhase: 'failed' })
        }
        break
      }

      case 'mirofish_complete':
        set({ mirofishPhase: 'completed' })
        break

      case 'complete':
        set((state) => ({
          isStreaming: false,
          currentRound: state.liteMode ? 2 : 3,
          currentPhase: 'synthesis',
          viewMode: state.liteMode ? 'agent' : 'supervisor',
          streamingSubagents: [],
        }))
        break
    }
  },

  setSelectedAgent: (agent) => set({ selectedAgent: agent, viewMode: 'agent' }),
  setViewMode: (mode) => set({ viewMode: mode }),
  reset: () =>
    set({
      sessionId: null,
      isStreaming: false,
      currentRound: 0,
      currentPhase: 'idle',
      liteMode: false,
      liteSupportAgents: [],
      agents: makeInitialAgents(),
      moderatorR1: null,
      moderatorR2: null,
      supervisorResult: null,
      selectedAgent: null,
      viewMode: 'agent',
      streamError: null,
      citationMaps: {},
      pipelineStages: makeInitialStages(),
      discoveredSources: {},
      supportEvidence: {},
      evidenceBundle: null,
      supportAgentPolicy: { rag: true, api: true, mcp: true, web: true, graph: true },
      subagentEvidence: {},
      activeSubagents: [],
      streamingSubagents: [],
      // MiroFish swarm state
      mirofishPhase: 'idle',
      mirofishBrandResult: null,
      mirofishMarketResult: null,
      mirofishBrandEntities: [],
      mirofishMarketEntities: [],
      mirofishBrandPersonas: [],
      mirofishMarketPersonas: [],
      mirofishBrandPhase: '',
      mirofishMarketPhase: '',
    }),
  setStreaming: (streaming) => set({ isStreaming: streaming }),
  setStreamError: (error) => set({ streamError: error }),
}))
