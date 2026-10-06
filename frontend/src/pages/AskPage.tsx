import { useState } from 'react'
import { Link } from 'react-router-dom'
import { api } from '../api/client'
import { useApp } from '../context/AppContext'
import type { ChatResponse } from '../types'

type Tab = 'answer' | 'graph' | 'cypher' | 'calculation' | 'execution'

export function AskPage() {
  const [question, setQuestion] = useState('')
  const [tab, setTab] = useState<Tab>('answer')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const { lastResponse, setLastResponse, setHighlightSubgraph, setLastQueryMs } = useApp()
  const response = lastResponse

  async function submit(e: React.FormEvent) {
    e.preventDefault()
    if (!question.trim()) return
    setLoading(true)
    setError(null)
    try {
      const res = await api.chat(question.trim())
      setLastResponse(res)
      setHighlightSubgraph(res.subgraph)
      setLastQueryMs(res.execution_ms.total)
      setTab('answer')
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Request failed')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="space-y-4">
      <h1 className="text-xl font-semibold">Ask</h1>
      <form onSubmit={submit} className="flex gap-2">
        <input
          value={question}
          onChange={(e) => setQuestion(e.target.value)}
          placeholder="Ask about customers, stocks, sectors…"
          className="flex-1 rounded-md border border-slate-600 bg-slate-900 px-3 py-2 text-sm text-white placeholder:text-slate-500"
        />
        <button
          type="submit"
          disabled={loading}
          className="rounded-md bg-sky-600 px-4 py-2 text-sm font-medium text-white hover:bg-sky-500 disabled:opacity-50"
        >
          {loading ? '…' : 'Ask'}
        </button>
      </form>
      {error && <p className="text-sm text-red-300">{error}</p>}
      {response && <ResponsePanel response={response} tab={tab} setTab={setTab} />}
    </div>
  )
}

function ResponsePanel({
  response,
  tab,
  setTab,
}: {
  response: ChatResponse
  tab: Tab
  setTab: (t: Tab) => void
}) {
  const tabs: Tab[] = ['answer', 'graph', 'cypher', 'calculation', 'execution']
  return (
    <div className="rounded-lg border border-slate-700 bg-slate-900/50">
      <div className="flex flex-wrap gap-1 border-b border-slate-700 p-2">
        {tabs.map((t) => (
          <button
            key={t}
            type="button"
            onClick={() => setTab(t)}
            className={`rounded px-2 py-1 text-xs capitalize ${tab === t ? 'bg-slate-700 text-white' : 'text-slate-400 hover:text-white'}`}
          >
            {t === 'graph' ? 'Graph path' : t}
          </button>
        ))}
      </div>
      <div className="p-4 text-sm text-slate-200">
        {tab === 'answer' && (
          <>
            <p>{response.answer}</p>
            <p className="mt-3 text-xs text-slate-500">{response.disclaimer}</p>
            {response.results.length > 0 && (
              <pre className="mt-3 max-h-48 overflow-auto rounded bg-slate-950 p-2 text-xs">
                {JSON.stringify(response.results, null, 2)}
              </pre>
            )}
          </>
        )}
        {tab === 'graph' && (
          <>
            <p className="mb-2 text-slate-400">
              {response.subgraph.nodes.length} nodes, {response.subgraph.edges.length} edges
            </p>
            <Link to="/graph" className="text-sky-400 hover:underline">
              Open in Graph explorer →
            </Link>
          </>
        )}
        {tab === 'cypher' && (
          <pre className="overflow-auto whitespace-pre-wrap rounded bg-slate-950 p-3 text-xs text-emerald-200/90">
            {response.cypher}
            {'\n\n'}
            {JSON.stringify(response.parameters, null, 2)}
          </pre>
        )}
        {tab === 'calculation' &&
          (response.calculations.length ? (
            <ul className="space-y-2">
              {response.calculations.map((c) => (
                <li key={c.label} className="rounded border border-slate-700 p-2">
                  <div className="font-medium">{c.label}</div>
                  <div className="text-slate-400">{c.expression}</div>
                  <div>{c.value.toLocaleString('en-IN')}</div>
                </li>
              ))}
            </ul>
          ) : (
            <p className="text-slate-500">No calculations for this intent.</p>
          ))}
        {tab === 'execution' && (
          <ul className="space-y-1 text-slate-300">
            <li>Intent: {response.intent}</li>
            <li>Stages: {response.stages.join(' → ')}</li>
            <li>Neo4j: {response.execution_ms.neo4j} ms</li>
            <li>Calculation: {response.execution_ms.calculation} ms</li>
            <li>Total: {response.execution_ms.total} ms</li>
          </ul>
        )}
      </div>
    </div>
  )
}
