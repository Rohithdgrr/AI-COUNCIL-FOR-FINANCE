import { describe, it, expect } from 'vitest'
import { render, screen } from '@testing-library/react'
import LiteModePanel from '../LiteModePanel'
import { COUNCIL_AGENTS } from '@/types/council'
import type { EvidenceBundle, SupportAgentPolicy, AgentRoundState, AgentStatus, SubagentEvidence } from '@/types/council'

const primaryInfo = COUNCIL_AGENTS[0]! // risk — always defined

const makeAgents = () => {
  const agents: Record<string, { round1: AgentRoundState; round2: AgentRoundState }> = {}
  for (const a of COUNCIL_AGENTS) {
    agents[a.key] = {
      round1: { status: 'done' as AgentStatus, output: `${a.label} analysis complete.`, confidence: 70 },
      round2: { status: 'idle' as AgentStatus, output: '', confidence: 0 },
    }
  }
  agents['risk']!.round2 = { status: 'done' as AgentStatus, output: 'Final synthesized answer from risk agent.', confidence: 85 }
  return agents
}

const defaultPolicy: SupportAgentPolicy = { rag: true, api: true, mcp: true, web: true, graph: true }

const defaultBundle: EvidenceBundle = {
  support_evidence: [
    { agent: 'rag', role: 'support', summary: 'RAG finding', sources: ['[1]'], confidence: 70, flags: [], links: [] },
    { agent: 'api', role: 'support', summary: 'API finding', sources: ['[2]'], confidence: 65, flags: [], links: [] },
  ],
  citation_map: { '[1]': 'https://example.com/1', '[2]': 'https://example.com/2' },
  data_quality_summary: 'Average support confidence: 68%. Data quality: Moderate.',
  conflicts: [],
  source_counts: { rag: 1, api: 1 },
}

const defaultProps = {
  primaryAgentInfo: primaryInfo,
  agents: makeAgents(),
  isStreaming: false,
  evidenceBundle: null as EvidenceBundle | null,
  citationMaps: {} as Record<string, Record<string, string>>,
  pipelineStages: {
    rag_fetching: { status: 'done', count: 5 },
    api_called: { status: 'done', count: 3 },
    mcp_fetched: { status: 'done', count: 8 },
    sources_ready: { status: 'done', count: 16 },
  },
  supportAgentPolicy: defaultPolicy,
}

describe('LiteModePanel', () => {
  it('renders research pipeline header with primary agent name', () => {
    render(<LiteModePanel {...defaultProps} />)
    expect(screen.getByText(/Risk Sentinel Research Pipeline/)).toBeDefined()
  })

  it('shows subagent count', () => {
    render(<LiteModePanel {...defaultProps} />)
    expect(screen.getByText(/5 hybrid subagents gathering evidence/)).toBeDefined()
  })

  it('renders subagent evidence cards when provided', () => {
    const subagentEv: Record<string, SubagentEvidence> = {
      risk_rag: {
        subagent_key: 'risk_rag',
        parent_agent: 'risk',
        data_channel: 'rag',
        domain_hint: 'risk docs',
        summary: 'RAG finding for risk',
        sources: ['[1]'],
        confidence: 80,
        flags: [],
        links: [],
      },
    }
    const props = { ...defaultProps, subagentEvidence: subagentEv }
    render(<LiteModePanel {...props} />)
    expect(screen.getByText(/risk.*rag/i)).toBeDefined()
  })

  it('renders evidence bundle when provided', () => {
    const props = { ...defaultProps, evidenceBundle: defaultBundle }
    render(<LiteModePanel {...props} />)
    expect(screen.getByText('Evidence Bundle')).toBeDefined()
  })

  it('shows primary agent synthesis output', () => {
    render(<LiteModePanel {...defaultProps} />)
    expect(screen.getByText(/Final synthesized answer/)).toBeDefined()
  })

  it('shows confidence badge when primary is done', () => {
    render(<LiteModePanel {...defaultProps} />)
    const badges = screen.getAllByText('85%')
    expect(badges.length).toBeGreaterThan(0)
  })

  it('shows researching state when streaming', () => {
    const streamingAgents = {
      ...defaultProps.agents,
      risk: {
        round1: { status: 'done' as AgentStatus, output: 'R1 done', confidence: 70 },
        round2: { status: 'thinking' as AgentStatus, output: '', confidence: 0 },
      },
    }
    const streamingProps = {
      ...defaultProps,
      isStreaming: true,
      agents: streamingAgents,
    }
    render(<LiteModePanel {...streamingProps} />)
    expect(screen.getByText('Researching')).toBeDefined()
  })

  it('renders fullscreen button on subagent evidence section', () => {
    render(<LiteModePanel {...defaultProps} isStreaming={true} />)
    // The fullscreen button should be present in the subagent section header
    const buttons = document.querySelectorAll('button[title="Fullscreen"]')
    expect(buttons.length).toBeGreaterThan(0)
  })

  it('renders subagent skeleton cards when streaming without evidence', () => {
    render(<LiteModePanel {...defaultProps} isStreaming={true} />)
    // Should show "Hybrid Subagent Evidence" section header
    expect(screen.getByText('Hybrid Subagent Evidence')).toBeDefined()
  })
})
