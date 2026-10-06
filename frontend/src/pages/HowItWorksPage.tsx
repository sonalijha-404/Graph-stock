import { Background, Controls, MarkerType, ReactFlow, type Edge, type Node } from 'reactflow'
import 'reactflow/dist/style.css'
import { useMemo } from 'react'
import { useApp } from '../context/AppContext'

const STAGE_IDS = ['intent', 'template', 'neo4j', 'impact', 'answer'] as const

const EXPLAIN: Record<string, string> = {
  question: 'Natural-language question from the user.',
  intent: 'Rule router (or LLM) picks a catalog intent and entities.',
  template: 'Backend binds parameters to a fixed Cypher template.',
  neo4j: 'Read-only graph traversal returns holdings and relationships.',
  impact: 'Python computes estimated exposure — not the LLM.',
  answer: 'Structured response with subgraph, Cypher, and timings.',
}

export function HowItWorksPage() {
  const { lastResponse } = useApp()
  const active = new Set(lastResponse?.stages || [])

  const nodes: Node[] = useMemo(
    () => [
      { id: 'question', position: { x: 0, y: 80 }, data: { label: 'Question' }, style: nodeStyle(active.has('intent')) },
      { id: 'intent', position: { x: 180, y: 80 }, data: { label: 'Intent' }, style: nodeStyle(active.has('intent')) },
      { id: 'template', position: { x: 360, y: 80 }, data: { label: 'Template' }, style: nodeStyle(active.has('template')) },
      { id: 'neo4j', position: { x: 540, y: 80 }, data: { label: 'Neo4j' }, style: nodeStyle(active.has('neo4j')) },
      { id: 'impact', position: { x: 720, y: 80 }, data: { label: 'Impact' }, style: nodeStyle(active.has('impact')) },
      { id: 'answer', position: { x: 900, y: 80 }, data: { label: 'Answer' }, style: nodeStyle(active.has('answer')) },
    ],
    [active],
  )

  const edges: Edge[] = [
    edge('question', 'intent'),
    edge('intent', 'template'),
    edge('template', 'neo4j'),
    edge('neo4j', 'impact'),
    edge('impact', 'answer'),
  ]

  const selectedExplain = lastResponse
    ? STAGE_IDS.filter((s) => active.has(s))
        .map((s) => `${s}: ${EXPLAIN[s]}`)
        .join('\n')
    : EXPLAIN.intent

  return (
    <div className="space-y-4">
      <h1 className="text-xl font-semibold">How it works</h1>
      <p className="text-sm text-slate-400">
        Highlighted nodes match stages from your last query. Stock-holder questions skip Impact.
      </p>
      <div className="h-[280px] rounded-lg border border-slate-700 bg-slate-900">
        <ReactFlow nodes={nodes} edges={edges} fitView nodesDraggable={false} nodesConnectable={false} proOptions={{ hideAttribution: true }}>
          <Background color="#334155" gap={16} />
          <Controls showInteractive={false} />
        </ReactFlow>
      </div>
      <pre className="whitespace-pre-wrap rounded border border-slate-700 bg-slate-950 p-3 text-xs text-slate-300">
        {selectedExplain}
        {'\n\n'}
        {lastResponse ? `Last stages: ${lastResponse.stages.join(' → ')}` : 'Run a question on Ask to light the pipeline.'}
      </pre>
    </div>
  )
}

function nodeStyle(on: boolean) {
  return {
    background: on ? '#0ea5e9' : '#1e293b',
    color: '#f8fafc',
    border: '1px solid #475569',
    borderRadius: 8,
    fontSize: 12,
    padding: 8,
  }
}

function edge(a: string, b: string): Edge {
  return {
    id: `${a}-${b}`,
    source: a,
    target: b,
    markerEnd: { type: MarkerType.ArrowClosed },
    style: { stroke: '#64748b' },
  }
}
