import { describe, it, expect, beforeEach } from 'vitest'
import { useCouncilV2Store } from '../councilV2Store'
import type { SupportEvidence, EvidenceBundle } from '@/types/council'

describe('councilV2Store — Lite Mode', () => {
  beforeEach(() => {
    useCouncilV2Store.getState().reset()
  })

  it('initializes with empty supportEvidence and null evidenceBundle', () => {
    const state = useCouncilV2Store.getState()
    expect(state.supportEvidence).toEqual({})
    expect(state.evidenceBundle).toBeNull()
    expect(state.supportAgentPolicy).toEqual({ rag: true, api: true, mcp: true, web: true, graph: true })
  })

  it('handles start event with lite_mode and support_agent_policy', () => {
    useCouncilV2Store.getState().handleV2Event({
      type: 'start',
      session_id: 'test-session',
      query: 'test query',
      lite_mode: true,
      primary_agent: 'risk',
      support_agents: ['supply', 'logistics', 'market', 'finance', 'brand'],
      support_agent_policy: { rag: true, api: true, mcp: false, web: true, graph: false },
    } as any)

    const state = useCouncilV2Store.getState()
    expect(state.liteMode).toBe(true)
    expect(state.liteSupportAgents).toEqual(['supply', 'logistics', 'market', 'finance', 'brand'])
    expect(state.supportAgentPolicy.mcp).toBe(false)
    expect(state.supportAgentPolicy.graph).toBe(false)
    expect(state.supportEvidence).toEqual({})
    expect(state.evidenceBundle).toBeNull()
  })

  it('handles support_evidence event', () => {
    // Start first
    useCouncilV2Store.getState().handleV2Event({
      type: 'start',
      session_id: 'test',
      lite_mode: true,
      primary_agent: 'risk',
      support_agents: ['supply'],
    } as any)

    const evidence: SupportEvidence = {
      agent: 'supply',
      role: 'support',
      summary: 'Supply chain is stable',
      sources: ['[1]', '[2]'],
      confidence: 75,
      flags: [],
      links: ['https://example.com/1'],
    }

    useCouncilV2Store.getState().handleV2Event({
      type: 'support_evidence',
      agent: 'supply',
      evidence,
    } as any)

    const state = useCouncilV2Store.getState()
    expect(state.supportEvidence['supply']).toEqual(evidence)
  })

  it('handles evidence_bundle event', () => {
    useCouncilV2Store.getState().handleV2Event({
      type: 'start',
      session_id: 'test',
      lite_mode: true,
      primary_agent: 'risk',
      support_agents: ['supply'],
    } as any)

    const bundle: EvidenceBundle = {
      support_evidence: [
        { agent: 'supply', role: 'support', summary: 'Stable', sources: ['[1]'], confidence: 70, flags: [], links: [] },
      ],
      citation_map: { '[1]': 'https://example.com/1' },
      data_quality_summary: 'Average support confidence: 70%. Data quality: Moderate.',
      conflicts: [],
      source_counts: { supply: 1 },
    }

    useCouncilV2Store.getState().handleV2Event({
      type: 'evidence_bundle',
      bundle,
    } as any)

    const state = useCouncilV2Store.getState()
    expect(state.evidenceBundle).toEqual(bundle)
  })

  it('accumulates multiple support_evidence events', () => {
    useCouncilV2Store.getState().handleV2Event({
      type: 'start',
      session_id: 'test',
      lite_mode: true,
      primary_agent: 'risk',
      support_agents: ['supply', 'logistics'],
    } as any)

    const supplyEvidence: SupportEvidence = {
      agent: 'supply', role: 'support', summary: 'Supply stable', sources: ['[1]'], confidence: 70, flags: [], links: [],
    }
    const logisticsEvidence: SupportEvidence = {
      agent: 'logistics', role: 'support', summary: 'Routes clear', sources: ['[2]'], confidence: 65, flags: [], links: [],
    }

    useCouncilV2Store.getState().handleV2Event({ type: 'support_evidence', agent: 'supply', evidence: supplyEvidence } as any)
    useCouncilV2Store.getState().handleV2Event({ type: 'support_evidence', agent: 'logistics', evidence: logisticsEvidence } as any)

    const state = useCouncilV2Store.getState()
    expect(Object.keys(state.supportEvidence)).toEqual(['supply', 'logistics'])
  })

  it('resets lite mode fields on reset', () => {
    useCouncilV2Store.getState().handleV2Event({
      type: 'start',
      session_id: 'test',
      lite_mode: true,
      primary_agent: 'risk',
      support_agents: ['supply'],
    } as any)

    useCouncilV2Store.getState().handleV2Event({
      type: 'support_evidence',
      agent: 'supply',
      evidence: { agent: 'supply', role: 'support', summary: 'Test', sources: [], confidence: 50, flags: [], links: [] },
    } as any)

    useCouncilV2Store.getState().reset()

    const state = useCouncilV2Store.getState()
    expect(state.liteMode).toBe(false)
    expect(state.liteSupportAgents).toEqual([])
    expect(state.supportEvidence).toEqual({})
    expect(state.evidenceBundle).toBeNull()
    expect(state.supportAgentPolicy).toEqual({ rag: true, api: true, mcp: true, web: true, graph: true })
  })

  it('complete event sets viewMode to agent when liteMode', () => {
    useCouncilV2Store.getState().handleV2Event({
      type: 'start',
      session_id: 'test',
      lite_mode: true,
      primary_agent: 'risk',
      support_agents: ['supply'],
    } as any)

    useCouncilV2Store.getState().handleV2Event({
      type: 'complete',
      session_id: 'test',
      confidence: 0.85,
      recommendation: 'Final answer',
      primary_agent: 'risk',
      lite_mode: true,
    } as any)

    const state = useCouncilV2Store.getState()
    expect(state.isStreaming).toBe(false)
    expect(state.currentPhase).toBe('synthesis')
    expect(state.viewMode).toBe('agent')
  })
})
