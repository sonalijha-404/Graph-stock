import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { api } from '../api/client'
import { useApp } from '../context/AppContext'
import type { CatalogKind, CustomerRow, PortfolioRow, SectorRow, Stats, StockRow } from '../types'

const SCENARIOS = [
  { label: 'Who owns TCS', question: 'Who owns TCS?' },
  { label: 'TCS + Infosys', question: 'Who owns both TCS and Infosys?' },
  { label: 'IT exposure', question: 'Who is highly exposed to IT?' },
  { label: 'TCS −10%', question: 'What happens if TCS drops 10%?' },
  { label: 'IT sector −10%', question: 'What happens if the IT sector drops 10%?' },
  { label: 'Explain Rahul Sharma', question: "Explain Rahul Sharma's exposure" },
]

export function DashboardPage() {
  const [stats, setStats] = useState<Stats | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [loading, setLoading] = useState(true)
  const [catalog, setCatalog] = useState<CatalogKind | null>(null)
  const [rows, setRows] = useState<CustomerRow[] | PortfolioRow[] | StockRow[] | SectorRow[]>([])
  const [listLoading, setListLoading] = useState(false)
  const { setLastResponse, setHighlightSubgraph, setLastQueryMs } = useApp()
  const navigate = useNavigate()

  useEffect(() => {
    let cancelled = false
    ;(async () => {
      try {
        const s = await api.stats()
        if (!cancelled) {
          setStats(s)
          setError(null)
        }
      } catch (e) {
        if (!cancelled) setError(e instanceof Error ? e.message : 'Failed to load dashboard')
      } finally {
        if (!cancelled) setLoading(false)
      }
    })()
    return () => {
      cancelled = true
    }
  }, [])

  async function openCatalog(kind: CatalogKind) {
    if (catalog === kind) {
      setCatalog(null)
      return
    }
    setCatalog(kind)
    setListLoading(true)
    setError(null)
    try {
      if (kind === 'customers') setRows(await api.customers())
      else if (kind === 'portfolios') setRows(await api.portfolios())
      else if (kind === 'stocks') setRows(await api.stocks())
      else setRows(await api.sectors())
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Failed to load list')
      setRows([])
    } finally {
      setListLoading(false)
    }
  }

  function openInGraph(mode: 'stock' | 'customer' | 'sector', query: string) {
    navigate('/graph', { state: { mode, query } })
  }

  async function runScenario(question: string) {
    setLoading(true)
    setError(null)
    try {
      const res = await api.chat(question)
      setLastResponse(res)
      setHighlightSubgraph(res.subgraph)
      setLastQueryMs(res.execution_ms.total)
      navigate('/ask')
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Query failed')
    } finally {
      setLoading(false)
    }
  }

  if (loading && !stats) {
    return <p className="text-slate-400">Loading dashboard…</p>
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-xl font-semibold text-white">Dashboard</h1>
        <p className="text-sm text-slate-400">
          Live counts from Neo4j. Click Customers, Portfolios, Stocks, or Sectors to open the demo list.
        </p>
      </div>
      {error && <p className="rounded border border-red-900/50 bg-red-950/30 px-3 py-2 text-sm text-red-300">{error}</p>}
      {stats && (
        <div className="grid grid-cols-2 gap-3 md:grid-cols-4">
          <Card title="Customers" value={String(stats.customers)} active={catalog === 'customers'} onClick={() => openCatalog('customers')} />
          <Card title="Portfolios" value={String(stats.portfolios)} active={catalog === 'portfolios'} onClick={() => openCatalog('portfolios')} />
          <Card title="Stocks" value={String(stats.stocks)} active={catalog === 'stocks'} onClick={() => openCatalog('stocks')} />
          <Card title="Sectors" value={String(stats.sectors)} active={catalog === 'sectors'} onClick={() => openCatalog('sectors')} />
          <Card title="Total value" value={`₹${stats.total_market_value.toLocaleString('en-IN')}`} />
          <Card
            title="Top sector"
            value={stats.top_sector ? `${stats.top_sector.sector}` : '—'}
          />
          <Card
            title="Max concentration"
            value={
              stats.highest_concentration
                ? `${stats.highest_concentration.symbol} ${stats.highest_concentration.concentration.toFixed(1)}%`
                : '—'
            }
          />
          <Card title="Latest event" value={stats.latest_event?.title ?? '—'} />
        </div>
      )}
      <div>
        <h2 className="mb-2 text-sm font-medium text-slate-300">Demo scenarios</h2>
        <div className="flex flex-wrap gap-2">
          {SCENARIOS.map((s) => (
            <button
              key={s.label}
              type="button"
              onClick={() => runScenario(s.question)}
              className="rounded-md border border-slate-600 bg-slate-800 px-3 py-1.5 text-sm text-slate-200 hover:bg-slate-700"
            >
              {s.label}
            </button>
          ))}
        </div>
      </div>
      {catalog && (
        <CatalogPanel
          kind={catalog}
          loading={listLoading}
          rows={rows}
          onOpenGraph={openInGraph}
        />
      )}
    </div>
  )
}

function Card({
  title,
  value,
  onClick,
  active,
}: {
  title: string
  value: string
  onClick?: () => void
  active?: boolean
}) {
  const className = `rounded-lg border px-4 py-3 text-left ${
    active ? 'border-sky-500 bg-slate-800' : 'border-slate-700 bg-slate-900/60'
  } ${onClick ? 'cursor-pointer hover:border-sky-700' : ''}`
  if (!onClick) {
    return (
      <div className={className}>
        <div className="text-xs uppercase tracking-wide text-slate-500">{title}</div>
        <div className="mt-1 text-lg font-medium text-white">{value}</div>
      </div>
    )
  }
  return (
    <button type="button" onClick={onClick} className={className}>
      <div className="text-xs uppercase tracking-wide text-slate-500">{title}</div>
      <div className="mt-1 text-lg font-medium text-white">{value}</div>
    </button>
  )
}

function CatalogPanel({
  kind,
  loading,
  rows,
  onOpenGraph,
}: {
  kind: CatalogKind
  loading: boolean
  rows: CustomerRow[] | PortfolioRow[] | StockRow[] | SectorRow[]
  onOpenGraph: (mode: 'stock' | 'customer' | 'sector', query: string) => void
}) {
  const titles: Record<CatalogKind, string> = {
    customers: 'Customers',
    portfolios: 'Portfolios',
    stocks: 'Stocks',
    sectors: 'Sectors',
  }
  return (
    <div className="rounded-lg border border-slate-700 bg-slate-900/40">
      <div className="border-b border-slate-800 px-4 py-3 text-sm font-medium text-white">
        {titles[kind]} · {loading ? '…' : rows.length}
      </div>
      <div className="max-h-[28rem] overflow-auto">
        {loading ? (
          <p className="px-4 py-3 text-sm text-slate-400">Loading demo data…</p>
        ) : (
          <table className="w-full border-collapse text-left text-sm">
            <thead className="sticky top-0 bg-slate-900 text-xs uppercase tracking-wide text-slate-500">
              {kind === 'customers' && (
                <tr>
                  <th className="px-4 py-2 font-medium">ID</th>
                  <th className="px-4 py-2 font-medium">Name</th>
                  <th className="px-4 py-2 font-medium">Risk</th>
                  <th className="px-4 py-2 font-medium">Portfolios</th>
                </tr>
              )}
              {kind === 'portfolios' && (
                <tr>
                  <th className="px-4 py-2 font-medium">Portfolio</th>
                  <th className="px-4 py-2 font-medium">Customer</th>
                  <th className="px-4 py-2 font-medium">Sectors</th>
                  <th className="px-4 py-2 font-medium">Stocks</th>
                  <th className="px-4 py-2 font-medium">Value</th>
                </tr>
              )}
              {kind === 'stocks' && (
                <tr>
                  <th className="px-4 py-2 font-medium">Symbol</th>
                  <th className="px-4 py-2 font-medium">Company</th>
                  <th className="px-4 py-2 font-medium">Sector</th>
                  <th className="px-4 py-2 font-medium">Price</th>
                  <th className="px-4 py-2 font-medium">Holdings</th>
                </tr>
              )}
              {kind === 'sectors' && (
                <tr>
                  <th className="px-4 py-2 font-medium">Sector</th>
                  <th className="px-4 py-2 font-medium">Stocks</th>
                  <th className="px-4 py-2 font-medium">Symbols</th>
                </tr>
              )}
            </thead>
            <tbody>
              {kind === 'customers' &&
                (rows as CustomerRow[]).map((row) => (
                  <tr
                    key={row.customer_id}
                    className="cursor-pointer border-t border-slate-800 hover:bg-slate-800/60"
                    onClick={() => onOpenGraph('customer', row.customer_id)}
                  >
                    <td className="px-4 py-2 text-slate-400">{row.customer_id}</td>
                    <td className="px-4 py-2">{row.name}</td>
                    <td className="px-4 py-2">{row.risk_profile}</td>
                    <td className="px-4 py-2">{row.portfolios}</td>
                  </tr>
                ))}
              {kind === 'portfolios' &&
                (rows as PortfolioRow[]).map((row) => (
                  <tr key={row.portfolio_id} className="border-t border-slate-800">
                    <td className="px-4 py-2">
                      <div>{row.name}</div>
                      <div className="text-xs text-slate-500">{row.portfolio_id} · {row.portfolio_type}</div>
                    </td>
                    <td
                      className="cursor-pointer px-4 py-2 text-sky-300"
                      onClick={() => onOpenGraph('customer', row.customer_id)}
                    >
                      {row.customer_name}
                    </td>
                    <td className="px-4 py-2">{row.sectors.join(', ')}</td>
                    <td className="px-4 py-2 text-slate-300">{row.symbols.join(', ')}</td>
                    <td className="px-4 py-2">₹{row.value.toLocaleString('en-IN')}</td>
                  </tr>
                ))}
              {kind === 'stocks' &&
                (rows as StockRow[]).map((row) => (
                  <tr
                    key={row.symbol}
                    className="cursor-pointer border-t border-slate-800 hover:bg-slate-800/60"
                    onClick={() => onOpenGraph('stock', row.symbol)}
                  >
                    <td className="px-4 py-2">{row.symbol}</td>
                    <td className="px-4 py-2">{row.company_name}</td>
                    <td className="px-4 py-2">{row.sector}</td>
                    <td className="px-4 py-2">₹{row.current_price.toLocaleString('en-IN')}</td>
                    <td className="px-4 py-2">{row.holders}</td>
                  </tr>
                ))}
              {kind === 'sectors' &&
                (rows as SectorRow[]).map((row) => (
                  <tr
                    key={row.name}
                    className="cursor-pointer border-t border-slate-800 hover:bg-slate-800/60"
                    onClick={() => onOpenGraph('sector', row.name)}
                  >
                    <td className="px-4 py-2">{row.name}</td>
                    <td className="px-4 py-2">{row.stocks}</td>
                    <td className="px-4 py-2 text-slate-300">{row.symbols.join(', ')}</td>
                  </tr>
                ))}
            </tbody>
          </table>
        )}
      </div>
    </div>
  )
}
