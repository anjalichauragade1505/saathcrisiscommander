import { useEffect, useState, useRef } from 'react'
import { WifiOff, Wifi, MapPin, Send } from 'lucide-react'
import { api } from '../api'

export default function FieldReporterView({ zones, refreshKey, onChanged }) {
  const [zoneId, setZoneId] = useState(zones[0]?.id || null)
  const [tasks, setTasks] = useState([])
  const [message, setMessage] = useState('')
  const [queue, setQueue] = useState([])
  const [syncedNotice, setSyncedNotice] = useState(null)
  const wasDown = useRef(false)

  const zone = zones.find(z => z.id === Number(zoneId))
  const networkDown = zone?.field_network_down

  useEffect(() => {
    if (zoneId) api.getFieldTasks(zoneId).then(d => setTasks(d.tasks)).catch(() => {})
  }, [zoneId, refreshKey])

  // when connectivity is restored and we have a queue, sync it
  useEffect(() => {
    async function trySync() {
      if (wasDown.current && !networkDown && queue.length > 0 && zoneId) {
        const res = await api.fieldSync({ zone_id: Number(zoneId), reports: queue })
        setSyncedNotice(res.synced)
        setQueue([])
        onChanged()
      }
      wasDown.current = networkDown
    }
    trySync()
  }, [networkDown])

  async function submitReport(text) {
    if (!zoneId || !text) return
    const clientTimestamp = new Date().toISOString()
    if (networkDown) {
      setQueue(q => [...q, { message: text, client_timestamp: clientTimestamp }])
      setMessage('')
      return
    }
    try {
      await api.fieldReport({ zone_id: Number(zoneId), message: text, client_timestamp: clientTimestamp })
      setMessage('')
      onChanged()
    } catch (e) {
      if (e.status === 503) {
        setQueue(q => [...q, { message: text, client_timestamp: clientTimestamp }])
        setMessage('')
      }
    }
  }

  return (
    <div className="max-w-md mx-auto space-y-4">
      <div className="panel p-4">
        <div className="font-display font-semibold mb-2 text-sm">SAATH FIELD</div>
        <label className="text-xs text-gray-400">Your zone</label>
        <select value={zoneId || ''} onChange={e => setZoneId(e.target.value)}
          className="w-full mt-1 mb-3 bg-bgmain border border-panelborder rounded px-2 py-1.5 text-sm">
          {zones.map(z => <option key={z.id} value={z.id}>{z.name}</option>)}
        </select>

        <div className={`flex items-center gap-2 text-xs rounded-lg px-3 py-2 border ${
          networkDown ? 'bg-critical/10 border-critical/40 text-critical' : 'bg-safe/10 border-safe/40 text-safe'
        }`}>
          {networkDown ? <WifiOff size={14} /> : <Wifi size={14} />}
          {networkDown ? 'No connectivity — reports will queue locally' : 'Connected'}
        </div>

        {queue.length > 0 && (
          <div className="mt-2 text-xs text-moderate">📥 {queue.length} report(s) saved locally, will sync when connectivity returns</div>
        )}
        {syncedNotice && (
          <div className="mt-2 text-xs text-safe">
            ✓ Synced {syncedNotice.length} report(s) — avg delay {Math.round(syncedNotice.reduce((a, s) => a + s.delay_seconds, 0) / syncedNotice.length)}s
          </div>
        )}
      </div>

      {zone && (
        <div className="panel p-4">
          <div className="flex items-center gap-2 text-critical text-xs font-semibold mb-1">🔴 PRIORITY ZONE</div>
          <div className="font-display font-semibold">{zone.name}</div>
          <div className="text-xs text-gray-400">{zone.affected_population_est.toLocaleString()} affected — {zone.severity_label}</div>
        </div>
      )}

      {tasks.length > 0 && (
        <div className="panel p-4">
          <div className="text-xs text-gray-400 mb-2">Active tasks in this zone</div>
          {tasks.map(t => (
            <div key={t.id} className="text-sm text-gray-200 border-b border-panelborder/50 py-1.5 last:border-0">
              {t.quantity}x {t.resource_type.replace('_', ' ')} — {t.priority} priority
            </div>
          ))}
        </div>
      )}

      <div className="panel p-4 space-y-2">
        <button onClick={() => submitReport('Marked arrived at zone')}
          className="w-full bg-cyan/15 border border-cyan/40 text-cyan rounded-lg py-2 text-sm flex items-center justify-center gap-2">
          <MapPin size={14} /> Mark Arrived
        </button>
        <div className="flex gap-2">
          <input value={message} onChange={e => setMessage(e.target.value)} placeholder="Report situation…"
            className="flex-1 bg-bgmain border border-panelborder rounded-lg px-3 py-2 text-sm" />
          <button onClick={() => submitReport(message)}
            className="bg-violet/20 border border-violet/40 text-violet rounded-lg px-3">
            <Send size={14} />
          </button>
        </div>
        <button onClick={() => submitReport('EMERGENCY — requesting immediate backup')}
          className="w-full bg-critical/15 border border-critical/40 text-critical rounded-lg py-2 text-sm">
          🚨 Emergency
        </button>
      </div>
    </div>
  )
}
