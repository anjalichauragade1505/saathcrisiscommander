import { useState } from 'react'
import { X, Zap } from 'lucide-react'
import { api } from '../api'

const EVENT_TYPES = [
  { id: 'flood', label: 'Flood (rainfall)' },
  { id: 'earthquake', label: 'Earthquake' },
  { id: 'road_block', label: 'Road blocked' },
  { id: 'road_clear', label: 'Road cleared' },
  { id: 'communication_failure', label: 'Communication failure' },
  { id: 'connectivity_restored', label: 'Connectivity restored' },
]

export default function InjectEventModal({ open, onClose, zones, roads, onInjected }) {
  const [type, setType] = useState('flood')
  const [rainfall, setRainfall] = useState(60)
  const [epicenter, setEpicenter] = useState(zones[0]?.id || '')
  const [magnitude, setMagnitude] = useState(7.5)
  const [roadId, setRoadId] = useState(roads[0]?.id || '')
  const [zoneId, setZoneId] = useState(zones[0]?.id || '')
  const [busy, setBusy] = useState(false)

  if (!open) return null

  async function submit() {
    setBusy(true)
    try {
      let payload = { type }
      if (type === 'flood') payload.rainfall_mm = Number(rainfall)
      if (type === 'earthquake') { payload.epicenter_zone_id = Number(epicenter); payload.magnitude = Number(magnitude) }
      if (type === 'road_block' || type === 'road_clear') payload.road_id = Number(roadId)
      if (type === 'communication_failure' || type === 'connectivity_restored') payload.zone_id = Number(zoneId)

      await api.injectEvent(payload)
      onInjected()
      onClose()
    } catch (e) {
      console.error(e)
    } finally {
      setBusy(false)
    }
  }

  return (
    <div className="fixed inset-0 bg-black/60 flex items-center justify-center z-50 p-4" onClick={onClose}>
      <div className="panel w-full max-w-md p-5" onClick={e => e.stopPropagation()}>
        <div className="flex justify-between items-center mb-4">
          <div className="flex items-center gap-2 text-violet font-display font-semibold">
            <Zap size={16} /> INJECT NEW EVENT
          </div>
          <button onClick={onClose}><X size={16} className="text-gray-400" /></button>
        </div>

        <div className="space-y-1 mb-4">
          {EVENT_TYPES.map(et => (
            <label key={et.id} className="flex items-center gap-2 text-sm py-1 cursor-pointer">
              <input type="radio" name="eventtype" checked={type === et.id} onChange={() => setType(et.id)} />
              {et.label}
            </label>
          ))}
        </div>

        {type === 'flood' && (
          <div className="mb-4">
            <label className="text-xs text-gray-400">Rainfall (mm/hr) — 60+ saturates</label>
            <input type="number" value={rainfall} onChange={e => setRainfall(e.target.value)}
              className="w-full mt-1 bg-bgmain border border-panelborder rounded px-2 py-1.5 text-sm" />
          </div>
        )}

        {type === 'earthquake' && (
          <div className="mb-4 space-y-2">
            <div>
              <label className="text-xs text-gray-400">Epicenter zone</label>
              <select value={epicenter} onChange={e => setEpicenter(e.target.value)}
                className="w-full mt-1 bg-bgmain border border-panelborder rounded px-2 py-1.5 text-sm">
                {zones.map(z => <option key={z.id} value={z.id}>{z.name}</option>)}
              </select>
            </div>
            <div>
              <label className="text-xs text-gray-400">Magnitude</label>
              <input type="number" step="0.1" value={magnitude} onChange={e => setMagnitude(e.target.value)}
                className="w-full mt-1 bg-bgmain border border-panelborder rounded px-2 py-1.5 text-sm" />
            </div>
          </div>
        )}

        {(type === 'road_block' || type === 'road_clear') && (
          <div className="mb-4">
            <label className="text-xs text-gray-400">Road</label>
            <select value={roadId} onChange={e => setRoadId(e.target.value)}
              className="w-full mt-1 bg-bgmain border border-panelborder rounded px-2 py-1.5 text-sm">
              {roads.map(r => <option key={r.id} value={r.id}>{r.name}</option>)}
            </select>
          </div>
        )}

        {(type === 'communication_failure' || type === 'connectivity_restored') && (
          <div className="mb-4">
            <label className="text-xs text-gray-400">Zone</label>
            <select value={zoneId} onChange={e => setZoneId(e.target.value)}
              className="w-full mt-1 bg-bgmain border border-panelborder rounded px-2 py-1.5 text-sm">
              {zones.map(z => <option key={z.id} value={z.id}>{z.name}</option>)}
            </select>
          </div>
        )}

        <button disabled={busy} onClick={submit}
          className="w-full bg-violet/20 border border-violet/50 text-violet rounded-lg py-2 text-sm font-medium hover:bg-violet/30 disabled:opacity-50">
          {busy ? 'Simulating…' : 'SIMULATE EVENT'}
        </button>
      </div>
    </div>
  )
}
