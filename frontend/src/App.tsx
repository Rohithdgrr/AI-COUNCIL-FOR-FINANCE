import { useEffect } from 'react'
import { Routes, Route } from 'react-router-dom'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import Navbar from './components/layout/Navbar'
import ToastContainer from './components/shared/Toast'
import Dashboard from './pages/Dashboard'
import Chat from './pages/Chat'
import Brand from './pages/Brand'
import Debate from './pages/Debate'
import Settings from './pages/Settings'
import MCPExplorer from './pages/MCPExplorer'
import SwarmVisualizer from './pages/SwarmVisualizer'
import DataSources from './pages/DataSources'
import NotFound from './pages/NotFound'
import { useSettingsStore } from './store/settingsStore'
import { apiKeyManager } from './lib/secureStorage'

const queryClient = new QueryClient({
  defaultOptions: {
    queries: { retry: 1, staleTime: 30000 },
  },
})

function App() {
  const { settings } = useSettingsStore()

  // Initialize API keys from environment variables if not already set
  useEffect(() => {
    if (!apiKeyManager.getApiKey() && import.meta.env.VITE_API_KEY) {
      apiKeyManager.setApiKey(import.meta.env.VITE_API_KEY)
    }
    if (!apiKeyManager.getMcpApiKey() && import.meta.env.VITE_MCP_API_KEY) {
      apiKeyManager.setMcpApiKey(import.meta.env.VITE_MCP_API_KEY)
    }
  }, [])

  // Apply global theme, font size, and font family from settings
  useEffect(() => {
    const root = document.documentElement

    // Theme
    if (settings.theme === 'dark') {
      root.classList.add('dark')
    } else {
      root.classList.remove('dark')
    }

    // Font size
    const fontSizeMap = { small: '14px', medium: '16px', large: '18px' }
    root.style.fontSize = fontSizeMap[settings.font_size] || '16px'

    // Font family
    const fontFamilyMap = {
      system: "'DM Sans', system-ui, sans-serif",
      serif: "'Georgia', serif",
      mono: "'JetBrains Mono', monospace",
    }
    root.style.fontFamily = fontFamilyMap[settings.font_family] || fontFamilyMap.system
  }, [settings.theme, settings.font_size, settings.font_family])

  return (
    <QueryClientProvider client={queryClient}>
      <div className={`min-h-screen transition-colors duration-300 ${settings.theme === 'dark' ? 'bg-gray-950 text-gray-100' : 'bg-slate-50 text-gray-900'}`}>
        <Navbar />
        <main className="pt-14 lg:pt-16 transition-all duration-300">
          <Routes>
            <Route path="/" element={<Dashboard />} />
            <Route path="/dashboard" element={<Dashboard />} />
            <Route path="/chat" element={<Chat />} />
            <Route path="/debate" element={<Debate />} />
            <Route path="/brand" element={<Brand />} />
            <Route path="/mcp" element={<MCPExplorer />} />
            <Route path="/rag" element={<SwarmVisualizer />} />
            <Route path="/data-sources" element={<DataSources />} />
            <Route path="/settings" element={<Settings />} />
            <Route path="*" element={<NotFound />} />
          </Routes>
        </main>
        <ToastContainer />
      </div>
    </QueryClientProvider>
  )
}

export default App
