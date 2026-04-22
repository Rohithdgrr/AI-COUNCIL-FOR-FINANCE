import { useEffect } from 'react'
import { useQueryClient } from '@tanstack/react-query'
import { useWebSocket } from '@/hooks/useWebSocket'

const DASHBOARD_QUERIES = [
  ['market', 'ticker'],
  ['market', 'risk'],
  ['market', 'brand'],
  ['supply-chain-stocks'],
  ['commodity-prices'],
  ['forex-rates'],
  ['risk', 'suppliers'],
  ['risk', 'heatmap'],
  ['health'],
  ['rag', 'stats'],
  ['ingest', 'status'],
  ['models', 'status'],
] as const

export function useDashboardLiveStream() {
  const queryClient = useQueryClient()
  const { on } = useWebSocket('dashboard')

  useEffect(() => {
    const off = on('dashboard_snapshot', () => {
      DASHBOARD_QUERIES.forEach((queryKey) => {
        queryClient.invalidateQueries({ queryKey: [...queryKey] })
      })
    })

    return off
  }, [on, queryClient])
}