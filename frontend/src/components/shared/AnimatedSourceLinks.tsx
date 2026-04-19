import { useState, useEffect, useCallback } from 'react';
import { motion, AnimatePresence } from 'framer-motion';

interface Source {
  label: string;
  url: string;
}

const sources: Source[] = [
  { label: "GDELT Global Events", url: "https://www.gdeltproject.org/" },
  { label: "Finnhub Stock API", url: "https://finnhub.io/" },
  { label: "Yahoo Finance", url: "https://finance.yahoo.com/" },
  { label: "Open-Meteo Weather", url: "https://open-meteo.com/" },
  { label: "USGS Earthquake Data", url: "https://earthquake.usgs.gov/" },
  { label: "World Bank API", url: "https://data.worldbank.org/" },
  { label: "GDACS Disaster Alerts", url: "https://www.gdacs.org/" },
  { label: "SEC EDGAR Filings", url: "https://www.sec.gov/edgar/" },
  { label: "OpenCorporates", url: "https://opencorporates.com/" },
  { label: "Reddit Sentiment API", url: "https://www.reddit.com/dev/api/" },
  { label: "NewsAPI", url: "https://newsapi.org/" },
  { label: "Alpha Vantage", url: "https://www.alphavantage.co/" },
];

const MAX_VISIBLE = 4;
const INTERVAL_MS = 800;

const AnimatedSourceLinks = ({ isActive }: { isActive: boolean }) => {
  const [visibleSources, setVisibleSources] = useState<Source[]>([]);
  const [currentIndex, setCurrentIndex] = useState(0);

  const addNextSource = useCallback(() => {
    const nextSource = sources[currentIndex];
    if (!nextSource) {
      // Reset to beginning if we go past
      setCurrentIndex(0);
      return;
    }

    setVisibleSources(prev => {
      const updated = [...prev, nextSource];
      if (updated.length > MAX_VISIBLE) {
        return updated.slice(1);
      }
      return updated;
    });

    setCurrentIndex(prev => {
      const next = prev + 1;
      return next >= sources.length ? 0 : next;
    });
  }, []);

  useEffect(() => {
    if (!isActive) {
      setVisibleSources([]);
      setCurrentIndex(0);
      return;
    }

    // Reset when sources change
    setVisibleSources([]);
    setCurrentIndex(0);

    // Start with first source if available
    const firstSource = sources[0];
    if (firstSource) {
      setVisibleSources([firstSource]);
      setCurrentIndex(1);
    }

    const interval = setInterval(addNextSource, INTERVAL_MS);
    return () => clearInterval(interval);
  }, [isActive, sources, addNextSource]);

  return (
    <div className="relative overflow-hidden h-[60px] w-[280px]">
      {/* Top gradient fade */}
      <div className="absolute top-0 left-0 right-0 h-4 bg-gradient-to-b from-[#0d1117] to-transparent z-10 pointer-events-none" />
      
      <div className="flex flex-col justify-center h-full py-1">
        <AnimatePresence mode="popLayout">
          {visibleSources.map((source, index) => (
            <motion.a
              key={`${source.url}-${index}`}
              href={source.url}
              target="_blank"
              rel="noopener noreferrer"
              initial={{ scale: 0.7, opacity: 0, y: 10 }}
              animate={{ scale: 1, opacity: 1, y: 0 }}
              exit={{ scale: 0.7, opacity: 0 }}
              transition={{ duration: 0.2 }}
              className="text-xs text-blue-400 hover:text-blue-300 hover:underline text-center py-0.5 truncate px-2"
            >
              {source.label}
            </motion.a>
          ))}
        </AnimatePresence>
      </div>

      {/* Bottom gradient fade */}
      <div className="absolute bottom-0 left-0 right-0 h-4 bg-gradient-to-t from-[#0d1117] to-transparent z-10 pointer-events-none" />
    </div>
  );
};

export default AnimatedSourceLinks;