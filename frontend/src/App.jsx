import { useEffect, useState, useCallback } from 'react'
import { Zap, RotateCcw } from 'lucide-react'
import { api } from './api'
import TopBar from './components/TopBar'
import StatsRow from './components/StatsRow'
import SituationMap from './components/SituationMap'
import AgentActivityPanel from './components/AgentActivityPanel'
import IncidentFeedPanel from './components/IncidentFeedPanel'
import PendingApprovalsPanel from './components/PendingApprovalsPanel'
import ResourceOverviewPanel from './components/ResourceOverviewPanel'
import RiskForecastPanel from './components/RiskForecastPanel'
import InjectEventModal from './components/InjectEventModal'
import FieldReporterView from './components/FieldReporterView'
import FoodOfficerView from './components/FoodOfficerView'

const POLL_MS = 2000

export default function App() {
  const [role, setRole] = useState('commander')
  const [state, setState] = useState(null)
  const [roads, setRoads] = useState([])
  const [modalOpen, setModalOpen] = useState(false)
  const [refreshKey, setRefreshKey] = useState(0)
  const [elapsedSeconds, setElapsedSeconds] = useState(0)
  const [error, setError] = useState(null)

  const refresh = useCallback(() => setRefreshKey(k => k + 1), [])

  useEffect(() => {
    let cancelled = false
    async function load() {
      try {
        const [s, r] = await Promise.all([api.getState(), api.getRoads()])
        if (!cancelled) { setState(s); setRoads(r.roads); setError(null) }
      } catch (e) {
        if (!cancelled) setError('Cannot reach backend — is it running on the configured VITE_API_URL?')
      }
    }
    load()
    const interval = setInterval(load, POLL_MS)
    return () => { cancelled = true; clearInterval(interval) }
  }, [refreshKey])

  useEffect(() => {
    const t = setInterval(() => setElapsedSeconds(s => s + 1), 1000)
    return () => clearInterval(t)
  }, [])

  async function handleReset() {
    await api.resetSimulation()
    setElapsedSeconds(0)
    refresh()
  }

  if (error) {
    return (
      <div className="min-h-screen flex items-center justify-center text-center p-6">
        <div className="panel p-6 max-w-md">
          <div className="text-critical font-display font-semibold mb-2">Connection error</div>
          <div className="text-sm text-gray-400">{error}</div>
        </div>
      </div>
    )
  }

  if (!state) {
    return <div className="min-h-screen flex items-center justify-center text-gray-500 text-sm">Loading simulation…</div>
  }

  return (
    <div className="min-h-screen p-4 max-w-[1400px] mx-auto">
      <TopBar role={role} setRole={setRole} elapsedSeconds={elapsedSeconds} />

      {role === 'commander' && (
        <>
          <StatsRow stats={state.stats} />
          <div className="grid grid-cols-1 xl:grid-cols-3 gap-4 mb-4">
            <div className="xl:col-span-2">
              <SituationMap zones={state.zones} roads={roads} />
            </div>
            <div className="space-y-4">
              <IncidentFeedPanel incidents={state.incidents} />
              <AgentActivityPanel activity={state.agent_activity} />
            </div>
          </div>
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-4 mb-4">
            <PendingApprovalsPanel pendingActions={state.pending_actions} onChanged={refresh} />
            <ResourceOverviewPanel resources={state.resources} />
            <RiskForecastPanel refreshKey={refreshKey} />
          </div>

          <div className="fixed bottom-6 right-6 flex flex-col gap-2 items-end">
            <button onClick={handleReset}
              className="flex items-center gap-2 bg-panel border border-panelborder text-gray-300 px-4 py-2 rounded-full text-xs hover:border-cyan/50">
              <RotateCcw size={13} /> Reset Simulation
            </button>
            <button onClick={() => setModalOpen(true)}
              className="flex items-center gap-2 bg-violet/20 border border-violet/50 text-violet px-5 py-3 rounded-full text-sm font-medium glow-cyan hover:bg-violet/30">
              <Zap size={16} /> Inject New Event
            </button>
          </div>

          <InjectEventModal
            open={modalOpen} onClose={() => setModalOpen(false)}
            zones={state.zones} roads={roads} onInjected={refresh}
          />
        </>
      )}

      {role === 'field' && (
        <FieldReporterView zones={state.zones} refreshKey={refreshKey} onChanged={refresh} />
      )}

      {role === 'food_officer' && (
        <FoodOfficerView refreshKey={refreshKey} onChanged={refresh} />
      )}
    </div>
  )
}
