import { useState } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import {
  Fish, BookOpen, Search, Upload, Loader2, AlertCircle, FileText, Database, BarChart3, Link as LinkIcon,
  Network, Users, Play, TrendingUp, AlertTriangle, Lightbulb, ChevronDown, ChevronUp, Zap
} from 'lucide-react'
import { useRAGQuery, useRAGStats, useRAGCollections } from '@/hooks/useRAGQuery'
import { ragApi } from '@/lib/api'
import type { RAGResponse, Citation } from '@/types/rag'
import { useCouncilV2Store } from '@/store/councilV2Store'
import ConfidenceBadge from '@/components/shared/ConfidenceBadge'

// ── RAG Tab Components ──────────────────────────────────────────────────────────

function CitationCard({ citation, index }: { citation: Citation; index: number }) {
  return (
    <div className="border border-gray-200 rounded-xl p-4 bg-white space-y-2">
      <div className="flex items-center justify-between">
        <span className="text-xs font-bold text-gray-400">#{index + 1}</span>
        <div className="flex items-center gap-2">
          <span className="text-[10px] font-semibold text-gray-500">{citation.source}</span>
          <span className="text-[10px] font-bold px-2 py-0.5 rounded-full bg-blue-50 text-blue-600">
            {(citation.score * 100).toFixed(1)}%
          </span>
        </div>
      </div>
      <p className="text-sm text-gray-700 leading-relaxed line-clamp-4">{citation.content}</p>
      {citation.metadata && Object.keys(citation.metadata).length > 0 && (
        <div className="text-[10px] text-gray-400 font-mono overflow-x-auto">
          {Object.entries(citation.metadata).map(([k, v]) => (
            <span key={k} className="mr-3">{k}: {String(v)}</span>
          ))}
        </div>
      )}
    </div>
  )
}

function RAGTab() {
  const [query, setQuery] = useState('')
  const [mode, setMode] = useState<'standard' | 'hybrid' | 'graph'>('hybrid')
  const [topK, setTopK] = useState(5)
  const [result, setResult] = useState<RAGResponse | null>(null)
  const [queryError, setQueryError] = useState<string | null>(null)

  const ragMutation = useRAGQuery()
  const { data: stats, isLoading: statsLoading } = useRAGStats()
  const { data: collectionsData, isLoading: collLoading } = useRAGCollections()

  const [uploading, setUploading] = useState(false)
  const [uploadUrl, setUploadUrl] = useState('')
  const [uploadMsg, setUploadMsg] = useState<string | null>(null)

  const handleQuery = async () => {
    if (!query.trim()) return
    setQueryError(null)
    setResult(null)
    try {
      const res = await ragMutation.mutateAsync({ query: query.trim(), mode, topK })
      setResult(res as RAGResponse)
    } catch (err: unknown) {
      setQueryError(err instanceof Error ? err.message : 'Query failed')
    }
  }

  const handleUploadUrl = async () => {
    if (!uploadUrl.trim()) return
    setUploading(true)
    setUploadMsg(null)
    try {
      await ragApi.uploadUrl(uploadUrl.trim())
      setUploadMsg('URL ingested successfully')
      setUploadUrl('')
    } catch {
      setUploadMsg('Upload failed')
    } finally {
      setUploading(false)
    }
  }

  const collections = (collectionsData as { collections?: { name: string; document_count?: number }[] })?.collections || []

  return (
    <div className="space-y-6">
      {/* Stats Row */}
      <div className="grid grid-cols-3 gap-4">
        <div className="bg-white border border-gray-200 rounded-xl p-4 flex items-center gap-3">
          <FileText className="w-5 h-5 text-blue-500" />
          <div>
            <p className="text-2xl font-black text-gray-900">{statsLoading ? '...' : (stats as Record<string, number>)?.documents || 0}</p>
            <p className="text-[11px] text-gray-500 font-medium">Documents</p>
          </div>
        </div>
        <div className="bg-white border border-gray-200 rounded-xl p-4 flex items-center gap-3">
          <Database className="w-5 h-5 text-violet-500" />
          <div>
            <p className="text-2xl font-black text-gray-900">{statsLoading ? '...' : (stats as Record<string, number>)?.collections || 0}</p>
            <p className="text-[11px] text-gray-500 font-medium">Collections</p>
          </div>
        </div>
        <div className="bg-white border border-gray-200 rounded-xl p-4 flex items-center gap-3">
          <BarChart3 className="w-5 h-5 text-emerald-500" />
          <div>
            <p className="text-2xl font-black text-gray-900">{statsLoading ? '...' : (stats as Record<string, number>)?.queries || 0}</p>
            <p className="text-[11px] text-gray-500 font-medium">Queries</p>
          </div>
        </div>
      </div>

      {/* Query Section */}
      <div className="bg-white border border-gray-200 rounded-xl p-6 space-y-4">
        <h2 className="text-lg font-bold text-gray-900">Query Documents</h2>
        <div className="flex gap-2">
          <div className="relative flex-1">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
            <input
              type="text"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              onKeyDown={(e) => e.key === 'Enter' && handleQuery()}
              placeholder="Search documents..."
              className="w-full pl-10 pr-4 py-3 border border-gray-200 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-violet-300"
            />
          </div>
          <button
            onClick={handleQuery}
            disabled={ragMutation.isPending || !query.trim()}
            className="px-6 py-3 bg-violet-600 hover:bg-violet-700 text-white text-sm font-semibold rounded-xl disabled:opacity-50 transition-colors"
          >
            {ragMutation.isPending ? <Loader2 className="w-4 h-4 animate-spin" /> : 'Search'}
          </button>
        </div>

        {/* Mode selector */}
        <div className="flex items-center gap-3">
          <span className="text-xs font-bold text-gray-500">Mode:</span>
          {(['standard', 'hybrid', 'graph'] as const).map((m) => (
            <button
              key={m}
              onClick={() => setMode(m)}
              className={`px-3 py-1.5 rounded-lg text-xs font-semibold transition-colors ${
                mode === m ? 'bg-violet-600 text-white' : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
              }`}
            >
              {m.charAt(0).toUpperCase() + m.slice(1)}
            </button>
          ))}
          <span className="text-xs text-gray-400 ml-2">Top K:</span>
          <input
            type="number"
            min={1}
            max={20}
            value={topK}
            onChange={(e) => setTopK(Number(e.target.value))}
            className="w-16 px-2 py-1 border border-gray-200 rounded-lg text-xs text-center"
          />
        </div>

        {queryError && (
          <div className="p-3 bg-red-50 border border-red-200 rounded-lg text-red-700 text-xs flex items-center gap-2">
            <AlertCircle className="w-4 h-4 shrink-0" /> {queryError}
          </div>
        )}

        {result && (
          <div className="space-y-4 mt-4">
            <div className="flex items-center justify-between">
              <h3 className="text-sm font-bold text-gray-700">Answer</h3>
              <div className="flex items-center gap-3 text-[11px] text-gray-500">
                <span>{result.chunks_retrieved} chunks</span>
                <span>{result.latency_ms}ms</span>
                <span className="font-bold text-violet-600">{(result.confidence * 100).toFixed(0)}% confidence</span>
              </div>
            </div>
            <div className="prose prose-violet max-w-none text-sm text-gray-800 bg-gray-50 p-4 rounded-xl border border-gray-100">
              {result.answer}
            </div>
            {result.citations.length > 0 && (
              <div className="space-y-2">
                <h3 className="text-sm font-bold text-gray-700">Citations ({result.citations.length})</h3>
                <div className="grid gap-2">
                  {result.citations.map((c, i) => (
                    <CitationCard key={i} citation={c} index={i} />
                  ))}
                </div>
              </div>
            )}
          </div>
        )}
      </div>

      {/* Collections */}
      <div className="bg-white border border-gray-200 rounded-xl p-6 space-y-3">
        <h2 className="text-lg font-bold text-gray-900">Collections</h2>
        {collLoading ? (
          <Loader2 className="w-5 h-5 animate-spin text-gray-400" />
        ) : collections.length === 0 ? (
          <p className="text-sm text-gray-400">No collections found.</p>
        ) : (
          <div className="grid grid-cols-2 md:grid-cols-3 gap-2">
            {collections.map((c) => (
              <div key={c.name} className="flex items-center gap-2 px-3 py-2 bg-gray-50 rounded-lg border border-gray-100">
                <Database className="w-4 h-4 text-violet-500" />
                <span className="text-sm font-semibold text-gray-700">{c.name}</span>
                {c.document_count !== undefined && (
                  <span className="text-[10px] text-gray-400 ml-auto">{c.document_count} docs</span>
                )}
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Upload URL */}
      <div className="bg-white border border-gray-200 rounded-xl p-6 space-y-3">
        <h2 className="text-lg font-bold text-gray-900">Ingest URL</h2>
        <div className="flex gap-2">
          <div className="relative flex-1">
            <LinkIcon className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
            <input
              type="url"
              value={uploadUrl}
              onChange={(e) => setUploadUrl(e.target.value)}
              placeholder="https://example.com/document"
              className="w-full pl-10 pr-4 py-2.5 border border-gray-200 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-blue-300"
            />
          </div>
          <button
            onClick={handleUploadUrl}
            disabled={uploading || !uploadUrl.trim()}
            className="flex items-center gap-2 px-4 py-2.5 bg-blue-600 hover:bg-blue-700 text-white text-sm font-semibold rounded-xl disabled:opacity-50"
          >
            {uploading ? <Loader2 className="w-4 h-4 animate-spin" /> : <Upload className="w-4 h-4" />}
            Ingest
          </button>
        </div>
        {uploadMsg && (
          <p className={`text-xs ${uploadMsg.includes('success') ? 'text-emerald-600' : 'text-red-600'}`}>{uploadMsg}</p>
        )}
      </div>
    </div>
  )
}

// ── MiroFish Swarm Visualization Tab ───────────────────────────────────────────

const PHASE_LABELS: Record<string, { label: string; icon: typeof Network }> = {
  graph_building: { label: 'Building Knowledge Graph', icon: Network },
  persona_generation: { label: 'Generating Personas', icon: Users },
  simulation_running: { label: 'Running Simulation', icon: Play },
  report_generation: { label: 'Generating Report', icon: TrendingUp },
}

function SwarmAgentCard({
  agentType,
  accentColor,
  phase,
  entities,
  personas,
  result,
}: {
  agentType: 'brand' | 'market'
  accentColor: string
  phase: string
  entities: string[]
  personas: string[]
  result: (import('@/types/council').SimulationResult & { simulation_id?: string; status?: string; entities?: string[]; personas?: string[]; report_summary?: string }) | null
}) {
  const [expandedSection, setExpandedSection] = useState<string | null>('prediction')
  const isRunning = ['graph_building', 'persona_generation', 'simulation_running', 'report_generation', 'graph_ready', 'personas_ready'].includes(phase)
  const isComplete = phase === 'completed'
  const isFailed = phase === 'failed'

  return (
    <div className="rounded-2xl border bg-white shadow-sm overflow-hidden" style={{ borderColor: `${accentColor}30` }}>
      {/* Header */}
      <div className="flex items-center justify-between px-4 py-3 border-b" style={{ borderColor: `${accentColor}20`, background: `linear-gradient(135deg, ${accentColor}08 0%, ${accentColor}03 100%)` }}>
        <div className="flex items-center gap-2">
          <Fish className="w-4 h-4" style={{ color: accentColor }} />
          <span className="text-xs font-bold uppercase tracking-wider" style={{ color: accentColor }}>
            MiroFish Swarm
          </span>
          <span className="text-[10px] text-gray-400 font-medium">
            ({agentType} agent)
          </span>
        </div>
        {isRunning && <Loader2 className="w-4 h-4 animate-spin" style={{ color: accentColor }} />}
        {isComplete && <span className="text-[10px] font-bold text-emerald-600 bg-emerald-50 px-2 py-0.5 rounded-full">Complete</span>}
        {isFailed && <span className="text-[10px] font-bold text-red-600 bg-red-50 px-2 py-0.5 rounded-full">Failed</span>}
      </div>

      <div className="p-4">
        {/* Progress */}
        {isRunning && (
          <div className="space-y-3">
            <div className="space-y-2">
              {Object.entries(PHASE_LABELS).map(([key, { label }]) => (
                <div key={key} className="flex items-center gap-2">
                  <div
                    className={`w-2 h-2 rounded-full transition-colors ${phase === key ? 'animate-pulse' : ''}`}
                    style={{ backgroundColor: phase === key ? accentColor : ['graph_ready', 'personas_ready'].includes(phase) && Object.keys(PHASE_LABELS).indexOf(key) < Object.keys(PHASE_LABELS).indexOf(phase) ? '#22c55e' : '#d1d5db' }}
                  />
                  <span className={`text-[10px] font-medium ${phase === key ? 'text-gray-900' : 'text-gray-400'}`}>
                    {label}
                  </span>
                </div>
              ))}
            </div>

            {entities.length > 0 && (
              <div>
                <p className="text-[10px] font-bold uppercase tracking-wider text-gray-400 mb-1">Entities ({entities.length})</p>
                <div className="flex flex-wrap gap-1">
                  {entities.map((e, i) => (
                    <span key={i} className="px-2 py-0.5 rounded-md text-[10px] font-medium bg-gray-50 border border-gray-100 text-gray-600">{e}</span>
                  ))}
                </div>
              </div>
            )}

            {personas.length > 0 && (
              <div>
                <p className="text-[10px] font-bold uppercase tracking-wider text-gray-400 mb-1">Personas ({personas.length})</p>
                <div className="flex flex-wrap gap-1">
                  {personas.map((p, i) => (
                    <span key={i} className="px-2 py-0.5 rounded-md text-[10px] font-medium border" style={{ borderColor: `${accentColor}30`, color: accentColor, background: `${accentColor}08` }}>{p}</span>
                  ))}
                </div>
              </div>
            )}
          </div>
        )}

        {/* Results */}
        {isComplete && result && (
          <div className="space-y-4">
            {/* Prediction */}
            <div>
              <button onClick={() => setExpandedSection(expandedSection === 'prediction' ? null : 'prediction')} className="flex items-center justify-between w-full text-left">
                <div className="flex items-center gap-2">
                  <TrendingUp className="w-4 h-4" style={{ color: accentColor }} />
                  <span className="text-sm font-bold text-gray-900">Prediction</span>
                  <ConfidenceBadge confidence={result.confidence * 100} />
                </div>
                {expandedSection === 'prediction' ? <ChevronUp className="w-4 h-4 text-gray-400" /> : <ChevronDown className="w-4 h-4 text-gray-400" />}
              </button>
              <AnimatePresence>
                {expandedSection === 'prediction' && (
                  <motion.div initial={{ height: 0, opacity: 0 }} animate={{ height: 'auto', opacity: 1 }} exit={{ height: 0, opacity: 0 }} className="overflow-hidden">
                    <div className="mt-2 pl-6 text-sm text-gray-700 leading-relaxed">{result.prediction}</div>
                  </motion.div>
                )}
              </AnimatePresence>
            </div>

            {/* Key Factors */}
            {result.key_factors.length > 0 && (
              <div>
                <button onClick={() => setExpandedSection(expandedSection === 'factors' ? null : 'factors')} className="flex items-center justify-between w-full text-left">
                  <div className="flex items-center gap-2">
                    <Lightbulb className="w-4 h-4 text-amber-500" />
                    <span className="text-sm font-bold text-gray-900">Key Factors ({result.key_factors.length})</span>
                  </div>
                  {expandedSection === 'factors' ? <ChevronUp className="w-4 h-4 text-gray-400" /> : <ChevronDown className="w-4 h-4 text-gray-400" />}
                </button>
                <AnimatePresence>
                  {expandedSection === 'factors' && (
                    <motion.div initial={{ height: 0, opacity: 0 }} animate={{ height: 'auto', opacity: 1 }} exit={{ height: 0, opacity: 0 }} className="overflow-hidden">
                      <ul className="mt-2 pl-6 space-y-1">
                        {result.key_factors.map((f: string, i: number) => (
                          <li key={i} className="text-sm text-gray-700 flex items-start gap-2">
                            <span className="w-1.5 h-1.5 rounded-full mt-1.5 shrink-0" style={{ backgroundColor: accentColor }} />
                            {f}
                          </li>
                        ))}
                      </ul>
                    </motion.div>
                  )}
                </AnimatePresence>
              </div>
            )}

            {/* Risks */}
            {result.risks.length > 0 && (
              <div>
                <button onClick={() => setExpandedSection(expandedSection === 'risks' ? null : 'risks')} className="flex items-center justify-between w-full text-left">
                  <div className="flex items-center gap-2">
                    <AlertTriangle className="w-4 h-4 text-red-500" />
                    <span className="text-sm font-bold text-gray-900">Risks ({result.risks.length})</span>
                  </div>
                  {expandedSection === 'risks' ? <ChevronUp className="w-4 h-4 text-gray-400" /> : <ChevronDown className="w-4 h-4 text-gray-400" />}
                </button>
                <AnimatePresence>
                  {expandedSection === 'risks' && (
                    <motion.div initial={{ height: 0, opacity: 0 }} animate={{ height: 'auto', opacity: 1 }} exit={{ height: 0, opacity: 0 }} className="overflow-hidden">
                      <ul className="mt-2 pl-6 space-y-1">
                        {result.risks.map((r: string, i: number) => (
                          <li key={i} className="text-sm text-red-700 flex items-start gap-2">
                            <span className="w-1.5 h-1.5 rounded-full bg-red-400 mt-1.5 shrink-0" />
                            {r}
                          </li>
                        ))}
                      </ul>
                    </motion.div>
                  )}
                </AnimatePresence>
              </div>
            )}

            {/* Recommendations */}
            {result.recommendations.length > 0 && (
              <div>
                <button onClick={() => setExpandedSection(expandedSection === 'recs' ? null : 'recs')} className="flex items-center justify-between w-full text-left">
                  <div className="flex items-center gap-2">
                    <Lightbulb className="w-4 h-4 text-green-500" />
                    <span className="text-sm font-bold text-gray-900">Recommendations ({result.recommendations.length})</span>
                  </div>
                  {expandedSection === 'recs' ? <ChevronUp className="w-4 h-4 text-gray-400" /> : <ChevronDown className="w-4 h-4 text-gray-400" />}
                </button>
                <AnimatePresence>
                  {expandedSection === 'recs' && (
                    <motion.div initial={{ height: 0, opacity: 0 }} animate={{ height: 'auto', opacity: 1 }} exit={{ height: 0, opacity: 0 }} className="overflow-hidden">
                      <ul className="mt-2 pl-6 space-y-1">
                        {result.recommendations.map((r: string, i: number) => (
                          <li key={i} className="text-sm text-green-700 flex items-start gap-2">
                            <span className="w-1.5 h-1.5 rounded-full bg-green-400 mt-1.5 shrink-0" />
                            {r}
                          </li>
                        ))}
                      </ul>
                    </motion.div>
                  )}
                </AnimatePresence>
              </div>
            )}

            {/* Entities & Personas summary */}
            <div className="grid grid-cols-2 gap-3 pt-2 border-t border-gray-100">
              <div>
                <p className="text-[10px] font-bold uppercase tracking-wider text-gray-400 mb-1">Entities</p>
                <div className="flex flex-wrap gap-1">
                  {(result.entities || entities).map((e: string, i: number) => (
                    <span key={i} className="px-1.5 py-0.5 rounded text-[9px] font-medium bg-gray-50 border border-gray-100 text-gray-500">{e}</span>
                  ))}
                </div>
              </div>
              <div>
                <p className="text-[10px] font-bold uppercase tracking-wider text-gray-400 mb-1">Personas</p>
                <div className="flex flex-wrap gap-1">
                  {(result.personas || personas).map((p: string, i: number) => (
                    <span key={i} className="px-1.5 py-0.5 rounded text-[9px] font-medium border" style={{ borderColor: `${accentColor}20`, color: accentColor }}>{p}</span>
                  ))}
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Idle state */}
        {!isRunning && !isComplete && !isFailed && (
          <div className="text-center py-6">
            <Fish className="w-8 h-8 text-gray-300 mx-auto mb-2" />
            <p className="text-sm text-gray-400">Run a council debate with MiroFish enabled to see swarm visualization</p>
          </div>
        )}

        {/* Failed state */}
        {isFailed && (
          <div className="text-center py-4">
            <AlertTriangle className="w-8 h-8 text-red-400 mx-auto mb-2" />
            <p className="text-sm text-red-600 font-medium">Simulation failed</p>
          </div>
        )}
      </div>
    </div>
  )
}

function MiroFishTab() {
  const {
    mirofishPhase,
    mirofishBrandResult,
    mirofishMarketResult,
    mirofishBrandEntities,
    mirofishMarketEntities,
    mirofishBrandPersonas,
    mirofishMarketPersonas,
    mirofishBrandPhase,
    mirofishMarketPhase,
  } = useCouncilV2Store()

  const isSwarmActive = mirofishPhase !== 'idle'

  return (
    <div className="space-y-6">
      {/* Swarm Status Banner */}
      <div className={`rounded-xl p-4 flex items-center gap-3 ${isSwarmActive ? 'bg-gradient-to-r from-cyan-50 to-blue-50 border border-cyan-200' : 'bg-gray-50 border border-gray-200'}`}>
        <div className={`w-10 h-10 rounded-xl flex items-center justify-center ${isSwarmActive ? 'bg-gradient-to-br from-cyan-500 to-blue-600 shadow-lg shadow-cyan-500/20' : 'bg-gray-200'}`}>
          <Fish className={`w-5 h-5 ${isSwarmActive ? 'text-white' : 'text-gray-400'}`} />
        </div>
        <div>
          <h2 className="text-lg font-bold text-gray-900">MiroFish Swarm Simulation</h2>
          <p className="text-xs text-gray-500">
            {isSwarmActive
              ? `Phase: ${mirofishPhase.replace(/_/g, ' ')} — Brand & Market agents running multi-persona simulation`
              : 'Enable MiroFish toggle in the Council Debate page to run swarm simulations for Brand & Market agents after 3 rounds'}
          </p>
        </div>
        {isSwarmActive && mirofishPhase !== 'completed' && (
          <Loader2 className="w-5 h-5 animate-spin text-cyan-500 ml-auto" />
        )}
        {mirofishPhase === 'completed' && (
          <span className="text-xs font-bold text-emerald-600 bg-emerald-50 px-3 py-1 rounded-full ml-auto">Swarm Complete</span>
        )}
      </div>

      {/* Animated Swarm Visualization */}
      {isSwarmActive && (
        <div className="bg-white border border-gray-200 rounded-xl p-6 overflow-hidden relative" style={{ minHeight: '120px' }}>
          <p className="text-[10px] font-bold uppercase tracking-wider text-gray-400 mb-3">Swarm Activity</p>
          <div className="flex items-center gap-4">
            {/* Fish particles animation */}
            <div className="flex gap-2">
              {Array.from({ length: 8 }).map((_, i) => (
                <motion.div
                  key={i}
                  animate={{
                    x: [0, 20, -10, 15, 0],
                    y: [0, -10, 5, -8, 0],
                    rotate: [0, 10, -5, 8, 0],
                  }}
                  transition={{
                    duration: 3 + i * 0.5,
                    repeat: Infinity,
                    ease: 'easeInOut',
                    delay: i * 0.3,
                  }}
                  className="text-lg"
                  style={{ color: i % 2 === 0 ? '#EC4899' : '#F97316' }}
                >
                  🐟
                </motion.div>
              ))}
            </div>
            <div className="flex-1">
              <div className="flex items-center gap-2">
                <Zap className="w-4 h-4 text-cyan-500" />
                <span className="text-sm font-semibold text-gray-700">
                  {mirofishPhase === 'completed' ? 'Simulation Complete' : `Processing: ${mirofishPhase.replace(/_/g, ' ')}...`}
                </span>
              </div>
              <div className="mt-2 h-2 bg-gray-100 rounded-full overflow-hidden">
                <motion.div
                  className="h-full bg-gradient-to-r from-cyan-500 to-blue-500 rounded-full"
                  animate={{ width: mirofishPhase === 'completed' ? '100%' : ['0%', '60%', '30%', '80%', '50%'] }}
                  transition={mirofishPhase === 'completed' ? { duration: 0.5 } : { duration: 4, repeat: Infinity, ease: 'easeInOut' }}
                />
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Agent Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <SwarmAgentCard
          agentType="brand"
          accentColor="#EC4899"
          phase={mirofishBrandPhase}
          entities={mirofishBrandEntities}
          personas={mirofishBrandPersonas}
          result={mirofishBrandResult}
        />
        <SwarmAgentCard
          agentType="market"
          accentColor="#F97316"
          phase={mirofishMarketPhase}
          entities={mirofishMarketEntities}
          personas={mirofishMarketPersonas}
          result={mirofishMarketResult}
        />
      </div>

      {/* How it works */}
      {!isSwarmActive && (
        <div className="bg-white border border-gray-200 rounded-xl p-6">
          <h3 className="text-sm font-bold text-gray-900 mb-3">How MiroFish Swarm Works</h3>
          <div className="grid grid-cols-4 gap-3">
            {[
              { icon: Network, label: '1. Graph Build', desc: 'Extract entities & relationships from the query', color: '#6366F1' },
              { icon: Users, label: '2. Generate Personas', desc: 'Create 5 AI personas (competitor, customer, analyst, etc.)', color: '#8B5CF6' },
              { icon: Play, label: '3. Simulate', desc: '3 rounds of parallel persona interactions', color: '#06B6D4' },
              { icon: TrendingUp, label: '4. Report', desc: 'Synthesize predictions, risks & recommendations', color: '#10B981' },
            ].map(({ icon: Icon, label, desc, color }) => (
              <div key={label} className="text-center p-3 rounded-lg bg-gray-50 border border-gray-100">
                <Icon className="w-5 h-5 mx-auto mb-1" style={{ color }} />
                <p className="text-xs font-bold text-gray-700">{label}</p>
                <p className="text-[10px] text-gray-400 mt-0.5">{desc}</p>
              </div>
            ))}
          </div>
          <p className="text-[10px] text-gray-400 mt-3 text-center">
            MiroFish only activates for <span className="font-bold text-pink-500">Brand</span> and <span className="font-bold text-orange-500">Market</span> agents after 3 council debate rounds
          </p>
        </div>
      )}
    </div>
  )
}

// ── Main Page ───────────────────────────────────────────────────────────────────

type TabKey = 'swarm' | 'rag'

export default function SwarmVisualizer() {
  const [activeTab, setActiveTab] = useState<TabKey>('swarm')

  const tabs: { key: TabKey; label: string; icon: typeof Fish }[] = [
    { key: 'swarm', label: 'Swarm Simulation', icon: Fish },
    { key: 'rag', label: 'RAG Explorer', icon: BookOpen },
  ]

  return (
    <div className="min-h-screen bg-gray-50 p-6 space-y-6">
      {/* Header */}
      <div className="flex items-center gap-3">
        <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-cyan-600 to-blue-600 flex items-center justify-center shadow-lg shadow-cyan-500/20">
          <Fish className="w-5 h-5 text-white" />
        </div>
        <div>
          <h1 className="text-2xl font-black text-gray-900">Swarm Visualizer</h1>
          <p className="text-sm text-gray-500">MiroFish simulation monitoring & RAG document explorer</p>
        </div>
      </div>

      {/* Tab Selector */}
      <div className="flex items-center gap-2 bg-white border border-gray-200 rounded-xl p-1.5 w-fit">
        {tabs.map(({ key, label, icon: Icon }) => (
          <button
            key={key}
            onClick={() => setActiveTab(key)}
            className={`flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-semibold transition-all ${
              activeTab === key
                ? 'bg-gradient-to-r from-cyan-600 to-blue-600 text-white shadow-sm'
                : 'text-gray-600 hover:bg-gray-50'
            }`}
          >
            <Icon className="w-4 h-4" />
            {label}
          </button>
        ))}
      </div>

      {/* Tab Content */}
      <AnimatePresence mode="wait">
        <motion.div
          key={activeTab}
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          exit={{ opacity: 0, y: -10 }}
          transition={{ duration: 0.2 }}
        >
          {activeTab === 'swarm' ? <MiroFishTab /> : <RAGTab />}
        </motion.div>
      </AnimatePresence>
    </div>
  )
}
