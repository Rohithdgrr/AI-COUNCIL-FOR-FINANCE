import React, { useState } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { RefreshCw, TrendingUp, TrendingDown, DollarSign } from 'lucide-react'
import { useForex, ForexCurrency } from '@/hooks/useForex'

// Loading skeleton component
const ForexCardSkeleton: React.FC = () => (
  <motion.div
    initial={{ opacity: 0 }}
    animate={{ opacity: 1 }}
    className="bg-white rounded-xl shadow-lg border border-gray-200 p-6"
  >
    <div className="flex items-center space-x-3 mb-4">
      <div className="w-12 h-12 bg-gray-200 rounded-full animate-pulse" />
      <div className="flex-1">
        <div className="h-5 bg-gray-200 rounded w-24 mb-1 animate-pulse" />
        <div className="h-3 bg-gray-200 rounded w-20 animate-pulse" />
      </div>
    </div>
    <div className="space-y-3">
      <div className="h-8 bg-gray-200 rounded w-32 animate-pulse" />
      <div className="h-4 bg-gray-200 rounded w-20 animate-pulse" />
    </div>
  </motion.div>
)

// Individual forex card
const ForexCard: React.FC<{ currency: ForexCurrency }> = ({ currency }) => {
  const isPositive = currency.change >= 0
  const TrendIcon = isPositive ? TrendingUp : TrendingDown
  
  // Format rate based on currency
  const formatRate = (rate: number, code: string) => {
    if (code === 'JPY' || code === 'INR') {
      return rate.toFixed(2)
    }
    return rate.toFixed(4)
  }
  
  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      whileHover={{ y: -2, boxShadow: '0 10px 30px rgba(0, 0, 0, 0.1)' }}
      className={`bg-white rounded-xl shadow-lg border p-6 transition-all duration-300 ${
        isPositive ? 'border-green-200' : 'border-red-200'
      }`}
    >
      <div className="flex items-center space-x-3 mb-4">
        <div className="w-12 h-12 rounded-full bg-gradient-to-br from-blue-50 to-blue-100 flex items-center justify-center text-2xl shadow-sm">
          {currency.flag}
        </div>
        <div className="flex-1 min-w-0">
          <h3 className="font-semibold text-gray-900 truncate">{currency.name}</h3>
          <p className="text-sm text-gray-500 truncate">{currency.country}</p>
        </div>
      </div>

      <div className="space-y-2">
        <div className="flex items-baseline space-x-1">
          <span className="text-sm text-gray-500">1 USD =</span>
          <span className="text-2xl font-bold text-gray-900">
            {currency.code === 'INR' ? '₹' : 
             currency.code === 'EUR' ? '€' :
             currency.code === 'GBP' ? '£' :
             currency.code === 'JPY' ? '¥' :
             currency.code === 'CNY' ? '¥' : '$'}
            {formatRate(currency.rate, currency.code)}
          </span>
        </div>

        <div className="flex items-center space-x-2">
          <div className={`flex items-center space-x-1 px-2 py-0.5 rounded-full text-xs font-medium ${
            isPositive ? 'bg-green-100 text-green-700' : 'bg-red-100 text-red-700'
          }`}>
            <TrendIcon className="w-3 h-3" />
            <span>{isPositive ? '+' : ''}{currency.change_percent.toFixed(2)}%</span>
          </div>
          <span className="text-xs text-gray-400">24h change</span>
        </div>
      </div>
    </motion.div>
  )
}

export const ForexRates: React.FC = () => {
  const [currentPage, setCurrentPage] = useState(0)
  const {
    currencies,
    isLoading,
    error,
    refresh,
    lastUpdated,
    count
  } = useForex()

  const CURRENCIES_PER_PAGE = 3
  const totalPages = Math.ceil(count / CURRENCIES_PER_PAGE)
  const startIndex = currentPage * CURRENCIES_PER_PAGE
  const endIndex = Math.min(startIndex + CURRENCIES_PER_PAGE, count)
  const paginatedCurrencies = currencies.slice(startIndex, endIndex)

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
          <TrendingDown className="w-5 h-5" />
          <span>Failed to load forex rates</span>
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
          <h2 className="text-2xl font-bold text-gray-900 flex items-center gap-2">
            <DollarSign className="w-6 h-6 text-blue-600" />
            Forex Rates (1 USD)
          </h2>
          <p className="text-sm text-gray-600">Live currency conversion for global supply chain impact</p>
        </div>
        <div className="flex items-center space-x-3">
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

      {/* Currency Cards with Navigation */}
      <div className="relative">
        <div className="flex items-center gap-4">
          {/* Left Arrow */}
          {!isLoading && currentPage > 0 && (
            <motion.button
              whileHover={{ scale: 1.1 }}
              whileTap={{ scale: 0.9 }}
              onClick={handlePreviousPage}
              className="flex-shrink-0 p-3 bg-blue-500 text-white rounded-full shadow-lg hover:bg-blue-600 transition-colors"
            >
              <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
              </svg>
            </motion.button>
          )}
          
          {/* Cards Grid */}
          <div className="flex-1 grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            <AnimatePresence mode="wait">
              {isLoading ? (
                Array.from({ length: 3 }, (_, i) => (
                  <ForexCardSkeleton key={`skeleton-${i}`} />
                ))
              ) : (
                paginatedCurrencies.map((currency) => (
                  <ForexCard
                    key={currency.code}
                    currency={currency}
                  />
                ))
              )}
            </AnimatePresence>
          </div>
          
          {/* Right Arrow */}
          {!isLoading && currentPage < totalPages - 1 && (
            <motion.button
              whileHover={{ scale: 1.1 }}
              whileTap={{ scale: 0.9 }}
              onClick={handleNextPage}
              className="flex-shrink-0 p-3 bg-blue-500 text-white rounded-full shadow-lg hover:bg-blue-600 transition-colors"
            >
              <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
              </svg>
            </motion.button>
          )}
        </div>
      </div>

      {/* Footer */}
      <div className="text-center text-sm text-gray-500 pt-4 border-t">
        Rates powered by Yahoo Finance × SupplyChainGPT
      </div>
    </motion.div>
  )
}
