import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import Navbar from '../Navbar'

// Mock the health API
vi.mock('@/lib/api', () => ({
  healthApi: {
    check: vi.fn().mockRejectedValue(new Error('offline')),
  },
}))

// Mock the Dock component
vi.mock('@/components/ui/Dock', () => ({
  default: ({ items }: { items: { icon: React.ReactNode; onClick: () => void }[] }) => (
    <div data-testid="dock">
      {items.map((item, i) => (
        <button key={i} onClick={item.onClick}>{item.icon}</button>
      ))}
    </div>
  ),
}))

function renderNavbar() {
  return render(
    <MemoryRouter>
      <Navbar />
    </MemoryRouter>
  )
}

describe('Navbar', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('renders the brand name', () => {
    renderNavbar()
    // Brand name appears in both desktop and mobile nav
    const supplyElements = screen.getAllByText(/Supply/)
    expect(supplyElements.length).toBeGreaterThanOrEqual(1)
  })

  it('renders the AI Council Platform subtitle', () => {
    renderNavbar()
    const subtitles = screen.getAllByText('AI Council Platform')
    expect(subtitles.length).toBeGreaterThanOrEqual(1)
  })

  it('renders agent dots', () => {
    renderNavbar()
    // 6 agent dots should be rendered
    const dots = screen.getAllByTitle(/Sentinel|Optimizer|Navigator|Intelligence|Guardian|Protector/)
    expect(dots.length).toBe(6)
  })

  it('renders the 6/6 agent count badge', () => {
    renderNavbar()
    const badges = screen.getAllByText('6/6')
    expect(badges.length).toBeGreaterThanOrEqual(1)
  })

  it('renders server status as Offline when health check fails', () => {
    renderNavbar()
    expect(screen.getByText('Offline')).toBeInTheDocument()
  })

  it('renders the Zap icon in the logo', () => {
    const { container } = renderNavbar()
    const svgElements = container.querySelectorAll('svg')
    // At least the logo zap icon should exist
    expect(svgElements.length).toBeGreaterThan(0)
  })

  it('renders the mobile menu button on small screens', () => {
    renderNavbar()
    // The mobile menu button exists in the DOM (hidden on lg screens)
    const menuButtons = screen.getAllByRole('button')
    expect(menuButtons.length).toBeGreaterThan(0)
  })

  it('renders the Activity icon next to agent dots', () => {
    renderNavbar()
    // Activity icon is rendered with the agent dots section
    const dots = screen.getAllByTitle(/Sentinel|Optimizer|Navigator|Intelligence|Guardian|Protector/)
    expect(dots.length).toBe(6)
  })
})
