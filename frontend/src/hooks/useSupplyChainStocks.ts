import { useQuery, useQueryClient } from '@tanstack/react-query'
import { marketApi } from '@/lib/api'

export interface StockData {
  ticker: string
  companyName: string
  price: number
  changePercent: number
  riskScore: number
  sector: string
  data_freshness?: string
  market_hours?: boolean
  timestamp?: number
}

export interface SupplyChainStocksResponse {
  stocks: StockData[]
  timestamp: string
}

export function useSupplyChainStocks() {
  const queryClient = useQueryClient()

  const {
    data: stocksData,
    isLoading,
    error,
    refetch,
    dataUpdatedAt,
  } = useQuery<SupplyChainStocksResponse>({
    queryKey: ['supply-chain-stocks'],
    queryFn: async () => {
      const response = await marketApi.supplyChainStocks()
      return response.data
    },
    staleTime: 60 * 1000, // 1 minute
    gcTime: 5 * 60 * 1000, // 5 minutes
    refetchInterval: 5 * 60 * 1000, // 5 minutes auto-refresh
  })

  const refresh = () => {
    queryClient.invalidateQueries({ queryKey: ['supply-chain-stocks'] })
    return refetch()
  }

  const refreshStocks = refresh

  const getTimeSinceUpdate = () => {
    if (!dataUpdatedAt) return null
    const now = Date.now()
    const diff = now - dataUpdatedAt
    const minutes = Math.floor(diff / (1000 * 60))
    
    if (minutes < 1) return 'Just now'
    if (minutes === 1) return '1 min ago'
    return `${minutes} min ago`
  }

  const getFreshnessLabel = () => {
    if (!stocksData) return 'Unknown'
    const freshness = (stocksData as any).data_freshness || 'real_time'
    return freshness === 'real_time' ? 'Live' : 'Delayed'
  }

  const getFreshnessColor = () => {
    const freshness = (stocksData as any)?.data_freshness || 'real_time'
    return freshness === 'real_time' ? 'text-green-600' : 'text-amber-600'
  }

  return {
    data: stocksData,
    isLoading,
    error,
    refresh,
    refreshStocks,
    getTimeSinceUpdate,
    getFreshnessLabel,
    getFreshnessColor,
    timestamp: stocksData?.timestamp || 0,
  }
}
