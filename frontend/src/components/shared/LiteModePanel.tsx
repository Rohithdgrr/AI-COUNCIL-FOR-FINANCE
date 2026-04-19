import { useState, useCallback } from 'react'
import { ShieldCheck, Zap, Loader2, AlertTriangle, BookOpen, Maximize2, Minimize2, X } from 'lucide-react'
import type { AgentInfo, SupportEvidence, EvidenceBundle, AgentRoundState, SupportAgentPolicy, SubagentEvidence } from '@/types/council'
import { COUNCIL_AGENTS, SUBAGENT_DEFS, SUBAGENT_CHANNEL_META, type SubagentChannel } from '@/types/council'
import CitedMarkdownRenderer from './CitedMarkdownRenderer'
import SubagentEvidenceCard from './SubagentEvidenceCard'
import ConfidenceBadge from './ConfidenceBadge'
import EvidencePipelineStrip from './EvidencePipelineStrip'

interface LiteModePanelProps {
  primaryAgentInfo: AgentInfo
  supportAgentKeys?: string[]
  agents: Record<string, { round1: AgentRoundState; round2: AgentRoundState }>
  discoveredSources?: Record<string, { num: number; title: string; url: string }[]>
  isStreaming: boolean
  supportEvidence?: Record<string, SupportEvidence>
  evidenceBundle: EvidenceBundle | null
  citationMaps: Record<string, Record<string, string>>
  pipelineStages: {
    rag_fetching: { status: string; count: number }
    api_called: { status: string; count: number }
    mcp_fetched: { status: string; count: number }
    sources_ready: { status: string; count: number }
  }
  supportAgentPolicy: SupportAgentPolicy
  subagentEvidence?: Record<string, SubagentEvidence>
  activeSubagents?: string[]
}

export default function LiteModePanel({
  primaryAgentInfo,
  agents,
  isStreaming,
  evidenceBundle,
  citationMaps,
  pipelineStages,
  supportAgentPolicy,
  subagentEvidence,
  activeSubagents,
}: LiteModePanelProps) {
  const [isFullscreen, setIsFullscreen] = useState(false)
  const primaryRoundState = agents[primaryAgentInfo.key]?.round2
  const primaryOutput = primaryRoundState?.output || ''
  const primaryConfidence = primaryRoundState?.confidence || 0
  const isSynthesizing = primaryRoundState?.status === 'thinking'
  const isDone = primaryRoundState?.status === 'done'

  const subagentCount = subagentEvidence ? Object.keys(subagentEvidence).length || 5 : 5
  const hasSubagentResults = subagentEvidence && Object.keys(subagentEvidence).length > 0
  const hasActiveSubagents = activeSubagents && activeSubagents.length > 0

  const toggleFullscreen = useCallback(() => setIsFullscreen((v) => !v), [])

  // Subagent evidence section (shared between normal and fullscreen)
  const subagentSection = (
    <>
      {/* Section header with fullscreen button */}
      <div className="flex items-center justify-between mb-3 px-1">
        <div className="flex items-center gap-2">
          <Zap className="w-3.5 h-3.5 text-violet-500" />
          <p className="text-[10px] font-black uppercase tracking-[0.2em] text-slate-400">
            Hybrid Subagent Evidence
          </p>
          <span className="text-[10px] text-gray-300 font-medium">
            ({subagentCount} researchers)
          </span>
        </div>
        <button
          onClick={toggleFullscreen}
          className="p-1.5 rounded-lg hover:bg-gray-100 transition-colors text-gray-400 hover:text-gray-600"
          title={isFullscreen ? 'Exit fullscreen' : 'Fullscreen'}
        >
          {isFullscreen ? <Minimize2 className="w-4 h-4" /> : <Maximize2 className="w-4 h-4" />}
        </button>
      </div>

      {/* Subagent cards or progress cards */}
      {hasSubagentResults ? (
        <div className={`grid gap-3 ${isFullscreen ? 'grid-cols-1 lg:grid-cols-2 xl:grid-cols-3' : 'sm:grid-cols-2 xl:grid-cols-3'}`}>
          {Object.values(subagentEvidence!).map((se) => (
            <SubagentEvidenceCard key={se.subagent_key} evidence={se} defaultExpanded={isFullscreen} />
          ))}
        </div>
      ) : hasActiveSubagents ? (
        <div className="grid gap-3 sm:grid-cols-2 xl:grid-cols-3">
          {SUBAGENT_DEFS[primaryAgentInfo.key]?.map((sd) => {
            const isActive = activeSubagents!.includes(sd.key)
            const meta = SUBAGENT_CHANNEL_META[sd.data_channel as SubagentChannel]
            return (
              <div
                key={sd.key}
                className="rounded-2xl border bg-white/80 p-4 shadow-sm animate-pulse"
                style={{ borderColor: `${meta.color}30` }}
              >
                <div className="flex items-center justify-between gap-2">
                  <div className="flex items-center gap-2">
                    <span className="w-2.5 h-2.5 rounded-full" style={{ backgroundColor: meta.color }} />
                    <p className="text-sm font-semibold text-slate-900 truncate">{sd.label}</p>
                  </div>
                  <span
                    className="text-[10px] font-bold uppercase tracking-wider"
                    style={{ color: isActive ? meta.color : '#94a3b8' }}
                  >
                    {isActive ? 'Researching' : 'Queued'}
                  </span>
                </div>
                <div className="mt-2 h-1.5 rounded-full bg-slate-100 overflow-hidden">
                  <div
                    className="h-full rounded-full transition-all duration-500"
                    style={{
                      width: isActive ? '65%' : '12%',
                      backgroundColor: meta.color,
                    }}
                  />
                </div>
                <div className="mt-2 flex items-center justify-between text-[10px] text-gray-400 font-medium">
                  <span>{sd.data_channel}</span>
                  {isActive && <Loader2 className="w-3 h-3 animate-spin" style={{ color: meta.color }} />}
                </div>
              </div>
            )
          })}
        </div>
      ) : isStreaming ? (
        /* Default: show subagent skeleton cards while waiting for events */
        <div className="grid gap-3 sm:grid-cols-2 xl:grid-cols-3">
          {SUBAGENT_DEFS[primaryAgentInfo.key]?.map((sd) => {
            const meta = SUBAGENT_CHANNEL_META[sd.data_channel as SubagentChannel]
            return (
              <div
                key={sd.key}
                className="rounded-2xl border bg-white/80 p-4 shadow-sm"
                style={{ borderColor: `${meta.color}20` }}
              >
                <div className="flex items-center justify-between gap-2">
                  <div className="flex items-center gap-2">
                    <span className="w-2.5 h-2.5 rounded-full opacity-40" style={{ backgroundColor: meta.color }} />
                    <p className="text-sm font-semibold text-slate-400 truncate">{sd.label}</p>
                  </div>
                  <span className="text-[10px] font-bold uppercase tracking-wider text-gray-300">
                    Waiting
                  </span>
                </div>
                <div className="mt-2 h-1.5 rounded-full bg-slate-50 overflow-hidden">
                  <div className="h-full rounded-full w-0 transition-all duration-500" style={{ backgroundColor: meta.color }} />
                </div>
                <div className="mt-2 text-[10px] text-gray-300 font-medium">{sd.data_channel}</div>
              </div>
            )
          })}
        </div>
      ) : null}
    </>
  )

  // Fullscreen overlay
  if (isFullscreen) {
    return (
      <div className="fixed inset-0 z-50 bg-white/95 backdrop-blur-xl overflow-y-auto">
        <div className="max-w-7xl mx-auto p-6 space-y-6">
          {/* Fullscreen header */}
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div
                className="w-10 h-10 rounded-xl flex items-center justify-center"
                style={{ background: `linear-gradient(135deg, ${primaryAgentInfo.hexColor}30, ${primaryAgentInfo.hexColor}10)` }}
              >
                <ShieldCheck className="w-5 h-5" style={{ color: primaryAgentInfo.hexColor }} />
              </div>
              <div>
                <h2 className="text-lg font-black text-gray-900">{primaryAgentInfo.label} — Research Pipeline</h2>
                <p className="text-xs text-gray-400">{subagentCount} hybrid subagents • Full evidence view</p>
              </div>
            </div>
            <button
              onClick={toggleFullscreen}
              className="p-2 rounded-xl hover:bg-gray-100 transition-colors text-gray-500 hover:text-gray-700"
            >
              <X className="w-5 h-5" />
            </button>
          </div>

          {/* Pipeline strip */}
          <EvidencePipelineStrip
            policy={supportAgentPolicy}
            stages={{
              rag_fetching: pipelineStages.rag_fetching.status as any,
              api_called: pipelineStages.api_called.status as any,
              mcp_fetched: pipelineStages.mcp_fetched.status as any,
              sources_ready: pipelineStages.sources_ready.status as any,
            }}
            counts={{
              rag_fetching: pipelineStages.rag_fetching.count,
              api_called: pipelineStages.api_called.count,
              mcp_fetched: pipelineStages.mcp_fetched.count,
              sources_ready: pipelineStages.sources_ready.count,
            }}
          />

          {/* Subagent evidence in fullscreen */}
          {subagentSection}

          {/* Evidence Bundle Summary */}
          {evidenceBundle && (
            <div className="rounded-2xl border border-violet-200/60 bg-violet-50/40 backdrop-blur-md p-5">
              <div className="flex items-center gap-2 mb-2">
                <BookOpen className="w-4 h-4 text-violet-600" />
                <span className="text-xs font-bold text-violet-700 uppercase tracking-wider">Evidence Bundle</span>
              </div>
              <CitedMarkdownRenderer
                content={evidenceBundle.data_quality_summary}
                accentColor={primaryAgentInfo.hexColor}
              />
              {evidenceBundle.conflicts.length > 0 && (
                <div className="mt-2 flex items-center gap-1.5">
                  <AlertTriangle className="w-3.5 h-3.5 text-amber-500" />
                  <span className="text-xs text-amber-700 font-medium">
                    Conflicts: {evidenceBundle.conflicts.join(', ')}
                  </span>
                </div>
              )}
              <div className="mt-3 flex flex-wrap gap-2">
                {Object.entries(evidenceBundle.source_counts).map(([key, count]) => {
                  const channelMeta = SUBAGENT_CHANNEL_META[key as SubagentChannel]
                  const agentInfo = COUNCIL_AGENTS.find((a) => a.key === key)
                  const color = channelMeta?.color || agentInfo?.hexColor || '#6B7280'
                  const label = channelMeta?.shortLabel || agentInfo?.label || key
                  return (
                    <span
                      key={key}
                      className="inline-flex items-center gap-1 px-2.5 py-1 rounded-full text-[11px] font-bold"
                      style={{ color, background: `${color}10` }}
                    >
                      <span className="w-1.5 h-1.5 rounded-full" style={{ backgroundColor: color }} />
                      {label}: {count as number}
                    </span>
                  )
                })}
              </div>
            </div>
          )}

          {/* Primary Agent Synthesis in fullscreen */}
          {(isSynthesizing || primaryOutput) && (
            <div
              className="rounded-3xl p-8 relative overflow-hidden"
              style={{
                background: `linear-gradient(135deg, rgba(255,255,255,0.95) 0%, ${primaryAgentInfo.hexColor}05 100%)`,
                border: `2px solid ${primaryAgentInfo.hexColor}30`,
              }}
            >
              <div className="flex items-center gap-4 mb-6">
                <div
                  className="w-14 h-14 rounded-2xl flex items-center justify-center shadow-lg"
                  style={{
                    background: `linear-gradient(135deg, ${primaryAgentInfo.hexColor}30, ${primaryAgentInfo.hexColor}10)`,
                    boxShadow: `0 0 20px ${primaryAgentInfo.hexColor}40`,
                  }}
                >
                  <ShieldCheck className="w-7 h-7" style={{ color: primaryAgentInfo.hexColor }} />
                </div>
                <div className="flex-1">
                  <h3 className="text-2xl font-black text-gray-900">{primaryAgentInfo.label}</h3>
                  <span className="text-[11px] font-extrabold uppercase tracking-widest" style={{ color: primaryAgentInfo.hexColor }}>
                    {isSynthesizing ? 'Synthesizing...' : isDone ? 'Final answer ready' : ''}
                  </span>
                </div>
                {primaryConfidence > 0 && <ConfidenceBadge confidence={primaryConfidence} size="lg" showLabel />}
              </div>

              {isSynthesizing && !primaryOutput && (
                <div className="flex flex-col items-center justify-center py-16 text-gray-300 gap-4">
                  <div className="relative">
                    <Loader2 className="w-10 h-10 animate-spin text-gray-200" />
                    <div className="absolute inset-0 w-10 h-10 rounded-full border-t-2 animate-spin" style={{ borderColor: primaryAgentInfo.hexColor, animationDuration: '0.6s' }} />
                  </div>
                  <span className="text-xs font-black uppercase tracking-[0.3em] animate-pulse text-gray-400">
                    Synthesizing evidence from {subagentCount} subagents...
                  </span>
                </div>
              )}

              {primaryOutput && (
                <div className="text-gray-700 font-inter leading-relaxed text-[16px] font-medium prose prose-violet max-w-none prose-headings:font-outfit prose-headings:text-gray-950 prose-headings:font-black prose-strong:text-gray-950 prose-strong:font-bold prose-table:border-collapse prose-th:bg-gray-50 prose-th:p-3 prose-th:text-left prose-th:text-xs prose-th:font-bold prose-th:uppercase prose-th:tracking-wider prose-th:text-gray-500 prose-td:p-3 prose-td:text-sm prose-td:border-b prose-td:border-gray-100 prose-tr:hover:prose-td:bg-gray-50/50">
                  <CitedMarkdownRenderer
                    content={primaryOutput}
                    urlMap={citationMaps[primaryAgentInfo.key] || {}}
                    accentColor={primaryAgentInfo.hexColor}
                  />
                </div>
              )}
            </div>
          )}
        </div>
      </div>
    )
  }

  // Normal (non-fullscreen) view — integrated into research pipeline
  return (
    <div className="space-y-5">
      {/* Research Pipeline Header (replaces old "Lite Mode" header) */}
      <div
        className="p-5 rounded-2xl relative overflow-hidden backdrop-blur-3xl"
        style={{
          background: `linear-gradient(135deg, rgba(255,255,255,0.92) 0%, ${primaryAgentInfo.hexColor}06 100%)`,
          border: `1.5px solid ${primaryAgentInfo.hexColor}25`,
          boxShadow: `0 0 20px ${primaryAgentInfo.hexColor}08`,
        }}
      >
        <div className="relative z-10">
          <div className="flex items-center gap-3 mb-3">
            <div
              className="w-9 h-9 rounded-xl flex items-center justify-center"
              style={{ background: `linear-gradient(135deg, ${primaryAgentInfo.hexColor}25, ${primaryAgentInfo.hexColor}08)` }}
            >
              <ShieldCheck className="w-5 h-5" style={{ color: primaryAgentInfo.hexColor }} />
            </div>
            <div className="flex-1">
              <h2 className="text-base font-black text-gray-900">{primaryAgentInfo.label} Research Pipeline</h2>
              <p className="text-[11px] text-gray-400 font-medium">
                {subagentCount} hybrid subagents gathering evidence
              </p>
            </div>
            <div className="flex items-center gap-2">
              {isStreaming && !isDone && (
                <span className="flex items-center gap-1.5 px-2.5 py-1 rounded-full text-[11px] font-bold bg-violet-50 text-violet-600 border border-violet-200">
                  <Loader2 className="w-3 h-3 animate-spin" />
                  Researching
                </span>
              )}
              {isDone && (
                <ConfidenceBadge confidence={primaryConfidence} size="md" showLabel />
              )}
            </div>
          </div>

          {/* Evidence Pipeline Strip */}
          <EvidencePipelineStrip
            policy={supportAgentPolicy}
            stages={{
              rag_fetching: pipelineStages.rag_fetching.status as any,
              api_called: pipelineStages.api_called.status as any,
              mcp_fetched: pipelineStages.mcp_fetched.status as any,
              sources_ready: pipelineStages.sources_ready.status as any,
            }}
            counts={{
              rag_fetching: pipelineStages.rag_fetching.count,
              api_called: pipelineStages.api_called.count,
              mcp_fetched: pipelineStages.mcp_fetched.count,
              sources_ready: pipelineStages.sources_ready.count,
            }}
          />
        </div>
      </div>

      {/* Subagent Evidence Section */}
      {subagentSection}

      {/* Evidence Bundle Summary */}
      {evidenceBundle && (
        <div className="rounded-2xl border border-violet-200/60 bg-violet-50/40 backdrop-blur-md p-4">
          <div className="flex items-center gap-2 mb-2">
            <BookOpen className="w-4 h-4 text-violet-600" />
            <span className="text-xs font-bold text-violet-700 uppercase tracking-wider">Evidence Bundle</span>
          </div>
          <CitedMarkdownRenderer
            content={evidenceBundle.data_quality_summary}
            accentColor={primaryAgentInfo.hexColor}
          />
          {evidenceBundle.conflicts.length > 0 && (
            <div className="mt-2 flex items-center gap-1.5">
              <AlertTriangle className="w-3.5 h-3.5 text-amber-500" />
              <span className="text-xs text-amber-700 font-medium">
                Conflicts: {evidenceBundle.conflicts.join(', ')}
              </span>
            </div>
          )}
          <div className="mt-2 flex flex-wrap gap-2">
            {Object.entries(evidenceBundle.source_counts).map(([key, count]) => {
              const channelMeta = SUBAGENT_CHANNEL_META[key as SubagentChannel]
              const agentInfo = COUNCIL_AGENTS.find((a) => a.key === key)
              const color = channelMeta?.color || agentInfo?.hexColor || '#6B7280'
              const label = channelMeta?.shortLabel || agentInfo?.label || key
              return (
                <span
                  key={key}
                  className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[10px] font-bold"
                  style={{ color, background: `${color}10` }}
                >
                  <span className="w-1.5 h-1.5 rounded-full" style={{ backgroundColor: color }} />
                  {label}: {count as number}
                </span>
              )
            })}
          </div>
        </div>
      )}

      {/* Primary Agent Synthesis */}
      {(isSynthesizing || primaryOutput) && (
        <div
          className="rounded-[2rem] p-8 relative overflow-hidden backdrop-blur-3xl group"
          style={{
            background: `linear-gradient(135deg, rgba(255,255,255,0.9) 0%, ${primaryAgentInfo.hexColor}08 100%)`,
            borderColor: `${primaryAgentInfo.hexColor}50`,
            borderWidth: '2px',
            borderStyle: 'solid',
            boxShadow: `0 0 35px ${primaryAgentInfo.hexColor}20`,
          }}
        >
          <div className="absolute -bottom-24 -right-24 w-[400px] h-[400px] rounded-full blur-[100px] opacity-15 pointer-events-none" style={{ backgroundColor: primaryAgentInfo.hexColor }} />
          <div className="relative z-10">
            <div className="flex items-center gap-4 mb-6">
              <div
                className="w-14 h-14 rounded-2xl flex items-center justify-center shadow-lg"
                style={{
                  background: `linear-gradient(135deg, ${primaryAgentInfo.hexColor}30, ${primaryAgentInfo.hexColor}10)`,
                  boxShadow: `0 0 20px ${primaryAgentInfo.hexColor}40`,
                }}
              >
                <ShieldCheck className="w-7 h-7" style={{ color: primaryAgentInfo.hexColor }} />
              </div>
              <div className="flex-1">
                <h3 className="text-2xl font-black text-gray-900">{primaryAgentInfo.label}</h3>
                <div className="flex items-center gap-2 mt-0.5">
                  <span className="text-[10px] text-gray-400 font-bold tracking-[0.2em] uppercase">Synthesis</span>
                  <span className="w-1 h-1 rounded-full bg-gray-300" />
                  <span className="text-[11px] font-extrabold uppercase tracking-widest flex items-center gap-1" style={{ color: primaryAgentInfo.hexColor }}>
                    <Zap className="w-3 h-3" />
                    {isSynthesizing ? 'Synthesizing...' : isDone ? 'Final answer ready' : ''}
                  </span>
                </div>
              </div>
              {primaryConfidence > 0 && <ConfidenceBadge confidence={primaryConfidence} size="lg" showLabel />}
            </div>

            {isSynthesizing && !primaryOutput && (
              <div className="flex flex-col items-center justify-center py-16 text-gray-300 gap-4">
                <div className="relative">
                  <Loader2 className="w-10 h-10 animate-spin text-gray-200" />
                  <div className="absolute inset-0 w-10 h-10 rounded-full border-t-2 animate-spin" style={{ borderColor: primaryAgentInfo.hexColor, animationDuration: '0.6s' }} />
                </div>
                <span className="text-xs font-black uppercase tracking-[0.3em] animate-pulse text-gray-400">
                  Synthesizing evidence from {subagentCount} subagents...
                </span>
              </div>
            )}

            {primaryOutput && (
              <div className="text-gray-700 font-inter leading-relaxed text-[16px] font-medium prose prose-violet max-w-none prose-headings:font-outfit prose-headings:text-gray-950 prose-headings:font-black prose-strong:text-gray-950 prose-strong:font-bold prose-table:border-collapse prose-th:bg-gray-50 prose-th:p-3 prose-th:text-left prose-th:text-xs prose-th:font-bold prose-th:uppercase prose-th:tracking-wider prose-th:text-gray-500 prose-td:p-3 prose-td:text-sm prose-td:border-b prose-td:border-gray-100 prose-tr:hover:prose-td:bg-gray-50/50">
                <CitedMarkdownRenderer
                  content={primaryOutput}
                  urlMap={citationMaps[primaryAgentInfo.key] || {}}
                  accentColor={primaryAgentInfo.hexColor}
                />
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  )
}
