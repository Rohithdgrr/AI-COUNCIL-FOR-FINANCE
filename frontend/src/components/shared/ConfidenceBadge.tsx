import { ShieldCheck, AlertTriangle, XCircle } from 'lucide-react'

interface ConfidenceBadgeProps {
  confidence: number
  size?: 'sm' | 'md' | 'lg'
  showLabel?: boolean
}

function getConfidenceTier(confidence: number) {
  if (confidence >= 70) return { color: '#059669', bg: 'rgba(5,150,105,0.1)', border: 'rgba(5,150,105,0.3)', label: 'High', icon: ShieldCheck }
  if (confidence >= 40) return { color: '#D97706', bg: 'rgba(217,119,6,0.1)', border: 'rgba(217,119,6,0.3)', label: 'Medium', icon: AlertTriangle }
  return { color: '#DC2626', bg: 'rgba(220,38,38,0.1)', border: 'rgba(220,38,38,0.3)', label: 'Low', icon: XCircle }
}

const sizeClasses = {
  sm: 'px-2 py-0.5 text-[10px] gap-1',
  md: 'px-3 py-1 text-xs gap-1.5',
  lg: 'px-4 py-1.5 text-sm gap-2',
}

export default function ConfidenceBadge({ confidence, size = 'md', showLabel = false }: ConfidenceBadgeProps) {
  const tier = getConfidenceTier(confidence)
  const Icon = tier.icon
  const sizeClass = sizeClasses[size]

  return (
    <span
      className={`inline-flex items-center rounded-full font-bold ${sizeClass}`}
      style={{
        color: tier.color,
        background: tier.bg,
        border: `1px solid ${tier.border}`,
      }}
    >
      <Icon className={size === 'sm' ? 'w-3 h-3' : size === 'lg' ? 'w-4 h-4' : 'w-3.5 h-3.5'} />
      <span>{Math.round(confidence)}%</span>
      {showLabel && <span className="opacity-70 ml-0.5">{tier.label}</span>}
    </span>
  )
}
