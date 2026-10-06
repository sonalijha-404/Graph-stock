export interface GraphNode {
  id: string
  type: string
  label: string
  properties: Record<string, unknown>
}

export interface GraphEdge {
  id: string
  type: string
  source: string
  target: string
}

export type GraphViewMode = 'partial' | 'complete'

export interface Subgraph {
  nodes: GraphNode[]
  edges: GraphEdge[]
  truncated: boolean
  view?: GraphViewMode
  node_limit?: number
}

export interface ChatResponse {
  answer: string
  intent: string
  entities: Record<string, unknown>
  cypher: string
  parameters: Record<string, unknown>
  subgraph: Subgraph
  results: Record<string, unknown>[]
  calculations: { label: string; expression: string; value: number }[]
  stages: string[]
  execution_ms: { neo4j: number; calculation: number; total: number }
  disclaimer: string
}

export interface Stats {
  customers: number
  portfolios: number
  stocks: number
  sectors: number
  total_market_value: number
  top_sector: { sector: string; value: number } | null
  highest_concentration: {
    portfolio_id: string
    portfolio_name: string
    symbol: string
    concentration: number
  } | null
  latest_event: {
    event_id: string
    title: string
    change_percent: number
    severity: string
  } | null
}

export interface Health {
  status: string
  neo4j: string
}

export interface CustomerRow {
  customer_id: string
  name: string
  risk_profile: string
  country: string
  portfolios: number
}

export interface PortfolioRow {
  portfolio_id: string
  name: string
  portfolio_type: string
  customer_id: string
  customer_name: string
  symbols: string[]
  sectors: string[]
  value: number
}

export interface StockRow {
  symbol: string
  company_name: string
  current_price: number
  sector: string
  holders: number
}

export interface SectorRow {
  name: string
  stocks: number
  symbols: string[]
}

export type CatalogKind = 'customers' | 'portfolios' | 'stocks' | 'sectors'
