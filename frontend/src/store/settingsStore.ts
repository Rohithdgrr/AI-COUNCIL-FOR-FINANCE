import { create } from 'zustand'
import { persist } from 'zustand/middleware'

interface AppSettings {
  api_key: string
  mcp_api_key: string
  theme: 'dark' | 'light'
  sidebar_collapsed: boolean
  lite_mode: boolean
  lite_primary_agent: string
  rag_chunk_size: number
  rag_chunk_overlap: number
  rag_top_k: number
  mcp_rate_limit: number
  // Response style
  response_verbosity: 'concise' | 'standard' | 'detailed'
  response_include_sources: boolean
  response_include_confidence: boolean
  response_auto_expand_references: boolean
  // Typography
  font_size: 'small' | 'medium' | 'large'
  font_family: 'system' | 'serif' | 'mono'
  // Notifications
  notifications_enabled: boolean
  notifications_sound: boolean
  notifications_debate_complete: boolean
  notifications_error_alerts: boolean
  // Advanced
  max_debate_rounds: number
  auto_start_debate: boolean
  stream_tokens: boolean
  show_pipeline_stages: boolean
  show_agent_confidence: boolean
  highlight_key_insights: boolean
  // Data sources
  preferred_data_sources: string[]
  enable_web_scraping: boolean
  enable_news_api: boolean
  enable_financial_api: boolean
  // Lite Mode support agent policy
  support_agent_policy: {
    rag: boolean
    api: boolean
    mcp: boolean
    web: boolean
    graph: boolean
  }
  // MiroFish swarm simulation
  mirofish_enabled: boolean
}

interface SettingsState {
  settings: AppSettings
  isLoaded: boolean
  updateSettings: (partial: Partial<AppSettings>) => void
  loadFromApi: (data: Record<string, unknown>) => void
  reset: () => void
}

const defaultSettings: AppSettings = {
  api_key: 'dev-key',
  mcp_api_key: 'dev-mcp-key',
  theme: 'light',
  sidebar_collapsed: false,
  lite_mode: false,
  lite_primary_agent: 'risk',
  rag_chunk_size: 512,
  rag_chunk_overlap: 50,
  rag_top_k: 5,
  mcp_rate_limit: 30,
  // Response style
  response_verbosity: 'standard',
  response_include_sources: true,
  response_include_confidence: true,
  response_auto_expand_references: false,
  // Typography
  font_size: 'medium',
  font_family: 'system',
  // Notifications
  notifications_enabled: true,
  notifications_sound: false,
  notifications_debate_complete: true,
  notifications_error_alerts: true,
  // Advanced
  max_debate_rounds: 3,
  auto_start_debate: false,
  stream_tokens: true,
  show_pipeline_stages: true,
  show_agent_confidence: true,
  highlight_key_insights: true,
  // Data sources
  preferred_data_sources: ['firecrawl', 'finnhub', 'fred'],
  enable_web_scraping: true,
  enable_news_api: true,
  enable_financial_api: true,
  // Lite Mode support agent policy
  support_agent_policy: {
    rag: true,
    api: true,
    mcp: true,
    web: true,
    graph: true,
  },
  // MiroFish swarm simulation
  mirofish_enabled: false,
}

export const useSettingsStore = create<SettingsState>()(
  persist(
    (set) => ({
      settings: defaultSettings,
      isLoaded: false,

      updateSettings: (partial) =>
        set((state) => ({
          settings: { ...state.settings, ...partial },
        })),

      loadFromApi: (data) =>
        set((state) => ({
          settings: { ...state.settings, ...data },
          isLoaded: true,
        })),

      reset: () => set({ settings: defaultSettings, isLoaded: false }),
    }),
    { name: 'supplychaingpt-settings' }
  )
)
