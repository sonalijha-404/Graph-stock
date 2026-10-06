import type {
  ChatResponse,
  CustomerRow,
  GraphViewMode,
  Health,
  PortfolioRow,
  SectorRow,
  Stats,
  StockRow,
  Subgraph,
} from '../types'

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
  customers: () => request<CustomerRow[]>('/customers'),
  portfolios: () => request<PortfolioRow[]>('/portfolios'),
  stocks: () => request<StockRow[]>('/stocks'),
  sectors: () => request<SectorRow[]>('/sectors'),
  chat: (question: string) =>
    request<ChatResponse>('/chat', { method: 'POST', body: JSON.stringify({ question }) }),
  graphStock: (symbol: string, view: GraphViewMode = 'partial') =>
    request<Subgraph>(`/graph/stock/${encodeURIComponent(symbol)}?view=${view}`),
  graphCustomer: (id: string, view: GraphViewMode = 'partial') =>
    request<Subgraph>(`/graph/customer/${encodeURIComponent(id)}?view=${view}`),
  graphSector: (name: string, view: GraphViewMode = 'partial') =>
    request<Subgraph>(`/graph/sector/${encodeURIComponent(name)}?view=${view}`),
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
