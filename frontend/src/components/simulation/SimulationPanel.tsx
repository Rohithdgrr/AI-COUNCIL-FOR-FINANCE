import { useState } from 'react'
import { Play, Loader2, Users, Network, AlertTriangle, TrendingUp, Lightbulb, MessageSquare, ChevronDown, ChevronUp, X } from 'lucide-react'
import { useSimulationStore } from '@/store/simulationStore'
import CitedMarkdownRenderer from '@/components/shared/CitedMarkdownRenderer'
import ConfidenceBadge from '@/components/shared/ConfidenceBadge'

interface SimulationPanelProps {
  agentType: 'brand' | 'market'
  accentColor?: string
  onClose?: () => void
}

export default function SimulationPanel({ agentType, accentColor = '#3b82f6', onClose }: SimulationPanelProps) {
  const [query, setQuery] = useState('')
  const [showChat, setShowChat] = useState(false)
  const [chatInput, setChatInput] = useState('')
  const [expandedSection, setExpandedSection] = useState<string | null>('prediction')

  const {
    activeSimulation: sim,
    simulationPhase: phase,
    simulationEntities: entities,
    simulationPersonas: personas,
    startSimulation,
    chatWithSimulation,
    chatHistory,
    reset,
  } = useSimulationStore()

  const isRunning = ['graph_building', 'persona_generation', 'simulation_running', 'report_generation'].includes(phase)
  const isComplete = phase === 'completed'
  const isFailed = phase === 'failed'

  const handleRun = () => {
    if (!query.trim()) return
    startSimulation(query, agentType)
  }

  const handleChat = () => {
    if (!chatInput.trim()) return
    chatWithSimulation(chatInput)
    setChatInput('')
  }

  const phaseLabels: Record<string, { label: string; icon: typeof Network }> = {
    graph_building: { label: 'Building Knowledge Graph', icon: Network },
    persona_generation: { label: 'Generating Personas', icon: Users },
    simulation_running: { label: 'Running Simulation', icon: Play },
    report_generation: { label: 'Generating Report', icon: TrendingUp },
  }

  return (
    <div className="rounded-2xl border bg-white shadow-sm overflow-hidden" style={{ borderColor: `${accentColor}30` }}>
      {/* Header */}
      <div className="flex items-center justify-between px-4 py-3 border-b" style={{ borderColor: `${accentColor}20`, background: `linear-gradient(135deg, ${accentColor}05 0%, ${accentColor}02 100%)` }}>
        <div className="flex items-center gap-2">
          <div className="w-2 h-2 rounded-full" style={{ backgroundColor: accentColor }} />
          <span className="text-xs font-bold uppercase tracking-wider" style={{ color: accentColor }}>
            MiroFish Simulation
          </span>
          <span className="text-[10px] text-gray-400 font-medium">
            ({agentType} agent)
          </span>
        </div>
        {onClose && (
          <button onClick={onClose} className="p-1 rounded-lg hover:bg-gray-100 text-gray-400 hover:text-gray-600">
            <X className="w-4 h-4" />
          </button>
        )}
      </div>

      <div className="p-4">
        {/* Input area (when not running/complete) */}
        {!isRunning && !isComplete && (
          <div className="space-y-3">
            <textarea
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              placeholder={`Ask a "what if" scenario for ${agentType}... e.g. "If a competitor launches a negative campaign, how does sentiment evolve?"`}
              className="w-full bg-gray-50 border border-gray-200 rounded-xl px-4 py-3 text-sm text-gray-900 placeholder:text-gray-400 focus:outline-none focus:ring-2 resize-none min-h-[80px]"
              rows={3}
            />
            <button
              onClick={handleRun}
              disabled={!query.trim()}
              className="flex items-center gap-2 px-4 py-2 rounded-xl text-white text-xs font-bold transition-all shadow-sm disabled:opacity-40"
              style={{ background: accentColor }}
            >
              <Play className="w-3.5 h-3.5" />
              Run Simulation
            </button>
          </div>
        )}

        {/* Progress indicator */}
        {isRunning && (
          <div className="space-y-3">
            <div className="flex items-center gap-3">
              <Loader2 className="w-5 h-5 animate-spin" style={{ color: accentColor }} />
              <div>
                <p className="text-sm font-semibold text-gray-900">
                  {phaseLabels[phase]?.label || 'Processing...'}
                </p>
                <p className="text-[10px] text-gray-400">This may take 30-60 seconds</p>
              </div>
            </div>

            {/* Phase progress bar */}
            <div className="space-y-2">
              {Object.entries(phaseLabels).map(([key, { label }]) => (
                <div key={key} className="flex items-center gap-2">
                  <div className={`w-2 h-2 rounded-full transition-colors ${phase === key ? 'animate-pulse' : ''}`}
                       style={{ backgroundColor: phase === key ? accentColor : key === 'graph_building' && phase !== 'graph_building' ? '#22c55e' : '#d1d5db' }} />
                  <span className={`text-[10px] font-medium ${phase === key ? 'text-gray-900' : 'text-gray-400'}`}>
                    {label}
                  </span>
                </div>
              ))}
            </div>

            {/* Entities discovered */}
            {entities.length > 0 && (
              <div className="mt-3">
                <p className="text-[10px] font-bold uppercase tracking-wider text-gray-400 mb-1">Entities ({entities.length})</p>
                <div className="flex flex-wrap gap-1">
                  {entities.map((e, i) => (
                    <span key={i} className="px-2 py-0.5 rounded-md text-[10px] font-medium bg-gray-50 border border-gray-100 text-gray-600">
                      {e}
                    </span>
                  ))}
                </div>
              </div>
            )}

            {/* Personas generated */}
            {personas.length > 0 && (
              <div className="mt-3">
                <p className="text-[10px] font-bold uppercase tracking-wider text-gray-400 mb-1">Personas ({personas.length})</p>
                <div className="flex flex-wrap gap-1">
                  {personas.map((p, i) => (
                    <span key={i} className="px-2 py-0.5 rounded-md text-[10px] font-medium border" style={{ borderColor: `${accentColor}30`, color: accentColor, background: `${accentColor}08` }}>
                      {p}
                    </span>
                  ))}
                </div>
              </div>
            )}

            <button onClick={reset} className="text-[10px] text-gray-400 hover:text-gray-600 mt-2">Cancel</button>
          </div>
        )}

        {/* Results */}
        {isComplete && sim?.result && (
          <div className="space-y-4">
            {/* Prediction */}
            <div>
              <button onClick={() => setExpandedSection(expandedSection === 'prediction' ? null : 'prediction')}
                      className="flex items-center justify-between w-full text-left">
                <div className="flex items-center gap-2">
                  <TrendingUp className="w-4 h-4" style={{ color: accentColor }} />
                  <span className="text-sm font-bold text-gray-900">Prediction</span>
                  <ConfidenceBadge confidence={sim.result.confidence * 100} />
                </div>
                {expandedSection === 'prediction' ? <ChevronUp className="w-4 h-4 text-gray-400" /> : <ChevronDown className="w-4 h-4 text-gray-400" />}
              </button>
              {expandedSection === 'prediction' && (
                <div className="mt-2 pl-6">
                  <CitedMarkdownRenderer content={sim.result.prediction} accentColor={accentColor} />
                </div>
              )}
            </div>

            {/* Key Factors */}
            {sim.result.key_factors.length > 0 && (
              <div>
                <button onClick={() => setExpandedSection(expandedSection === 'factors' ? null : 'factors')}
                        className="flex items-center justify-between w-full text-left">
                  <div className="flex items-center gap-2">
                    <Lightbulb className="w-4 h-4 text-amber-500" />
                    <span className="text-sm font-bold text-gray-900">Key Factors ({sim.result.key_factors.length})</span>
                  </div>
                  {expandedSection === 'factors' ? <ChevronUp className="w-4 h-4 text-gray-400" /> : <ChevronDown className="w-4 h-4 text-gray-400" />}
                </button>
                {expandedSection === 'factors' && (
                  <ul className="mt-2 pl-6 space-y-1">
                    {sim.result.key_factors.map((f, i) => (
                      <li key={i} className="text-sm text-gray-700 flex items-start gap-2">
                        <span className="w-1.5 h-1.5 rounded-full mt-1.5 shrink-0" style={{ backgroundColor: accentColor }} />
                        {f}
                      </li>
                    ))}
                  </ul>
                )}
              </div>
            )}

            {/* Risks */}
            {sim.result.risks.length > 0 && (
              <div>
                <button onClick={() => setExpandedSection(expandedSection === 'risks' ? null : 'risks')}
                        className="flex items-center justify-between w-full text-left">
                  <div className="flex items-center gap-2">
                    <AlertTriangle className="w-4 h-4 text-red-500" />
                    <span className="text-sm font-bold text-gray-900">Risks ({sim.result.risks.length})</span>
                  </div>
                  {expandedSection === 'risks' ? <ChevronUp className="w-4 h-4 text-gray-400" /> : <ChevronDown className="w-4 h-4 text-gray-400" />}
                </button>
                {expandedSection === 'risks' && (
                  <ul className="mt-2 pl-6 space-y-1">
                    {sim.result.risks.map((r, i) => (
                      <li key={i} className="text-sm text-red-700 flex items-start gap-2">
                        <span className="w-1.5 h-1.5 rounded-full bg-red-400 mt-1.5 shrink-0" />
                        {r}
                      </li>
                    ))}
                  </ul>
                )}
              </div>
            )}

            {/* Recommendations */}
            {sim.result.recommendations.length > 0 && (
              <div>
                <button onClick={() => setExpandedSection(expandedSection === 'recs' ? null : 'recs')}
                        className="flex items-center justify-between w-full text-left">
                  <div className="flex items-center gap-2">
                    <Lightbulb className="w-4 h-4 text-green-500" />
                    <span className="text-sm font-bold text-gray-900">Recommendations ({sim.result.recommendations.length})</span>
                  </div>
                  {expandedSection === 'recs' ? <ChevronUp className="w-4 h-4 text-gray-400" /> : <ChevronDown className="w-4 h-4 text-gray-400" />}
                </button>
                {expandedSection === 'recs' && (
                  <ul className="mt-2 pl-6 space-y-1">
                    {sim.result.recommendations.map((r, i) => (
                      <li key={i} className="text-sm text-green-700 flex items-start gap-2">
                        <span className="w-1.5 h-1.5 rounded-full bg-green-400 mt-1.5 shrink-0" />
                        {r}
                      </li>
                    ))}
                  </ul>
                )}
              </div>
            )}

            {/* Chat with simulation */}
            <div className="border-t border-gray-100 pt-3">
              <button onClick={() => setShowChat(!showChat)}
                      className="flex items-center gap-2 text-xs font-bold" style={{ color: accentColor }}>
                <MessageSquare className="w-3.5 h-3.5" />
                {showChat ? 'Hide Chat' : 'Chat with Simulation'}
              </button>

              {showChat && (
                <div className="mt-3 space-y-2">
                  {chatHistory.map((msg, i) => (
                    <div key={i} className={`text-sm p-2 rounded-lg ${msg.role === 'user' ? 'bg-gray-50 text-gray-700' : 'bg-blue-50 text-gray-800'}`}>
                      <span className="text-[10px] font-bold uppercase text-gray-400 mr-2">{msg.role}</span>
                      {msg.content}
                    </div>
                  ))}
                  <div className="flex gap-2">
                    <input
                      value={chatInput}
                      onChange={(e) => setChatInput(e.target.value)}
                      onKeyDown={(e) => e.key === 'Enter' && handleChat()}
                      placeholder="Ask a follow-up question..."
                      className="flex-1 bg-gray-50 border border-gray-200 rounded-lg px-3 py-1.5 text-xs focus:outline-none focus:ring-1 focus:ring-blue-300"
                    />
                    <button onClick={handleChat} className="px-3 py-1.5 rounded-lg text-white text-xs font-bold" style={{ background: accentColor }}>
                      Ask
                    </button>
                  </div>
                </div>
              )}
            </div>

            {/* Reset */}
            <button onClick={reset} className="text-[10px] text-gray-400 hover:text-gray-600">
              Run New Simulation
            </button>
          </div>
        )}

        {/* Failed */}
        {isFailed && (
          <div className="text-center py-4">
            <AlertTriangle className="w-8 h-8 text-red-400 mx-auto mb-2" />
            <p className="text-sm text-red-600 font-medium">Simulation failed</p>
            <button onClick={reset} className="text-xs text-gray-400 hover:text-gray-600 mt-2">Try Again</button>
          </div>
        )}
      </div>
    </div>
  )
}
