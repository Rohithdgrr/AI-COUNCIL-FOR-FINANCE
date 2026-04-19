import { useState, useEffect } from 'react'
import { Link, useLocation, useNavigate } from 'react-router-dom'
import { Shield, MessageSquare, Eye, Settings, Wifi, WifiOff, Menu, X, Activity, Zap, Wrench, Fish } from 'lucide-react'
import { healthApi } from '@/lib/api'
import Dock from '@/components/ui/Dock'

const navItems = [
  { path: '/', label: 'Dashboard', icon: Shield },
  { path: '/chat', label: 'Council Chat', icon: MessageSquare },
  { path: '/mcp', label: 'MCP Explorer', icon: Wrench },
  { path: '/rag', label: 'Swarm Visualizer', icon: Fish },
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
        <div 
          className="mx-auto backdrop-blur-2xl border-b shadow-sm"
          style={{
            background: 'linear-gradient(135deg, rgba(255,255,255,0.92) 0%, rgba(248,250,252,0.95) 100%)',
            borderColor: 'rgba(0,0,0,0.06)',
          }}
        >
          <div className="max-w-[1600px] mx-auto px-6 h-16 flex items-center justify-between">
            {/* Left: Brand */}
            <Link to="/" className="flex items-center gap-3 group">
              <div className="relative">
                <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-blue-600 via-violet-600 to-purple-600 flex items-center justify-center shadow-lg shadow-blue-500/25 group-hover:shadow-blue-500/40 transition-shadow duration-300">
                  <Zap className="w-5 h-5 text-white" />
                </div>
                <div className="absolute -top-0.5 -right-0.5 w-2.5 h-2.5 bg-emerald-400 rounded-full border-2 border-white animate-pulse" />
              </div>
              <div className="flex flex-col">
                <span className="text-[17px] font-bold font-heading tracking-tight text-gray-900 group-hover:text-blue-700 transition-colors">
                  SupplyChain<span className="text-transparent bg-clip-text bg-gradient-to-r from-blue-600 to-violet-600">GPT</span>
                </span>
                <span className="text-[10px] font-heading font-medium text-gray-400 tracking-widest uppercase -mt-0.5">AI Council Platform</span>
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
            <div className="flex items-center gap-4">
              {/* Agent Dots */}
              <div className="flex items-center gap-1.5 px-3 py-1.5 rounded-xl bg-gray-50 border border-gray-100">
                <Activity className="w-3 h-3 text-gray-400 mr-1" />
                {AGENT_COLORS.map((agent) => (
                  <div
                    key={agent.name}
                    className="w-2.5 h-2.5 rounded-full hover:scale-150 transition-transform duration-200 cursor-default"
                    style={{ backgroundColor: agent.hex }}
                    title={agent.name}
                  />
                ))}
                <span className="ml-1.5 text-[10px] font-bold font-heading text-emerald-600 bg-emerald-50 px-1.5 py-0.5 rounded">6/6</span>
              </div>

              {/* Server Status */}
              <div
                className={`flex items-center gap-2 px-3 py-1.5 rounded-xl text-xs font-medium ${
                  serverOnline
                    ? 'bg-emerald-50 text-emerald-700 border border-emerald-100'
                    : 'bg-red-50 text-red-600 border border-red-100'
                }`}
              >
                {serverOnline ? (
                  <Wifi className="w-3.5 h-3.5" />
                ) : (
                  <WifiOff className="w-3.5 h-3.5" />
                )}
                {serverOnline ? 'Online' : 'Offline'}
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
            {/* Agents */}
            <div className="px-5 py-4 border-t border-gray-100">
              <p className="text-[10px] font-heading font-bold text-gray-400 uppercase tracking-wider mb-3">Active Agents</p>
              <div className="flex flex-wrap gap-2">
                {AGENT_COLORS.map((agent) => (
                  <div key={agent.name} className="flex items-center gap-1.5 px-2.5 py-1 rounded-full bg-gray-50 border border-gray-100">
                    <span className="w-2 h-2 rounded-full" style={{ backgroundColor: agent.hex }} />
                    <span className="text-[11px] font-heading font-medium" style={{ color: agent.hex }}>{agent.name}</span>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </>
      )}
    </>
  )
}
