import { useState, useMemo } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { 
  Crown, RotateCcw, Users, 
  Zap, BarChart3, MessageSquare, ArrowRight, StopCircle, Star
} from "lucide-react"
import { useCouncilV2Store } from '@/store/councilV2Store'
import { useCouncilV2Stream } from '@/hooks/useCouncilV2Stream'
import { useSettingsStore } from '@/store/settingsStore'
import { AGENTS_CONFIG } from '@/config/agents.config'
import { COUNCIL_AGENTS } from '@/types/council'
import type { AgentInfo } from '@/types/council'
import AgentCard from '@/components/shared/AgentCard'
import RoundTab from '@/components/shared/RoundTab'
import ModelBadge from '@/components/shared/ModelBadge'
import CitedMarkdownRenderer from '@/components/shared/CitedMarkdownRenderer'
import AnimatedList from '@/components/shared/AnimatedList'
import AnimatedSourceLinks from '@/components/shared/AnimatedSourceLinks'
import SourcesPanel from '@/components/shared/SourcesPanel'
import LiteModePanel from '@/components/shared/LiteModePanel'
import { toast } from '@/components/shared/Toast'

const ROUND_CONFIG = [
  {
    number: 1,
    label: "Round 1",
    sublabel: "Individual Analysis",
    icon: BarChart3,
    description: "All 6 agents analyze in parallel"
  },
  {
    number: 2,
    label: "Round 2",
    sublabel: "Council Debate",
    icon: MessageSquare,
    description: "Agents challenge each other's findings"
  },
  {
    number: 3,
    label: "Round 3",
    sublabel: "Final Verdict",
    icon: Crown,
    description: "Moderator synthesizes the decision"
  }
]

export default function Debate() {
  const store = useCouncilV2Store()
  const { 
    currentRound, agents, moderatorR1, moderatorR2,
    supervisorResult, viewMode,
    isStreaming, reset, citationMaps, pipelineStages, discoveredSources,
    liteMode, liteSupportAgents, supportEvidence, evidenceBundle, supportAgentPolicy,
  } = store
  const { settings, updateSettings } = useSettingsStore()

  const { startStream, stopStream } = useCouncilV2Stream()
  const [queryInput, setQueryInput] = useState('')
  const [selectedAgents, setSelectedAgents] = useState<string[]>([])
  const [activeRound, setActiveRound] = useState(currentRound || 1)
  
  // Memoize completed rounds to avoid recreation on every render
  const completedRounds = useMemo(() => {
    const rounds: number[] = []
    if (moderatorR1) rounds.push(1)
    if (moderatorR2) rounds.push(2)
    if (supervisorResult) rounds.push(3)
    return rounds
  }, [moderatorR1, moderatorR2, supervisorResult])

  // Build agentConfidence map from store agents with null safety
  const agentConfidence: Record<string, number> = {}
  const agentOutputs: Record<string, string> = {}
  for (const [key, state] of Object.entries(agents)) {
    const roundKey = activeRound <= 1 ? 'round1' : 'round2'
    // Add null safety check
    if (state && state[roundKey]) {
      agentConfidence[key] = state[roundKey].confidence ?? 0
      agentOutputs[key] = state[roundKey].output ?? ''
    }
  }

  const handleQuerySubmit = (e: React.FormEvent) => {
    e.preventDefault()
    if (!queryInput.trim() || isStreaming) return
    // Use reactive settings from store hook instead of getState()
    const isLite = settings.lite_mode
    const primaryAgent = isLite ? settings.lite_primary_agent : undefined
    const supportAgents = isLite && primaryAgent
      ? COUNCIL_AGENTS.map((a) => a.key).filter((k) => k !== primaryAgent).slice(0, 5)
      : undefined
    startStream(queryInput.trim(), { liteMode: isLite, primaryAgent, supportAgents })
  }

  const handleReset = () => {
    // Trigger fade-out (handled by AnimatePresence on the outer container)
    // and then reset the store
    reset()
    window.scrollTo({ top: 0, behavior: 'smooth' })
    toast('info', "Council Reset: Ready for a new supply chain analysis session.")
  }

  const toggleAgent = (id: string) => {
    if (selectedAgents.includes(id)) {
      setSelectedAgents(selectedAgents.filter(a => a !== id))
    } else {
      setSelectedAgents([...selectedAgents, id])
    }
  }

  const isRound3Complete = completedRounds.includes(3)

  return (
    <div className="flex h-screen bg-council-bg text-white overflow-hidden font-inter">
      {/* LEFT: MAIN DEBATE AREA */}
      <div className="flex-1 flex flex-col min-w-0 relative">
        
        {/* TOP BAR / ROUNDS */}
        <div className="px-8 py-6 border-b border-white/[0.06] bg-council-bg/50 backdrop-blur-md z-20">
          <div className="flex items-center justify-between mb-6">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-indigo-600 to-purple-600 flex items-center justify-center shadow-lg shadow-indigo-500/20">
                <Crown className="w-5 h-5 text-white" />
              </div>
              <div>
                <h1 className="text-2xl font-black tracking-tight font-outfit text-white">Supply Chain Command Center</h1>
                <p className="text-[11px] text-white/40 font-medium uppercase tracking-widest">Real-time market data, risk monitoring & council insights</p>
              </div>
            </div>

            <div className="flex items-center gap-2">
               {ROUND_CONFIG.map((round) => (
                 <RoundTab
                   key={round.number}
                   {...round}
                   isCompleted={completedRounds.includes(round.number)}
                   isActive={activeRound === round.number}
                   isLocked={round.number > 1 && !completedRounds.includes(round.number - 1)}
                   onClick={() => setActiveRound(round.number)}
                 />
               ))}
               {/* Astra ⭐ Swarm Toggle */}
               <button
                 onClick={() => updateSettings({ mirofish_enabled: !settings.mirofish_enabled })}
                 className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-[11px] font-bold uppercase tracking-wider transition-all duration-200 ${
                   settings.mirofish_enabled
                     ? 'bg-gradient-to-r from-cyan-600 to-blue-600 text-white shadow-lg shadow-cyan-500/20'
                     : 'bg-white/[0.06] text-white/40 hover:bg-white/[0.1] hover:text-white/60 border border-white/[0.08]'
                 }`}
                 title="Toggle Astra ⭐ Swarm simulation for Brand & Market agents after 3 rounds"
               >
                 <Star className="w-3.5 h-3.5" />
                 <span>Astra ⭐</span>
                 {store.mirofishPhase !== 'idle' && (
                   <span className={`w-1.5 h-1.5 rounded-full ${store.mirofishPhase === 'completed' ? 'bg-emerald-400' : 'bg-cyan-400 animate-pulse'}`} />
                 )}
               </button>
            </div>
          </div>
        </div>

        {/* PIPELINE STAGES & SOURCES DISCOVERY */}
        {(isStreaming || Object.keys(discoveredSources).length > 0) && (
          <div className="px-8 py-4 bg-white/[0.02] border-b border-white/[0.06]">
            {/* Main stage indicators */}
            <div className="flex items-center gap-2 flex-wrap">
              {Object.entries(pipelineStages).map(([key, stage]) => {
                const icons: Record<string, string> = {
                  rag_fetching: '🔍',
                  api_called: '🌐',
                  mcp_fetched: '🔧',
                  sources_ready: '📚'
                }
                const labels: Record<string, string> = {
                  rag_fetching: 'RAG Knowledge Base',
                  api_called: 'Live APIs',
                  mcp_fetched: 'MCP Tools',
                  sources_ready: 'Sources Ready'
                }
                const isActive = stage.status === 'active'
                const isDone = stage.status === 'done'
                return (
                  <div 
                    key={key}
                    className={`
                      flex items-center gap-2 px-3 py-1.5 rounded-full text-xs font-medium
                      transition-all duration-300
                      ${isDone ? 'bg-emerald-500/20 text-emerald-400 border border-emerald-500/30' : 
                        isActive ? 'bg-indigo-500/20 text-indigo-400 border border-indigo-500/30' : 
                        'bg-white/5 text-white/30 border border-white/10'}
                    `}
                    style={isActive ? { animation: 'pulse 2s infinite' } : {}}
                  >
                    <span>{icons[key]}</span>
                    <span>{labels[key]}</span>
                    {isActive && stage.detail && (
                      <span className="text-white/50">— {stage.detail}</span>
                    )}
                    {isDone && stage.count > 0 && (
                      <span className="ml-1">({stage.count})</span>
                    )}
                    {key !== 'sources_ready' && (
                      <span className="text-white/20 ml-1">→</span>
                    )}
                  </div>
                )
              })}
              
              {/* Animated Source Links - glowing pill container */}
              <div className="ml-2 flex items-center">
                <div className="
                  relative overflow-hidden
                  rounded-full px-4 py-2
                  bg-white/5 border border-indigo-500/40
                  shadow-[0_0_15px_rgba(99,102,241,0.3)]
                ">
                  <AnimatedSourceLinks isActive={isStreaming} />
                </div>
              </div>
            </div>
            
            {/* Live source discovery display with AnimatedList */}
            {Object.keys(discoveredSources).length > 0 && (
              <div className="mt-4 border-t border-white/10 pt-3">
                <div className="flex items-center justify-between mb-2">
                  <span className="text-[10px] text-white/40 uppercase tracking-wider flex items-center gap-2">
                    <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse"></span>
                    Live Source Discovery
                  </span>
                  <span className="text-[10px] text-white/30">
                    {Object.values(discoveredSources).flat().length} sources found
                  </span>
                </div>
                <AnimatedList
                  items={Object.entries(discoveredSources).flatMap(([agent, sources]) => {
                    const agentInfo = COUNCIL_AGENTS.find(a => a.key === agent)
                    return sources.map(src => ({
                      num: src.num,
                      title: src.title,
                      url: src.url,
                      agent: agent,
                      agentColor: agentInfo?.hexColor || '#666'
                    }))
                  })}
                  maxHeight="200px"
                />
              </div>
            )}
          </div>
        )}

        {/* ASTRA ⭐ SWARM PHASE INDICATOR */}
        {store.mirofishPhase !== 'idle' && (
          <div className="px-8 py-3 bg-gradient-to-r from-cyan-900/20 to-blue-900/20 border-b border-cyan-500/10">
            <div className="flex items-center gap-3">
              <Star className="w-4 h-4 text-cyan-400" />
              <span className="text-[11px] font-bold uppercase tracking-wider text-cyan-300">
                Astra ⭐ Swarm
              </span>
              <div className="flex items-center gap-2">
                {['graph_building', 'persona_generation', 'simulation_running', 'report_generation'].map((phase) => {
                  const phaseLabels: Record<string, string> = {
                    graph_building: 'Graph',
                    persona_generation: 'Personas',
                    simulation_running: 'Simulation',
                    report_generation: 'Report',
                  }
                  const isPhaseActive = store.mirofishBrandPhase === phase || store.mirofishMarketPhase === phase
                  const isPhaseDone = ['graph_ready', 'personas_ready', 'completed'].includes(store.mirofishBrandPhase) &&
                    ['graph_building', 'persona_generation', 'simulation_running', 'report_generation'].indexOf(phase) <
                    ['graph_building', 'persona_generation', 'simulation_running', 'report_generation'].indexOf(
                      store.mirofishBrandPhase === 'graph_ready' ? 'persona_generation' :
                      store.mirofishBrandPhase === 'personas_ready' ? 'simulation_running' :
                      store.mirofishBrandPhase === 'completed' ? 'report_generation' : store.mirofishBrandPhase
                    )
                  return (
                    <div
                      key={phase}
                      className={`flex items-center gap-1 px-2 py-0.5 rounded-full text-[9px] font-bold transition-all ${
                        isPhaseActive ? 'bg-cyan-500/30 text-cyan-300 animate-pulse' :
                        isPhaseDone ? 'bg-emerald-500/20 text-emerald-400' :
                        'bg-white/5 text-white/20'
                      }`}
                    >
                      {phaseLabels[phase]}
                    </div>
                  )
                })}
              </div>
              {store.mirofishPhase === 'completed' && (
                <span className="text-[10px] font-bold text-emerald-400 bg-emerald-500/20 px-2 py-0.5 rounded-full ml-auto">
                  Swarm Complete — View in Swarm Visualizer
                </span>
              )}
              {store.mirofishPhase !== 'completed' && (
                <span className="text-[10px] text-cyan-400/60 ml-auto">
                  Brand & Market agents running multi-persona simulation...
                </span>
              )}
            </div>
          </div>
        )}

        {/* CHAT CONTENT */}
        <div className="flex-1 overflow-y-auto px-8 py-8 scrollbar-thin scrollbar-thumb-white/10">
          <AnimatePresence mode="wait">
            {!isStreaming && completedRounds.length === 0 ? (
              <motion.div 
                key="initial-state"
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -20 }}
                className="max-w-2xl mx-auto mt-20 text-center"
              >
                <div className="inline-flex p-4 rounded-3xl bg-indigo-500/10 border border-indigo-500/20 mb-6">
                  <Zap className="w-8 h-8 text-indigo-400" />
                </div>
                <h2 className="text-3xl font-bold font-poppins mb-4 text-gradient-indigo">Activate the Council</h2>
                <p className="text-white/50 leading-relaxed mb-10">
                  Ask a complex supply chain question. Six specialized experts will analyze, debate, and synthesize a data-driven path forward.
                </p>
                
                <form onSubmit={handleQuerySubmit} className="relative group">
                  {/* Lite Mode Toggle */}
                  <div className="mb-4 rounded-xl border border-white/10 bg-white/[0.03] p-3">
                    <div className="flex items-center justify-between gap-3">
                      <div className="flex items-center gap-2">
                        <Zap className="w-4 h-4 text-violet-400" />
                        <span className="text-sm text-white/60 font-medium">Lite Mode</span>
                        <span className="text-[10px] text-white/30">1 primary + 5 support</span>
                      </div>
                      <button
                        type="button"
                        onClick={() => updateSettings({ lite_mode: !settings.lite_mode })}
                        className={`relative w-10 h-5 rounded-full transition-colors duration-200 ${settings.lite_mode ? 'bg-violet-600' : 'bg-white/10'}`}
                      >
                        <span className={`absolute top-0.5 left-0.5 w-4 h-4 bg-white rounded-full shadow transition-transform duration-200 ${settings.lite_mode ? 'translate-x-5' : 'translate-x-0'}`} />
                      </button>
                    </div>
                    {settings.lite_mode && (
                      <div className="mt-3 flex flex-wrap gap-1.5">
                        {COUNCIL_AGENTS.map((agent) => {
                          const isActive = settings.lite_primary_agent === agent.key
                          return (
                            <button
                              key={agent.key}
                              type="button"
                              onClick={() => updateSettings({ lite_primary_agent: agent.key })}
                              className={`px-2.5 py-1 rounded-full text-[10px] font-bold border transition-all ${isActive ? 'text-white border-transparent' : 'bg-white/5 text-white/40 border-white/10 hover:border-white/20'}`}
                              style={isActive ? { backgroundColor: agent.hexColor, borderColor: agent.hexColor } : undefined}
                            >
                              {agent.label}
                            </button>
                          )
                        })}
                      </div>
                    )}
                  </div>
                  <input
                    type="text"
                    value={queryInput}
                    onChange={(e) => setQueryInput(e.target.value)}
                    placeholder="Analyze the impact of Red Sea disruptions on electronics OEMs..."
                    className="w-full bg-white/[0.03] border border-white/10 rounded-2xl px-6 py-5 pr-16 text-lg focus:outline-none focus:border-indigo-500/50 focus:bg-white/[0.05] transition-all"
                  />
                  <button 
                    type="submit"
                    className="absolute right-3 top-3 bottom-3 px-4 bg-indigo-600 rounded-xl hover:bg-indigo-500 transition-colors shadow-lg shadow-indigo-900/40"
                  >
                    <ArrowRight className="w-5 h-5" />
                  </button>
                </form>
              </motion.div>
            ) : (
              <motion.div
                key="active-debate"
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                className="space-y-6 max-w-4xl mx-auto"
              >
                {/* LITE MODE PANEL */}
                {liteMode && (() => {
                  const primaryAgentKey = settings.lite_primary_agent || 'risk'
                  const primaryInfo = (COUNCIL_AGENTS.find((a) => a.key === primaryAgentKey) ?? COUNCIL_AGENTS[0]) as AgentInfo
                  const supportKeys = liteSupportAgents.length
                    ? liteSupportAgents
                    : COUNCIL_AGENTS.map((a) => a.key).filter((k) => k !== primaryInfo.key).slice(0, 5)
                  return (
                    <LiteModePanel
                      primaryAgentInfo={primaryInfo}
                      supportAgentKeys={supportKeys}
                      agents={agents}
                      discoveredSources={discoveredSources}
                      isStreaming={isStreaming}
                      supportEvidence={supportEvidence}
                      evidenceBundle={evidenceBundle}
                      citationMaps={citationMaps}
                      pipelineStages={pipelineStages}
                      supportAgentPolicy={supportAgentPolicy}
                      subagentEvidence={store.subagentEvidence}
                      activeSubagents={store.activeSubagents}
                    />
                  )
                })()}

                {/* AGENT OUTPUTS FOR CURRENT ROUND (full council only) */}
                {!liteMode && (
                <div className="grid grid-cols-1 gap-6">
                  {COUNCIL_AGENTS.map((agentInfo) => {
                    const agentState = agents[agentInfo.key]
                    if (!agentState) return null
                    const roundKey = activeRound <= 1 ? 'round1' : 'round2'
                    const roundState = agentState?.[roundKey]
                    if (!roundState) return null
                    const content = roundState.output
                    if (!content && roundState.status === 'idle') return null
                    const config = AGENTS_CONFIG.find(a => a.id === agentInfo.key)
                    if (!config) return null
                    
                    return (
                      <motion.div
                        layout
                        key={agentInfo.key}
                        initial={{ opacity: 0, scale: 0.95, y: 20 }}
                        animate={{ opacity: 1, scale: 1, y: 0 }}
                        className="glass-premium p-8 rounded-[2rem] relative overflow-hidden group"
                        style={{ 
                          borderColor: `${agentInfo.hexColor}30`,
                        }}
                      >
                         {/* TOP ACCENT BLOOM */}
                         <div className="absolute -top-24 -right-24 w-48 h-48 rounded-full blur-[80px] opacity-10 transition-opacity group-hover:opacity-20"
                              style={{ backgroundColor: agentInfo.hexColor }} />
                         
                         <div className="relative z-10">
                           <div className="flex items-start justify-between mb-8">
                             <div className="flex items-center gap-4">
                               <div className="w-14 h-14 rounded-2xl flex items-center justify-center border border-white/10 shadow-lg shadow-black/20"
                                    style={{ 
                                      background: `linear-gradient(135deg, ${agentInfo.hexColor}30 0%, ${agentInfo.hexColor}10 100%)`,
                                      borderColor: `${agentInfo.hexColor}40`
                                    }}>
                                 <span className="text-2xl drop-shadow-md">{config.emoji}</span>
                               </div>
                               <div>
                                 <h3 className="font-extrabold font-outfit text-2xl tracking-tight text-white mb-0.5">
                                   {agentInfo.label}
                                 </h3>
                                 <div className="flex items-center gap-2">
                                   <span className="text-[10px] text-white/30 uppercase tracking-[0.2em] font-bold">
                                     Round {activeRound} • {roundState.status === 'thinking' ? 'Processing...' : roundState.status === 'done' ? 'Complete' : roundState.status}
                                   </span>
                                   <div className="w-1 h-1 rounded-full bg-white/20" />
                                   <span className="text-[10px] font-bold" style={{ color: agentInfo.hexColor }}>
                                      {config.role.split('+')[0]?.trim() ?? config.role}
                                   </span>
                                 </div>
                               </div>
                             </div>

                             <div className="flex flex-col items-end gap-2">
                                {roundState.confidence > 0 && (
                                  <div className="px-3 py-1 rounded-full bg-white/5 border border-white/10 flex items-center gap-2 backdrop-blur-md">
                                    <div className="w-1.5 h-1.5 rounded-full animate-pulse shadow-[0_0_8px_rgba(255,255,255,0.5)]" style={{ backgroundColor: agentInfo.hexColor }} />
                                    <span className="text-xs font-black font-outfit" style={{ color: agentInfo.hexColor }}>
                                      {roundState.confidence}%
                                    </span>
                                  </div>
                                )}
                                <ModelBadge 
                                  model={config.model} 
                                  modelProvider={config.modelProvider} 
                                  modelColor={config.modelColor} 
                                  modelIcon={config.modelIcon} 
                                />
                             </div>
                           </div>

<div className="prose prose-invert max-w-none 
                                           text-white/80 leading-relaxed text-[15px] font-medium font-inter
                                           prose-headings:font-outfit prose-headings:text-white prose-headings:font-bold
                                           prose-strong:text-white prose-strong:font-bold prose-strong:font-outfit
                                           prose-p:mb-6 prose-li:mb-2
                                           selection:bg-white/10">
                              <CitedMarkdownRenderer 
                                content={content} 
                                urlMap={citationMaps[agentInfo.key] || {}} 
                                accentColor={agentInfo.hexColor}
                              />
                            </div>

                           {/* SOURCES & REFERENCES PANEL */}
                           <div className="mt-4">
                             <SourcesPanel
                               sources={Object.entries(discoveredSources).flatMap(([agent, srcs]) => {
                                 if (agent !== agentInfo.key) return []
                                 return srcs.map(src => ({
                                   num: src.num,
                                   title: src.title,
                                   url: src.url,
                                   agent: agent,
                                   agentColor: agentInfo.hexColor,
                                 }))
                               })}
                               citationMap={citationMaps[agentInfo.key] || {}}
                               accentColor={agentInfo.hexColor}
                             />
                           </div>

                           {/* DECORATIVE BOTTOM LINE */}
                           <div className="mt-8 h-[1px] w-full bg-gradient-to-r from-transparent via-white/10 to-transparent" />
                         </div>
                      </motion.div>
                    )
                  })}
                </div>
                )}

                {/* SUPERVISOR VERDICT (full council only) */}
                {!liteMode && supervisorResult && viewMode === 'supervisor' && (
                  <motion.div
                    initial={{ opacity: 0, scale: 0.95 }}
                    animate={{ opacity: 1, scale: 1 }}
                    className="glass-premium p-8 rounded-[2rem] border-emerald-500/30 relative overflow-hidden"
                  >
                    <div className="flex items-center gap-4 mb-6">
                      <div className="w-12 h-12 rounded-2xl bg-emerald-500/20 flex items-center justify-center">
                        <Crown className="w-6 h-6 text-emerald-400" />
                      </div>
                      <div>
                        <h3 className="font-extrabold text-xl text-white">Supervisor — Final Verdict</h3>
                        <span className="text-[10px] text-emerald-400/60 uppercase tracking-widest">Round 3</span>
                      </div>
                      <div className="ml-auto px-4 py-2 rounded-full bg-emerald-500/10 border border-emerald-500/20">
                        <span className="text-sm font-black text-emerald-400">{supervisorResult.confidence}%</span>
                      </div>
                    </div>
                    <div className="prose prose-invert max-w-none text-white/80">
                      <CitedMarkdownRenderer 
                        content={supervisorResult.output} 
                        urlMap={citationMaps['supervisor'] || {}}
                        accentColor="#10b981"
                      />
                    </div>

                    {/* Supervisor Sources & References */}
                    <div className="mt-4">
                      <SourcesPanel
                        sources={Object.entries(discoveredSources).flatMap(([agent, srcs]) => {
                          if (agent !== 'supervisor') return []
                          return srcs.map(src => ({
                            num: src.num,
                            title: src.title,
                            url: src.url,
                            agent: 'supervisor',
                            agentColor: '#10b981',
                          }))
                        })}
                        citationMap={citationMaps['supervisor'] || {}}
                        accentColor="#10b981"
                      />
                    </div>
                  </motion.div>
                )}

                {/* FINAL RECOMMENDATION / RESET BUTTON */}
                {isRound3Complete && (
                  <motion.div
                    initial={{ opacity: 0, scale: 0.8 }}
                    animate={{ opacity: 1, scale: 1 }}
                    transition={{ duration: 0.6, delay: 0.8, type: "spring" }}
                    className="flex justify-center py-10"
                  >
                    <button 
                      onClick={handleReset}
                      className="
                        group relative flex items-center gap-3 px-8 py-4
                        rounded-2xl font-semibold text-base tracking-wide
                        bg-gradient-to-r from-indigo-600/20 to-purple-600/20
                        hover:from-indigo-600/40 hover:to-purple-600/40
                        border border-indigo-500/30 hover:border-indigo-400/60
                        backdrop-filter backdrop-blur-xl
                        text-indigo-300 hover:text-white
                        shadow-lg shadow-indigo-900/30
                        hover:shadow-indigo-500/20 hover:shadow-xl
                        transition-all duration-300 ease-in-out
                        hover:scale-105 active:scale-95
                      "
                    >
                      <RotateCcw className="w-5 h-5 group-hover:rotate-180 transition-transform duration-500" />
                      Start New Council Session
                      <span className="absolute -top-2 -right-2 flex h-4 w-4">
                        <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-indigo-400 opacity-75"></span>
                        <span className="relative inline-flex rounded-full h-4 w-4 bg-indigo-500"></span>
                      </span>
                    </button>
                  </motion.div>
                )}
              </motion.div>
            )}
          </AnimatePresence>
        </div>

        {/* STOP BUTTON OVERLAY */}
        {isStreaming && (
          <div className="absolute bottom-8 left-1/2 -translate-x-1/2 z-30">
             <button 
               onClick={stopStream}
               className="flex items-center gap-2 px-6 py-3 bg-red-500/10 border border-red-500/30 rounded-full text-red-400 hover:bg-red-500/20 transition-all backdrop-blur-md"
             >
               <StopCircle className="w-4 h-4" />
               Halt Council Operation
             </button>
          </div>
        )}
      </div>

      {/* RIGHT: AGENTS SELECTION PANEL */}
      <div className="w-[320px] bg-council-surface border-l border-white/[0.06] flex flex-col z-20">
        
        {/* PANEL HEADER */}
        <div className="px-4 pt-5 pb-3 border-b border-white/[0.06]">
          <div className="flex items-center gap-2 mb-1">
            <div className="w-7 h-7 rounded-lg bg-indigo-500/20 border border-indigo-500/30 flex items-center justify-center">
              <Users className="w-3.5 h-3.5 text-indigo-400" />
            </div>
            <h2 className="text-[17px] font-bold tracking-tight font-poppins text-gradient-indigo">
              Council Agents
            </h2>
          </div>
          <p className="text-[11px] text-white/35 font-medium tracking-wide pl-9 font-inter">
            6 Specialized AI Experts • Select to focus
          </p>

          <div className="flex items-center gap-2 mt-2.5 pl-9">
            <div className="flex -space-x-1">
              {selectedAgents.slice(0,3).map(id => (
                <div key={id} className="w-4 h-4 rounded-full border border-indigo-500/50 bg-indigo-500/20 flex items-center justify-center text-[7px]">
                  {AGENTS_CONFIG.find(a => a.id === id)?.emoji}
                </div>
              ))}
            </div>
            {selectedAgents.length > 0 && (
              <span className="text-[10px] text-indigo-400 font-semibold">
                {selectedAgents.length} active
              </span>
            )}
          </div>

          <div className="mt-3 flex gap-1">
            {[1, 2, 3].map(round => (
              <div
                key={round}
                className="flex-1 h-0.5 rounded-full transition-all duration-500"
                style={{
                  background: completedRounds.includes(round)
                    ? "linear-gradient(90deg, #6366f1, #a855f7)"
                    : activeRound === round
                    ? "rgba(99, 102, 241, 0.4)"
                    : "rgba(255,255,255,0.08)"
                }}
              />
            ))}
          </div>
          <div className="flex justify-between mt-1 px-0.5">
            {["Analysis", "Debate", "Verdict"].map((label, i) => (
              <span key={label} className="text-[8px] tracking-wider uppercase"
                style={{
                  color: completedRounds.includes(i+1) ? "#818cf8" : "rgba(255,255,255,0.25)"
                }}
              >
                {label}
              </span>
            ))}
          </div>
        </div>

        {/* AGENT LIST */}
        <div className="flex-1 overflow-y-auto px-3 py-3 space-y-2.5 scrollbar-thin scrollbar-thumb-white/10 hover:scrollbar-thumb-indigo-500/30">
          <AnimatePresence mode="popLayout">
                {AGENTS_CONFIG.filter(a => a.id !== 'moderator').map(agent => (
              <AgentCard
                key={agent.id}
                agent={agent}
                isSelected={selectedAgents.includes(agent.id)}
                agentConfidence={agentConfidence}
                handleSelectAgent={toggleAgent}
              />
            ))}
          </AnimatePresence>
        </div>

        {/* PANEL FOOTER */}
        <div className="px-4 py-3 border-t border-white/[0.06]">
          <div className="flex items-center justify-center gap-1.5 text-[9px] uppercase tracking-widest text-white/20 font-semibold">
            <Zap className="w-2.5 h-2.5 text-indigo-500/50" />
            Powered by LangGraph + AWS Bedrock
            <Zap className="w-2.5 h-2.5 text-indigo-500/50" />
          </div>
        </div>
      </div>
    </div>
  )
}
