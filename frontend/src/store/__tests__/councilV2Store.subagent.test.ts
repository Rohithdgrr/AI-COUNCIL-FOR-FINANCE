import { describe, it, expect, beforeEach } from 'vitest'
import { useCouncilV2Store } from '../councilV2Store'
import type { SubagentEvidence } from '@/types/council'

describe('councilV2Store subagent events', () => {
  beforeEach(() => {
    useCouncilV2Store.getState().reset()
  })

  it('initializes with empty subagentEvidence and activeSubagents', () => {
    const state = useCouncilV2Store.getState()
    expect(state.subagentEvidence).toEqual({})
    expect(state.activeSubagents).toEqual([])
  })

  it('handles subagent_start event', () => {
    useCouncilV2Store.getState().handleV2Event({
      type: 'start',
      session_id: 's1',
      lite_mode: true,
    } as any)
    useCouncilV2Store.getState().handleV2Event({
      type: 'subagent_start',
      subagent_key: 'risk_rag',
      parent_agent: 'risk',
      data_channel: 'rag',
      label: 'RAG Risk Analyst',
    } as any)

    const state = useCouncilV2Store.getState()
    expect(state.activeSubagents).toContain('risk_rag')
  })

  it('handles subagent_evidence event', () => {
    useCouncilV2Store.getState().handleV2Event({
      type: 'start',
      session_id: 's1',
      lite_mode: true,
    } as any)

    const evidence: SubagentEvidence = {
      subagent_key: 'risk_rag',
      parent_agent: 'risk',
      data_channel: 'rag',
      domain_hint: 'risk docs',
      summary: 'Found risk indicators',
      sources: ['[1]'],
      confidence: 80,
      flags: [],
      links: [],
    }

    useCouncilV2Store.getState().handleV2Event({
      type: 'subagent_evidence',
      subagent_key: 'risk_rag',
      evidence,
    } as any)

    const state = useCouncilV2Store.getState()
    expect(state.subagentEvidence['risk_rag']!).toEqual(evidence)
  })

  it('handles multiple subagent_evidence events', () => {
    useCouncilV2Store.getState().handleV2Event({
      type: 'start',
      session_id: 's1',
      lite_mode: true,
    } as any)

    const ev1: SubagentEvidence = {
      subagent_key: 'risk_rag',
      parent_agent: 'risk',
      data_channel: 'rag',
      domain_hint: 'risk docs',
      summary: 'RAG finding',
      sources: ['[1]'],
      confidence: 80,
      flags: [],
      links: [],
    }
    const ev2: SubagentEvidence = {
      subagent_key: 'risk_api',
      parent_agent: 'risk',
      data_channel: 'api',
      domain_hint: 'risk APIs',
      summary: 'API finding',
      sources: ['[2]'],
      confidence: 70,
      flags: ['needs_verification'],
      links: [],
    }

    useCouncilV2Store.getState().handleV2Event({
      type: 'subagent_evidence',
      subagent_key: 'risk_rag',
      evidence: ev1,
    } as any)
    useCouncilV2Store.getState().handleV2Event({
      type: 'subagent_evidence',
      subagent_key: 'risk_api',
      evidence: ev2,
    } as any)

    const state = useCouncilV2Store.getState()
    expect(Object.keys(state.subagentEvidence)).toHaveLength(2)
    expect(state.subagentEvidence['risk_rag']!.confidence).toBe(80)
    expect(state.subagentEvidence['risk_api']!.flags).toContain('needs_verification')
  })

  it('stores subagent_evidence from evidence_bundle event', () => {
    useCouncilV2Store.getState().handleV2Event({
      type: 'start',
      session_id: 's1',
    } as any)

    const subagentEv: SubagentEvidence[] = [
      {
        subagent_key: 'risk_web',
        parent_agent: 'risk',
        data_channel: 'web',
        domain_hint: 'risk web',
        summary: 'Web finding',
        sources: ['[1]'],
        confidence: 65,
        flags: [],
        links: [],
      },
    ]

    useCouncilV2Store.getState().handleV2Event({
      type: 'evidence_bundle',
      bundle: {
        support_evidence: [],
        citation_map: {},
        data_quality_summary: 'Test',
        conflicts: [],
        source_counts: {},
      },
      subagent_evidence: subagentEv,
    } as any)

    const state = useCouncilV2Store.getState()
    expect(state.subagentEvidence['risk_web']).toBeDefined()
    expect(state.subagentEvidence['risk_web']!.confidence).toBe(65)
  })

  it('resets subagentEvidence on reset', () => {
    useCouncilV2Store.getState().handleV2Event({
      type: 'start',
      session_id: 's1',
    } as any)

    useCouncilV2Store.getState().handleV2Event({
      type: 'subagent_evidence',
      subagent_key: 'risk_rag',
      evidence: {
        subagent_key: 'risk_rag',
        parent_agent: 'risk',
        data_channel: 'rag',
        domain_hint: 'risk docs',
        summary: 'Test',
        sources: [],
        confidence: 50,
        flags: [],
        links: [],
      },
    } as any)

    useCouncilV2Store.getState().reset()
    const state = useCouncilV2Store.getState()
    expect(state.subagentEvidence).toEqual({})
    expect(state.activeSubagents).toEqual([])
  })

  it('start event resets subagentEvidence and activeSubagents', () => {
    useCouncilV2Store.getState().handleV2Event({
      type: 'start',
      session_id: 's1',
    } as any)

    useCouncilV2Store.getState().handleV2Event({
      type: 'subagent_start',
      subagent_key: 'risk_rag',
    } as any)

    // New start event should reset
    useCouncilV2Store.getState().handleV2Event({
      type: 'start',
      session_id: 's2',
    } as any)

    const state = useCouncilV2Store.getState()
    expect(state.subagentEvidence).toEqual({})
    expect(state.activeSubagents).toEqual([])
  })
})
