import { Radio } from 'lucide-react'

const ICON_COLOR = {
  alert: '#EF4444', flood: '#22D3EE', quake: '#F59E0B', plan: '#8B5CF6',
  approved: '#22C55E', rejected: '#EF4444', ai: '#8B5CF6', field: '#22D3EE',
  sync: '#EAB308', info: '#94A3B8',
}

export default function IncidentFeedPanel({ incidents }) {
  return (
    <div className="panel p-4">
      <div className="flex items-center justify-between mb-3">
        <div className="flex items-center gap-2">
          <Radio size={15} className="text-cyan" />
          <span className="font-display text-sm font-semibold">LIVE INCIDENT FEED</span>
        </div>
        <span className="text-[10px] text-critical flex items-center gap-1">
          <span className="w-1.5 h-1.5 rounded-full bg-critical pulse-dot" /> Live
        </span>
      </div>
      <div className="space-y-2 max-h-64 overflow-y-auto pr-1">
        {incidents.length === 0 && <div className="text-xs text-gray-500">No events yet. Inject one to begin.</div>}
        {incidents.map(i => (
          <div key={i.id} className="flex gap-2 text-xs">
            <span className="w-1.5 h-1.5 rounded-full mt-1.5 shrink-0" style={{ background: ICON_COLOR[i.icon] || '#94A3B8' }} />
            <div>
              <div className="font-mono text-[10px] text-gray-500">
                {i.timestamp ? new Date(i.timestamp).toLocaleTimeString() : ''}
              </div>
              <div className="text-gray-200">{i.message}</div>
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}
