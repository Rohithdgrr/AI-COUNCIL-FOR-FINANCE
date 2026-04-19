import { useState } from 'react'
import { Wrench, Search, ChevronDown, ChevronRight, Play, Loader2, Network, CheckCircle2, Box } from 'lucide-react'
import { useMCPManifest, useMCPInvoke } from '@/hooks/useMCPTools'
import { COUNCIL_AGENTS } from '@/types/council'
import type { MCPTool } from '@/types/mcp'
import { motion, AnimatePresence } from 'framer-motion'

const CATEGORY_COLORS: Record<string, string> = {
  financial: '#10b981', commodity: '#f59e0b', forex: '#06b6d4', news: '#8b5cf6',
  geopolitical: '#ef4444', economic: '#a855f7', disaster: '#dc2626', weather: '#0ea5e9',
}

function ToolCard({ tool, onInvoke }: { tool: MCPTool; onInvoke: (tool: MCPTool) => void }) {
  const [expanded, setExpanded] = useState(false)
  const catColor = CATEGORY_COLORS[tool.category] || '#64748b'

  return (
    <div className="group relative">
      <div className="absolute -inset-[1px] bg-gradient-to-r from-indigo-500 to-cyan-500 rounded-lg opacity-0 group-hover:opacity-30 transition-opacity duration-300 blur-sm pointer-events-none" />
      <motion.div layout className="relative bg-white/90 backdrop-blur-md border border-slate-200/80 rounded-lg overflow-hidden shadow-sm transition-all hover:border-transparent z-10 group-hover:shadow-[0_0_20px_rgba(79,70,229,0.15)]">
        
        {/* Top Edge Highlight */}
        <div className="absolute top-0 left-0 w-full h-[2px] opacity-30" style={{ backgroundImage: `linear-gradient(to right, ${catColor}, transparent)` }} />

        <button 
          onClick={() => setExpanded(!expanded)} 
          className="w-full flex items-center gap-4 p-5 text-left outline-none bg-transparent hover:bg-slate-50/50 transition-colors"
        >
          <div className="w-10 h-10 rounded shadow-sm border flex items-center justify-center shrink-0" style={{ backgroundColor: `${catColor}10`, color: catColor, borderColor: `${catColor}30` }}>
             <Wrench className="w-4 h-4" />
          </div>
          <div className="flex-1 min-w-0">
            <div className="flex items-center gap-2.5 mb-1">
              <span className="text-base font-bold text-slate-900 tracking-tight truncate">{tool.name}</span>
              <span className="text-[8px] font-black uppercase tracking-widest px-2 py-0.5 rounded border shadow-sm" style={{ backgroundColor: `${catColor}10`, color: catColor, borderColor: `${catColor}30` }}>
                {tool.category}
              </span>
            </div>
            <p className="text-[11px] text-slate-500 truncate font-medium">{tool.description}</p>
          </div>
          <div className="shrink-0 w-6 h-6 rounded bg-slate-100 border border-slate-200 flex items-center justify-center text-slate-500 transition-colors group-hover:bg-slate-200 group-hover:text-slate-800">
            {expanded ? <ChevronDown className="w-3.5 h-3.5" /> : <ChevronRight className="w-3.5 h-3.5" />}
          </div>
        </button>

        <AnimatePresence>
          {expanded && (
            <motion.div initial={{ height: 0 }} animate={{ height: 'auto' }} exit={{ height: 0 }} className="overflow-hidden bg-slate-50 border-t border-slate-200/60">
              <div className="p-5 flex flex-col gap-5">
                 
                <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
                   
                   {/* Parameter Schema Block */}
                   <div>
                     <h4 className="text-[9px] font-black text-slate-400 uppercase tracking-widest mb-2 flex items-center gap-1.5"><Box className="w-3 h-3 text-slate-400" /> Parameter Schema</h4>
                     <div className="bg-white rounded border border-slate-200 shadow-inner overflow-hidden">
                       {Object.entries(tool.input_schema.properties || {}).map(([key, prop], i) => (
                         <div key={key} className={`px-4 py-2.5 flex items-center justify-between text-xs ${i !== 0 ? 'border-t border-slate-100' : ''}`}>
                           <div className="flex items-center gap-2">
                              <span className="font-bold text-slate-800 tracking-tight">{key}</span>
                              {tool.input_schema.required?.includes(key) && <span className="text-[8px] uppercase font-black text-red-500 tracking-widest bg-red-50 border border-red-100 px-1 rounded">REQ</span>}
                           </div>
                           <span className="text-slate-500 font-mono text-[10px] bg-slate-100 px-2 py-0.5 rounded border border-slate-200">{prop.type}</span>
                         </div>
                       ))}
                       {Object.keys(tool.input_schema.properties || {}).length === 0 && <div className="p-4 text-xs text-slate-400 italic">No parameters required</div>}
                     </div>
                   </div>

                   {/* System Health Block */}
                   <div>
                     <h4 className="text-[9px] font-black text-slate-400 uppercase tracking-widest mb-2 flex items-center gap-1.5"><CheckCircle2 className="w-3 h-3 text-slate-400" /> Execution Telemetry</h4>
                     <div className="bg-white rounded border border-slate-200 shadow-inner p-4 h-[calc(100%-24px)] flex flex-col">
                        {!tool.health ? <span className="text-xs font-medium text-slate-400">Node idle.</span> : (
                           <>
                              <div className="flex items-end justify-between mb-2">
                                 <span className="text-[9px] font-bold text-slate-500 uppercase tracking-widest">Success Index</span>
                                 <span className="text-lg font-black text-slate-800">{(tool.health.success_rate * 100).toFixed(0)}%</span>
                              </div>
                              <div className="w-full h-1.5 bg-slate-100 rounded-none overflow-visible relative">
                                 <div className="absolute left-0 top-0 h-full bg-indigo-500 shadow-[0_0_10px_rgba(99,102,241,0.5)]" style={{ width: `${Math.max(tool.health.success_rate * 100, 5)}%` }} />
                              </div>
                              <div className="flex items-center justify-between text-[9px] font-bold text-slate-400 uppercase tracking-widest mt-auto">
                                 <span>Hits: {tool.health.calls}</span>
                                 <span>Ping: {tool.health.avg_latency_ms}ms</span>
                              </div>
                           </>
                        )}
                     </div>
                   </div>

                </div>

                {/* Footer Controls */}
                <div className="flex flex-col sm:flex-row sm:items-center justify-between mt-1 pt-4 border-t border-slate-200 gap-4">
                   <div className="flex items-center gap-2 overflow-x-auto no-scrollbar pb-1">
                      <span className="text-[8px] font-black text-slate-400 uppercase tracking-widest mr-1 shrink-0">Bound Agents:</span>
                      {tool.allowed_agents?.map((a) => {
                         const agent = COUNCIL_AGENTS.find((c) => c.key === a)
                         return <span key={a} className="shrink-0 text-[8px] font-bold px-2 py-0.5 rounded border uppercase tracking-wider bg-white shadow-sm" style={{ color: agent?.hexColor || '#333', borderColor: `${agent?.hexColor}40` || '#eee' }}>{agent?.label || a}</span>
                      })}
                   </div>
                   
                   <div className="relative group/btn shrink-0">
                     <div className="absolute -inset-[1px] bg-indigo-500/50 rounded-md opacity-0 group-hover/btn:opacity-100 blur transition-opacity" />
                     <button onClick={(e) => { e.stopPropagation(); onInvoke(tool) }} className="w-full sm:w-auto relative px-6 py-2 rounded-md text-[10px] font-black uppercase tracking-widest text-white bg-slate-900 border border-slate-800 shadow-sm transition-all active:scale-95 flex items-center justify-center gap-2 group-hover/btn:bg-indigo-600 group-hover/btn:border-indigo-500">
                       <Play className="w-3 h-3" /> Execute Tool
                     </button>
                   </div>
                </div>

              </div>
            </motion.div>
          )}
        </AnimatePresence>
      </motion.div>
    </div>
  )
}

export default function MCPExplorer() {
  const { data: manifest, isLoading } = useMCPManifest()
  const [search, setSearch] = useState('')
  const [selectedCategory, setSelectedCategory] = useState<string | null>(null)
  const [invokeTool, setInvokeTool] = useState<MCPTool | null>(null)

  const tools = manifest?.tools || []
  const categories = manifest?.categories || []

  const filtered = tools.filter((t) => {
    const matchesSearch = !search || t.name.toLowerCase().includes(search.toLowerCase()) || t.description.toLowerCase().includes(search.toLowerCase())
    const matchesCategory = !selectedCategory || t.category === selectedCategory
    return matchesSearch && matchesCategory
  })

  return (
    <div className="relative min-h-[calc(100vh-4rem)] bg-[#f8fafc] overflow-hidden p-4 md:p-8 text-slate-800">
      
      {/* Structural Minimal Background */}
      <div className="absolute inset-0 bg-[radial-gradient(#e2e8f0_1px,transparent_1px)] [background-size:20px_20px] opacity-30 pointer-events-none" />

      <div className="max-w-7xl mx-auto relative z-10 flex flex-col h-full gap-8">
        
        {/* Sharp Header */}
        <div className="flex flex-col md:flex-row items-end justify-between gap-6 shrink-0 border-b border-slate-200 pb-6">
          <div className="flex items-center gap-4">
            <div className="relative flex items-center justify-center w-12 h-12 bg-slate-900 text-white rounded-md shadow-lg shadow-slate-900/20">
               <Network className="w-6 h-6" />
            </div>
            <div>
              <h1 className="text-3xl font-black text-slate-900 tracking-tight">MCP Protocol</h1>
              <div className="flex items-center gap-2 mt-1">
                 <div className="w-1.5 h-1.5 rounded-none bg-indigo-500 shadow-[0_0_8px_rgba(99,102,241,0.8)]" />
                 <p className="text-[9px] font-bold uppercase tracking-widest text-slate-400">{tools.length} Nodes Indexed</p>
              </div>
            </div>
          </div>
        </div>

        {/* Control Nav Plane */}
        <div className="bg-white/80 backdrop-blur-md border border-slate-200 rounded-lg p-3 flex flex-col md:flex-row items-center gap-4 shadow-sm z-20">
           <div className="relative w-full md:w-[350px] shrink-0 group">
             <div className="absolute -inset-[1px] bg-indigo-500 rounded opacity-0 group-focus-within:opacity-20 blur transition-opacity" />
             <div className="relative bg-white border border-slate-200 rounded flex items-center px-3 group-focus-within:border-indigo-400 transition-colors">
                <Search className="w-3.5 h-3.5 text-slate-400 shrink-0" />
                <input 
                  type="text" value={search} onChange={(e) => setSearch(e.target.value)} 
                  placeholder="Query protocol graph..." 
                  className="w-full bg-transparent px-3 py-2.5 text-xs font-bold text-slate-800 outline-none placeholder:text-slate-400 placeholder:font-medium" 
                />
             </div>
           </div>
           
           <div className="flex items-center gap-2 overflow-x-auto w-full no-scrollbar px-1 py-1">
             <button onClick={() => setSelectedCategory(null)} className={`px-4 py-2 shrink-0 rounded text-[9px] font-black uppercase tracking-widest transition-all border ${!selectedCategory ? 'bg-slate-900 text-white border-slate-800 shadow-md' : 'bg-white text-slate-500 border-slate-200 hover:bg-slate-50'}`}>All Nodes</button>
             {categories.map((cat) => {
                const bgC = CATEGORY_COLORS[cat] || '#64748b'
                const isSelected = selectedCategory === cat
                return (
                  <button 
                    key={cat} 
                    onClick={() => setSelectedCategory(isSelected ? null : cat)} 
                    className={`px-4 py-2 shrink-0 rounded text-[9px] font-black uppercase tracking-widest transition-all border ${isSelected ? 'shadow-md border-transparent text-white' : 'bg-white border-slate-200 hover:bg-slate-50 hover:border-slate-300'}`} 
                    style={isSelected ? { backgroundColor: bgC } : { color: bgC }}
                  >
                    {cat}
                  </button>
                )
             })}
           </div>
        </div>

        {/* Node Grid */}
        {isLoading ? (
          <div className="flex flex-col items-center justify-center py-20 opacity-60">
            <Loader2 className="w-8 h-8 text-indigo-500 animate-[spin_3s_linear_infinite] mb-4" />
            <span className="text-[10px] font-black uppercase tracking-widest text-slate-500">Establishing Initial Handshake</span>
          </div>
        ) : (
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 relative z-10 pb-10 content-start">
             <AnimatePresence>
               {filtered.map((tool) => (
                 <ToolCard key={tool.name} tool={tool} onInvoke={setInvokeTool} />
               ))}
               {filtered.length === 0 && (
                  <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="col-span-full py-16 flex flex-col items-center border border-dashed border-slate-300 rounded-lg bg-slate-50/50">
                     <Search className="w-8 h-8 text-slate-300 mb-3" />
                     <span className="text-xs font-bold text-slate-500 uppercase tracking-widest">0 Nodes matched criteria</span>
                  </motion.div>
               )}
             </AnimatePresence>
          </div>
        )}
      </div>
    </div>
  )
}
