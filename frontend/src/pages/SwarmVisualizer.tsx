import { useState, useEffect } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import {
  Star, Search, Loader2,
  Network, Users, Play, TrendingUp, AlertTriangle, Lightbulb, ChevronDown, ChevronUp, Zap,
  Maximize2, Minimize2, Grid3X3, LayoutList, BarChart2, Target, Sparkles, Activity
} from 'lucide-react'
import { useCouncilV2Store } from '@/store/councilV2Store'
import { useMiroFishSwarm } from '@/hooks/useMiroFishSwarm'

const PHASE_LABELS: Record<string, { label: string; icon: typeof Network }> = {
  graph_building: { label: 'Synthesizing Graph', icon: Network },
  persona_generation: { label: 'Spawning Personas', icon: Users },
  simulation_running: { label: 'Executing Swarm Logic', icon: Play },
  report_generation: { label: 'Compiling Analysis', icon: TrendingUp },
}

function SharpContainer({ children, title, icon: Icon, color = 'blue', extraHeaderControls = null, className = "" }: any) {
  return (
    <div className={`group relative h-full ${className}`}>
      <div className={`absolute -inset-[1px] bg-gradient-to-br from-${color}-500 to-transparent rounded-lg opacity-0 group-hover:opacity-30 transition-opacity duration-300 blur-sm pointer-events-none`} />
      <div className="relative h-full flex flex-col bg-white/90 backdrop-blur-md border border-slate-200/80 rounded-lg overflow-hidden shadow-sm transition-shadow group-hover:shadow-[0_0_15px_rgba(200,200,210,0.2)] z-10">
        <div className={`absolute top-0 left-0 w-full h-[2px] bg-gradient-to-r from-${color}-500 to-transparent opacity-50`} />
        {title && (
           <div className="px-5 py-3 border-b border-slate-100 flex items-center justify-between bg-white/50">
              <h2 className="text-xs font-black uppercase tracking-widest text-slate-600 flex items-center gap-2">
                 {Icon && <Icon className={`w-4 h-4 text-${color}-500`} />} {title}
              </h2>
              {extraHeaderControls}
           </div>
        )}
        <div className="p-5 flex-1 flex flex-col overflow-hidden">
           {children}
        </div>
      </div>
    </div>
  )
}

function SwarmAgentCard({
  agentType, accentColor, phase, entities, personas, result, isFullscreen, autoExpand = true,
}: {
  agentType: 'brand' | 'market'; accentColor: string; phase: string; entities: string[]; personas: string[]; result: any; isFullscreen?: boolean; autoExpand?: boolean;
}) {
  const [expandedSection, setExpandedSection] = useState<string | null>('prediction')
  const isRunning = ['graph_building', 'persona_generation', 'simulation_running', 'report_generation', 'graph_ready', 'personas_ready'].includes(phase)
  const isComplete = phase === 'completed'
  const isFailed = phase === 'failed'

  useEffect(() => {
    if (autoExpand && isRunning && expandedSection === null) setExpandedSection('prediction')
  }, [autoExpand, isRunning, expandedSection])

  const tailwindColorBase = agentType === 'brand' ? 'pink' : 'orange'

  return (
    <div className={`${isFullscreen ? 'fixed inset-6 z-[100] shadow-2xl flex flex-col' : 'h-full'} `}>
      <SharpContainer 
         title={`Astra Swarm Engine: ${agentType.toUpperCase()} Core`} 
         icon={Star} 
         color={tailwindColorBase}
         extraHeaderControls={
            <div className="flex items-center gap-3">
               {isRunning && <span className={`flex items-center gap-2 px-3 py-1.5 rounded bg-${tailwindColorBase}-50 text-${tailwindColorBase}-700 border border-${tailwindColorBase}-200 text-[10px] font-black uppercase tracking-widest animate-pulse`}><Loader2 className="w-3 h-3 animate-spin inline" /> Computing</span>}
               {isComplete && <span className="text-[10px] font-black text-emerald-700 bg-emerald-50 border border-emerald-200 px-3 py-1.5 rounded uppercase tracking-widest">Sys Complete</span>}
               {isFailed && <span className="text-[10px] font-black text-red-700 bg-red-50 border border-red-200 px-3 py-1.5 rounded uppercase tracking-widest">Sys Failure</span>}
               {isFullscreen ? (
                 <button onClick={() => window.dispatchEvent(new CustomEvent('closeFullscreen', { detail: agentType }))} className="p-1 hover:bg-slate-200 rounded text-slate-500 hover:text-slate-800 transition-colors" title="Minimize">
                   <Minimize2 className="w-4 h-4" />
                 </button>
               ) : (
                 <button onClick={() => window.dispatchEvent(new CustomEvent('openFullscreen', { detail: agentType }))} className={`p-1 hover:bg-${tailwindColorBase}-100 rounded text-${tailwindColorBase}-500 transition-colors`} title="Maximize Data Core">
                   <Maximize2 className="w-4 h-4" />
                 </button>
               )}
            </div>
         }
      >
          <div className={`${isFullscreen ? 'flex-1 overflow-y-auto' : 'h-full flex flex-col'} `}>
             {!isRunning && !isComplete && !isFailed && (
                <div className="flex flex-col items-center justify-center h-full min-h-[300px] text-center border border-dashed border-slate-300 rounded bg-slate-50/50">
                   <Activity className="w-8 h-8 text-slate-300 mb-4" />
                   <p className="text-xs font-black text-slate-500 uppercase tracking-widest">Sub-System Idle</p>
                   <p className="text-[10px] text-slate-400 mt-2 max-w-xs font-bold">Awaiting prompt injection to commence swarm propagation sequence.</p>
                </div>
             )}
             
             {isComplete && result && (
                <div className="space-y-5">
                   {/* Probability Main Bar */}
                   <div className="bg-slate-50 rounded-md p-5 border border-slate-200 shadow-sm relative overflow-hidden flex flex-col justify-center">
                      <div className="absolute top-0 right-0 p-4 opacity-10 select-none pointer-events-none">
                         <BarChart2 className="w-24 h-24" style={{ color: accentColor }} />
                      </div>
                      <div className="relative z-10">
                         <div className="flex items-end justify-between mb-2">
                            <span className="text-xs font-black uppercase tracking-widest text-slate-600">Net Swarm Confidence Rating</span>
                            <span className="text-xs font-black uppercase tracking-widest text-slate-400">Accuracy Probable</span>
                         </div>
                         <div className="flex items-center gap-4 mb-3">
                            <span className="text-5xl font-black text-slate-900 tracking-tighter leading-none">{(result.confidence * 100).toFixed(1)}%</span>
                         </div>
                         <div className="w-full h-2 bg-slate-200 rounded-none overflow-hidden">
                            <motion.div initial={{ width: 0 }} animate={{ width: `${result.confidence * 100}%` }} transition={{ duration: 1.5, ease: 'easeOut' }} className="h-full rounded-none" style={{ background: `linear-gradient(90deg, ${accentColor}, ${accentColor}88)` }} />
                         </div>
                      </div>
                   </div>
                   
                   <div className="space-y-4">
                      {/* Prediction Expandable */}
                      <div className="bg-white rounded-md border border-slate-200 overflow-hidden shadow-sm">
                         <button onClick={() => setExpandedSection(expandedSection === 'prediction' ? null : 'prediction')} className="w-full px-5 py-3 flex items-center justify-between hover:bg-slate-50 transition-colors border-b border-transparent data-[expanded=true]:border-slate-100" data-expanded={expandedSection === 'prediction'}>
                            <div className="flex items-center gap-3">
                               <TrendingUp className="w-4 h-4" style={{ color: accentColor }} />
                               <span className="text-[11px] font-black text-slate-800 uppercase tracking-widest">Synthesized Prediction</span>
                            </div>
                            {expandedSection === 'prediction' ? <ChevronUp className="w-4 h-4 text-slate-400" /> : <ChevronDown className="w-4 h-4 text-slate-400" />}
                         </button>
                         <AnimatePresence>
                            {expandedSection === 'prediction' && (
                               <motion.div initial={{ height: 0 }} animate={{ height: 'auto' }} exit={{ height: 0 }} className="overflow-hidden bg-slate-50 border-t border-slate-100">
                                  <div className="p-5 text-xs text-slate-700 leading-relaxed font-mono">
                                     {result.prediction}
                                  </div>
                               </motion.div>
                            )}
                         </AnimatePresence>
                      </div>
                      
                      {/* Risks Expandable */}
                      {result.risks?.length > 0 && (
                         <div className="bg-white rounded-md border border-slate-200 overflow-hidden shadow-sm">
                            <button onClick={() => setExpandedSection(expandedSection === 'risks' ? null : 'risks')} className="w-full px-5 py-3 flex items-center justify-between hover:bg-slate-50 transition-colors border-b border-transparent data-[expanded=true]:border-slate-100" data-expanded={expandedSection === 'risks'}>
                               <div className="flex items-center gap-3">
                                  <AlertTriangle className="w-4 h-4 text-red-500" />
                                  <span className="text-[11px] font-black text-slate-800 uppercase tracking-widest">Computed Error Vectors ({result.risks.length})</span>
                               </div>
                               {expandedSection === 'risks' ? <ChevronUp className="w-4 h-4 text-slate-400" /> : <ChevronDown className="w-4 h-4 text-slate-400" />}
                            </button>
                            <AnimatePresence>
                               {expandedSection === 'risks' && (
                                  <motion.div initial={{ height: 0 }} animate={{ height: 'auto' }} exit={{ height: 0 }} className="overflow-hidden bg-slate-50 border-t border-slate-100">
                                     <ul className="p-5 space-y-3">
                                        {result.risks.map((r: string, i: number) => (
                                           <li key={i} className="text-xs font-bold text-red-900 flex items-start gap-3 bg-red-50/80 p-3 rounded border border-red-100">
                                              <div className="w-1.5 h-1.5 rounded-none bg-red-500 mt-1.5 shrink-0" />
                                              {r}
                                           </li>
                                        ))}
                                     </ul>
                                  </motion.div>
                               )}
                            </AnimatePresence>
                         </div>
                      )}
                   </div>
                </div>
             )}
          </div>
      </SharpContainer>
    </div>
  )
}

function MiroFishTab() {
  const { mirofishPhase, mirofishBrandResult, mirofishMarketResult, mirofishBrandEntities, mirofishMarketEntities, mirofishBrandPersonas, mirofishMarketPersonas, mirofishBrandPhase, mirofishMarketPhase, mirofishEnabled, currentRound, isStreaming, liteMode } = useCouncilV2Store()
  const [isFullscreenBrand, setIsFullscreenBrand] = useState(false)
  const [isFullscreenMarket, setIsFullscreenMarket] = useState(false)
  const [autoExpand, setAutoExpand] = useState(true)

  const isSwarmActive = mirofishPhase !== 'idle'

  useEffect(() => {
    const handleCloseFullscreen = (e: Event) => {
      const detail = (e as CustomEvent).detail
      if (detail === 'brand') setIsFullscreenBrand(false)
      if (detail === 'market') setIsFullscreenMarket(false)
    }
    const handleOpenFullscreen = (e: Event) => {
      const detail = (e as CustomEvent).detail
      if (detail === 'brand') { setIsFullscreenBrand(true); setIsFullscreenMarket(false); }
      if (detail === 'market') { setIsFullscreenMarket(true); setIsFullscreenBrand(false); }
    }
    window.addEventListener('closeFullscreen', handleCloseFullscreen)
    window.addEventListener('openFullscreen', handleOpenFullscreen)
    return () => {
      window.removeEventListener('closeFullscreen', handleCloseFullscreen)
      window.removeEventListener('openFullscreen', handleOpenFullscreen)
    }
  }, [])

  return (
    <div className="flex-1 min-h-0 flex flex-col pt-1">
      {/* Viewport removed standard Banner and Controls, now handled via Card Headers */}
      <div className={`transition-all duration-500 flex-1 min-h-0 ${isFullscreenBrand || isFullscreenMarket ? 'grid grid-cols-1 gap-3' : 'grid grid-cols-1 lg:grid-cols-2 gap-3'}`}>
         <SwarmAgentCard agentType="brand" accentColor="#EC4899" phase={mirofishBrandPhase} entities={mirofishBrandEntities} personas={mirofishBrandPersonas} result={mirofishBrandResult} isFullscreen={isFullscreenBrand} autoExpand={autoExpand} />
         <SwarmAgentCard agentType="market" accentColor="#F97316" phase={mirofishMarketPhase} entities={mirofishMarketEntities} personas={mirofishMarketPersonas} result={mirofishMarketResult} isFullscreen={isFullscreenMarket} autoExpand={autoExpand} />
      </div>
    </div>
  )
}

export default function SwarmVisualizer() {
  const { runSimulation, stopSimulation, isRunning, isComplete, isFailed, phase } = useMiroFishSwarm()
  const [query, setQuery] = useState('')
  const [horizonDays, setHorizonDays] = useState(30)
  const [numPersonas, setNumPersonas] = useState(50)
  const [rounds, setRounds] = useState(3)

  return (
    <div className="h-[calc(100vh-4rem)] bg-[#f8fafc] p-3 md:p-4 relative overflow-hidden flex flex-col">
      <div className="absolute inset-0 bg-[radial-gradient(#e2e8f0_1px,transparent_1px)] [background-size:20px_20px] opacity-40 pointer-events-none" />
      
      <div className="w-full h-full relative z-10 flex flex-col gap-3">
         
         {/* System Header */}
         <div className="flex flex-col md:flex-row items-end justify-between gap-3 shrink-0 border-b border-slate-200 pb-3">
           <div className="flex items-center gap-3">
             <div className="w-10 h-10 bg-slate-900 text-cyan-400 rounded-md flex items-center justify-center border border-slate-800 shadow-lg shadow-slate-900/20">
                <Star className="w-5 h-5" />
             </div>
             <div>
               <h1 className="text-2xl font-black text-slate-900 tracking-tight leading-none">Astra Swarm Array</h1>
               <div className="flex items-center gap-2 mt-1.5">
                  <div className="w-1.5 h-1.5 rounded-none bg-cyan-500 shadow-[0_0_8px_rgba(34,211,238,0.8)]" />
                  <p className="text-[10px] font-bold uppercase tracking-widest text-slate-500">Stochastic Prediction Engine</p>
               </div>
             </div>
           </div>
         </div>

         {/* Injection Module */}
         <div className="bg-white rounded-md p-3 border border-slate-200 shadow-sm relative z-10 shrink-0">
            <div className="flex flex-col md:flex-row gap-3">
               <div className="relative flex-1 group">
                  <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400 group-focus-within:text-cyan-500 transition-colors" />
                  <input type="text" value={query} onChange={(e) => setQuery(e.target.value)} disabled={isRunning} placeholder="Inject simulation hypothesis query here..." className="w-full pl-9 pr-4 py-2.5 bg-slate-50 border border-slate-300 rounded text-xs font-bold text-slate-800 focus:outline-none focus:border-cyan-500 focus:bg-white transition-all shadow-inner disabled:opacity-50" />
               </div>
               <button onClick={() => !isRunning ? query.trim() && runSimulation(query.trim(), { horizonDays, numPersonas, rounds }) : stopSimulation()} className={`px-6 py-2.5 rounded text-[10px] font-black tracking-widest uppercase shadow-sm transition-all focus:outline-none focus:ring-2 focus:ring-offset-2 flex items-center justify-center min-w-[160px] ${isRunning ? 'bg-red-500 hover:bg-red-600 text-white focus:ring-red-500' : 'bg-slate-900 hover:bg-slate-800 text-white focus:ring-slate-900'}`}>
                  {isRunning ? <><Loader2 className="w-3.5 h-3.5 mr-2 animate-spin" /> Halt System</> : <><Zap className="w-3.5 h-3.5 mr-2" /> Inject Run</>}
               </button>
            </div>
         </div>

         <MiroFishTab />
      </div>
    </div>
  )
}
