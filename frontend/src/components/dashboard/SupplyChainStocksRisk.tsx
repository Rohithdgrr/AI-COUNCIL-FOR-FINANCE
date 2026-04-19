import { useState, useMemo } from 'react'
import { motion } from 'framer-motion'
import { 
  TrendingUp, TrendingDown, AlertTriangle, 
  RefreshCw, Filter, ArrowUpDown, Search,
  Building2, Package, Truck, Zap, Cpu
} from 'lucide-react'
import { useSupplyChainStocks } from '@/hooks/useSupplyChainStocks'

// Loading skeleton component
const LoadingSkeleton = () => (
  <div className="space-y-3">
    {Array.from({ length: 5 }, (_, i) => (
      <div key={i} className="grid grid-cols-7 gap-4 p-3 rounded-lg border border-gray-100">
        <div className="flex items-center gap-3">
          <div className="w-8 h-8 rounded-lg bg-gray-200 animate-pulse"></div>
          <div className="flex-1">
            <div className="h-4 bg-gray-200 rounded animate-pulse mb-1"></div>
            <div className="h-3 bg-gray-200 rounded animate-pulse w-20"></div>
          </div>
        </div>
        <div className="h-4 bg-gray-200 rounded animate-pulse"></div>
        <div className="h-4 bg-gray-200 rounded animate-pulse"></div>
        <div className="h-4 bg-gray-200 rounded animate-pulse"></div>
        <div className="h-4 bg-gray-200 rounded animate-pulse"></div>
        <div className="h-3 bg-gray-200 rounded animate-pulse"></div>
        <div className="h-4 bg-gray-200 rounded animate-pulse w-16"></div>
      </div>
    ))}
  </div>
)

interface StockRiskData {
  ticker: string
  companyName: string
  currentPrice: number
  changePercent: number
  riskScore: number
  sector: string
  reason: string
  data_freshness?: string
  market_hours?: boolean
  timestamp?: number
}

const SECTOR_ICONS: Record<string, typeof Building2> = {
  'Semiconductors': Cpu,
  'Automotive': Truck,
  'Pharma': Package,
  'Technology': Zap,
  'Manufacturing': Building2,
  'Retail': Package,
  'Energy': Zap,
  'Materials': Package
}

const SECTOR_COLORS: Record<string, string> = {
  'Semiconductors': 'from-blue-500 to-blue-600',
  'Automotive': 'from-gray-500 to-gray-600',
  'Pharma': 'from-green-500 to-green-600',
  'Technology': 'from-purple-500 to-purple-600',
  'Manufacturing': 'from-orange-500 to-orange-600',
  'Retail': 'from-pink-500 to-pink-600',
  'Energy': 'from-yellow-500 to-yellow-600',
  'Materials': 'from-brown-500 to-brown-600'
}

// Static risk assessment data for 30 supply chain stocks
const SUPPLY_CHAIN_RISK_DATA: Record<string, Omit<StockRiskData, 'currentPrice' | 'changePercent' | 'data_freshness' | 'market_hours' | 'timestamp'>> = {
  // Semiconductors
  'NVDA': { ticker: 'NVDA', companyName: 'NVIDIA Corporation', riskScore: 85, sector: 'Semiconductors', reason: 'Critical AI chip supply chain concentration in Taiwan' },
  'TSM': { ticker: 'TSM', companyName: 'Taiwan Semiconductor', riskScore: 90, sector: 'Semiconductors', reason: 'Geopolitical risk - China tensions over Taiwan' },
  'ASML': { ticker: 'ASML', companyName: 'ASML Holding', riskScore: 78, sector: 'Semiconductors', reason: 'Monopoly on EUV lithography equipment supply chain' },
  'AMD': { ticker: 'AMD', companyName: 'Advanced Micro Devices', riskScore: 75, sector: 'Semiconductors', reason: 'Foundry dependency and global chip shortage risks' },
  'AVGO': { ticker: 'AVGO', companyName: 'Broadcom Inc.', riskScore: 72, sector: 'Semiconductors', reason: 'Semiconductor supply chain and component sourcing' },
  'MU': { ticker: 'MU', companyName: 'Micron Technology', riskScore: 68, sector: 'Semiconductors', reason: 'Memory chip manufacturing concentration in Asia' },
  'QCOM': { ticker: 'QCOM', companyName: 'Qualcomm Inc.', riskScore: 65, sector: 'Semiconductors', reason: 'Mobile chip supply chain and licensing risks' },
  'INTC': { ticker: 'INTC', companyName: 'Intel Corporation', riskScore: 70, sector: 'Semiconductors', reason: 'Manufacturing constraints and geopolitical tensions' },
  'AMAT': { ticker: 'AMAT', companyName: 'Applied Materials', riskScore: 67, sector: 'Semiconductors', reason: 'Semiconductor equipment supply chain dependencies' },
  'LRCX': { ticker: 'LRCX', companyName: 'Lam Research', riskScore: 66, sector: 'Semiconductors', reason: 'Etching equipment supply chain concentration' },
  
  // Automotive
  'TSLA': { ticker: 'TSLA', companyName: 'Tesla Inc.', riskScore: 80, sector: 'Automotive', reason: 'Battery supply chain and raw material constraints' },
  'TM': { ticker: 'TM', companyName: 'Toyota Motor', riskScore: 65, sector: 'Automotive', reason: 'Global semiconductor shortage affecting production' },
  'F': { ticker: 'F', companyName: 'Ford Motor Company', riskScore: 78, sector: 'Automotive', reason: 'Chip shortage impact and parts sourcing issues' },
  'GM': { ticker: 'GM', companyName: 'General Motors', riskScore: 75, sector: 'Automotive', reason: 'Electronics component shortages and logistics delays' },
  'STLA': { ticker: 'STLA', companyName: 'Stellantis NV', riskScore: 70, sector: 'Automotive', reason: 'European supply chain disruptions and energy costs' },
  'HMC': { ticker: 'HMC', companyName: 'Honda Motor', riskScore: 68, sector: 'Automotive', reason: 'Asian supply chain dependency and export risks' },
  
  // Pharma
  'LLY': { ticker: 'LLY', companyName: 'Eli Lilly', riskScore: 55, sector: 'Pharma', reason: 'Global API sourcing and manufacturing dependencies' },
  'JNJ': { ticker: 'JNJ', companyName: 'Johnson & Johnson', riskScore: 48, sector: 'Pharma', reason: 'Medical device supply chain and regulatory risks' },
  'PFE': { ticker: 'PFE', companyName: 'Pfizer Inc.', riskScore: 52, sector: 'Pharma', reason: 'Raw material sourcing from Asia-Pacific region' },
  'MRK': { ticker: 'MRK', companyName: 'Merck & Co.', riskScore: 50, sector: 'Pharma', reason: 'Vaccine production and cold chain logistics' },
  'AZN': { ticker: 'AZN', companyName: 'AstraZeneca', riskScore: 54, sector: 'Pharma', reason: 'Global clinical trial and manufacturing network' },
  'NVO': { ticker: 'NVO', companyName: 'Novo Nordisk', riskScore: 58, sector: 'Pharma', reason: 'Specialized drug manufacturing and supply chain' },
  
  // Industrial / Manufacturing
  'CAT': { ticker: 'CAT', companyName: 'Caterpillar Inc.', riskScore: 72, sector: 'Industrial', reason: 'Steel and component supply chain disruptions' },
  'HON': { ticker: 'HON', companyName: 'Honeywell', riskScore: 60, sector: 'Industrial', reason: 'Aerospace and industrial component supply chain' },
  'GE': { ticker: 'GE', companyName: 'General Electric', riskScore: 65, sector: 'Industrial', reason: 'Aviation and energy equipment supply chain' },
  'DE': { ticker: 'DE', companyName: 'Deere & Co.', riskScore: 68, sector: 'Industrial', reason: 'Agricultural equipment and electronics supply chain' },
  
  // Electronics / Tech
  'AAPL': { ticker: 'AAPL', companyName: 'Apple Inc.', riskScore: 75, sector: 'Electronics', reason: 'China manufacturing dependency and Red Sea disruptions' },
  'MSFT': { ticker: 'MSFT', companyName: 'Microsoft Corporation', riskScore: 45, sector: 'Electronics', reason: 'Hardware manufacturing dependencies' },
  'AMZN': { ticker: 'AMZN', companyName: 'Amazon.com Inc.', riskScore: 58, sector: 'Electronics', reason: 'Cloud infrastructure and device supply chain' },
  'BABA': { ticker: 'BABA', companyName: 'Alibaba Group', riskScore: 70, sector: 'Electronics', reason: 'Chinese regulatory and export control risks' },
  'SONY': { ticker: 'SONY', companyName: 'Sony Corporation', riskScore: 62, sector: 'Electronics', reason: 'Imaging sensor supply chain concentration' },
  
  // Logistics
  'ZTO': { ticker: 'ZTO', companyName: 'ZTO Express', riskScore: 73, sector: 'Logistics', reason: 'Chinese logistics network and export dependencies' },
  'FDX': { ticker: 'FDX', companyName: 'FedEx Corporation', riskScore: 55, sector: 'Logistics', reason: 'Global shipping network and fuel price volatility' },
  'UPS': { ticker: 'UPS', companyName: 'United Parcel Service', riskScore: 53, sector: 'Logistics', reason: 'International shipping and customs delays' },
  'MAERSK': { ticker: 'MAERSK', companyName: 'A.P. Moller-Maersk', riskScore: 78, sector: 'Logistics', reason: 'Red Sea disruptions and global container shipping' }
}

type SortField = 'riskScore' | 'changePercent' | 'currentPrice'
type FilterType = 'all' | 'highRisk' | 'disasterAffected'

export default function SupplyChainStocksRisk() {
  const { 
    data: stocksData, 
    isLoading, 
    error, 
    refreshStocks, 
    getTimeSinceUpdate, 
    getFreshnessLabel, 
    getFreshnessColor 
  } = useSupplyChainStocks()
  
  const [sortField, setSortField] = useState<SortField>('riskScore')
  const [sortDirection, setSortDirection] = useState<'asc' | 'desc'>('desc')
  const [filterType, setFilterType] = useState<FilterType>('all')
  const [searchTerm, setSearchTerm] = useState('')
  const [isRefreshing, setIsRefreshing] = useState(false)
  const [currentPage, setCurrentPage] = useState(1)
  
  const STOCKS_PER_PAGE = 5

  // Combine real stock data with risk assessment data
  const stocks = useMemo(() => {
    if (!stocksData?.stocks) return []
    
    return stocksData.stocks
      .map((stock: any) => {
        const riskData = SUPPLY_CHAIN_RISK_DATA[stock.symbol]
        if (!riskData) return null
        
        return {
          ticker: stock.symbol,
          companyName: riskData.companyName,
          currentPrice: stock.current_price,
          changePercent: stock.change_percent,
          riskScore: riskData.riskScore,
          sector: riskData.sector,
          reason: riskData.reason,
          data_freshness: stock.data_freshness,
          market_hours: stock.market_hours,
          timestamp: stock.timestamp,
          error: stock.error
        }
      })
      .filter((stock: any): stock is StockRiskData => stock !== null)
  }, [stocksData])

  const filteredAndSortedStocks = useMemo(() => {
    let filtered = stocks

    // Apply filter
    if (filterType === 'highRisk') {
      filtered = filtered.filter((stock) => stock.riskScore > 70)
    } else if (filterType === 'disasterAffected') {
      filtered = filtered.filter((stock) => 
        stock.reason.toLowerCase().includes('disaster') ||
        stock.reason.toLowerCase().includes('war') ||
        stock.reason.toLowerCase().includes('geopolitical')
      )
    }

    // Apply search
    if (searchTerm) {
      filtered = filtered.filter((stock) =>
        stock.ticker.toLowerCase().includes(searchTerm.toLowerCase()) ||
        stock.companyName.toLowerCase().includes(searchTerm.toLowerCase()) ||
        stock.sector.toLowerCase().includes(searchTerm.toLowerCase())
      )
    }

    // Apply sorting
    filtered = [...filtered].sort((a, b) => {
      const aValue = a[sortField]
      const bValue = b[sortField]
      const multiplier = sortDirection === 'asc' ? 1 : -1
      return (aValue - bValue) * multiplier
    })

    return filtered
  }, [stocks, sortField, sortDirection, filterType, searchTerm])

  // Pagination calculations
  const totalPages = Math.ceil(filteredAndSortedStocks.length / STOCKS_PER_PAGE)
  const startIndex = (currentPage - 1) * STOCKS_PER_PAGE
  const endIndex = startIndex + STOCKS_PER_PAGE
  const paginatedStocks = filteredAndSortedStocks.slice(startIndex, endIndex)

  // Reset to page 1 when filters change
  useMemo(() => {
    setCurrentPage(1)
  }, [filterType, searchTerm])

  const handlePageChange = (page: number) => {
    setCurrentPage(page)
  }

  const handleNextPage = () => {
    if (currentPage < totalPages) {
      setCurrentPage(currentPage + 1)
    }
  }

  const handlePrevPage = () => {
    if (currentPage > 1) {
      setCurrentPage(currentPage - 1)
    }
  }

  const handleSort = (field: SortField) => {
    if (sortField === field) {
      setSortDirection(sortDirection === 'asc' ? 'desc' : 'asc')
    } else {
      setSortField(field)
      setSortDirection('desc')
    }
  }

  const handleRefresh = async () => {
    setIsRefreshing(true)
    await refreshStocks()
    setIsRefreshing(false)
  }

  const getRiskColor = (score: number) => {
    if (score < 30) return 'text-emerald-600 bg-emerald-50 border-emerald-200'
    if (score < 70) return 'text-amber-600 bg-amber-50 border-amber-200'
    return 'text-red-600 bg-red-50 border-red-200'
  }

  const getRiskLabel = (score: number) => {
    if (score < 30) return 'Low'
    if (score < 70) return 'Medium'
    return 'High'
  }

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      className="bg-white/70 backdrop-blur-xl rounded-2xl border border-white/80 shadow-[0_8px_30px_rgb(0,0,0,0.04)] p-6"
    >
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-red-500 to-orange-500 flex items-center justify-center shadow-lg">
            <AlertTriangle className="w-5 h-5 text-white" />
          </div>
          <div>
            <h3 className="text-lg font-bold text-gray-900">Top 30 Stocks Impacted by Supply Chain Risks</h3>
            <p className="text-xs text-gray-500">Real-time risk assessment and market impact</p>
          </div>
        </div>
        <div className="flex items-center gap-3">
          {stocksData?.timestamp && (
            <span className="text-xs text-gray-500">
              Last Updated: {getTimeSinceUpdate(stocksData.timestamp)}
            </span>
          )}
          <button
            onClick={handleRefresh}
            disabled={isRefreshing}
            className="flex items-center gap-2 px-4 py-2 bg-gray-50 hover:bg-gray-100 border border-gray-200 rounded-lg transition-all duration-200 disabled:opacity-50"
          >
            <RefreshCw className={`w-4 h-4 ${isRefreshing ? 'animate-spin' : ''}`} />
            <span className="text-sm font-medium text-gray-700">Refresh</span>
          </button>
        </div>
      </div>

      {/* Filters and Search */}
      <div className="flex flex-col sm:flex-row gap-4 mb-6">
        <div className="flex items-center gap-2">
          <Filter className="w-4 h-4 text-gray-500" />
          <select
            value={filterType}
            onChange={(e) => setFilterType(e.target.value as FilterType)}
            className="text-sm border border-gray-200 rounded-lg px-3 py-1.5 focus:outline-none focus:ring-2 focus:ring-blue-500"
          >
            <option value="all">All Stocks</option>
            <option value="highRisk">High Risk Only</option>
            <option value="disasterAffected">Affected by Current Wars/Disasters</option>
          </select>
        </div>

        <div className="flex-1 relative">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
          <input
            type="text"
            placeholder="Search by ticker, company, or sector..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="w-full pl-10 pr-4 border border-gray-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
        </div>
      </div>

      {/* Sort Controls */}
      <div className="flex items-center gap-2 mb-4">
        <ArrowUpDown className="w-4 h-4 text-gray-500" />
        <span className="text-sm text-gray-600">Sort by:</span>
        <div className="flex gap-1">
          {[
            { field: 'riskScore' as SortField, label: 'Risk Score' },
            { field: 'changePercent' as SortField, label: '% Change' },
            { field: 'currentPrice' as SortField, label: 'Price' }
          ].map(({ field, label }) => (
            <button
              key={field}
              onClick={() => handleSort(field)}
              className={`px-3 py-1 text-sm rounded-lg transition-all duration-200 ${
                sortField === field
                  ? 'bg-blue-500 text-white'
                  : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
              }`}
            >
              {label}
              {sortField === field && (
                <span className="ml-1">
                  {sortDirection === 'asc' ? '↑' : '↓'}
                </span>
              )}
            </button>
          ))}
        </div>
      </div>

      {/* Stocks Table */}
      <div className="overflow-x-auto">
        <div className="min-w-[800px]">
          <div className="grid grid-cols-7 gap-4 pb-2 border-b border-gray-200 text-xs font-semibold text-gray-600 uppercase tracking-wider">
            <div>Company</div>
            <div>Price</div>
            <div>Change</div>
            <div>Risk Score</div>
            <div>Sector</div>
            <div>Risk Factors</div>
            <div>Actions</div>
          </div>

          <div className="space-y-3">
            {isLoading ? (
              <LoadingSkeleton />
            ) : (
              paginatedStocks.map((stock, index) => {
              const SectorIcon = SECTOR_ICONS[stock.sector] || Building2
              const isPositive = stock.changePercent >= 0
              
              return (
                <motion.div
                  key={stock.ticker}
                  initial={{ opacity: 0, x: -20 }}
                  animate={{ opacity: 1, x: 0 }}
                  transition={{ delay: index * 0.05 }}
                  className="grid grid-cols-7 gap-4 p-3 rounded-lg hover:bg-gray-50 transition-all duration-200 border border-gray-100 hover:border-gray-200"
                >
                  {/* Company Info */}
                  <div className="flex items-center gap-3">
                    <div className={`w-8 h-8 rounded-lg bg-gradient-to-br ${SECTOR_COLORS[stock.sector] || 'from-gray-500 to-gray-600'} flex items-center justify-center`}>
                      <SectorIcon className="w-4 h-4 text-white" />
                    </div>
                    <div>
                      <div className="font-semibold text-gray-900">{stock.ticker}</div>
                      <div className="text-xs text-gray-500 truncate max-w-[120px]">{stock.companyName}</div>
                    </div>
                  </div>

                  {/* Price */}
                  <div className="flex items-center">
                    <span className="font-medium text-gray-900">${stock.currentPrice.toFixed(2)}</span>
                  </div>

                  {/* Change */}
                  <div className="flex items-center">
                    <div className={`flex items-center gap-1 px-2 py-1 rounded-full text-xs font-medium ${
                      isPositive ? 'bg-emerald-50 text-emerald-700' : 'bg-red-50 text-red-700'
                    }`}>
                      {isPositive ? <TrendingUp className="w-3 h-3" /> : <TrendingDown className="w-3 h-3" />}
                      {Math.abs(stock.changePercent).toFixed(2)}%
                    </div>
                  </div>

                  {/* Risk Score */}
                  <div className="flex items-center">
                    <div className={`px-2 py-1 rounded-lg border text-xs font-bold ${getRiskColor(stock.riskScore)}`}>
                      {stock.riskScore}
                      <span className="ml-1 opacity-70">({getRiskLabel(stock.riskScore)})</span>
                    </div>
                  </div>

                  {/* Sector */}
                  <div className="flex items-center">
                    <span className="text-xs text-gray-600 bg-gray-50 px-2 py-1 rounded">{stock.sector}</span>
                  </div>

                  {/* Risk Factors */}
                  <div className="flex items-center">
                    <span className="text-xs text-gray-600 line-clamp-2">{stock.reason}</span>
                  </div>

                  {/* Actions */}
                  <div className="flex items-center">
                    <button className="text-blue-600 hover:text-blue-800 text-xs font-medium hover:underline">
                      Analyze
                    </button>
                  </div>
                </motion.div>
              )
              })
            )}
          </div>
        </div>
      </div>

      {/* Pagination Controls */}
      {totalPages > 1 && (
        <div className="mt-6 pt-4 border-t border-gray-200">
          <div className="flex items-center justify-between">
            <div className="text-sm text-gray-600">
              Showing {startIndex + 1}-{Math.min(endIndex, filteredAndSortedStocks.length)} of {filteredAndSortedStocks.length} stocks
            </div>
            <div className="flex items-center gap-2">
              <button
                onClick={handlePrevPage}
                disabled={currentPage === 1}
                className="px-3 py-1 text-sm border border-gray-300 rounded-lg hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                Previous
              </button>
              
              <div className="flex items-center gap-1">
                {Array.from({ length: totalPages }, (_, i) => i + 1).map((page) => (
                  <button
                    key={page}
                    onClick={() => handlePageChange(page)}
                    className={`w-8 h-8 text-sm rounded-lg transition-colors ${
                      currentPage === page
                        ? 'bg-blue-500 text-white'
                        : 'border border-gray-300 hover:bg-gray-50'
                    }`}
                  >
                    {page}
                  </button>
                ))}
              </div>
              
              <button
                onClick={handleNextPage}
                disabled={currentPage === totalPages}
                className="px-3 py-1 text-sm border border-gray-300 rounded-lg hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                Next
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Summary Stats */}
      <div className="mt-6 pt-4 border-t border-gray-200">
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
          <div className="text-center">
            <div className="text-2xl font-bold text-gray-900">{filteredAndSortedStocks.length}</div>
            <div className="text-xs text-gray-500">Total Stocks</div>
          </div>
          <div className="text-center">
            <div className="text-2xl font-bold text-red-600">
              {filteredAndSortedStocks.filter(s => s.riskScore > 70).length}
            </div>
            <div className="text-xs text-gray-500">High Risk</div>
          </div>
          <div className="text-center">
            <div className="text-2xl font-bold text-amber-600">
              {filteredAndSortedStocks.filter(s => s.riskScore >= 30 && s.riskScore <= 70).length}
            </div>
            <div className="text-xs text-gray-500">Medium Risk</div>
          </div>
          <div className="text-center">
            <div className="text-2xl font-bold text-emerald-600">
              {filteredAndSortedStocks.filter(s => s.riskScore < 30).length}
            </div>
            <div className="text-xs text-gray-500">Low Risk</div>
          </div>
        </div>
        
        {/* Data Attribution */}
        <div className="mt-4 pt-4 border-t border-gray-100 flex items-center justify-between text-xs text-gray-400">
          <div className="flex items-center gap-2">
            <span>Prices powered by</span>
            <span className="font-semibold text-gray-600">Finnhub</span>
            <span>×</span>
            <span className="font-semibold text-blue-600">SupplyChainGPT</span>
          </div>
          <div className="flex items-center gap-1">
            {stocksData?.timestamp && (
              <span>Updated {getTimeSinceUpdate(stocksData.timestamp)}</span>
            )}
            {stocksData?.market_hours !== undefined && (
              <span className={`ml-2 px-2 py-0.5 rounded-full text-xs font-medium ${
                stocksData.market_hours 
                  ? 'bg-emerald-50 text-emerald-700 border border-emerald-200' 
                  : 'bg-amber-50 text-amber-700 border border-amber-200'
              }`}>
                {stocksData.market_hours ? 'Market Open' : 'Market Closed'}
              </span>
            )}
          </div>
        </div>
      </div>
    </motion.div>
  )
}
