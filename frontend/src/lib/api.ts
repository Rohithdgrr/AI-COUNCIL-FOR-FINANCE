import axios from 'axios'
import type { APIError } from '@/types/api'
import { apiKeyManager } from './secureStorage'

const API_BASE = '/api'

const api = axios.create({
  baseURL: API_BASE,
  timeout: 120000,
  headers: { 'Content-Type': 'application/json' },
})

// Request interceptor — attach API key securely
api.interceptors.request.use((config) => {
  const apiKey = apiKeyManager.getApiKey()
  if (apiKey) {
    config.headers['X-API-Key'] = apiKey
  }
  return config
})

// Response interceptor — handle errors
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response) {
      const status = error.response.status
      if (status === 401) {
        const err: APIError = { detail: 'Invalid API key', status_code: 401 }
        return Promise.reject(err)
      }
      if (status === 429) {
        const err: APIError = { detail: 'Rate limit exceeded', status_code: 429 }
        return Promise.reject(err)
      }
      if (status >= 500) {
        const err: APIError = { detail: error.response.data?.detail || 'Server error', status_code: status }
        return Promise.reject(err)
      }
    }
    return Promise.reject(error)
  }
)

// MCP client — separate instance with MCP API key
const mcpApi = axios.create({
  baseURL: '/mcp',
  timeout: 120000,
  headers: { 'Content-Type': 'application/json' },
})

mcpApi.interceptors.request.use((config) => {
  const mcpKey = apiKeyManager.getMcpApiKey()
  if (mcpKey) {
    config.headers['X-MCP-API-Key'] = mcpKey
  }
  return config
})

// --- Council ---
export const councilApi = {
  analyze: (query: string, context?: Record<string, unknown>) =>
    api.post('/council/analyze', { query, context }),
  query: (query: string, context?: Record<string, unknown>, stream = false) =>
    api.post('/council/query', { query, context, stream }),
  streamUrl: () => `${API_BASE}/council/stream`,
  session: (sessionId: string) =>
    api.get(`/council/session/${sessionId}`),
  history: (limit = 20, offset = 0) =>
    api.get('/council/history', { params: { limit, offset } }),
  exportPdf: (sessionId: string) =>
    api.get(`/council/export/${sessionId}`, { responseType: 'blob' }),
}

// --- RAG ---
export const ragApi = {
  upload: (files: File[]) => {
    const formData = new FormData()
    files.forEach((f) => formData.append('files', f))
    return api.post('/rag/upload', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    })
  },
  uploadUrl: (url: string, maxDepth?: number) =>
    api.post('/rag/upload-url', { url, max_depth: maxDepth ?? null }),
  query: (query: string, topK = 5) =>
    api.post('/rag/query', { query, top_k: topK }),
  graphQuery: (query: string) =>
    api.post('/rag/graph-query', { query }),
  hybridQuery: (query: string, topK = 5) =>
    api.post('/rag/hybrid-query', { query, top_k: topK }),
  collections: () => api.get('/rag/collections'),
  deleteCollection: (name: string) => api.delete(`/rag/collections/${name}`),
  documents: () => api.get('/rag/documents'),
  stats: () => api.get('/rag/stats'),
  health: () => api.get('/rag/health'),
}

// --- Risk ---
export const riskApi = {
  suppliers: () => api.get('/risk/suppliers'),
  heatmap: () => api.get('/risk/heatmap'),
  supplierScore: (id: string) => api.get(`/risk/score/${id}`),
}

// --- Optimize ---
export const optimizeApi = {
  routes: (data: Record<string, unknown>) => api.post('/optimize/routes', data),
  allocation: (data: Record<string, unknown>) => api.post('/optimize/allocation', data),
}

// --- Ingest ---
export const ingestApi = {
  erp: (data: Record<string, unknown>) => api.post('/ingest/erp', data),
  news: (articles: Record<string, unknown>[]) => api.post('/ingest/news', { articles }),
  social: (posts: Record<string, unknown>[], platform?: string) =>
    api.post('/ingest/social', { posts, platform }),
  status: () => api.get('/ingest/status'),
}

// --- Settings ---
export const settingsApi = {
  get: () => api.get('/settings/app'),
  update: (data: Record<string, unknown>) => api.put('/settings/app', data),
}

// --- Health ---
export const healthApi = {
  check: () => api.get('/health'),
  ready: () => api.get('/ready'),
}

// --- Models ---
export const modelsApi = {
  list: () => api.get('/models/status'),
}

// --- MCP ---
export const mcpApiMethods = {
  listTools: () => mcpApi.get('/tools'),
  manifest: () => mcpApi.get('/manifest'),
  toolsForAgent: (agent: string) => mcpApi.get(`/tools/${agent}`),
  health: () => mcpApi.get('/health'),
  invoke: (tool: string, params: Record<string, unknown>) =>
    mcpApi.post(`/tools/${tool}/invoke`, params),
}

// --- Observability ---
export const observabilityApi = {
  traces: (sessionId?: string, limit = 20) =>
    api.get('/observability/traces', { params: { session_id: sessionId, limit } }),
  metrics: () => api.get('/observability/metrics'),
  spans: (sessionId?: string) =>
    api.get('/observability/spans', { params: { session_id: sessionId } }),
}

// --- Market (Real-Time Data) ---
export const marketApi = {
  ticker: () => api.get('/market/ticker'),
  company: (symbol: string) => api.get(`/market/company/${symbol}`),
  riskDashboard: () => api.get('/market/risk-dashboard'),
  brandIntel: () => api.get('/market/brand-intel'),
  forexRates: () => api.get('/market/forex-rates'),
  commodityPrices: () => api.get('/market/commodity-prices'),
  supplyChainStocks: () => api.get('/market/supply-chain-stocks'),
  globalNews: () => api.get('/market/global-news'),
}

export { api, mcpApi }
export default api
