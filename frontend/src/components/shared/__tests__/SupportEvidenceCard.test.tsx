import { describe, it, expect } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/react'
import SupportEvidenceCard from '../SupportEvidenceCard'
import type { SupportEvidence } from '@/types/council'

const mockEvidence: SupportEvidence = {
  agent: 'risk',
  role: 'support',
  summary: 'Line 1\nLine 2\nLine 3\nLine 4\nLine 5',
  sources: ['[1]', '[2]', '[3]'],
  confidence: 75,
  flags: ['contradiction'],
  links: ['https://example.com/source1', 'https://example.com/source2'],
}

describe('SupportEvidenceCard', () => {
  it('renders agent label from COUNCIL_AGENTS', () => {
    render(<SupportEvidenceCard evidence={mockEvidence} />)
    expect(screen.getByText('Risk Sentinel')).toBeDefined()
  })

  it('renders confidence badge', () => {
    render(<SupportEvidenceCard evidence={mockEvidence} />)
    expect(screen.getByText('75%')).toBeDefined()
  })

  it('shows source count', () => {
    render(<SupportEvidenceCard evidence={mockEvidence} />)
    expect(screen.getByText('3 sources')).toBeDefined()
  })

  it('shows flags', () => {
    render(<SupportEvidenceCard evidence={mockEvidence} />)
    expect(screen.getByText('contradiction')).toBeDefined()
  })

  it('shows first 3 lines by default', () => {
    render(<SupportEvidenceCard evidence={mockEvidence} />)
    expect(screen.getByText('Line 1')).toBeDefined()
    expect(screen.getByText('Line 2')).toBeDefined()
    expect(screen.getByText('Line 3')).toBeDefined()
  })

  it('expands to show more lines', () => {
    render(<SupportEvidenceCard evidence={mockEvidence} />)
    const expandBtn = screen.getByText('Show more')
    fireEvent.click(expandBtn)
    expect(screen.getByText('Line 4')).toBeDefined()
    expect(screen.getByText('Line 5')).toBeDefined()
  })

  it('shows links when expanded', () => {
    render(<SupportEvidenceCard evidence={mockEvidence} defaultExpanded />)
    const links = screen.getAllByText(/example\.com/).length
    expect(links).toBeGreaterThan(0)
  })

  it('renders with no flags', () => {
    const noFlags: SupportEvidence = { ...mockEvidence, flags: [] }
    render(<SupportEvidenceCard evidence={noFlags} />)
    expect(screen.getByText('Risk Sentinel')).toBeDefined()
  })

  it('renders with empty summary', () => {
    const emptySummary: SupportEvidence = { ...mockEvidence, summary: '' }
    render(<SupportEvidenceCard evidence={emptySummary} />)
    expect(screen.getByText('No evidence collected')).toBeDefined()
  })
})
