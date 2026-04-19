/** Zustand store for MiroFish simulation state */

import { create } from 'zustand'
import type { SimulationState, ReviewResult } from '@/types/council'

interface SimulationStore {
  // Active simulation
  activeSimulation: SimulationState | null
  simulationPhase: 'idle' | 'graph_building' | 'persona_generation' | 'simulation_running' | 'report_generation' | 'completed' | 'failed'
  simulationEntities: string[]
  simulationPersonas: string[]

  // Review swarm
  reviewResult: ReviewResult | null
  reviewLoading: boolean

  // Chat
  chatHistory: { role: 'user' | 'assistant'; content: string }[]

  // Actions
  startSimulation: (query: string, agentType: string, horizonDays?: number, numPersonas?: number, rounds?: number) => Promise<void>
  runReview: (agentName: string, output: string, sources?: string[]) => Promise<void>
  chatWithSimulation: (question: string) => Promise<void>
  reset: () => void
}

const API_BASE = '/simulation'

export const useSimulationStore = create<SimulationStore>((set, get) => ({
  activeSimulation: null,
  simulationPhase: 'idle',
  simulationEntities: [],
  simulationPersonas: [],
  reviewResult: null,
  reviewLoading: false,
  chatHistory: [],

  startSimulation: async (query, agentType, horizonDays = 30, numPersonas = 5, rounds = 3) => {
    set({ simulationPhase: 'graph_building', simulationEntities: [], simulationPersonas: [], activeSimulation: null })

    try {
      const response = await fetch(`${API_BASE}/run`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ query, agent_type: agentType, horizon_days: horizonDays, num_personas: numPersonas, rounds, stream: true }),
      })

      if (!response.ok || !response.body) throw new Error('Simulation request failed')

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
          if (!line.startsWith('data: ')) continue
          try {
            const data = JSON.parse(line.slice(6))

            switch (data.type) {
              case 'sim_start':
                set({ simulationPhase: 'graph_building' })
                break
              case 'sim_progress':
                set({ simulationPhase: data.phase as SimulationStore['simulationPhase'] })
                break
              case 'sim_graph_ready':
                set({ simulationEntities: data.entities || [], simulationPhase: 'persona_generation' })
                break
              case 'sim_personas_ready':
                set({ simulationPersonas: data.personas || [], simulationPhase: 'simulation_running' })
                break
              case 'sim_round':
                // Update round progress
                break
              case 'sim_complete': {
                const result = data.result
                const simState: SimulationState = {
                  id: data.simulation_id,
                  config: { name: '', seed_query: query, horizon_days: horizonDays, num_personas: numPersonas, rounds, focus_areas: [] },
                  status: 'completed',
                  entities: [],
                  relationships: [],
                  personas: [],
                  rounds: [],
                  result: result ? {
                    prediction: result.prediction || '',
                    confidence: result.confidence || 0,
                    key_factors: result.key_factors || [],
                    scenarios: result.scenarios || [],
                    risks: result.risks || [],
                    opportunities: result.opportunities || [],
                    recommendations: result.recommendations || [],
                  } : null,
                  agent_type: agentType,
                }
                set({ activeSimulation: simState, simulationPhase: 'completed' })
                break
              }
            }
          } catch {
            // ignore parse errors
          }
        }
      }
    } catch (e) {
      console.error('Simulation failed:', e)
      set({ simulationPhase: 'failed' })
    }
  },

  runReview: async (agentName, output, sources = []) => {
    set({ reviewLoading: true, reviewResult: null })
    try {
      const response = await fetch(`${API_BASE}/review`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ agent_name: agentName, output, sources, min_score: 0.6 }),
      })
      if (!response.ok) throw new Error('Review request failed')
      const result = await response.json()
      set({ reviewResult: result as ReviewResult, reviewLoading: false })
    } catch (e) {
      console.error('Review failed:', e)
      set({ reviewLoading: false })
    }
  },

  chatWithSimulation: async (question) => {
    const sim = get().activeSimulation
    if (!sim) return

    set(s => ({ chatHistory: [...s.chatHistory, { role: 'user', content: question }] }))

    try {
      const response = await fetch(`${API_BASE}/chat`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ simulation_id: sim.id, question }),
      })
      if (!response.ok) throw new Error('Chat request failed')
      const data = await response.json()
      set(s => ({ chatHistory: [...s.chatHistory, { role: 'assistant', content: data.answer || 'No response' }] }))
    } catch (e) {
      set(s => ({ chatHistory: [...s.chatHistory, { role: 'assistant', content: `Error: ${e}` }] }))
    }
  },

  reset: () => {
    set({
      activeSimulation: null,
      simulationPhase: 'idle',
      simulationEntities: [],
      simulationPersonas: [],
      reviewResult: null,
      reviewLoading: false,
      chatHistory: [],
    })
  },
}))
