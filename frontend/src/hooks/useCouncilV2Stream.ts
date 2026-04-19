import { useCallback, useRef } from 'react'
import { useCouncilV2Store } from '@/store/councilV2Store'
import { useSettingsStore } from '@/store/settingsStore'
import type { CouncilV2StreamEvent, SupportAgentPolicy } from '@/types/council'

export function useCouncilV2Stream() {
  const { handleV2Event, isStreaming, reset, setStreaming, setStreamError } = useCouncilV2Store()
  const abortRef = useRef<AbortController | null>(null)

  const startStream = useCallback(async (
    query: string,
    options?: {
      liteMode?: boolean
      primaryAgent?: string
      supportAgents?: string[]
      supportAgentPolicy?: SupportAgentPolicy
    },
  ) => {
    reset()
    abortRef.current = new AbortController()

    // Resolve policy from options or settings store
    const settingsPolicy = useSettingsStore.getState().settings.support_agent_policy
    const policy = options?.supportAgentPolicy ?? settingsPolicy
    const mirofishEnabled = useSettingsStore.getState().settings.mirofish_enabled

    try {
      const apiKey = localStorage.getItem('api_key') || 'dev-key'
      const response = await fetch('/api/council/v2/stream', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-API-Key': apiKey,
        },
        body: JSON.stringify({
          query,
          lite_mode: options?.liteMode ?? false,
          primary_agent: options?.primaryAgent,
          support_agents: options?.supportAgents ?? [],
          support_agent_policy: policy,
          mirofish_enabled: mirofishEnabled,
        }),
        signal: abortRef.current.signal,
      })

      if (!response.ok || !response.body) {
        throw new Error(`Stream failed: ${response.status}`)
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
        setStreamError(err.message)
        setStreaming(false)
      }
    }
  }, [handleV2Event, reset, setStreamError, setStreaming])

  const stopStream = useCallback(() => {
    abortRef.current?.abort()
    setStreaming(false)
  }, [setStreaming])

  return { startStream, stopStream, isStreaming }
}
