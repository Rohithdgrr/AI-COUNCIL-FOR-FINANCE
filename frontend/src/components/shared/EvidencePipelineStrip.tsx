import { Database, Globe, Cpu, Search, GitBranch, Check, Loader2 } from 'lucide-react'
import type { SupportAgentPolicy } from '@/types/council'

type StageStatus = 'idle' | 'active' | 'done'

interface EvidencePipelineStripProps {
  policy: SupportAgentPolicy
  stages: {
    rag_fetching: StageStatus
    api_called: StageStatus
    mcp_fetched: StageStatus
    sources_ready: StageStatus
  }
  counts: {
    rag_fetching: number
    api_called: number
    mcp_fetched: number
    sources_ready: number
  }
}

const STAGE_CONFIG = [
  { key: 'rag_fetching', label: 'RAG', icon: <Database className="w-3 h-3" />, color: '#7c3aed', policyKey: 'rag' as const },
  { key: 'api_called', label: 'APIs', icon: <Globe className="w-3 h-3" />, color: '#0ea5e9', policyKey: 'api' as const },
  { key: 'mcp_fetched', label: 'Web/MCP', icon: <Cpu className="w-3 h-3" />, color: '#f59e0b', policyKey: 'mcp' as const },
  { key: 'mcp_web', label: 'Scraping', icon: <Search className="w-3 h-3" />, color: '#ec4899', policyKey: 'web' as const },
  { key: 'mcp_graph', label: 'Graph/DB', icon: <GitBranch className="w-3 h-3" />, color: '#059669', policyKey: 'graph' as const },
]

export default function EvidencePipelineStrip({ policy, stages, counts }: EvidencePipelineStripProps) {
  const activeStages = STAGE_CONFIG.filter((s) => policy[s.policyKey] !== false)

  if (activeStages.length === 0) return null

  return (
    <div className="flex items-center gap-1.5 flex-wrap">
      {activeStages.map((cfg, idx) => {
        const stageKey = cfg.key as keyof typeof stages
        const status: StageStatus = stages[stageKey] || 'idle'
        const count: number = counts[stageKey] || 0
        const isActive = status === 'active'
        const isDone = status === 'done'
        const isIdle = status === 'idle'

        return (
          <div key={cfg.key} className="flex items-center gap-1">
            <div
              className="flex items-center gap-1 px-2.5 py-1 rounded-full text-[10px] font-bold transition-all duration-300"
              style={{
                background: isDone ? `${cfg.color}12` : isActive ? `${cfg.color}15` : 'rgba(148,163,184,0.06)',
                color: isDone || isActive ? cfg.color : '#94a3b8',
                border: `1px solid ${isDone ? `${cfg.color}30` : isActive ? `${cfg.color}40` : 'transparent'}`,
                boxShadow: isActive ? `0 0 8px ${cfg.color}20` : 'none',
                opacity: isIdle ? 0.5 : 1,
              }}
            >
              <span style={{ color: isDone || isActive ? cfg.color : '#94a3b8' }}>
                {isDone ? <Check className="w-3 h-3" /> : cfg.icon}
              </span>
              <span>{cfg.label}</span>
              {isActive && <Loader2 className="w-2.5 h-2.5 animate-spin" style={{ color: cfg.color }} />}
              {isDone && count > 0 && (
                <span
                  className="ml-0.5 px-1 py-0.5 rounded-full text-[8px] font-black text-white"
                  style={{ background: cfg.color }}
                >
                  {count}
                </span>
              )}
            </div>
            {idx < activeStages.length - 1 && (
              <span className="text-gray-300 text-[9px]">→</span>
            )}
          </div>
        )
      })}
    </div>
  )
}
