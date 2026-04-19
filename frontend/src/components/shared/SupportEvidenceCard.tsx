import { useState } from 'react'
import { ChevronDown, ExternalLink, Flag, BookOpen } from 'lucide-react'
import type { SupportEvidence } from '@/types/council'
import { COUNCIL_AGENTS } from '@/types/council'
import ConfidenceBadge from './ConfidenceBadge'

interface SupportEvidenceCardProps {
  evidence: SupportEvidence
  defaultExpanded?: boolean
}

export default function SupportEvidenceCard({ evidence, defaultExpanded = false }: SupportEvidenceCardProps) {
  const [expanded, setExpanded] = useState(defaultExpanded)
  const agentInfo = COUNCIL_AGENTS.find((a) => a.key === evidence.agent)
  const agentColor = agentInfo?.hexColor || '#6B7280'
  const agentLabel = agentInfo?.label || evidence.agent

  const summaryLines = evidence.summary
    .split('\n')
    .filter((l) => l.trim())
    .slice(0, expanded ? undefined : 3)

  return (
    <div
      className="rounded-2xl border bg-white/80 backdrop-blur-md p-4 transition-all duration-200 hover:shadow-md"
      style={{
        borderColor: `${agentColor}30`,
        background: `linear-gradient(135deg, rgba(255,255,255,0.9) 0%, ${agentColor}05 100%)`,
      }}
    >
      {/* Header */}
      <div className="flex items-center justify-between gap-2 mb-3">
        <div className="flex items-center gap-2">
          <span className="w-2.5 h-2.5 rounded-full shrink-0" style={{ backgroundColor: agentColor }} />
          <span className="text-sm font-bold text-gray-900 truncate">{agentLabel}</span>
          <span className="text-[10px] font-semibold uppercase tracking-wider text-gray-400">Support</span>
        </div>
        <ConfidenceBadge confidence={evidence.confidence} size="sm" />
      </div>

      {/* Summary */}
      <div className="text-sm text-gray-700 leading-relaxed space-y-1">
        {summaryLines.length === 0 && (
          <p className="text-gray-400 italic">No evidence collected</p>
        )}
        {summaryLines.map((line, i) => (
          <p key={i} className="whitespace-pre-wrap">{line}</p>
        ))}
        {!expanded && evidence.summary.split('\n').filter((l) => l.trim()).length > 3 && (
          <button
            onClick={() => setExpanded(true)}
            className="flex items-center gap-1 text-xs font-medium mt-1 transition-colors hover:opacity-80"
            style={{ color: agentColor }}
          >
            <ChevronDown className="w-3 h-3" />
            Show more
          </button>
        )}
        {expanded && (
          <button
            onClick={() => setExpanded(false)}
            className="flex items-center gap-1 text-xs font-medium mt-1 transition-colors hover:opacity-80"
            style={{ color: agentColor }}
          >
            <ChevronDown className="w-3 h-3 rotate-180" />
            Show less
          </button>
        )}
      </div>

      {/* Meta row: sources + flags */}
      <div className="flex items-center justify-between mt-3 pt-3 border-t border-gray-100">
        <div className="flex items-center gap-1.5 text-[11px] text-gray-400">
          <BookOpen className="w-3 h-3" />
          <span>{evidence.sources.length} sources</span>
        </div>
        {evidence.flags.length > 0 && (
          <div className="flex items-center gap-1">
            {evidence.flags.map((flag) => (
              <span
                key={flag}
                className="inline-flex items-center gap-0.5 px-1.5 py-0.5 rounded-full text-[9px] font-bold uppercase tracking-wider"
                style={{
                  color: flag === 'contradiction' ? '#DC2626' : flag === 'low_confidence' ? '#D97706' : '#6B7280',
                  background: flag === 'contradiction' ? 'rgba(220,38,38,0.08)' : flag === 'low_confidence' ? 'rgba(217,119,6,0.08)' : 'rgba(107,114,128,0.08)',
                }}
              >
                <Flag className="w-2.5 h-2.5" />
                {flag.replace(/_/g, ' ')}
              </span>
            ))}
          </div>
        )}
      </div>

      {/* Links (expanded only) */}
      {expanded && evidence.links.length > 0 && (
        <div className="mt-3 pt-3 border-t border-gray-100 space-y-1">
          {evidence.links.slice(0, 4).map((link, i) => (
            <a
              key={i}
              href={link}
              target="_blank"
              rel="noopener noreferrer"
              className="flex items-center gap-1.5 text-[11px] text-blue-600 hover:text-blue-800 truncate transition-colors"
            >
              <ExternalLink className="w-3 h-3 shrink-0" />
              {link.length > 60 ? link.slice(0, 60) + '...' : link}
            </a>
          ))}
        </div>
      )}
    </div>
  )
}
