import { useState, useEffect } from 'react'
import { Link, useLocation, useNavigate } from 'react-router-dom'
import { Shield, MessageSquare, Eye, Settings, Wifi, WifiOff, Menu, X, Activity, Zap, Wrench, Star, Database } from 'lucide-react'
import { healthApi } from '@/lib/api'
import Dock from '@/components/ui/Dock'
import { useCouncilV2Store } from '@/store/councilV2Store'

const navItems = [
  { path: '/', label: 'Dashboard', icon: Shield },
  { path: '/chat', label: 'Council Chat', icon: MessageSquare },
  { path: '/mcp', label: 'MCP Explorer', icon: Wrench },
  { path: '/rag', label: 'Astra Swarm', icon: Star },
  { path: '/brand', label: 'Brand Intel', icon: Eye },
  { path: '/settings', label: 'Settings', icon: Settings },
]

const AGENT_COLORS = [
  { name: 'Risk Sentinel', hex: '#EF4444' },
  { name: 'Supply Optimizer', hex: '#7C3AED' },
  { name: 'Logistics Navigator', hex: '#06B6D4' },
  { name: 'Market Intelligence', hex: '#F97316' },
  { name: 'Finance Guardian', hex: '#059669' },
  { name: 'Brand Protector', hex: '#EC4899' },
]

function MiroFishIndicator() {
  const { mirofishPhase, mirofishEnabled } = useCouncilV2Store()
  const isRunning = mirofishPhase !== 'idle' && mirofishPhase !== 'completed' && mirofishPhase !== 'failed'
  const isComplete = mirofishPhase === 'completed'
  const isFailed = mirofishPhase === 'failed'

  if (!mirofishEnabled && !isRunning && !isComplete && !isFailed) return null

  return (
    <Link
      to="/rag"
      className={`flex items-center gap-1.5 px-3 py-1.5 rounded-sm text-[9px] font-black uppercase tracking-widest transition-all duration-300 ${
        isRunning ? 'bg-cyan-50 text-cyan-700 border border-cyan-200 shadow-[0_0_10px_rgba(34,211,238,0.2)] animate-pulse' :
        isComplete ? 'bg-emerald-50 text-emerald-700 border border-emerald-200' :
        isFailed ? 'bg-red-50 text-red-700 border border-red-200' :
        'bg-slate-50 text-slate-500 border border-slate-200 hover:bg-white'
      }`}
    >
      <Star className={`w-3.5 h-3.5 ${isRunning ? 'text-cyan-500' : ''}`} />
      <span>
        {isRunning ? mirofishPhase.replace(/_/g, ' ') :
         isComplete ? 'Swarm Done' :
         isFailed ? 'Swarm Fail' :
         'Astra Array'}
      </span>
    </Link>
  )
}

export default function Navbar() {
  const location = useLocation()
  const navigate = useNavigate()
  const [serverOnline, setServerOnline] = useState(false)
  const [mobileOpen, setMobileOpen] = useState(false)

  useEffect(() => {
    const checkHealth = async () => {
      try {
        await healthApi.check()
        setServerOnline(true)
      } catch {
        setServerOnline(false)
      }
    }
    checkHealth()
    const interval = setInterval(checkHealth, 15000)
    return () => clearInterval(interval)
  }, [])

  return (
    <>
      {/* ─── Desktop Top Navigation ─── */}
      <header className="hidden lg:block fixed top-0 left-0 right-0 z-50">
        <div className="mx-auto bg-white/95 backdrop-blur-md border-b border-slate-200 shadow-sm">
          <div className="max-w-[1700px] mx-auto px-6 h-16 flex items-center justify-between">
            {/* Left: Brand */}
            <Link to="/" className="flex items-center gap-3 group">
              <div className="relative">
                <div className="w-10 h-10 rounded-md bg-slate-900 border border-slate-800 flex items-center justify-center shadow-lg shadow-slate-900/20 group-hover:bg-slate-800 transition-all duration-300">
                  <Zap className="w-5 h-5 text-cyan-400 group-hover:text-cyan-300 transition-colors" />
                </div>
              </div>
              <div className="flex flex-col">
                <span className="text-xl font-black font-heading tracking-tight text-slate-900 group-hover:text-slate-700 transition-colors">
                  Astra<span className="text-cyan-600">Core</span>
                </span>
                <span className="text-[9px] font-black font-heading text-slate-500 tracking-[0.2em] uppercase mt-0.5">Global Protocol Array</span>
              </div>
            </Link>

            {/* Center: Dock Nav Links */}
            <Dock
              items={navItems.map((item) => ({
                icon: <item.icon size={20} />,
                label: window.innerWidth > 1024 ? item.label : undefined, // Label pops up on hover via CSS
                onClick: () => navigate(item.path),
                className: location.pathname === item.path ? '!bg-blue-50 !text-blue-600 !border-blue-200' : ''
              }))}
              panelHeight={48}
              baseItemSize={40}
              magnification={70}
              className="mt-1 px-8"
            />


            {/* Right: Agent dots + Server status */}
            <div className="flex items-center gap-3">
              {/* Astra Status */}
              <MiroFishIndicator />

              {/* Server Status Animation Improved */}
              <div
                className={`flex items-center gap-2 px-3 py-1.5 rounded-sm border transition-all duration-300 ${
                  serverOnline
                    ? 'bg-slate-900 text-white border-slate-800'
                    : 'bg-red-50 text-red-600 border-red-200'
                }`}
              >
                {serverOnline ? (
                  <div className="relative flex items-center gap-2">
                    <div className="w-2 h-2 rounded-none bg-emerald-500 shadow-[0_0_8px_rgba(16,185,129,0.8)] animate-pulse" />
                    <span className="text-[9px] font-black uppercase tracking-widest">Sys Online</span>
                  </div>
                ) : (
                  <div className="relative flex items-center gap-2">
                    <div className="w-2 h-2 rounded-none bg-red-500 shadow-[0_0_8px_rgba(239,68,68,0.8)]" />
                    <span className="text-[9px] font-black uppercase tracking-widest">Off-Grid</span>
                  </div>
                )}
              </div>
            </div>
          </div>
        </div>
      </header>

      {/* ─── Mobile Top Bar ─── */}
      <div className="lg:hidden fixed top-0 left-0 right-0 z-50 bg-white/90 backdrop-blur-xl border-b border-gray-200/60 shadow-sm h-14 flex items-center justify-between px-4">
        <Link to="/" className="flex items-center gap-2.5">
          <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-blue-600 via-violet-600 to-purple-600 flex items-center justify-center shadow-md">
            <Zap className="w-4 h-4 text-white" />
          </div>
          <span className="text-[15px] font-bold font-heading text-gray-900">
            SupplyChain<span className="text-transparent bg-clip-text bg-gradient-to-r from-blue-600 to-violet-600">GPT</span>
          </span>
        </Link>
        <button
          onClick={() => setMobileOpen(!mobileOpen)}
          className="p-2 rounded-lg text-gray-500 hover:text-gray-700 hover:bg-gray-50 transition-colors"
        >
          {mobileOpen ? <X className="w-5 h-5" /> : <Menu className="w-5 h-5" />}
        </button>
      </div>

      {/* ─── Mobile Drawer ─── */}
      {mobileOpen && (
        <>
          <div className="lg:hidden fixed inset-0 bg-black/20 backdrop-blur-sm z-50" onClick={() => setMobileOpen(false)} />
          <div className="lg:hidden fixed top-0 right-0 h-screen w-[280px] bg-white z-50 shadow-2xl animate-in-right border-l border-gray-200">
            <div className="flex items-center justify-between px-5 h-14 border-b border-gray-100">
              <span className="text-[15px] font-bold font-heading text-gray-900">
                SupplyChain<span className="text-transparent bg-clip-text bg-gradient-to-r from-blue-600 to-violet-600">GPT</span>
              </span>
              <button onClick={() => setMobileOpen(false)} className="p-1.5 rounded-lg hover:bg-gray-100">
                <X className="w-5 h-5 text-gray-500" />
              </button>
            </div>
            <nav className="py-4 px-3 space-y-1">
              {navItems.map(({ path, label, icon: Icon }) => {
                const active = location.pathname === path
                return (
                  <Link
                    key={path}
                    to={path}
                    onClick={() => setMobileOpen(false)}
                    className={`group flex items-center gap-3 px-4 py-3 rounded-xl text-sm font-heading font-medium transition-all duration-200 ${
                      active
                        ? 'text-blue-700 bg-blue-50'
                        : 'text-gray-600 hover:bg-gray-50'
                    }`}
                  >
                    <div className={`w-9 h-9 rounded-xl flex items-center justify-center ${
                      active ? 'bg-blue-100 text-blue-600' : 'bg-gray-100 text-gray-500'
                    }`}>
                      <Icon className="w-4.5 h-4.5" />
                    </div>
                    {label}
                  </Link>
                )
              })}
            </nav>
          </div>
        </>
      )}
    </>
  )
}
