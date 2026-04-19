import { describe, it, expect, beforeEach, vi } from 'vitest'
import { render, act } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import App from '../App'
import { useSettingsStore } from '../store/settingsStore'

// Mock the API modules
vi.mock('@/lib/api', () => ({
  healthApi: { check: vi.fn().mockRejectedValue(new Error('offline')) },
  settingsApi: { update: vi.fn().mockResolvedValue({}) },
  marketApi: { ticker: vi.fn().mockRejectedValue(new Error('offline')) },
  ragApi: { stats: vi.fn().mockRejectedValue(new Error('offline')) },
}))

// Mock WebSocket
vi.mock('@/hooks/useCouncilV2Stream', () => ({
  useCouncilV2Stream: () => ({
    startStream: vi.fn(),
    stopStream: vi.fn(),
  }),
}))

describe('App - Global Settings Application', () => {
  beforeEach(() => {
    useSettingsStore.getState().reset()
    document.documentElement.classList.remove('dark')
    document.documentElement.style.fontSize = ''
    document.documentElement.style.fontFamily = ''
  })

  it('applies light theme by default', () => {
    render(
      <MemoryRouter>
        <App />
      </MemoryRouter>
    )
    expect(document.documentElement.classList.contains('dark')).toBe(false)
  })

  it('applies dark theme when setting is changed', () => {
    useSettingsStore.getState().updateSettings({ theme: 'dark' })
    render(
      <MemoryRouter>
        <App />
      </MemoryRouter>
    )
    expect(document.documentElement.classList.contains('dark')).toBe(true)
  })

  it('applies medium font size by default', () => {
    render(
      <MemoryRouter>
        <App />
      </MemoryRouter>
    )
    expect(document.documentElement.style.fontSize).toBe('16px')
  })

  it('applies small font size when setting is changed', () => {
    useSettingsStore.getState().updateSettings({ font_size: 'small' })
    render(
      <MemoryRouter>
        <App />
      </MemoryRouter>
    )
    expect(document.documentElement.style.fontSize).toBe('14px')
  })

  it('applies large font size when setting is changed', () => {
    useSettingsStore.getState().updateSettings({ font_size: 'large' })
    render(
      <MemoryRouter>
        <App />
      </MemoryRouter>
    )
    expect(document.documentElement.style.fontSize).toBe('18px')
  })

  it('applies system font family by default', () => {
    render(
      <MemoryRouter>
        <App />
      </MemoryRouter>
    )
    expect(document.documentElement.style.fontFamily).toContain('DM Sans')
  })

  it('applies serif font family when setting is changed', () => {
    useSettingsStore.getState().updateSettings({ font_family: 'serif' })
    render(
      <MemoryRouter>
        <App />
      </MemoryRouter>
    )
    expect(document.documentElement.style.fontFamily).toContain('Georgia')
  })

  it('applies mono font family when setting is changed', () => {
    useSettingsStore.getState().updateSettings({ font_family: 'mono' })
    render(
      <MemoryRouter>
        <App />
      </MemoryRouter>
    )
    expect(document.documentElement.style.fontFamily).toContain('JetBrains Mono')
  })

  it('removes dark class when switching from dark to light', () => {
    useSettingsStore.getState().updateSettings({ theme: 'dark' })
    render(
      <MemoryRouter>
        <App />
      </MemoryRouter>
    )
    expect(document.documentElement.classList.contains('dark')).toBe(true)

    act(() => {
      useSettingsStore.getState().updateSettings({ theme: 'light' })
    })
    expect(document.documentElement.classList.contains('dark')).toBe(false)
  })
})
