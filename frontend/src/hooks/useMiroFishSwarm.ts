import { useCallback, useRef } from 'react'
import { useCouncilV2Store } from '@/store/councilV2Store'
import type { CouncilV2StreamEvent } from '@/types/council'

/**
 * Hook to run a standalone MiroFish swarm simulation (brand + market agents).
 * Uses the /api/simulation/swarm SSE endpoint and feeds events into councilV2Store.
 */
export function useMiroFishSwarm() {
  const { handleV2Event, mirofishPhase } = useCouncilV2Store()
  const abortRef = useRef<AbortController | null>(null)

  const runSimulation = useCallback(async (query: string, options?: {
    horizonDays?: number
    numPersonas?: number
    rounds?: number
  }) => {
    // Reset mirofish state only (not the whole council store)
    const store = useCouncilV2Store.getState()
    store.reset()

    abortRef.current = new AbortController()

    try {
      const apiKey = localStorage.getItem('api_key') || 'dev-key'
      const API_BASE = (import.meta as any).env?.VITE_API_BASE_URL || '/api'
      const response = await fetch(`${API_BASE}/astra/swarm`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-API-Key': apiKey,
        },
        body: JSON.stringify({
          query,
          horizon_days: options?.horizonDays ?? 30,
          num_personas: options?.numPersonas ?? 50,
          rounds: options?.rounds ?? 3,
        }),
        signal: abortRef.current.signal,
      })

      if (!response.ok || !response.body) {
        throw new Error(`Simulation failed: ${response.status}`)
      }

      const reader = response.body.getReader()
      const decoder = new TextDecoder()
      let buffer = ''

      while (true) {
        const { done, value } = await reader.read()
        if (done) break

        buffer += decoder.decode(value, { stream: true })
        const lines = buffer.split('\n')
        buffer = lines.pop() || ''

        for (const line of lines) {
          if (line.startsWith('data: ')) {
            try {
              const event: CouncilV2StreamEvent = JSON.parse(line.slice(6))
              handleV2Event(event)
            } catch {
              // skip malformed JSON
            }
          }
        }
      }
    } catch (err: unknown) {
      if (err instanceof Error && err.name !== 'AbortError') {
        handleV2Event({ type: 'mirofish_agent_error', agent: 'brand', error: err.message })
      }
    }
  }, [handleV2Event])

  const stopSimulation = useCallback(() => {
    abortRef.current?.abort()
  }, [])

  const isRunning = mirofishPhase !== 'idle' && mirofishPhase !== 'completed' && mirofishPhase !== 'failed'
  const isComplete = mirofishPhase === 'completed'
  const isFailed = mirofishPhase === 'failed'

  return {
    runSimulation,
    stopSimulation,
    isRunning,
    isComplete,
    isFailed,
    phase: mirofishPhase,
  }
}
