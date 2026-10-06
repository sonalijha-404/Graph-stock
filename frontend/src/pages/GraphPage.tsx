import { useCallback, useEffect, useState } from 'react'
import { useLocation } from 'react-router-dom'
import { api } from '../api/client'
import { useApp } from '../context/AppContext'
import { GraphView } from '../graph/GraphView'
import type { GraphViewMode, Subgraph } from '../types'

const NODE_TYPES = ['Customer', 'Portfolio', 'Holding', 'Stock', 'Sector']

export function GraphPage() {
  const { highlightSubgraph } = useApp()
  const location = useLocation()
  const incoming = (location.state ?? {}) as { mode?: 'stock' | 'customer' | 'sector'; query?: string }
  const [query, setQuery] = useState(incoming.query ?? 'TCS')
  const [mode, setMode] = useState<'stock' | 'customer' | 'sector'>(incoming.mode ?? 'stock')
  const [data, setData] = useState<Subgraph | null>(null)
  const [filter, setFilter] = useState<string[]>([])
  const [error, setError] = useState<string | null>(null)
  const [loading, setLoading] = useState(false)
  const [viewMode, setViewMode] = useState<GraphViewMode>('partial')
  const [showAnswerHighlight, setShowAnswerHighlight] = useState(!incoming.query)

  const load = useCallback(
    async (view: GraphViewMode = viewMode) => {
      setLoading(true)
      setError(null)
      setShowAnswerHighlight(false)
      try {
        let g: Subgraph
        if (mode === 'stock') g = await api.graphStock(query, view)
        else if (mode === 'customer') g = await api.graphCustomer(query, view)
        else g = await api.graphSector(query, view)
        setData(g)
        setViewMode(view)
      } catch (e) {
        setError(e instanceof Error ? e.message : 'Load failed')
        setData(null)
      } finally {
        setLoading(false)
      }
    },
    [mode, query, viewMode],
  )

  useEffect(() => {
    load('partial')
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  const usingHighlight =
    showAnswerHighlight && viewMode === 'partial' && (highlightSubgraph?.nodes.length ?? 0) > 0
  const display = usingHighlight ? highlightSubgraph! : data

  function switchView(next: GraphViewMode) {
    if (next === 'partial' && highlightSubgraph?.nodes.length) {
      setShowAnswerHighlight(true)
      setViewMode('partial')
      return
    }
    load(next)
  }

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
          onClick={() => load(viewMode)}
          disabled={loading}
          className="rounded bg-sky-600 px-3 py-1.5 text-sm text-white hover:bg-sky-500 disabled:opacity-50"
        >
          Search
        </button>
        <div className="flex rounded-md border border-slate-600 p-0.5 text-xs">
          <button
            type="button"
            onClick={() => switchView('partial')}
            className={`rounded px-2.5 py-1 ${viewMode === 'partial' && !loading ? 'bg-slate-700 text-white' : 'text-slate-400'}`}
          >
            Partial view
          </button>
          <button
            type="button"
            onClick={() => switchView('complete')}
            disabled={loading}
            className={`rounded px-2.5 py-1 ${viewMode === 'complete' ? 'bg-sky-700 text-white' : 'text-slate-400'}`}
          >
            Complete view
          </button>
        </div>
      </div>
      {usingHighlight && (
        <p className="text-sm text-slate-400">
          Showing the subgraph from your last Ask answer (partial, up to 80 nodes). Use{' '}
          <strong className="font-medium text-sky-300">Complete view</strong> to load the full neighborhood for your search above.
        </p>
      )}
      {display && !usingHighlight && (
        <p className="text-sm text-slate-500">
          {display.view === 'complete' ? 'Complete view' : 'Partial view'}
          {display.node_limit != null ? ` · up to ${display.node_limit} nodes` : ''}
          {' · '}
          {display.nodes.length} nodes, {display.edges.length} edges
        </p>
      )}
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
          highlight={usingHighlight ? undefined : highlightSubgraph ?? undefined}
          height={520}
          filterTypes={filter.length ? filter : undefined}
          truncatedHint={
            display.truncated
              ? viewMode === 'partial'
                ? 'Switch to Complete view to load more nodes for this search.'
                : 'This neighborhood is still large; only the first 500 nodes are shown.'
              : undefined
          }
        />
      )}
    </div>
  )
}
