import type { ChatResponse, Health, Stats, Subgraph } from '../types'

const BASE = '/api'

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${BASE}${path}`, {
    headers: { 'Content-Type': 'application/json', ...(init?.headers || {}) },
    ...init,
  })
  if (!res.ok) {
    const body = await res.json().catch(() => ({}))
    const msg = body?.error?.message || res.statusText
    throw new Error(msg)
  }
  return res.json()
}

export const api = {
  health: () => request<Health>('/health'),
  stats: () => request<Stats>('/stats'),
  chat: (question: string) =>
    request<ChatResponse>('/chat', { method: 'POST', body: JSON.stringify({ question }) }),
  graphStock: (symbol: string) => request<Subgraph>(`/graph/stock/${encodeURIComponent(symbol)}`),
  graphCustomer: (id: string) => request<Subgraph>(`/graph/customer/${encodeURIComponent(id)}`),
  graphSector: (name: string) => request<Subgraph>(`/graph/sector/${encodeURIComponent(name)}`),
  impactSimulate: (body: {
    scope: string
    symbol?: string
    sector?: string
    change_percent: number
  }) =>
    request<ChatResponse>('/impact/simulate', {
      method: 'POST',
      body: JSON.stringify(body),
    }),
}
