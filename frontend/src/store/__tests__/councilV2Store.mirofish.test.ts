/**
 * Tests for MiroFish event handling in councilV2Store.
 *
 * Verifies:
 * - mirofish_start event initializes MiroFish state
 * - mirofish_agent_progress events update per-agent phase tracking
 * - mirofish_agent_complete events store results
 * - mirofish_agent_error events mark agents as failed
 * - mirofish_complete event marks overall phase as completed
 * - reset clears all MiroFish state
 * - MiroFish state is only for brand + market agents
 */

import { describe, it, expect, beforeEach } from 'vitest'
import { useCouncilV2Store } from '../councilV2Store'
import type { CouncilV2StreamEvent } from '@/types/council'

describe('councilV2Store - MiroFish events', () => {
  beforeEach(() => {
    useCouncilV2Store.getState().reset()
  })

  it('initializes MiroFish state as idle', () => {
    const state = useCouncilV2Store.getState()
    expect(state.mirofishPhase).toBe('idle')
    expect(state.mirofishBrandResult).toBeNull()
    expect(state.mirofishMarketResult).toBeNull()
    expect(state.mirofishBrandEntities).toEqual([])
    expect(state.mirofishMarketEntities).toEqual([])
    expect(state.mirofishBrandPersonas).toEqual([])
    expect(state.mirofishMarketPersonas).toEqual([])
    expect(state.mirofishBrandPhase).toBe('')
    expect(state.mirofishMarketPhase).toBe('')
  })

  it('handles mirofish_start event', () => {
    const event: CouncilV2StreamEvent = {
      type: 'mirofish_start',
      agents: ['brand', 'market'],
    }
    useCouncilV2Store.getState().handleV2Event(event)

    const state = useCouncilV2Store.getState()
    expect(state.mirofishPhase).toBe('graph_building')
    expect(state.mirofishBrandPhase).toBe('graph_building')
    expect(state.mirofishMarketPhase).toBe('graph_building')
    expect(state.mirofishBrandResult).toBeNull()
    expect(state.mirofishMarketResult).toBeNull()
  })

  it('handles mirofish_agent_progress for brand', () => {
    // Start first
    useCouncilV2Store.getState().handleV2Event({ type: 'mirofish_start', agents: ['brand', 'market'] })

    const progressEvent: CouncilV2StreamEvent = {
      type: 'mirofish_agent_progress',
      agent: 'brand',
      phase: 'graph_ready',
      entities: ['Brand X', 'Competitor Y'],
      entity_count: 2,
    }
    useCouncilV2Store.getState().handleV2Event(progressEvent)

    const state = useCouncilV2Store.getState()
    expect(state.mirofishBrandPhase).toBe('graph_ready')
    expect(state.mirofishBrandEntities).toEqual(['Brand X', 'Competitor Y'])
    expect(state.mirofishPhase).toBe('persona_generation') // graph_ready maps to persona_generation
  })

  it('handles mirofish_agent_progress for market with personas', () => {
    useCouncilV2Store.getState().handleV2Event({ type: 'mirofish_start', agents: ['brand', 'market'] })

    const progressEvent: CouncilV2StreamEvent = {
      type: 'mirofish_agent_progress',
      agent: 'market',
      phase: 'personas_ready',
      personas: ['Market Analyst (analyst)', 'Consumer (customer)'],
      persona_count: 2,
    }
    useCouncilV2Store.getState().handleV2Event(progressEvent)

    const state = useCouncilV2Store.getState()
    expect(state.mirofishMarketPhase).toBe('personas_ready')
    expect(state.mirofishMarketPersonas).toEqual(['Market Analyst (analyst)', 'Consumer (customer)'])
    expect(state.mirofishPhase).toBe('simulation_running') // personas_ready maps to simulation_running
  })

  it('handles mirofish_agent_complete for brand', () => {
    useCouncilV2Store.getState().handleV2Event({ type: 'mirofish_start', agents: ['brand', 'market'] })

    const completeEvent: CouncilV2StreamEvent = {
      type: 'mirofish_agent_complete',
      agent: 'brand',
      result: {
        simulation_id: 'brand_sim_test',
        status: 'completed',
        prediction: 'Brand sentiment improving',
        confidence: 0.82,
        key_factors: ['Consumer trust'],
        risks: ['Viral content'],
        opportunities: ['Partnerships'],
        recommendations: ['Monitor social'],
        scenarios: [],
        entities: ['Brand X'],
        personas: ['Analyst (analyst)'],
        report_summary: 'Positive outlook',
      },
    }
    useCouncilV2Store.getState().handleV2Event(completeEvent)

    const state = useCouncilV2Store.getState()
    expect(state.mirofishBrandPhase).toBe('completed')
    expect(state.mirofishBrandResult).not.toBeNull()
    expect(state.mirofishBrandResult!.prediction).toBe('Brand sentiment improving')
    expect(state.mirofishBrandResult!.confidence).toBe(0.82)
  })

  it('handles mirofish_agent_complete for market', () => {
    useCouncilV2Store.getState().handleV2Event({ type: 'mirofish_start', agents: ['brand', 'market'] })

    const completeEvent: CouncilV2StreamEvent = {
      type: 'mirofish_agent_complete',
      agent: 'market',
      result: {
        simulation_id: 'market_sim_test',
        status: 'completed',
        prediction: 'Market growth expected',
        confidence: 0.75,
        key_factors: ['Demand surge'],
        risks: ['Supply constraints'],
        opportunities: ['New markets'],
        recommendations: ['Diversify suppliers'],
        scenarios: [],
        entities: ['Market Sector A'],
        personas: ['Trader (trader)'],
        report_summary: 'Growth outlook',
      },
    }
    useCouncilV2Store.getState().handleV2Event(completeEvent)

    const state = useCouncilV2Store.getState()
    expect(state.mirofishMarketPhase).toBe('completed')
    expect(state.mirofishMarketResult).not.toBeNull()
    expect(state.mirofishMarketResult!.prediction).toBe('Market growth expected')
  })

  it('handles mirofish_agent_error for brand', () => {
    useCouncilV2Store.getState().handleV2Event({ type: 'mirofish_start', agents: ['brand', 'market'] })

    const errorEvent: CouncilV2StreamEvent = {
      type: 'mirofish_agent_error',
      agent: 'brand',
      error: 'LLM timeout',
    }
    useCouncilV2Store.getState().handleV2Event(errorEvent)

    const state = useCouncilV2Store.getState()
    expect(state.mirofishBrandPhase).toBe('failed')
  })

  it('handles mirofish_agent_error for market', () => {
    useCouncilV2Store.getState().handleV2Event({ type: 'mirofish_start', agents: ['brand', 'market'] })

    const errorEvent: CouncilV2StreamEvent = {
      type: 'mirofish_agent_error',
      agent: 'market',
      error: 'Simulation crashed',
    }
    useCouncilV2Store.getState().handleV2Event(errorEvent)

    const state = useCouncilV2Store.getState()
    expect(state.mirofishMarketPhase).toBe('failed')
  })

  it('handles mirofish_complete event', () => {
    useCouncilV2Store.getState().handleV2Event({ type: 'mirofish_start', agents: ['brand', 'market'] })

    useCouncilV2Store.getState().handleV2Event({ type: 'mirofish_complete' })

    const state = useCouncilV2Store.getState()
    expect(state.mirofishPhase).toBe('completed')
  })

  it('resets all MiroFish state', () => {
    // Set up some MiroFish state
    useCouncilV2Store.getState().handleV2Event({ type: 'mirofish_start', agents: ['brand', 'market'] })
    useCouncilV2Store.getState().handleV2Event({
      type: 'mirofish_agent_progress',
      agent: 'brand',
      phase: 'graph_ready',
      entities: ['Entity1'],
    })

    // Reset
    useCouncilV2Store.getState().reset()

    const state = useCouncilV2Store.getState()
    expect(state.mirofishPhase).toBe('idle')
    expect(state.mirofishBrandResult).toBeNull()
    expect(state.mirofishMarketResult).toBeNull()
    expect(state.mirofishBrandEntities).toEqual([])
    expect(state.mirofishMarketEntities).toEqual([])
    expect(state.mirofishBrandPersonas).toEqual([])
    expect(state.mirofishMarketPersonas).toEqual([])
    expect(state.mirofishBrandPhase).toBe('')
    expect(state.mirofishMarketPhase).toBe('')
  })

  it('ignores mirofish progress events for non-brand/market agents', () => {
    useCouncilV2Store.getState().handleV2Event({ type: 'mirofish_start', agents: ['brand', 'market'] })

    // A progress event for 'risk' should not update any MiroFish state
    const riskEvent: CouncilV2StreamEvent = {
      type: 'mirofish_agent_progress',
      agent: 'risk',
      phase: 'graph_building',
    }
    useCouncilV2Store.getState().handleV2Event(riskEvent)

    const state = useCouncilV2Store.getState()
    // Brand and market phases should remain unchanged from the start event
    expect(state.mirofishBrandPhase).toBe('graph_building')
    expect(state.mirofishMarketPhase).toBe('graph_building')
  })

  it('full MiroFish lifecycle: start → progress → complete', () => {
    const { handleV2Event } = useCouncilV2Store.getState()

    // Start
    handleV2Event({ type: 'mirofish_start', agents: ['brand', 'market'] })
    expect(useCouncilV2Store.getState().mirofishPhase).toBe('graph_building')

    // Brand graph ready
    handleV2Event({ type: 'mirofish_agent_progress', agent: 'brand', phase: 'graph_ready', entities: ['E1'] })
    expect(useCouncilV2Store.getState().mirofishBrandPhase).toBe('graph_ready')
    expect(useCouncilV2Store.getState().mirofishBrandEntities).toEqual(['E1'])

    // Market graph ready
    handleV2Event({ type: 'mirofish_agent_progress', agent: 'market', phase: 'graph_ready', entities: ['E2'] })

    // Brand personas ready
    handleV2Event({ type: 'mirofish_agent_progress', agent: 'brand', phase: 'personas_ready', personas: ['P1'] })
    expect(useCouncilV2Store.getState().mirofishBrandPersonas).toEqual(['P1'])

    // Brand simulation complete
    handleV2Event({
      type: 'mirofish_agent_complete',
      agent: 'brand',
      result: {
        prediction: 'Brand outlook positive',
        confidence: 0.8,
        key_factors: ['Trust'],
        scenarios: [],
        risks: ['Viral'],
        opportunities: ['Growth'],
        recommendations: ['Monitor'],
      },
    })
    expect(useCouncilV2Store.getState().mirofishBrandPhase).toBe('completed')
    expect(useCouncilV2Store.getState().mirofishBrandResult).not.toBeNull()

    // Market simulation complete
    handleV2Event({
      type: 'mirofish_agent_complete',
      agent: 'market',
      result: {
        prediction: 'Market trending up',
        confidence: 0.75,
        key_factors: ['Demand'],
        scenarios: [],
        risks: ['Shortage'],
        opportunities: ['Expansion'],
        recommendations: ['Diversify'],
      },
    })
    expect(useCouncilV2Store.getState().mirofishMarketPhase).toBe('completed')

    // Overall complete
    handleV2Event({ type: 'mirofish_complete' })
    expect(useCouncilV2Store.getState().mirofishPhase).toBe('completed')
  })
})
