import { useEffect, useState } from 'react'
import { api } from '../api/client'
import { useApp } from '../context/AppContext'
import { GraphView } from '../graph/GraphView'
import type { Subgraph } from '../types'

const NODE_TYPES = ['Customer', 'Portfolio', 'Holding', 'Stock', 'Sector']

export function GraphPage() {
  const { highlightSubgraph } = useApp()
  const [query, setQuery] = useState('TCS')
  const [mode, setMode] = useState<'stock' | 'customer' | 'sector'>('stock')
  const [data, setData] = useState<Subgraph | null>(null)
  const [filter, setFilter] = useState<string[]>([])
  const [error, setError] = useState<string | null>(null)
  const [loading, setLoading] = useState(false)

  async function load() {
    setLoading(true)
    setError(null)
    try {
      let g: Subgraph
      if (mode === 'stock') g = await api.graphStock(query)
      else if (mode === 'customer') g = await api.graphCustomer(query)
      else g = await api.graphSector(query)
      setData(g)
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Load failed')
      setData(null)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    load()
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  const display = highlightSubgraph?.nodes.length ? highlightSubgraph : data

  return (
    <div className="space-y-4">
      <h1 className="text-xl font-semibold">Graph explorer</h1>
      <div className="flex flex-wrap items-end gap-2">
        <select
          value={mode}
          onChange={(e) => setMode(e.target.value as typeof mode)}
          className="rounded border border-slate-600 bg-slate-900 px-2 py-1.5 text-sm"
        >
          <option value="stock">Stock</option>
          <option value="customer">Customer ID</option>
          <option value="sector">Sector</option>
        </select>
        <input
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          className="rounded border border-slate-600 bg-slate-900 px-2 py-1.5 text-sm"
          placeholder={mode === 'customer' ? 'C001' : mode === 'sector' ? 'IT' : 'TCS'}
        />
        <button
          type="button"
          onClick={load}
          disabled={loading}
          className="rounded bg-sky-600 px-3 py-1.5 text-sm text-white hover:bg-sky-500"
        >
          Search
        </button>
      </div>
      <div className="flex flex-wrap gap-2">
        {NODE_TYPES.map((t) => {
          const on = !filter.length || filter.includes(t)
          return (
            <button
              key={t}
              type="button"
              onClick={() =>
                setFilter((f) => (f.includes(t) ? f.filter((x) => x !== t) : [...f, t]))
              }
              className={`rounded border px-2 py-0.5 text-xs ${on ? 'border-sky-600 text-sky-300' : 'border-slate-700 text-slate-600 line-through'}`}
            >
              {t}
            </button>
          )
        })}
        <button type="button" onClick={() => setFilter([])} className="text-xs text-slate-400 underline">
          Reset filters
        </button>
      </div>
      {error && <p className="text-sm text-red-300">{error}</p>}
      {display && (
        <GraphView
          data={display}
          highlight={highlightSubgraph ?? undefined}
          height={520}
          filterTypes={filter.length ? filter : undefined}
        />
      )}
    </div>
  )
}
