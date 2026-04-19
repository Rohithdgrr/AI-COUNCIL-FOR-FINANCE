import { describe, it, expect, beforeEach } from 'vitest'
import { useSettingsStore } from '../settingsStore'

describe('settingsStore - new features', () => {
  beforeEach(() => {
    useSettingsStore.getState().reset()
  })

  describe('theme toggle', () => {
    it('defaults to light theme', () => {
      expect(useSettingsStore.getState().settings.theme).toBe('light')
    })

    it('toggles to dark theme', () => {
      useSettingsStore.getState().updateSettings({ theme: 'dark' })
      expect(useSettingsStore.getState().settings.theme).toBe('dark')
    })

    it('toggles back to light theme', () => {
      useSettingsStore.getState().updateSettings({ theme: 'dark' })
      useSettingsStore.getState().updateSettings({ theme: 'light' })
      expect(useSettingsStore.getState().settings.theme).toBe('light')
    })
  })

  describe('font size', () => {
    it('defaults to medium', () => {
      expect(useSettingsStore.getState().settings.font_size).toBe('medium')
    })

    it('supports small font size', () => {
      useSettingsStore.getState().updateSettings({ font_size: 'small' })
      expect(useSettingsStore.getState().settings.font_size).toBe('small')
    })

    it('supports large font size', () => {
      useSettingsStore.getState().updateSettings({ font_size: 'large' })
      expect(useSettingsStore.getState().settings.font_size).toBe('large')
    })
  })

  describe('font family', () => {
    it('defaults to system', () => {
      expect(useSettingsStore.getState().settings.font_family).toBe('system')
    })

    it('supports serif font family', () => {
      useSettingsStore.getState().updateSettings({ font_family: 'serif' })
      expect(useSettingsStore.getState().settings.font_family).toBe('serif')
    })

    it('supports mono font family', () => {
      useSettingsStore.getState().updateSettings({ font_family: 'mono' })
      expect(useSettingsStore.getState().settings.font_family).toBe('mono')
    })
  })

  describe('highlight_key_insights', () => {
    it('defaults to true', () => {
      expect(useSettingsStore.getState().settings.highlight_key_insights).toBe(true)
    })

    it('can be toggled off', () => {
      useSettingsStore.getState().updateSettings({ highlight_key_insights: false })
      expect(useSettingsStore.getState().settings.highlight_key_insights).toBe(false)
    })

    it('can be toggled back on', () => {
      useSettingsStore.getState().updateSettings({ highlight_key_insights: false })
      useSettingsStore.getState().updateSettings({ highlight_key_insights: true })
      expect(useSettingsStore.getState().settings.highlight_key_insights).toBe(true)
    })
  })

  describe('mirofish_enabled', () => {
    it('defaults to false', () => {
      expect(useSettingsStore.getState().settings.mirofish_enabled).toBe(false)
    })

    it('can be enabled', () => {
      useSettingsStore.getState().updateSettings({ mirofish_enabled: true })
      expect(useSettingsStore.getState().settings.mirofish_enabled).toBe(true)
    })

    it('can be disabled after enabling', () => {
      useSettingsStore.getState().updateSettings({ mirofish_enabled: true })
      useSettingsStore.getState().updateSettings({ mirofish_enabled: false })
      expect(useSettingsStore.getState().settings.mirofish_enabled).toBe(false)
    })
  })

  describe('support_agent_policy', () => {
    it('defaults to all enabled', () => {
      const policy = useSettingsStore.getState().settings.support_agent_policy
      expect(policy.rag).toBe(true)
      expect(policy.api).toBe(true)
      expect(policy.mcp).toBe(true)
      expect(policy.web).toBe(true)
      expect(policy.graph).toBe(true)
    })

    it('can toggle individual policy channels', () => {
      useSettingsStore.getState().updateSettings({
        support_agent_policy: { rag: false, api: true, mcp: false, web: true, graph: true },
      })
      const policy = useSettingsStore.getState().settings.support_agent_policy
      expect(policy.rag).toBe(false)
      expect(policy.mcp).toBe(false)
      expect(policy.api).toBe(true)
    })

    it('preserves other policy channels when updating one', () => {
      const original = { ...useSettingsStore.getState().settings.support_agent_policy }
      useSettingsStore.getState().updateSettings({
        support_agent_policy: { ...original, web: false },
      })
      const policy = useSettingsStore.getState().settings.support_agent_policy
      expect(policy.web).toBe(false)
      expect(policy.rag).toBe(true)
      expect(policy.api).toBe(true)
    })
  })

  describe('response settings', () => {
    it('response_include_sources defaults to true', () => {
      expect(useSettingsStore.getState().settings.response_include_sources).toBe(true)
    })

    it('response_include_confidence defaults to true', () => {
      expect(useSettingsStore.getState().settings.response_include_confidence).toBe(true)
    })

    it('response_auto_expand_references defaults to false', () => {
      expect(useSettingsStore.getState().settings.response_auto_expand_references).toBe(false)
    })

    it('can toggle response_auto_expand_references', () => {
      useSettingsStore.getState().updateSettings({ response_auto_expand_references: true })
      expect(useSettingsStore.getState().settings.response_auto_expand_references).toBe(true)
    })
  })

  describe('data source toggles', () => {
    it('enable_web_scraping defaults to true', () => {
      expect(useSettingsStore.getState().settings.enable_web_scraping).toBe(true)
    })

    it('enable_news_api defaults to true', () => {
      expect(useSettingsStore.getState().settings.enable_news_api).toBe(true)
    })

    it('enable_financial_api defaults to true', () => {
      expect(useSettingsStore.getState().settings.enable_financial_api).toBe(true)
    })

    it('can disable web scraping', () => {
      useSettingsStore.getState().updateSettings({ enable_web_scraping: false })
      expect(useSettingsStore.getState().settings.enable_web_scraping).toBe(false)
    })
  })

  describe('advanced settings', () => {
    it('show_pipeline_stages defaults to true', () => {
      expect(useSettingsStore.getState().settings.show_pipeline_stages).toBe(true)
    })

    it('show_agent_confidence defaults to true', () => {
      expect(useSettingsStore.getState().settings.show_agent_confidence).toBe(true)
    })

    it('auto_start_debate defaults to false', () => {
      expect(useSettingsStore.getState().settings.auto_start_debate).toBe(false)
    })

    it('mcp_rate_limit defaults to 30', () => {
      expect(useSettingsStore.getState().settings.mcp_rate_limit).toBe(30)
    })

    it('can update mcp_rate_limit', () => {
      useSettingsStore.getState().updateSettings({ mcp_rate_limit: 15 })
      expect(useSettingsStore.getState().settings.mcp_rate_limit).toBe(15)
    })

    it('max_debate_rounds can be changed', () => {
      useSettingsStore.getState().updateSettings({ max_debate_rounds: 5 })
      expect(useSettingsStore.getState().settings.max_debate_rounds).toBe(5)
    })
  })

  describe('notification settings', () => {
    it('notifications_debate_complete defaults to true', () => {
      expect(useSettingsStore.getState().settings.notifications_debate_complete).toBe(true)
    })

    it('notifications_error_alerts defaults to true', () => {
      expect(useSettingsStore.getState().settings.notifications_error_alerts).toBe(true)
    })

    it('notifications_sound defaults to false', () => {
      expect(useSettingsStore.getState().settings.notifications_sound).toBe(false)
    })

    it('can toggle notification sound', () => {
      useSettingsStore.getState().updateSettings({ notifications_sound: true })
      expect(useSettingsStore.getState().settings.notifications_sound).toBe(true)
    })
  })
})
