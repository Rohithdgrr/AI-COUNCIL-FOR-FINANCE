import { apiKeyManager } from './secureStorage'

const WS_URL = import.meta.env.VITE_WS_URL || 'ws://localhost:8000/ws'

type EventHandler = (event: WSEvent) => void

interface WSEvent {
  type: string
  session_id?: string | null
  payload?: unknown
  timestamp: number
}

class WebSocketClient {
  private ws: WebSocket | null = null
  private handlers: Map<string, Set<EventHandler>> = new Map()
  private reconnectAttempts = 0
  private maxReconnectAttempts = 10
  private reconnectTimer: ReturnType<typeof setTimeout> | null = null

  connect(apiKey?: string) {
    if (this.ws?.readyState === WebSocket.OPEN) return

    // Use secure storage instead of localStorage
    const key = apiKey || apiKeyManager.getApiKey()
    
    // Don't expose API key in URL - send it in first message instead
    this.ws = new WebSocket(WS_URL)

    this.ws.onopen = () => {
      this.reconnectAttempts = 0
      console.log('[WS] Connected')
      
      // Send authentication message after connection
      if (key) {
        this.send({ type: 'auth', api_key: key })
      }
    }

    this.ws.onclose = () => {
      console.log('[WS] Disconnected')
      this._tryReconnect(apiKey)
    }

    this.ws.onerror = (err) => {
      console.error('[WS] Error:', err)
    }

    this.ws.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data) as WSEvent
        const eventType = data.type || 'unknown'

        // Call type-specific handlers
        const handlers = this.handlers.get(eventType)
        if (handlers) {
          handlers.forEach((h) => h(data))
        }

        // Call wildcard handlers
        const wildcards = this.handlers.get('*')
        if (wildcards) {
          wildcards.forEach((h) => h(data))
        }
      } catch {
        console.warn('[WS] Failed to parse message:', event.data)
      }
    }
  }

  private _tryReconnect(apiKey?: string) {
    if (this.reconnectAttempts >= this.maxReconnectAttempts) return
    const delay = Math.min(1000 * 2 ** this.reconnectAttempts, 30000)
    this.reconnectAttempts++
    console.log(`[WS] Reconnecting in ${delay}ms (attempt ${this.reconnectAttempts})`)
    this.reconnectTimer = setTimeout(() => this.connect(apiKey), delay)
  }

  disconnect() {
    if (this.reconnectTimer) clearTimeout(this.reconnectTimer)
    this.ws?.close()
    this.ws = null
  }

  send(data: Record<string, unknown>) {
    if (this.ws?.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify(data))
    }
  }

  subscribe(topic: string) {
    this.send({ type: 'subscribe', topic })
  }

  unsubscribe(topic: string) {
    this.send({ type: 'unsubscribe', topic })
  }

  on(eventType: string, handler: EventHandler) {
    if (!this.handlers.has(eventType)) {
      this.handlers.set(eventType, new Set())
    }
    this.handlers.get(eventType)!.add(handler)
  }

  off(eventType: string, handler: EventHandler) {
    this.handlers.get(eventType)?.delete(handler)
  }

  get connected() {
    return this.ws?.readyState === WebSocket.OPEN
  }
}

export const wsClient = new WebSocketClient()
export default wsClient
