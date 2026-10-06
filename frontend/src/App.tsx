import { NavLink, Route, Routes } from 'react-router-dom'
import { useEffect, useState } from 'react'
import { api } from './api/client'
import { AppProvider, useApp } from './context/AppContext'
import { AskPage } from './pages/AskPage'
import { DashboardPage } from './pages/DashboardPage'
import { GraphPage } from './pages/GraphPage'
import { HowItWorksPage } from './pages/HowItWorksPage'

function Shell() {
  const [health, setHealth] = useState<string>('…')
  const { lastQueryMs } = useApp()

  useEffect(() => {
    api.health()
      .then((h) => setHealth(h.neo4j === 'up' ? 'Neo4j up' : 'Neo4j down'))
      .catch(() => setHealth('API unreachable'))
  }, [])

  const nav = 'block rounded-md px-3 py-2 text-sm hover:bg-slate-800'
  const active = 'bg-slate-800 text-white font-medium'

  return (
    <div className="flex min-h-screen flex-col">
      <header className="flex items-center justify-between border-b border-slate-800 px-4 py-3">
        <div>
          <div className="font-semibold text-white">PortfolioGraph AI</div>
          <div className="text-xs text-slate-500">Synthetic · Neo4j</div>
        </div>
      </header>
      <div className="flex flex-1">
        <nav className="w-44 shrink-0 border-r border-slate-800 p-3 space-y-1">
          <NavLink to="/" end className={({ isActive }) => `${nav} ${isActive ? active : 'text-slate-400'}`}>
            Dashboard
          </NavLink>
          <NavLink to="/ask" className={({ isActive }) => `${nav} ${isActive ? active : 'text-slate-400'}`}>
            Ask
          </NavLink>
          <NavLink to="/graph" className={({ isActive }) => `${nav} ${isActive ? active : 'text-slate-400'}`}>
            Graph
          </NavLink>
          <NavLink to="/how" className={({ isActive }) => `${nav} ${isActive ? active : 'text-slate-400'}`}>
            How it works
          </NavLink>
        </nav>
        <main className="flex-1 overflow-auto p-6">
          <Routes>
            <Route path="/" element={<DashboardPage />} />
            <Route path="/ask" element={<AskPage />} />
            <Route path="/graph" element={<GraphPage />} />
            <Route path="/how" element={<HowItWorksPage />} />
          </Routes>
        </main>
      </div>
      <footer className="border-t border-slate-800 px-4 py-2 text-xs text-slate-500">
        {health}
        {lastQueryMs != null && ` · Last query ${lastQueryMs} ms`}
      </footer>
    </div>
  )
}

export default function App() {
  return (
    <AppProvider>
      <Shell />
    </AppProvider>
  )
}
