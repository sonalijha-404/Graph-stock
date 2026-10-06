import { createContext, useContext, useMemo, useState, type ReactNode } from 'react'
import type { ChatResponse, Subgraph } from '../types'

type AppContextValue = {
  lastResponse: ChatResponse | null
  setLastResponse: (r: ChatResponse | null) => void
  highlightSubgraph: Subgraph | null
  setHighlightSubgraph: (s: Subgraph | null) => void
  lastQueryMs: number | null
  setLastQueryMs: (n: number | null) => void
}

const AppContext = createContext<AppContextValue | null>(null)

export function AppProvider({ children }: { children: ReactNode }) {
  const [lastResponse, setLastResponse] = useState<ChatResponse | null>(null)
  const [highlightSubgraph, setHighlightSubgraph] = useState<Subgraph | null>(null)
  const [lastQueryMs, setLastQueryMs] = useState<number | null>(null)
  const value = useMemo(
    () => ({
      lastResponse,
      setLastResponse,
      highlightSubgraph,
      setHighlightSubgraph,
      lastQueryMs,
      setLastQueryMs,
    }),
    [lastResponse, highlightSubgraph, lastQueryMs],
  )
  return <AppContext.Provider value={value}>{children}</AppContext.Provider>
}

export function useApp() {
  const ctx = useContext(AppContext)
  if (!ctx) throw new Error('useApp outside provider')
  return ctx
}
