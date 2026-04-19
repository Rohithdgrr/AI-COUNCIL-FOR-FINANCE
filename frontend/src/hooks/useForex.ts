import { useQuery, useQueryClient } from '@tanstack/react-query'
import { marketApi } from '@/lib/api'

export interface ForexCurrency {
  code: string
  name: string
  country: string
  flag: string
  rate: number
  change: number
  change_percent: number
  symbol: string
  timestamp: number
}

export interface ForexResponse {
  currencies: ForexCurrency[]
  base_currency: string
  timestamp: number
  count: number
}

const CURRENCIES = [
  { code: 'INR', name: 'Indian Rupee', country: 'India', flag: '🇮🇳', symbol: 'INR=X' },
  { code: 'AUD', name: 'Australian Dollar', country: 'Australia', flag: '🇦🇺', symbol: 'AUD=X' },
  { code: 'CNY', name: 'Chinese Yuan', country: 'China', flag: '🇨🇳', symbol: 'CNY=X' },
  { code: 'EUR', name: 'Euro', country: 'Eurozone', flag: '🇪🇺', symbol: 'EUR=X' },
  { code: 'GBP', name: 'British Pound', country: 'United Kingdom', flag: '🇬🇧', symbol: 'GBP=X' },
  { code: 'KWD', name: 'Kuwaiti Dinar', country: 'Kuwait', flag: '🇰🇼', symbol: 'KWD=X' },
  { code: 'JPY', name: 'Japanese Yen', country: 'Japan', flag: '🇯🇵', symbol: 'JPY=X' },
  { code: 'USD', name: 'US Dollar', country: 'United States', flag: '🇺🇸', symbol: 'USD=X' },
  { code: 'SAR', name: 'Saudi Riyal', country: 'Saudi Arabia', flag: '🇸🇦', symbol: 'SAR=X' },
]

export function useForex() {
  const queryClient = useQueryClient()

  const {
    data: forexData,
    isLoading,
    error,
    refetch,
    dataUpdatedAt,
  } = useQuery<ForexResponse>({
    queryKey: ['forex-rates'],
    queryFn: async () => {
      const response = await marketApi.forexRates()
      return response.data
    },
    staleTime: 60 * 1000, // 1 minute
    gcTime: 5 * 60 * 1000, // 5 minutes
    refetchInterval: 2 * 60 * 1000, // 2 minutes auto-refresh
  })

  const refresh = () => {
    queryClient.invalidateQueries({ queryKey: ['forex-rates'] })
    return refetch()
  }

  const getTimeSinceUpdate = () => {
    if (!dataUpdatedAt) return null
    const now = Date.now()
    const diff = now - dataUpdatedAt
    const minutes = Math.floor(diff / (1000 * 60))
    
    if (minutes < 1) return 'Just now'
    if (minutes === 1) return '1 min ago'
    return `${minutes} min ago`
  }

  return {
    currencies: forexData?.currencies || [],
    isLoading,
    error,
    refresh,
    lastUpdated: getTimeSinceUpdate(),
    timestamp: forexData?.timestamp || 0,
    count: forexData?.count || 0,
  }
}

export { CURRENCIES }
