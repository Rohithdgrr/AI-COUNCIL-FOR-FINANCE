import { describe, it, expect } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/react'
import SubagentEvidenceCard from '../SubagentEvidenceCard'
import type { SubagentEvidence } from '@/types/council'

const mockEvidence: SubagentEvidence = {
  subagent_key: 'risk_rag',
  parent_agent: 'risk',
  data_channel: 'rag',
  domain_hint: 'geopolitical risk documents and compliance reports',
  summary: 'Found 3 key risk indicators\nSanctions risk elevated\nCompliance gap detected',
  sources: ['[1]', '[2]', '[3]'],
  confidence: 78,
  flags: [],
  links: ['https://example.com/risk1'],
}

describe('SubagentEvidenceCard', () => {
  it('renders subagent key and channel badge', () => {
    render(<SubagentEvidenceCard evidence={mockEvidence} />)
    expect(screen.getByText(/risk.*rag/i)).toBeDefined()
    expect(screen.getByText('RAG')).toBeDefined()
  })

  it('renders confidence badge', () => {
    render(<SubagentEvidenceCard evidence={mockEvidence} />)
    expect(screen.getByText('78%')).toBeDefined()
  })

  it('renders domain hint', () => {
    render(<SubagentEvidenceCard evidence={mockEvidence} />)
    expect(screen.getByText(/geopolitical risk/i)).toBeDefined()
  })

  it('renders Show Sources button with count', () => {
    render(<SubagentEvidenceCard evidence={mockEvidence} />)
    expect(screen.getByText('Show Sources (3)')).toBeDefined()
  })

  it('toggles sources panel when clicked', () => {
    render(<SubagentEvidenceCard evidence={mockEvidence} />)
    const button = screen.getByText('Show Sources (3)')
    fireEvent.click(button)
    expect(screen.getByText('Hide Sources')).toBeDefined()
    expect(screen.getByText('[1]')).toBeDefined()
  })

  it('renders flags when present', () => {
    const withFlags: SubagentEvidence = {
      ...mockEvidence,
      flags: ['needs_verification', 'low_confidence'],
    }
    render(<SubagentEvidenceCard evidence={withFlags} />)
    expect(screen.getByText('needs_verification')).toBeDefined()
    expect(screen.getByText('low_confidence')).toBeDefined()
  })

  it('renders "No evidence collected" for empty summary', () => {
    const emptySummary: SubagentEvidence = {
      ...mockEvidence,
      summary: '',
    }
    render(<SubagentEvidenceCard evidence={emptySummary} />)
    expect(screen.getByText('No evidence collected')).toBeDefined()
  })

  it('renders different channel colors', () => {
    const apiEvidence: SubagentEvidence = {
      ...mockEvidence,
      subagent_key: 'risk_api',
      data_channel: 'api',
    }
    const { container } = render(<SubagentEvidenceCard evidence={apiEvidence} />)
    expect(screen.getByText('API')).toBeDefined()
    expect(container.querySelector('[style*="#3B82F6"]')).toBeDefined()
  })
})
