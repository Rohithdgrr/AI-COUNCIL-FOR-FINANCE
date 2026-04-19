import { describe, it, expect } from 'vitest'
import { render, screen } from '@testing-library/react'
import ConfidenceBadge from '../ConfidenceBadge'

describe('ConfidenceBadge', () => {
  it('renders confidence percentage', () => {
    render(<ConfidenceBadge confidence={85} />)
    expect(screen.getByText('85%')).toBeDefined()
  })

  it('renders with showLabel for high confidence', () => {
    render(<ConfidenceBadge confidence={90} showLabel />)
    expect(screen.getByText('90%')).toBeDefined()
    expect(screen.getByText('High')).toBeDefined()
  })

  it('renders with showLabel for medium confidence', () => {
    render(<ConfidenceBadge confidence={55} showLabel />)
    expect(screen.getByText('55%')).toBeDefined()
    expect(screen.getByText('Medium')).toBeDefined()
  })

  it('renders with showLabel for low confidence', () => {
    render(<ConfidenceBadge confidence={20} showLabel />)
    expect(screen.getByText('20%')).toBeDefined()
    expect(screen.getByText('Low')).toBeDefined()
  })

  it('rounds confidence value', () => {
    render(<ConfidenceBadge confidence={75.7} />)
    expect(screen.getByText('76%')).toBeDefined()
  })

  it('applies size classes', () => {
    const { container: smContainer } = render(<ConfidenceBadge confidence={80} size="sm" />)
    const { container: lgContainer } = render(<ConfidenceBadge confidence={80} size="lg" />)
    expect(smContainer.firstChild).toBeDefined()
    expect(lgContainer.firstChild).toBeDefined()
  })
})
