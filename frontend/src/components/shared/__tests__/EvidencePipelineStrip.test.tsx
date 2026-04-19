import { describe, it, expect } from 'vitest'
import { render, screen } from '@testing-library/react'
import EvidencePipelineStrip from '../EvidencePipelineStrip'
import type { SupportAgentPolicy } from '@/types/council'

const defaultPolicy: SupportAgentPolicy = {
  rag: true,
  api: true,
  mcp: true,
  web: true,
  graph: true,
}

describe('EvidencePipelineStrip', () => {
  it('renders all stages with full policy', () => {
    render(
      <EvidencePipelineStrip
        policy={defaultPolicy}
        stages={{ rag_fetching: 'idle', api_called: 'idle', mcp_fetched: 'idle', sources_ready: 'idle' }}
        counts={{ rag_fetching: 0, api_called: 0, mcp_fetched: 0, sources_ready: 0 }}
      />
    )
    expect(screen.getByText('RAG')).toBeDefined()
    expect(screen.getByText('APIs')).toBeDefined()
    expect(screen.getByText('Web/MCP')).toBeDefined()
  })

  it('hides stages when policy disables them', () => {
    const partialPolicy: SupportAgentPolicy = { ...defaultPolicy, web: false, graph: false }
    render(
      <EvidencePipelineStrip
        policy={partialPolicy}
        stages={{ rag_fetching: 'idle', api_called: 'idle', mcp_fetched: 'idle', sources_ready: 'idle' }}
        counts={{ rag_fetching: 0, api_called: 0, mcp_fetched: 0, sources_ready: 0 }}
      />
    )
    expect(screen.getByText('RAG')).toBeDefined()
    expect(screen.queryByText('Scraping')).toBeNull()
    expect(screen.queryByText('Graph/DB')).toBeNull()
  })

  it('shows count when stage is done', () => {
    render(
      <EvidencePipelineStrip
        policy={defaultPolicy}
        stages={{ rag_fetching: 'done', api_called: 'idle', mcp_fetched: 'idle', sources_ready: 'idle' }}
        counts={{ rag_fetching: 5, api_called: 0, mcp_fetched: 0, sources_ready: 0 }}
      />
    )
    expect(screen.getByText('5')).toBeDefined()
  })

  it('returns null when all policies disabled', () => {
    const noPolicy: SupportAgentPolicy = { rag: false, api: false, mcp: false, web: false, graph: false }
    const { container } = render(
      <EvidencePipelineStrip
        policy={noPolicy}
        stages={{ rag_fetching: 'idle', api_called: 'idle', mcp_fetched: 'idle', sources_ready: 'idle' }}
        counts={{ rag_fetching: 0, api_called: 0, mcp_fetched: 0, sources_ready: 0 }}
      />
    )
    expect(container.firstChild).toBeNull()
  })
})
