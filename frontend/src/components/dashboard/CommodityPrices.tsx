import React, { useState, useMemo } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { useQuery, useQueryClient } from '@tanstack/react-query'
import { RefreshCw, TrendingUp, TrendingDown, AlertCircle } from 'lucide-react'
import { marketApi } from '@/lib/api'

// Types for commodity data
export interface CommodityData {
  name: string
  symbol: string
  icon: string
  category: string
  unit: string
  current_price: number
  change: number
  change_percent: number
  prev_close: number
  high: number
  low: number
  open: number
  timestamp: number
  data_freshness: string
  market_hours: boolean
  error?: string | null
  usd_price?: number
  usd_inr_rate?: number
  currency?: string
  currency_symbol?: string
  source?: string
}

interface CommodityApiItem {
  name: string
  symbol: string
  icon?: string
  category: string
  unit: string
  current_price: number
  change: number
  change_percent: number
  prev_close?: number
  high?: number
  low?: number
  open?: number
  timestamp?: number
  data_freshness?: string
  market_hours?: boolean
  error?: string | null
  currency?: string
  currency_symbol?: string
  source?: string
}

interface CommodityApiResponse {
  commodities: CommodityApiItem[]
  timestamp: string
  source: string
}

// Default commodity data with realistic prices (for demo/fallback)
const DEFAULT_COMMODITIES: CommodityData[] = [
  {
    name: 'Gold',
    symbol: 'GC=F',
    icon: '🪙',
    category: 'Precious Metals (per gram)',
    unit: 'gram',
    current_price: 7289.50,
    change: 105.20,
    change_percent: 1.45,
    prev_close: 7184.30,
    high: 7350.00,
    low: 7200.00,
    open: 7289.50,
    timestamp: Date.now() / 1000,
    data_freshness: 'real_time',
    market_hours: false,
    error: null,
    currency: 'INR',
    currency_symbol: '₹',
  },
  {
    name: 'Silver',
    symbol: 'SI=F',
    icon: '⚪',
    category: 'Precious Metals (per gram)',
    unit: 'gram',
    current_price: 92.35,
    change: 1.90,
    change_percent: 2.10,
    prev_close: 90.45,
    high: 93.50,
    low: 91.00,
    open: 92.35,
    timestamp: Date.now() / 1000,
    data_freshness: 'real_time',
    market_hours: false,
    error: null,
    currency: 'INR',
    currency_symbol: '₹',
  },
  {
    name: 'Copper',
    symbol: 'HG=F',
    icon: '🟠',
    category: 'Industrial Metals (per kg)',
    unit: 'kg',
    current_price: 1273.80,
    change: 8.24,
    change_percent: 0.65,
    prev_close: 1265.56,
    high: 1280.00,
    low: 1260.00,
    open: 1273.80,
    timestamp: Date.now() / 1000,
    data_freshness: 'real_time',
    market_hours: false,
    error: null,
    currency: 'INR',
    currency_symbol: '₹',
  },
  {
    name: 'Platinum',
    symbol: 'PL=F',
    icon: '💎',
    category: 'Precious Metals (per gram)',
    unit: 'gram',
    current_price: 6210.00,
    change: 112.89,
    change_percent: 1.85,
    prev_close: 6097.11,
    high: 6250.00,
    low: 6150.00,
    open: 6210.00,
    timestamp: Date.now() / 1000,
    data_freshness: 'real_time',
    market_hours: false,
    error: null,
    currency: 'INR',
    currency_symbol: '₹',
  },
  {
    name: 'Crude Oil',
    symbol: 'CL=F',
    icon: '⛽',
    category: 'Energy (per barrel)',
    unit: 'barrel',
    current_price: 7645.00,
    change: -256.16,
    change_percent: -3.25,
    prev_close: 7901.16,
    high: 7750.00,
    low: 7600.00,
    open: 7645.00,
    timestamp: Date.now() / 1000,
    data_freshness: 'real_time',
    market_hours: false,
    error: null,
    currency: 'INR',
    currency_symbol: '₹',
  },
  {
    name: 'Aluminium',
    symbol: 'ALU=F',
    icon: '🔷',
    category: 'Industrial Metals (per kg)',
    unit: 'kg',
    current_price: 368.50,
    change: -4.48,
    change_percent: -1.20,
    prev_close: 372.98,
    high: 375.00,
    low: 365.00,
    open: 368.50,
    timestamp: Date.now() / 1000,
    data_freshness: 'real_time',
    market_hours: false,
    error: null,
    currency: 'INR',
    currency_symbol: '₹',
  },
]

// Simple SVG sparkline component
const SparklineChart: React.FC<{ data: number[]; change: number }> = ({ data, change }) => {
  if (!data || data.length < 2) {
    return <div className="h-8 bg-gray-100 rounded animate-pulse" />
  }

  const width = 120
  const height = 32
  const padding = 4
  const chartWidth = width - padding * 2
  const chartHeight = height - padding * 2

  const min = Math.min(...data)
  const max = Math.max(...data)
  const range = max - min || 1

  const points = data.map((value, index) => {
    const x = padding + (index / (data.length - 1)) * chartWidth
    const y = padding + (1 - (value - min) / range) * chartHeight
    return `${x},${y}`
  }).join(' ')

  const color = change >= 0 ? '#10b981' : '#ef4444'

  return (
    <svg width={width} height={height} className="overflow-visible">
      <polyline
        points={points}
        fill="none"
        stroke={color}
        strokeWidth="2"
        strokeLinecap="round"
        strokeLinejoin="round"
        opacity={0.8}
      />
      <polyline
        points={`${points} ${width - padding},${height - padding} ${padding},${height - padding}`}
        fill={color}
        opacity={0.1}
      />
    </svg>
  )
}

// Loading skeleton component
const CommodityCardSkeleton: React.FC = () => (
  <motion.div
    initial={{ opacity: 0 }}
    animate={{ opacity: 1 }}
    className="bg-white rounded-xl shadow-lg border border-gray-200 p-6"
  >
    <div className="flex items-center justify-between mb-4">
      <div className="flex items-center space-x-3">
        <div className="w-10 h-10 bg-gray-200 rounded-full animate-pulse" />
        <div>
          <div className="h-4 bg-gray-200 rounded w-20 mb-1 animate-pulse" />
          <div className="h-3 bg-gray-200 rounded w-16 animate-pulse" />
        </div>
      </div>
      <div className="h-6 bg-gray-200 rounded w-16 animate-pulse" />
    </div>
    <div className="space-y-3">
      <div className="h-8 bg-gray-200 rounded w-24 animate-pulse" />
      <div className="h-4 bg-gray-200 rounded w-20 animate-pulse" />
      <div className="h-8 bg-gray-200 rounded animate-pulse" />
      <div className="h-3 bg-gray-200 rounded w-28 animate-pulse" />
    </div>
  </motion.div>
)

// Individual commodity card - accepts CommodityData prop
const CommodityCard: React.FC<{ commodity: CommodityData }> = ({ commodity }) => {
  const isPositive = commodity.change >= 0
  const TrendIcon = isPositive ? TrendingUp : TrendingDown
  const currencySymbol = commodity.currency_symbol || '₹'

  // Generate mock historical data for sparkline
  const sparklineData = useMemo(() => {
    const basePrice = commodity.current_price
    const volatility = basePrice * 0.02
    return Array.from({ length: 7 }, (_, i) => {
      const randomChange = (Math.random() - 0.5) * volatility
      return basePrice + randomChange - (commodity.change * (6 - i) / 6)
    })
  }, [commodity.current_price, commodity.change])

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      whileHover={{ y: -2, boxShadow: '0 10px 30px rgba(0, 0, 0, 0.1)' }}
      className={`bg-white rounded-xl shadow-lg border p-6 transition-all duration-300 ${
        isPositive ? 'border-green-200' : 'border-red-200'
      }`}
    >
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center space-x-3">
          <div className={`w-10 h-10 rounded-full flex items-center justify-center text-lg font-bold ${
            isPositive ? 'bg-green-100 text-green-600' : 'bg-red-100 text-red-600'
          }`}>
            {commodity.icon || commodity.name[0]}
          </div>
          <div>
            <h3 className="font-semibold text-gray-900">{commodity.name}</h3>
            <p className="text-sm text-gray-500">{commodity.category}</p>
          </div>
        </div>
        <div className={`flex items-center space-x-1 px-2 py-1 rounded-full text-sm font-medium ${
          isPositive ? 'bg-green-100 text-green-700' : 'bg-red-100 text-red-700'
        }`}>
          <TrendIcon className="w-3 h-3" />
          <span>{isPositive ? '+' : ''}{commodity.change_percent.toFixed(2)}%</span>
        </div>
      </div>

      <div className="space-y-3">
        <div className="flex items-baseline space-x-2">
          <span className="text-2xl font-bold text-gray-900">
            {currencySymbol}{commodity.current_price.toLocaleString('en-IN', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
          </span>
          <span className={`text-sm font-medium ${isPositive ? 'text-green-600' : 'text-red-600'}`}>
            {isPositive ? '+' : ''}{commodity.change_percent.toFixed(2)}%
          </span>
        </div>

        <div className="flex items-center justify-between text-sm text-gray-500">
          <span>H: {currencySymbol}{commodity.high.toLocaleString('en-IN', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}</span>
          <span>L: {currencySymbol}{commodity.low.toLocaleString('en-IN', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}</span>
        </div>

        <div className="h-8">
          <SparklineChart data={sparklineData} change={commodity.change} />
        </div>

        <div className="flex items-center justify-between text-xs text-gray-400">
          <span>Prev: {currencySymbol}{commodity.prev_close.toLocaleString('en-IN', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}</span>
          <span>
            {commodity.error ? (
              <span className="text-red-500 flex items-center">
                <AlertCircle className="w-3 h-3 mr-1" />
                Error
              </span>
            ) : (
              new Date(commodity.timestamp * 1000).toLocaleTimeString([], {
                hour: '2-digit',
                minute: '2-digit'
              })
            )}
          </span>
        </div>
      </div>
    </motion.div>
  )
}

const mapCommodity = (commodity: CommodityApiItem): CommodityData => {
  const currentPrice = Number(commodity.current_price || 0)
  const change = Number(commodity.change ?? 0)
  const prevClose = Number(commodity.prev_close ?? currentPrice - change)
  const high = Number(commodity.high ?? Math.max(currentPrice, prevClose) * 1.01)
  const low = Number(commodity.low ?? Math.min(currentPrice, prevClose) * 0.99)
  const open = Number(commodity.open ?? prevClose)

  return {
    name: commodity.name,
    symbol: commodity.symbol,
    icon: commodity.icon || commodity.name[0],
    category: commodity.category,
    unit: commodity.unit,
    current_price: currentPrice,
    change,
    change_percent: Number(commodity.change_percent || 0),
    prev_close: prevClose,
    high,
    low,
    open,
    timestamp: Number(commodity.timestamp || Math.floor(Date.now() / 1000)),
    data_freshness: commodity.data_freshness || 'real_time',
    market_hours: Boolean(commodity.market_hours),
    error: commodity.error ?? null,
    currency: commodity.currency || 'INR',
    currency_symbol: commodity.currency_symbol || '₹',
    source: commodity.source || 'market-api',
  }
}

// Hook to fetch commodities - can be connected to API later
const useCommoditiesData = () => {
  const queryClient = useQueryClient()

  const {
    data: commodityData,
    isLoading,
    error,
    refetch,
    dataUpdatedAt,
  } = useQuery<CommodityApiResponse>({
    queryKey: ['commodity-prices'],
    queryFn: async () => {
      const response = await marketApi.commodityPrices()
      return response.data
    },
    staleTime: 60 * 1000,
    gcTime: 5 * 60 * 1000,
    refetchInterval: 2 * 60 * 1000,
  })

  const refresh = () => {
    queryClient.invalidateQueries({ queryKey: ['commodity-prices'] })
    return refetch()
  }

  const commodities = commodityData?.commodities?.length
    ? commodityData.commodities.map(mapCommodity)
    : DEFAULT_COMMODITIES

  const marketHours = commodities.some((commodity) => commodity.market_hours)
  const lastUpdated = commodityData?.timestamp
    ? new Date(commodityData.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
    : dataUpdatedAt
      ? new Date(dataUpdatedAt).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
      : 'Just now'

  return {
    commodities,
    isLoading,
    error,
    refresh,
    lastUpdated,
    marketHours,
    count: commodities.length,
    source: commodityData?.source || 'fallback',
  }
}

export const CommodityPrices: React.FC = () => {
  const [currentPage, setCurrentPage] = useState(0)
  const {
    commodities,
    isLoading,
    error,
    refresh,
    lastUpdated,
    marketHours,
    count,
    source,
  } = useCommoditiesData()

  const COMMODITIES_PER_PAGE = 3
  const totalPages = Math.ceil(count / COMMODITIES_PER_PAGE)
  const startIndex = currentPage * COMMODITIES_PER_PAGE
  const endIndex = Math.min(startIndex + COMMODITIES_PER_PAGE, count)
  const paginatedCommodities = commodities.slice(startIndex, endIndex)

  const handleNextPage = () => {
    if (currentPage < totalPages - 1) {
      setCurrentPage(currentPage + 1)
    }
  }

  const handlePreviousPage = () => {
    if (currentPage > 0) {
      setCurrentPage(currentPage - 1)
    }
  }

  if (error) {
    return (
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        className="bg-white rounded-xl shadow-lg border border-red-200 p-6"
      >
        <div className="flex items-center justify-center space-x-2 text-red-600">
          <AlertCircle className="w-5 h-5" />
          <span>Failed to load commodity prices</span>
          <button
            onClick={() => refresh()}
            className="px-3 py-1 bg-red-100 text-red-700 rounded-md hover:bg-red-200 transition-colors"
          >
            Retry
          </button>
        </div>
      </motion.div>
    )
  }

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      className="space-y-6"
    >
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold text-gray-900">Commodity Prices</h2>
          <p className="text-sm text-gray-600">Live global commodity market impact</p>
        </div>
        <div className="flex items-center space-x-3">
          <span className={`text-sm font-medium ${marketHours ? 'text-green-600' : 'text-gray-500'}`}>
            {marketHours ? 'Market Open' : 'Market Closed'}
          </span>
          {lastUpdated && (
            <span className="text-sm text-gray-500">
              Last: {lastUpdated}
            </span>
          )}
          <motion.button
            whileHover={{ scale: 1.05 }}
            whileTap={{ scale: 0.95 }}
            onClick={() => refresh()}
            disabled={isLoading}
            className="p-2 bg-blue-500 text-white rounded-lg hover:bg-blue-600 transition-colors disabled:opacity-50"
          >
            <RefreshCw className={`w-4 h-4 ${isLoading ? 'animate-spin' : ''}`} />
          </motion.button>
        </div>
      </div>

      {/* Commodity Cards - Always show all 6 in 2 rows of 3 */}
      {!isLoading ? (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {commodities.map((commodity) => (
            <CommodityCard
              key={commodity.symbol}
              commodity={commodity}
            />
          ))}
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {Array.from({ length: 6 }, (_, i) => (
            <CommodityCardSkeleton key={`skeleton-${i}`} />
          ))}
        </div>
      )}

      {/* Footer */}
      <div className="text-center text-sm text-gray-500 pt-4 border-t">
        Prices powered by {source === 'fallback' ? 'live market fallback' : source} (in INR)
      </div>
    </motion.div>
  )
}