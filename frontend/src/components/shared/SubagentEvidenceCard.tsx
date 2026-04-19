import { useState, useEffect } from 'react'
import { ChevronDown, ChevronUp, ExternalLink, Flag, BookOpen, Link2, Loader2 } from 'lucide-react'
import type { SubagentEvidence } from '@/types/council'
import { SUBAGENT_CHANNEL_META, type SubagentChannel } from '@/types/council'
import ConfidenceBadge from './ConfidenceBadge'
import CitedMarkdownRenderer from './CitedMarkdownRenderer'
import { useCouncilV2Store } from '@/store/councilV2Store'

interface SubagentEvidenceCardProps {
  evidence: SubagentEvidence
  defaultExpanded?: boolean
}

export default function SubagentEvidenceCard({ evidence, defaultExpanded = false }: SubagentEvidenceCardProps) {
  const [expanded, setExpanded] = useState(defaultExpanded)
  const [showSources, setShowSources] = useState(false)
  const streamingSubagents = useCouncilV2Store((state) => state.streamingSubagents)
  const isStreamingThis = streamingSubagents.includes(evidence.subagent_key)

  // Auto-expand if streaming starts
  useEffect(() => {
    if (isStreamingThis) {
      setExpanded(true)
    }
  }, [isStreamingThis])

  const channel = evidence.data_channel as SubagentChannel
  const meta = SUBAGENT_CHANNEL_META[channel] || SUBAGENT_CHANNEL_META.rag
  
  const displaySummary = evidence.summary

  return (
    <div
      className="rounded-2xl border bg-white/80 backdrop-blur-md p-4 transition-all duration-200 hover:shadow-md"
      style={{
        borderColor: `${meta.color}30`,
        background: `linear-gradient(135deg, rgba(255,255,255,0.9) 0%, ${meta.color}08 100%)`,
      }}
    >
      {/* Header */}
      <div className="flex items-center justify-between gap-2 mb-3">
        <div className="flex items-center gap-2">
          {isStreamingThis ? (
            <Loader2 className="w-3.5 h-3.5 animate-spin" style={{ color: meta.color }} />
          ) : (
            <span
              className="w-2.5 h-2.5 rounded-full shrink-0"
              style={{ backgroundColor: meta.color }}
            />
          )}
          <span className="text-sm font-bold text-gray-900 truncate">
            {evidence.subagent_key.replace('_', ' → ')}
          </span>
          <span
            className="text-[10px] font-semibold uppercase tracking-wider px-1.5 py-0.5 rounded-full"
            style={{ color: meta.color, background: `${meta.color}15` }}
          >
            {meta.shortLabel}
          </span>
        </div>
        {!isStreamingThis && <ConfidenceBadge confidence={evidence.confidence} size="sm" />}
      </div>

      {/* Domain hint */}
      {evidence.domain_hint && (
        <p className="text-[11px] text-gray-400 italic mb-2">{evidence.domain_hint.slice(0, 120)}</p>
      )}

      {/* Summary — rendered as markdown with table support */}
      <div 
        className={`text-sm text-gray-700 leading-relaxed prose prose-sm max-w-none prose-table:border-collapse prose-th:bg-gray-50 prose-th:p-2 prose-th:text-left prose-th:text-[11px] prose-th:font-bold prose-th:uppercase prose-th:tracking-wider prose-th:text-gray-500 prose-td:p-2 prose-td:text-[13px] prose-td:border-b prose-td:border-gray-100 prose-tr:hover:prose-td:bg-gray-50/50 transition-all duration-300 relative ${
          !expanded ? 'max-h-[160px] overflow-hidden' : 'max-h-[5000px]'
        }`}
      >
        {!evidence.summary.trim() ? (
          <p className="text-gray-400 italic">No evidence collected</p>
        ) : (
          <CitedMarkdownRenderer
            content={displaySummary}
            accentColor={meta.color}
          />
        )}
        
        {/* Gradient fade for collapsed state */}
        {!expanded && evidence.summary.length > 200 && (
          <div className="absolute bottom-0 left-0 right-0 h-12 bg-gradient-to-t from-white/90 to-transparent pointer-events-none" />
        )}
      </div>

      <button
        onClick={() => setExpanded(!expanded)}
        className="flex items-center gap-1 text-xs font-medium mt-2 transition-colors hover:opacity-80"
        style={{ color: meta.color }}
      >
        {expanded ? (
          <><ChevronUp className="w-3 h-3" /> Show less</>
        ) : (
          <><ChevronDown className="w-3 h-3" /> Show more</>
        )}
      </button>

      {/* Footer: sources toggle, flags */}
      <div className="flex items-center justify-between mt-3 pt-3 border-t border-gray-100">
        <button
          onClick={() => setShowSources(!showSources)}
          className="flex items-center gap-1.5 text-[11px] font-medium transition-colors hover:opacity-80"
          style={{ color: meta.color }}
        >
          <Link2 className="w-3 h-3" />
          {showSources ? 'Hide Sources' : `Show Sources (${evidence.sources.length})`}
        </button>
        <div className="flex items-center gap-1">
          {evidence.flags.map((flag) => (
            <span
              key={flag}
              className="inline-flex items-center gap-0.5 px-1.5 py-0.5 rounded-full text-[9px] font-bold uppercase tracking-wider"
              style={{
                color: flag === 'error' ? '#DC2626' : '#D97706',
                background: flag === 'error' ? 'rgba(220,38,38,0.08)' : 'rgba(217,119,6,0.08)',
              }}
            >
              <Flag className="w-2.5 h-2.5" />
              {flag}
            </span>
          ))}
        </div>
      </div>

      {/* Sources Panel (toggleable) - Unified citations + links */}
      {showSources && (
        <div className="mt-2 space-y-1 pt-2 border-t border-gray-50">
          {(() => {
            const hasSources = evidence.sources.length > 0
            const hasLinks = evidence.links.length > 0

            if (!hasSources && !hasLinks) {
              return <p className="text-[11px] text-gray-400 italic">No sources available</p>
            }

            // Map sources to links if they exist, otherwise show them separately
            // Assuming sources [1], [2] correspond to links in order if count matches,
            // or just showing them as a combined list.
            const maxCount = Math.max(evidence.sources.length, evidence.links.length)
            const combinedItems = []

            for (let i = 0; i < maxCount; i++) {
              combinedItems.push({
                citation: evidence.sources[i] || null,
                link: evidence.links[i] || null,
              })
            }

            return combinedItems.slice(0, 15).map((item, i) => {
              const displayText = item.link 
                ? (item.link.length > 55 ? item.link.slice(0, 55) + '...' : item.link)
                : (item.citation || 'Source')

              return item.link ? (
                <a
                  key={i}
                  href={item.link}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="flex items-center gap-2 text-[11px] text-blue-500 hover:text-blue-700 transition-colors group"
                >
                  <div className="flex items-center gap-1.5 shrink-0">
                    <ExternalLink className="w-3 h-3" />
                    {item.citation && (
                      <span className="font-bold min-w-[18px] text-gray-400 group-hover:text-blue-400 transition-colors">
                        {item.citation}
                      </span>
                    )}
                  </div>
                  <span className="truncate">{displayText}</span>
                </a>
              ) : (
                <div key={i} className="flex items-center gap-2 text-[11px] text-gray-600">
                  <div className="flex items-center gap-1.5 shrink-0">
                    <BookOpen className="w-3 h-3 text-gray-400" />
                    {item.citation && (
                      <span className="font-bold min-w-[18px] text-gray-400">
                        {item.citation}
                      </span>
                    )}
                  </div>
                  <span className="truncate">{item.citation || 'Unknown Source'}</span>
                </div>
              )
            })
          })()}
        </div>
      )}
    </div>
  )
}
