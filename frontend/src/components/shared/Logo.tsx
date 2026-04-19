import { Star, Sparkles } from 'lucide-react'
import { motion } from 'framer-motion'

interface LogoProps {
  size?: 'sm' | 'md' | 'lg'
  showText?: boolean
  animated?: boolean
}

export default function Logo({ size = 'md', showText = true, animated = true }: LogoProps) {
  const sizes = {
    sm: { icon: 'w-6 h-6', text: 'text-sm', container: 'gap-2' },
    md: { icon: 'w-8 h-8', text: 'text-lg', container: 'gap-2.5' },
    lg: { icon: 'w-12 h-12', text: 'text-2xl', container: 'gap-3' },
  }

  const { icon, text, container } = sizes[size]

  return (
    <div className={`flex items-center ${container}`}>
      {/* Animated Star Logo */}
      <motion.div
        className="relative"
        animate={animated ? {
          rotate: [0, 360],
        } : {}}
        transition={{
          duration: 20,
          repeat: Infinity,
          ease: "linear"
        }}
      >
        {/* Outer glow */}
        <div className="absolute inset-0 bg-gradient-to-r from-cyan-500 to-blue-600 rounded-full blur-xl opacity-30" />
        
        {/* Main star */}
        <div className={`relative ${icon} bg-gradient-to-br from-cyan-500 via-blue-600 to-purple-600 rounded-xl flex items-center justify-center shadow-lg shadow-cyan-500/20`}>
          <Star className="w-[60%] h-[60%] text-white fill-white" />
        </div>
        
        {/* Sparkle accent */}
        {animated && (
          <motion.div
            className="absolute -top-1 -right-1"
            animate={{
              scale: [1, 1.2, 1],
              opacity: [0.5, 1, 0.5],
            }}
            transition={{
              duration: 2,
              repeat: Infinity,
              ease: "easeInOut"
            }}
          >
            <Sparkles className="w-3 h-3 text-yellow-400 fill-yellow-400" />
          </motion.div>
        )}
      </motion.div>

      {/* Text */}
      {showText && (
        <div className="flex flex-col">
          <motion.h1
            className={`${text} font-black bg-gradient-to-r from-cyan-400 via-blue-500 to-purple-600 bg-clip-text text-transparent leading-none`}
            initial={{ opacity: 0, x: -20 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ duration: 0.5 }}
          >
            SupplyChain<span className="text-cyan-400">GPT</span>
          </motion.h1>
          <span className="text-[10px] text-gray-400 font-medium tracking-wider uppercase">
            AI Council Platform
          </span>
        </div>
      )}
    </div>
  )
}
