import cytoscape, { type Core } from 'cytoscape'
import { useEffect, useRef, useState } from 'react'
import type { GraphNode, Subgraph } from '../types'

const COLORS: Record<string, string> = {
  Customer: '#60a5fa',
  Portfolio: '#34d399',
  Holding: '#fbbf24',
  Stock: '#f472b6',
  Sector: '#a78bfa',
  Exchange: '#94a3b8',
  MarketEvent: '#fb7185',
}

type Props = {
  data: Subgraph
  highlight?: Subgraph | null
  height?: number
  onSelectNode?: (node: GraphNode | null) => void
  filterTypes?: string[]
  truncatedHint?: string
}

export function GraphView({
  data,
  highlight,
  height = 420,
  onSelectNode,
  filterTypes,
  truncatedHint,
}: Props) {
  const ref = useRef<HTMLDivElement>(null)
  const cyRef = useRef<Core | null>(null)
  const [selected, setSelected] = useState<GraphNode | null>(null)

  useEffect(() => {
    if (!ref.current) return
    const highlightIds = new Set(highlight?.nodes.map((n) => n.id) || [])
    const nodes = data.nodes
      .filter((n) => !filterTypes?.length || filterTypes.includes(n.type))
      .map((n) => ({
        data: {
          id: n.id,
          label: n.label,
          type: n.type,
          muted: highlightIds.size > 0 && !highlightIds.has(n.id),
        },
      }))
    const nodeIds = new Set(nodes.map((n) => n.data.id))
    const edges = data.edges
      .filter((e) => nodeIds.has(e.source) && nodeIds.has(e.target))
      .map((e) => ({
        data: { id: e.id, source: e.source, target: e.target, label: e.type },
      }))

    if (cyRef.current) cyRef.current.destroy()
    const cy = cytoscape({
      container: ref.current,
      elements: [...nodes, ...edges],
      style: [
        {
          selector: 'node',
          style: {
            label: 'data(label)',
            'text-valign': 'bottom',
            'text-margin-y': 6,
            'font-size': 10,
            color: '#cbd5e1',
            'background-color': '#64748b',
            width: 28,
            height: 28,
            opacity: 1,
          },
        },
        {
          selector: 'edge',
          style: {
            width: 1.5,
            'line-color': '#475569',
            'target-arrow-color': '#475569',
            'target-arrow-shape': 'triangle',
            'curve-style': 'bezier',
            label: edges.length <= 40 ? 'data(label)' : '',
            'font-size': 8,
            color: '#94a3b8',
          },
        },
        { selector: ':selected', style: { 'border-width': 3, 'border-color': '#fff' } },
      ],
      layout: { name: 'cose', animate: false, padding: 30 },
    })
    cy.on('tap', 'node', (evt) => {
      const id = evt.target.id()
      const n = data.nodes.find((x) => x.id === id) || null
      setSelected(n)
      onSelectNode?.(n)
    })
    cy.on('tap', (evt) => {
      if (evt.target === cy) {
        setSelected(null)
        onSelectNode?.(null)
      }
    })
    cy.nodes().forEach((ele) => {
      const t = ele.data('type') as string
      ele.style('background-color', COLORS[t] || '#64748b')
      ele.style('opacity', ele.data('muted') ? 0.25 : 1)
    })
    cyRef.current = cy
    return () => {
      cy.destroy()
      cyRef.current = null
    }
  }, [data, highlight, filterTypes, onSelectNode])

  return (
    <div className="flex flex-col gap-2">
      <div ref={ref} className="rounded-lg border border-slate-700 bg-slate-900/50" style={{ height }} />
      {data.truncated && (
        <p className="text-xs text-amber-400/90">
          {truncatedHint ?? 'Partial view — use Complete view in the explorer to load more nodes.'}
        </p>
      )}
      {selected && (
        <pre className="max-h-32 overflow-auto rounded border border-slate-700 bg-slate-950 p-2 text-xs text-slate-300">
          {JSON.stringify(selected.properties, null, 2)}
        </pre>
      )}
    </div>
  )
}
