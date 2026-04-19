import { motion } from 'framer-motion'
import { ArrowRight, Sparkles, Zap } from 'lucide-react'
import { useState } from 'react'

interface EnhancedInputProps {
  value: string
  onChange: (value: string) => void
  onSubmit: () => void
  placeholder?: string
  disabled?: boolean
  showExamples?: boolean
}

const EXAMPLE_QUERIES = [
  "Analyze semiconductor supply chain risks from Taiwan tensions",
  "Impact of Red Sea disruptions on electronics OEMs",
  "Evaluate rare earth mineral sourcing alternatives to China",
  "Assess climate change risks on agricultural supply chains",
]

export default function EnhancedInput({
  value,
  onChange,
  onSubmit,
  placeholder = "Enter your supply chain query...",
  disabled = false,
  showExamples = true
}: EnhancedInputProps) {
  const [isFocused, setIsFocused] = useState(false)

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      onSubmit()
    }
  }

  const handleExampleClick = (example: string) => {
    onChange(example)
  }

  return (
    <div className="space-y-3">
      {/* Main Input Container */}
      <motion.div
        className={`relative group ${disabled ? 'opacity-50 cursor-not-allowed' : ''}`}
        animate={{
          scale: isFocused ? 1.01 : 1,
        }}
        transition={{ duration: 0.2 }}
      >
        {/* Animated gradient border */}
        <div className={`absolute -inset-[1px] bg-gradient-to-r from-cyan-500 via-blue-600 to-purple-600 rounded-2xl opacity-0 group-hover:opacity-100 blur transition-opacity duration-300 ${isFocused ? 'opacity-100' : ''}`} />
        
        {/* Input field */}
        <div className="relative">
          <textarea
            value={value}
            onChange={(e) => onChange(e.target.value)}
            onKeyDown={handleKeyDown}
            onFocus={() => setIsFocused(true)}
            onBlur={() => setIsFocused(false)}
            disabled={disabled}
            placeholder={placeholder}
            rows={3}
            className="w-full bg-gradient-to-br from-gray-900/90 to-gray-800/90 backdrop-blur-xl border border-white/10 rounded-2xl px-6 py-5 pr-16 text-base text-white placeholder-gray-400 focus:outline-none focus:border-cyan-500/50 transition-all resize-none"
          />
          
          {/* Submit button */}
          <motion.button
            type="button"
            onClick={onSubmit}
            disabled={disabled || !value.trim()}
            className={`absolute right-3 bottom-3 p-3 rounded-xl transition-all ${
              value.trim() && !disabled
                ? 'bg-gradient-to-r from-cyan-600 to-blue-600 text-white shadow-lg shadow-cyan-500/20 hover:shadow-cyan-500/40 hover:scale-105'
                : 'bg-gray-700/50 text-gray-500 cursor-not-allowed'
            }`}
            whileHover={value.trim() && !disabled ? { scale: 1.05 } : {}}
            whileTap={value.trim() && !disabled ? { scale: 0.95 } : {}}
          >
            <ArrowRight className="w-5 h-5" />
          </motion.button>
        </div>

        {/* Character count */}
        <div className="absolute -bottom-6 right-2 text-xs text-gray-500">
          {value.length} / 500
        </div>
      </motion.div>

      {/* Example queries */}
      {showExamples && !value && (
        <motion.div
          initial={{ opacity: 0, y: -10 }}
          animate={{ opacity: 1, y: 0 }}
          className="space-y-2"
        >
          <div className="flex items-center gap-2 text-xs text-gray-400">
            <Sparkles className="w-3 h-3" />
            <span>Try these examples:</span>
          </div>
          <div className="flex flex-wrap gap-2">
            {EXAMPLE_QUERIES.map((example, idx) => (
              <motion.button
                key={idx}
                onClick={() => handleExampleClick(example)}
                className="text-xs px-3 py-1.5 rounded-lg bg-white/[0.03] border border-white/10 text-gray-300 hover:bg-white/[0.08] hover:border-cyan-500/30 hover:text-cyan-400 transition-all"
                whileHover={{ scale: 1.02 }}
                whileTap={{ scale: 0.98 }}
              >
                <Zap className="w-3 h-3 inline mr-1" />
                {example.slice(0, 50)}...
              </motion.button>
            ))}
          </div>
        </motion.div>
      )}
    </div>
  )
}
