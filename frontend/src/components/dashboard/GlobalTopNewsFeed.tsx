import { useState, useEffect } from 'react'
import AnimatedList from '@/components/ui/AnimatedList'
import { api } from '@/lib/api'

interface NewsItem {
  title: string
  url: string
  source?: string
  category?: string
  time?: string
  description?: string
}

interface GlobalTopNewsFeedProps {
  apiEndpoint?: string
  itemsPerPage?: number
  onItemSelect?: (item: NewsItem, index: number) => void
  className?: string
  showGradients?: boolean
  enableArrowNavigation?: boolean
}

const GlobalTopNewsFeed = ({
  apiEndpoint = '/market/global-news',
  itemsPerPage = 5,
  onItemSelect,
  className = '',
  showGradients = true,
  enableArrowNavigation = true,
}: GlobalTopNewsFeedProps) => {
  const [newsItems, setNewsItems] = useState<NewsItem[]>([])
  const [currentPage, setCurrentPage] = useState(0)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    const requestUrl = `${apiEndpoint}${apiEndpoint.includes('?') ? '&' : '?'}_=${Date.now()}`

    api.get(requestUrl)
      .then((res) => res.data)
      .then((data) => {
        const items: NewsItem[] = Array.isArray(data)
          ? data
          : data.news || data.headlines || data.items || []

        const formattedItems = items.map((item: any) => {
          if (typeof item === 'string') {
            return {
              title: item,
              url: `https://www.google.com/search?q=${encodeURIComponent(item)}`,
              category: 'General',
            }
          }

          return {
            title: item.title || 'Untitled',
            url: item.url || '#',
            source: item.source || item.domain || 'Unknown',
            category: item.category || 'General',
            time: item.time || item.published_at || '',
            description: item.description || '',
          }
        })

        setNewsItems(formattedItems.slice(0, 30))
        setLoading(false)
      })
      .catch((err) => {
        console.error(err)
        setError(err.message)
        setLoading(false)
      })
  }, [apiEndpoint])

  const totalPages = Math.ceil(newsItems.length / itemsPerPage)
  const currentItems = newsItems.slice(
    currentPage * itemsPerPage,
    (currentPage + 1) * itemsPerPage
  )

  const handleNext = () => {
    if (currentPage < totalPages - 1) {
      setCurrentPage((prev) => prev + 1)
    }
  }

  const handlePrev = () => {
    if (currentPage > 0) {
      setCurrentPage((prev) => prev - 1)
    }
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64 text-gray-400">
        Loading top global news...
      </div>
    )
  }

  if (error || newsItems.length === 0) {
    return (
      <div className="p-6 text-center text-gray-400 bg-white/10 rounded-2xl">
        No news available at the moment
      </div>
    )
  }

  // Custom render item for AnimatedList - clickable links
  const renderNewsItem = (item: NewsItem, index: number, isSelected: boolean) => (
    <a
      href={item.url}
      target="_blank"
      rel="noopener noreferrer"
      onClick={() => {
        if (onItemSelect) {
          onItemSelect(item, index)
        }
      }}
      className={`block p-4 rounded-xl border transition-all ${
        isSelected
          ? 'bg-blue-50 border-blue-200 shadow-sm'
          : 'bg-white border-gray-100 hover:border-blue-200 hover:shadow-sm'
      }`}
    >
      <div className="flex items-center gap-2 mb-2 flex-wrap text-[11px] font-semibold uppercase tracking-wide">
        <span className="px-2 py-0.5 rounded-full bg-blue-50 text-blue-700 border border-blue-100">
          {item.category || 'General'}
        </span>
        {item.source && (
          <span className="px-2 py-0.5 rounded-full bg-gray-50 text-gray-600 border border-gray-100">
            {item.source}
          </span>
        )}
        {item.time && (
          <span className="text-gray-400 normal-case tracking-normal">
            {item.time}
          </span>
        )}
      </div>
      <p className="text-[15px] font-medium text-gray-800 group-hover:text-blue-700 leading-snug">
        {item.title}
      </p>
      {item.description && (
        <p className="mt-2 text-xs text-gray-500 line-clamp-2">
          {item.description}
        </p>
      )}
    </a>
  )

  return (
    <div className={`global-news-feed ${className}`}>
      <AnimatedList
        items={currentItems}
        renderItem={renderNewsItem}
        showGradients={showGradients}
        enableArrowNavigation={enableArrowNavigation}
        displayScrollbar={true}
        containerHeight="350px"
      />

      {/* Pagination */}
      <div className="flex justify-between items-center mt-6">
        {/* Previous Button - Left */}
        <button
          onClick={handlePrev}
          disabled={currentPage === 0}
          className={`w-11 h-11 rounded-full grid place-items-center transition-all ${
            currentPage > 0
              ? 'bg-white border border-gray-200 text-gray-700 hover:bg-gray-50 shadow-sm active:scale-95'
              : 'bg-gray-100 border border-gray-200 text-gray-400 cursor-not-allowed'
          }`}
          aria-label="Previous news"
        >
          <span className="text-lg leading-none">←</span>
        </button>

        {/* Progress indicator - Center */}
        <div className="text-center text-xs text-gray-400">
          Showing {currentPage * itemsPerPage + 1}–{Math.min((currentPage + 1) * itemsPerPage, newsItems.length)} of {newsItems.length}
        </div>

        {/* Next Button - Right */}
        <button
          onClick={handleNext}
          disabled={currentPage >= totalPages - 1}
          className={`w-11 h-11 rounded-full grid place-items-center transition-all ${
            currentPage < totalPages - 1
              ? 'bg-blue-600 text-white hover:bg-blue-700 shadow-lg shadow-blue-500/30 active:scale-95'
              : 'bg-emerald-100 text-emerald-600 cursor-default'
          }`}
          aria-label="Next news"
        >
          {currentPage < totalPages - 1 ? (
            <span className="text-lg leading-none">→</span>
          ) : (
            <span className="text-base leading-none">✓</span>
          )}
        </button>
      </div>

    </div>
  )
}

export default GlobalTopNewsFeed
