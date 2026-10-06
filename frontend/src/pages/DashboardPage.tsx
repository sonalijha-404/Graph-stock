import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { api } from '../api/client'
import { useApp } from '../context/AppContext'
import { GraphView } from '../graph/GraphView'
import type { Stats } from '../types'

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
  const [preview, setPreview] = useState<Awaited<ReturnType<typeof api.graphStock>> | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [loading, setLoading] = useState(true)
  const { setLastResponse, setHighlightSubgraph, setLastQueryMs } = useApp()
  const navigate = useNavigate()

  useEffect(() => {
    let cancelled = false
    ;(async () => {
      try {
        const [s, g] = await Promise.all([api.stats(), api.graphStock('TCS')])
        if (!cancelled) {
          setStats(s)
          setPreview(g)
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
        <p className="text-sm text-slate-400">Live counts and values from Neo4j (synthetic).</p>
      </div>
      {error && <p className="rounded border border-red-900/50 bg-red-950/30 px-3 py-2 text-sm text-red-300">{error}</p>}
      {stats && (
        <div className="grid grid-cols-2 gap-3 md:grid-cols-4">
          <Card title="Customers" value={String(stats.customers)} />
          <Card title="Portfolios" value={String(stats.portfolios)} />
          <Card title="Stocks" value={String(stats.stocks)} />
          <Card title="Sectors" value={String(stats.sectors)} />
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
      {preview && (
        <div>
          <h2 className="mb-2 text-sm font-medium text-slate-300">TCS exposure preview</h2>
          <GraphView data={preview} height={320} />
        </div>
      )}
    </div>
  )
}

function Card({ title, value }: { title: string; value: string }) {
  return (
    <div className="rounded-lg border border-slate-700 bg-slate-900/60 px-4 py-3">
      <div className="text-xs uppercase tracking-wide text-slate-500">{title}</div>
      <div className="mt-1 text-lg font-medium text-white">{value}</div>
    </div>
  )
}
