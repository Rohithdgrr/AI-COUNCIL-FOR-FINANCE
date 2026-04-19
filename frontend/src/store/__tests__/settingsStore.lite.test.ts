import { describe, it, expect, beforeEach } from 'vitest'
import { useSettingsStore } from '../settingsStore'

describe('settingsStore — Lite Mode', () => {
  beforeEach(() => {
    useSettingsStore.getState().reset()
  })

  it('initializes with lite_mode false', () => {
    const state = useSettingsStore.getState()
    expect(state.settings.lite_mode).toBe(false)
    expect(state.settings.lite_primary_agent).toBe('risk')
  })

  it('initializes with default support_agent_policy', () => {
    const state = useSettingsStore.getState()
    expect(state.settings.support_agent_policy).toEqual({
      rag: true,
      api: true,
      mcp: true,
      web: true,
      graph: true,
    })
  })

  it('toggles lite_mode', () => {
    useSettingsStore.getState().updateSettings({ lite_mode: true })
    expect(useSettingsStore.getState().settings.lite_mode).toBe(true)

    useSettingsStore.getState().updateSettings({ lite_mode: false })
    expect(useSettingsStore.getState().settings.lite_mode).toBe(false)
  })

  it('changes primary agent', () => {
    useSettingsStore.getState().updateSettings({ lite_primary_agent: 'supply' })
    expect(useSettingsStore.getState().settings.lite_primary_agent).toBe('supply')

    useSettingsStore.getState().updateSettings({ lite_primary_agent: 'market' })
    expect(useSettingsStore.getState().settings.lite_primary_agent).toBe('market')
  })

  it('updates support_agent_policy partially', () => {
    useSettingsStore.getState().updateSettings({
      support_agent_policy: {
        rag: true,
        api: true,
        mcp: false,
        web: true,
        graph: true,
      },
    })
    expect(useSettingsStore.getState().settings.support_agent_policy.mcp).toBe(false)
    expect(useSettingsStore.getState().settings.support_agent_policy.rag).toBe(true)
  })

  it('resets to defaults including support_agent_policy', () => {
    useSettingsStore.getState().updateSettings({
      lite_mode: true,
      lite_primary_agent: 'finance',
      support_agent_policy: { rag: false, api: false, mcp: false, web: false, graph: false },
    })

    useSettingsStore.getState().reset()

    const state = useSettingsStore.getState().settings
    expect(state.lite_mode).toBe(false)
    expect(state.lite_primary_agent).toBe('risk')
    expect(state.support_agent_policy).toEqual({
      rag: true,
      api: true,
      mcp: true,
      web: true,
      graph: true,
    })
  })
})
