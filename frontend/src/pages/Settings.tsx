import { useState } from 'react'
import { useSettingsStore } from '@/store/settingsStore'
import { settingsApi } from '@/lib/api'
import {
  Save, CheckCircle2, XCircle, Activity, Settings as SettingsIcon, Key, Cpu,
  MessageSquare, Type, Bell, Zap, Database, Globe, ChevronRight, RotateCcw
} from 'lucide-react'
import { useQuery } from '@tanstack/react-query'
import { marketApi } from '@/lib/api'
import { COUNCIL_AGENTS } from '@/types/council'

type SettingsTab = 'general' | 'response' | 'appearance' | 'notifications' | 'advanced' | 'datasources'

export default function Settings() {
  const { settings, updateSettings, reset } = useSettingsStore()
  const [activeTab, setActiveTab] = useState<SettingsTab>('general')
  const [saveSuccess, setSaveSuccess] = useState(false)

  const handleSave = async () => {
    try {
      await settingsApi.update(settings as unknown as Record<string, unknown>)
      setSaveSuccess(true)
      setTimeout(() => setSaveSuccess(false), 2000)
    } catch {
      // Settings saved locally even if API fails
    }
  }

  const handleReset = () => {
    reset()
  }

  const healthCheck = useQuery({
    queryKey: ['health'],
    queryFn: async () => {
      const { data } = await marketApi.ticker()
      return data
    },
    staleTime: 30000,
    refetchInterval: 60000,
  })

  const apiStatuses = [
    { name: 'Finnhub (Stocks)', live: healthCheck.data?.stocks?.some((s: Record<string, unknown>) => !s.mock) },
    { name: 'Frankfurter (Forex)', live: healthCheck.data?.forex && !healthCheck.data.forex.mock },
    { name: 'Open-Meteo (Weather)', live: true },
    { name: 'USGS (Earthquakes)', live: true },
    { name: 'Wikipedia', live: true },
    { name: 'Reddit', live: true },
    { name: 'World Bank', live: true },
    { name: 'GDACS (Disasters)', live: true },
    { name: 'GDELT (Geopolitics)', live: true },
    { name: 'Yahoo Finance (Commodities)', live: healthCheck.data?.commodities?.some((c: Record<string, unknown>) => !c.mock) },
  ]

  const tabs: { id: SettingsTab; label: string; icon: React.ReactNode }[] = [
    { id: 'general', label: 'General', icon: <SettingsIcon className="w-4 h-4" /> },
    { id: 'response', label: 'Response', icon: <MessageSquare className="w-4 h-4" /> },
    { id: 'appearance', label: 'Appearance', icon: <Type className="w-4 h-4" /> },
    { id: 'notifications', label: 'Notifications', icon: <Bell className="w-4 h-4" /> },
    { id: 'advanced', label: 'Advanced', icon: <Zap className="w-4 h-4" /> },
    { id: 'datasources', label: 'Data Sources', icon: <Database className="w-4 h-4" /> },
  ]

  return (
    <div className="max-w-4xl mx-auto px-4 sm:px-6 py-8">
      {/* Header */}
      <div className="mb-6 animate-in-up">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-indigo-500 to-violet-600 flex items-center justify-center shadow-lg shadow-indigo-200">
              <SettingsIcon className="w-5 h-5 text-white" />
            </div>
            <div>
              <h1 className="text-2xl font-bold font-heading text-gray-900">Settings</h1>
              <p className="text-gray-500 text-sm">Configure your application preferences</p>
            </div>
          </div>
          <div className="flex items-center gap-2">
            <button
              onClick={handleReset}
              className="flex items-center gap-1.5 px-3 py-2 text-sm text-gray-500 hover:text-gray-700 hover:bg-gray-100 rounded-lg transition-all"
            >
              <RotateCcw className="w-3.5 h-3.5" />
              Reset
            </button>
            <button
              onClick={handleSave}
              className="flex items-center gap-2 px-5 py-2.5 bg-gradient-to-r from-indigo-600 to-violet-600 rounded-xl text-white hover:from-indigo-700 hover:to-violet-700 transition-all duration-200 shadow-md hover:shadow-lg"
            >
              <Save className="w-4 h-4" />
              {saveSuccess ? 'Saved!' : 'Save Settings'}
            </button>
          </div>
        </div>
      </div>

      {/* Tab Navigation */}
      <div className="flex gap-1 mb-6 bg-gray-100 p-1 rounded-xl animate-in-up delay-50 overflow-x-auto">
        {tabs.map(tab => (
          <button
            key={tab.id}
            onClick={() => setActiveTab(tab.id)}
            className={`flex items-center gap-2 px-4 py-2.5 rounded-lg text-sm font-medium transition-all whitespace-nowrap ${
              activeTab === tab.id
                ? 'bg-white text-indigo-700 shadow-sm'
                : 'text-gray-500 hover:text-gray-700 hover:bg-white/50'
            }`}
          >
            {tab.icon}
            {tab.label}
          </button>
        ))}
      </div>

      <div className="space-y-6">
        {/* GENERAL TAB */}
        {activeTab === 'general' && (
          <>
            {/* Live API Status */}
            <div className="bg-white rounded-xl border border-gray-200 p-5 shadow-card animate-in-up">
              <h2 className="text-sm font-semibold font-heading text-emerald-600 uppercase mb-4 flex items-center gap-2">
                <Activity className="w-4 h-4" /> Live API Status
              </h2>
              <div className="grid grid-cols-2 gap-3">
                {apiStatuses.map(({ name, live }) => (
                  <div key={name} className="flex items-center gap-2.5 text-sm p-2.5 rounded-lg bg-gray-50 border border-gray-100">
                    {live ? (
                      <CheckCircle2 className="w-4 h-4 text-emerald-500 shrink-0" />
                    ) : (
                      <XCircle className="w-4 h-4 text-red-400 shrink-0" />
                    )}
                    <span className={live ? 'text-gray-700 font-medium' : 'text-gray-400'}>{name}</span>
                  </div>
                ))}
              </div>
            </div>

            {/* Lite Mode */}
            <div className="bg-white rounded-xl border border-gray-200 p-5 shadow-card animate-in-up">
              <h2 className="text-sm font-semibold font-heading text-violet-600 uppercase mb-4 flex items-center gap-2">
                <Zap className="w-4 h-4" /> Council Lite Mode
              </h2>
              <div className="flex items-start justify-between gap-4">
                <div>
                  <p className="text-sm font-medium text-gray-800">One primary agent plus five support agents</p>
                  <p className="text-xs text-gray-400 mt-0.5 max-w-2xl">
                    When enabled, new council runs use a faster synthesis path with focused evidence gathering and one final decision-maker.
                  </p>
                </div>
                <button
                  onClick={() => updateSettings({ lite_mode: !settings.lite_mode })}
                  className={`relative w-11 h-6 rounded-full transition-colors duration-200 ${settings.lite_mode ? 'bg-violet-600' : 'bg-gray-300'}`}
                >
                  <span
                    className={`absolute top-0.5 left-0.5 w-5 h-5 bg-white rounded-full shadow transition-transform duration-200 ${
                      settings.lite_mode ? 'translate-x-5' : 'translate-x-0'
                    }`}
                  />
                </button>
              </div>

              {settings.lite_mode && (
                <div className="mt-5">
                  <label className="text-xs text-gray-500 font-medium uppercase tracking-wider mb-2 block">Primary Agent</label>
                  <div className="grid grid-cols-2 md:grid-cols-3 gap-3">
                    {COUNCIL_AGENTS.map((agent) => {
                      const active = settings.lite_primary_agent === agent.key
                      return (
                        <button
                          key={agent.key}
                          onClick={() => updateSettings({ lite_primary_agent: agent.key })}
                          className={`px-4 py-3 rounded-xl text-sm font-medium transition-all border-2 text-left ${
                            active
                              ? 'border-violet-500 bg-violet-50 text-violet-700 shadow-sm'
                              : 'border-gray-200 bg-white text-gray-600 hover:border-gray-300'
                          }`}
                        >
                          <p className="font-semibold">{agent.label}</p>
                          <p className="text-[11px] mt-1 opacity-70">Primary decision-maker</p>
                        </button>
                      )
                    })}
                  </div>

                  <label className="text-xs text-gray-500 font-medium uppercase tracking-wider mb-2 mt-5 block">Support Agent Data Sources</label>
                  <p className="text-[11px] text-gray-400 mb-3">Choose which research channels the 5 support agents use for evidence gathering.</p>
                  <div className="grid grid-cols-2 md:grid-cols-3 gap-3">
                    {([
                      { key: 'rag', label: 'RAG Knowledge Base', desc: 'Internal vector store' },
                      { key: 'api', label: 'Live APIs', desc: 'GNews, Alpha Vantage, etc.' },
                      { key: 'mcp', label: 'MCP Tools', desc: 'Model Context Protocol' },
                      { key: 'web', label: 'Web Scraping', desc: 'DuckDuckGo, Firecrawl' },
                      { key: 'graph', label: 'Graph/DB', desc: 'Knowledge graph queries' },
                    ] as const).map((source) => {
                      const enabled = settings.support_agent_policy?.[source.key as keyof typeof settings.support_agent_policy] !== false
                      return (
                        <button
                          key={source.key}
                          onClick={() => updateSettings({
                            support_agent_policy: {
                              ...settings.support_agent_policy,
                              [source.key]: !enabled,
                            }
                          })}
                          className={`px-4 py-3 rounded-xl text-sm font-medium transition-all border-2 text-left ${
                            enabled
                              ? 'border-indigo-500 bg-indigo-50 text-indigo-700 shadow-sm'
                              : 'border-gray-200 bg-white text-gray-400 hover:border-gray-300'
                          }`}
                        >
                          <p className="font-semibold">{source.label}</p>
                          <p className="text-[11px] mt-1 opacity-70">{source.desc}</p>
                        </button>
                      )
                    })}
                  </div>
                </div>
              )}
            </div>

            {/* API Keys */}
            <div className="bg-white rounded-xl border border-gray-200 p-5 shadow-card animate-in-up">
              <h2 className="text-sm font-semibold font-heading text-blue-600 uppercase mb-4 flex items-center gap-2">
                <Key className="w-4 h-4" /> API Keys
              </h2>
              <div className="space-y-4">
                <div>
                  <label className="text-xs text-gray-500 font-medium uppercase tracking-wider">API Key</label>
                  <input
                    type="password"
                    value={settings.api_key}
                    onChange={(e) => updateSettings({ api_key: e.target.value })}
                    className="w-full bg-gray-50 border border-gray-200 rounded-lg px-3.5 py-2.5 text-sm text-gray-900 mt-1.5 focus:ring-2 focus:ring-blue-500/30 focus:border-blue-400 focus:outline-none transition-all"
                  />
                </div>
                <div>
                  <label className="text-xs text-gray-500 font-medium uppercase tracking-wider">MCP API Key</label>
                  <input
                    type="password"
                    value={settings.mcp_api_key}
                    onChange={(e) => updateSettings({ mcp_api_key: e.target.value })}
                    className="w-full bg-gray-50 border border-gray-200 rounded-lg px-3.5 py-2.5 text-sm text-gray-900 mt-1.5 focus:ring-2 focus:ring-blue-500/30 focus:border-blue-400 focus:outline-none transition-all"
                  />
                </div>
              </div>
            </div>

            {/* RAG Configuration */}
            <div className="bg-white rounded-xl border border-gray-200 p-5 shadow-card animate-in-up">
              <h2 className="text-sm font-semibold font-heading text-violet-600 uppercase mb-4 flex items-center gap-2">
                <Cpu className="w-4 h-4" /> RAG Configuration
              </h2>
              <div className="space-y-5">
                {[
                  { key: 'rag_chunk_size', label: 'Chunk Size', min: 128, max: 2048, step: 64, def: 512 },
                  { key: 'rag_chunk_overlap', label: 'Chunk Overlap', min: 0, max: 200, step: 10, def: 50 },
                  { key: 'rag_top_k', label: 'Top K', min: 1, max: 20, step: 1, def: 5 },
                ].map(s => (
                  <div key={s.key}>
                    <div className="flex items-center justify-between mb-2">
                      <label className="text-xs text-gray-500 font-medium uppercase tracking-wider">{s.label}</label>
                      <span className="text-sm font-bold text-gray-900 bg-gray-100 px-2.5 py-0.5 rounded-md">
                        {settings[s.key as keyof typeof settings] as number}
                      </span>
                    </div>
                    <input
                      type="range"
                      min={s.min}
                      max={s.max}
                      step={s.step}
                      value={settings[s.key as keyof typeof settings] as number}
                      onChange={(e) => updateSettings({ [s.key]: parseInt(e.target.value) || s.def })}
                      className="w-full accent-violet-600"
                    />
                    <div className="flex justify-between text-xs text-gray-400 mt-1">
                      <span>{s.min}</span><span>{s.max}</span>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </>
        )}

        {/* RESPONSE TAB */}
        {activeTab === 'response' && (
          <div className="bg-white rounded-xl border border-gray-200 p-5 shadow-card animate-in-up">
            <h2 className="text-sm font-semibold font-heading text-indigo-600 uppercase mb-4 flex items-center gap-2">
              <MessageSquare className="w-4 h-4" /> Response Style
            </h2>
            <div className="space-y-6">
              {/* Verbosity */}
              <div>
                <label className="text-xs text-gray-500 font-medium uppercase tracking-wider mb-3 block">Verbosity Level</label>
                <div className="grid grid-cols-3 gap-3">
                  {(['concise', 'standard', 'detailed'] as const).map(level => (
                    <button
                      key={level}
                      onClick={() => updateSettings({ response_verbosity: level })}
                      className={`px-4 py-3 rounded-xl text-sm font-medium capitalize transition-all border-2 ${
                        settings.response_verbosity === level
                          ? 'border-indigo-500 bg-indigo-50 text-indigo-700 shadow-sm'
                          : 'border-gray-200 bg-white text-gray-600 hover:border-gray-300'
                      }`}
                    >
                      {level}
                      {level === 'concise' && <p className="text-[10px] text-gray-400 mt-1">Brief summaries</p>}
                      {level === 'standard' && <p className="text-[10px] text-gray-400 mt-1">Balanced detail</p>}
                      {level === 'detailed' && <p className="text-[10px] text-gray-400 mt-1">In-depth analysis</p>}
                    </button>
                  ))}
                </div>
              </div>

              {/* Toggle Options */}
              <div className="space-y-3">
                {[
                  { key: 'response_include_sources', label: 'Include source citations', desc: 'Show [N] citation badges in responses' },
                  { key: 'response_include_confidence', label: 'Show confidence scores', desc: 'Display agent confidence percentages' },
                  { key: 'response_auto_expand_references', label: 'Auto-expand references', desc: 'Automatically open the sources panel' },
                  { key: 'highlight_key_insights', label: 'Highlight key insights', desc: 'Emphasize important findings with callout boxes' },
                ].map(opt => (
                  <div key={opt.key} className="flex items-center justify-between p-4 rounded-xl bg-gray-50 border border-gray-100">
                    <div>
                      <p className="text-sm font-medium text-gray-800">{opt.label}</p>
                      <p className="text-xs text-gray-400 mt-0.5">{opt.desc}</p>
                    </div>
                    <button
                      onClick={() => updateSettings({ [opt.key]: !settings[opt.key as keyof typeof settings] })}
                      className={`relative w-11 h-6 rounded-full transition-colors duration-200 ${
                        settings[opt.key as keyof typeof settings] ? 'bg-indigo-600' : 'bg-gray-300'
                      }`}
                    >
                      <span
                        className={`absolute top-0.5 left-0.5 w-5 h-5 bg-white rounded-full shadow transition-transform duration-200 ${
                          settings[opt.key as keyof typeof settings] ? 'translate-x-5' : 'translate-x-0'
                        }`}
                      />
                    </button>
                  </div>
                ))}
              </div>
            </div>
          </div>
        )}

        {/* APPEARANCE TAB */}
        {activeTab === 'appearance' && (
          <div className="bg-white rounded-xl border border-gray-200 p-5 shadow-card animate-in-up">
            <h2 className="text-sm font-semibold font-heading text-pink-600 uppercase mb-4 flex items-center gap-2">
              <Type className="w-4 h-4" /> Appearance
            </h2>
            <div className="space-y-6">
              {/* Theme */}
              <div>
                <label className="text-xs text-gray-500 font-medium uppercase tracking-wider mb-3 block">Theme</label>
                <div className="grid grid-cols-2 gap-3">
                  {(['light', 'dark'] as const).map(theme => (
                    <button
                      key={theme}
                      onClick={() => updateSettings({ theme })}
                      className={`px-4 py-4 rounded-xl text-sm font-medium capitalize transition-all border-2 ${
                        settings.theme === theme
                          ? theme === 'light'
                            ? 'border-indigo-500 bg-white text-gray-800 shadow-sm'
                            : 'border-indigo-500 bg-gray-900 text-white shadow-sm'
                          : 'border-gray-200 bg-white text-gray-600 hover:border-gray-300'
                      }`}
                    >
                      {theme === 'light' ? '☀️' : '🌙'} {theme}
                    </button>
                  ))}
                </div>
              </div>

              {/* Font Size */}
              <div>
                <label className="text-xs text-gray-500 font-medium uppercase tracking-wider mb-3 block">Font Size</label>
                <div className="grid grid-cols-3 gap-3">
                  {(['small', 'medium', 'large'] as const).map(size => (
                    <button
                      key={size}
                      onClick={() => updateSettings({ font_size: size })}
                      className={`px-4 py-3 rounded-xl text-sm font-medium capitalize transition-all border-2 ${
                        settings.font_size === size
                          ? 'border-indigo-500 bg-indigo-50 text-indigo-700 shadow-sm'
                          : 'border-gray-200 bg-white text-gray-600 hover:border-gray-300'
                      }`}
                    >
                      {size === 'small' && <span className="text-xs">A</span>}
                      {size === 'medium' && <span className="text-sm">A</span>}
                      {size === 'large' && <span className="text-base">A</span>}
                      <span className="ml-2">{size}</span>
                    </button>
                  ))}
                </div>
              </div>

              {/* Font Family */}
              <div>
                <label className="text-xs text-gray-500 font-medium uppercase tracking-wider mb-3 block">Font Family</label>
                <div className="grid grid-cols-3 gap-3">
                  {([
                    { value: 'system', label: 'System', sample: 'Aa Bb Cc' },
                    { value: 'serif', label: 'Serif', sample: 'Aa Bb Cc' },
                    { value: 'mono', label: 'Mono', sample: 'Aa Bb Cc' },
                  ] as const).map(font => (
                    <button
                      key={font.value}
                      onClick={() => updateSettings({ font_family: font.value })}
                      className={`px-4 py-3 rounded-xl transition-all border-2 ${
                        settings.font_family === font.value
                          ? 'border-indigo-500 bg-indigo-50 text-indigo-700 shadow-sm'
                          : 'border-gray-200 bg-white text-gray-600 hover:border-gray-300'
                      }`}
                    >
                      <p className="text-xs text-gray-400 mb-1">{font.label}</p>
                      <p
                        className="text-lg"
                        style={{
                          fontFamily: font.value === 'serif' ? 'Georgia, serif' : font.value === 'mono' ? 'monospace' : 'system-ui, sans-serif'
                        }}
                      >
                        {font.sample}
                      </p>
                    </button>
                  ))}
                </div>
              </div>
            </div>
          </div>
        )}

        {/* NOTIFICATIONS TAB */}
        {activeTab === 'notifications' && (
          <div className="bg-white rounded-xl border border-gray-200 p-5 shadow-card animate-in-up">
            <h2 className="text-sm font-semibold font-heading text-amber-600 uppercase mb-4 flex items-center gap-2">
              <Bell className="w-4 h-4" /> Notifications
            </h2>
            <div className="space-y-3">
              {[
                { key: 'notifications_enabled', label: 'Enable notifications', desc: 'Show in-app notifications for events' },
                { key: 'notifications_sound', label: 'Sound alerts', desc: 'Play a sound when notifications appear' },
                { key: 'notifications_debate_complete', label: 'Debate completion', desc: 'Notify when a council debate finishes' },
                { key: 'notifications_error_alerts', label: 'Error alerts', desc: 'Notify when errors or failures occur' },
              ].map(opt => (
                <div key={opt.key} className="flex items-center justify-between p-4 rounded-xl bg-gray-50 border border-gray-100">
                  <div>
                    <p className="text-sm font-medium text-gray-800">{opt.label}</p>
                    <p className="text-xs text-gray-400 mt-0.5">{opt.desc}</p>
                  </div>
                  <button
                    onClick={() => updateSettings({ [opt.key]: !settings[opt.key as keyof typeof settings] })}
                    className={`relative w-11 h-6 rounded-full transition-colors duration-200 ${
                      settings[opt.key as keyof typeof settings] ? 'bg-amber-500' : 'bg-gray-300'
                    }`}
                  >
                    <span
                      className={`absolute top-0.5 left-0.5 w-5 h-5 bg-white rounded-full shadow transition-transform duration-200 ${
                        settings[opt.key as keyof typeof settings] ? 'translate-x-5' : 'translate-x-0'
                      }`}
                    />
                  </button>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* ADVANCED TAB */}
        {activeTab === 'advanced' && (
          <div className="bg-white rounded-xl border border-gray-200 p-5 shadow-card animate-in-up">
            <h2 className="text-sm font-semibold font-heading text-red-600 uppercase mb-4 flex items-center gap-2">
              <Zap className="w-4 h-4" /> Advanced
            </h2>
            <div className="space-y-6">
              {/* Max Debate Rounds */}
              <div>
                <div className="flex items-center justify-between mb-2">
                  <label className="text-xs text-gray-500 font-medium uppercase tracking-wider">Max Debate Rounds</label>
                  <span className="text-sm font-bold text-gray-900 bg-gray-100 px-2.5 py-0.5 rounded-md">{settings.max_debate_rounds}</span>
                </div>
                <input
                  type="range"
                  min="1"
                  max="5"
                  step="1"
                  value={settings.max_debate_rounds}
                  onChange={(e) => updateSettings({ max_debate_rounds: parseInt(e.target.value) || 3 })}
                  className="w-full accent-red-500"
                />
                <div className="flex justify-between text-xs text-gray-400 mt-1">
                  <span>1</span><span>5</span>
                </div>
              </div>

              {/* Toggle Options */}
              <div className="space-y-3">
                {[
                  { key: 'auto_start_debate', label: 'Auto-start debate', desc: 'Automatically begin debate when query is submitted' },
                  { key: 'stream_tokens', label: 'Stream tokens', desc: 'Show real-time token streaming during generation' },
                  { key: 'show_pipeline_stages', label: 'Show pipeline stages', desc: 'Display the RAG/MCP pipeline progress bar' },
                  { key: 'show_agent_confidence', label: 'Show agent confidence', desc: 'Display confidence meters for each agent' },
                ].map(opt => (
                  <div key={opt.key} className="flex items-center justify-between p-4 rounded-xl bg-gray-50 border border-gray-100">
                    <div>
                      <p className="text-sm font-medium text-gray-800">{opt.label}</p>
                      <p className="text-xs text-gray-400 mt-0.5">{opt.desc}</p>
                    </div>
                    <button
                      onClick={() => updateSettings({ [opt.key]: !settings[opt.key as keyof typeof settings] })}
                      className={`relative w-11 h-6 rounded-full transition-colors duration-200 ${
                        settings[opt.key as keyof typeof settings] ? 'bg-red-500' : 'bg-gray-300'
                      }`}
                    >
                      <span
                        className={`absolute top-0.5 left-0.5 w-5 h-5 bg-white rounded-full shadow transition-transform duration-200 ${
                          settings[opt.key as keyof typeof settings] ? 'translate-x-5' : 'translate-x-0'
                        }`}
                      />
                    </button>
                  </div>
                ))}
              </div>

              {/* MCP Rate Limit */}
              <div>
                <div className="flex items-center justify-between mb-2">
                  <label className="text-xs text-gray-500 font-medium uppercase tracking-wider">MCP Rate Limit (req/min)</label>
                  <span className="text-sm font-bold text-gray-900 bg-gray-100 px-2.5 py-0.5 rounded-md">{settings.mcp_rate_limit}</span>
                </div>
                <input
                  type="range"
                  min="5"
                  max="60"
                  step="5"
                  value={settings.mcp_rate_limit}
                  onChange={(e) => updateSettings({ mcp_rate_limit: parseInt(e.target.value) || 30 })}
                  className="w-full accent-red-500"
                />
                <div className="flex justify-between text-xs text-gray-400 mt-1">
                  <span>5</span><span>60</span>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* DATA SOURCES TAB */}
        {activeTab === 'datasources' && (
          <div className="bg-white rounded-xl border border-gray-200 p-5 shadow-card animate-in-up">
            <h2 className="text-sm font-semibold font-heading text-cyan-600 uppercase mb-4 flex items-center gap-2">
              <Database className="w-4 h-4" /> Data Sources
            </h2>
            <div className="space-y-3">
              {[
                { key: 'enable_web_scraping', label: 'Web Scraping (Firecrawl)', desc: 'Scrape websites for real-time data', icon: <Globe className="w-4 h-4 text-cyan-500" /> },
                { key: 'enable_news_api', label: 'News & Social APIs', desc: 'Reddit, Wikipedia, GDELT news feeds', icon: <Activity className="w-4 h-4 text-cyan-500" /> },
                { key: 'enable_financial_api', label: 'Financial APIs', desc: 'Finnhub, Yahoo Finance, FRED economic data', icon: <ChevronRight className="w-4 h-4 text-cyan-500" /> },
              ].map(opt => (
                <div key={opt.key} className="flex items-center justify-between p-4 rounded-xl bg-gray-50 border border-gray-100">
                  <div className="flex items-center gap-3">
                    {opt.icon}
                    <div>
                      <p className="text-sm font-medium text-gray-800">{opt.label}</p>
                      <p className="text-xs text-gray-400 mt-0.5">{opt.desc}</p>
                    </div>
                  </div>
                  <button
                    onClick={() => updateSettings({ [opt.key]: !settings[opt.key as keyof typeof settings] })}
                    className={`relative w-11 h-6 rounded-full transition-colors duration-200 ${
                      settings[opt.key as keyof typeof settings] ? 'bg-cyan-500' : 'bg-gray-300'
                    }`}
                  >
                    <span
                      className={`absolute top-0.5 left-0.5 w-5 h-5 bg-white rounded-full shadow transition-transform duration-200 ${
                        settings[opt.key as keyof typeof settings] ? 'translate-x-5' : 'translate-x-0'
                      }`}
                    />
                  </button>
                </div>
              ))}
            </div>

            {/* Preferred Data Sources Priority */}
            <div className="mt-6">
              <label className="text-xs text-gray-500 font-medium uppercase tracking-wider mb-3 block">Preferred Data Sources Priority</label>
              <div className="space-y-2">
                {settings.preferred_data_sources.map((source, index) => (
                  <div key={source} className="flex items-center gap-3 p-3 rounded-lg bg-gray-50 border border-gray-100">
                    <span className="w-6 h-6 rounded-full bg-cyan-100 text-cyan-700 flex items-center justify-center text-xs font-bold">
                      {index + 1}
                    </span>
                    <span className="text-sm font-medium text-gray-700 capitalize flex-1">{source}</span>
                    <div className="flex gap-1">
                      <button
                        onClick={() => {
                          if (index > 0) {
                            const newSources = [...settings.preferred_data_sources]
                            const temp = newSources[index]
                            newSources[index] = newSources[index - 1] ?? ''
                            newSources[index - 1] = temp ?? ''
                            updateSettings({ preferred_data_sources: newSources })
                          }
                        }}
                        className="p-1 rounded hover:bg-gray-200 transition-colors text-gray-400 hover:text-gray-600 disabled:opacity-30"
                        disabled={index === 0}
                      >
                        ↑
                      </button>
                      <button
                        onClick={() => {
                          if (index < settings.preferred_data_sources.length - 1) {
                            const newSources = [...settings.preferred_data_sources]
                            const temp = newSources[index]
                            newSources[index] = newSources[index + 1] ?? ''
                            newSources[index + 1] = temp ?? ''
                            updateSettings({ preferred_data_sources: newSources })
                          }
                        }}
                        className="p-1 rounded hover:bg-gray-200 transition-colors text-gray-400 hover:text-gray-600 disabled:opacity-30"
                        disabled={index === settings.preferred_data_sources.length - 1}
                      >
                        ↓
                      </button>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}
