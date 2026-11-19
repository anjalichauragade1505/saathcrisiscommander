import { Cloud, Bell, Clock } from 'lucide-react'

export default function TopBar({ role, setRole, elapsedSeconds }) {
  const mins = Math.floor(elapsedSeconds / 60).toString().padStart(2, '0')
  const secs = Math.floor(elapsedSeconds % 60).toString().padStart(2, '0')
  const hrs = Math.floor(elapsedSeconds / 3600).toString().padStart(2, '0')

  const roles = [
    { id: 'commander', label: 'Incident Commander' },
    { id: 'field', label: 'Field Reporter' },
    { id: 'food_officer', label: 'District Food Officer' },
  ]

  return (
    <div className="flex flex-wrap items-center justify-between gap-3 px-4 py-3 panel mb-4">
      <div className="flex items-center gap-3">
        <div className="w-9 h-9 rounded-lg bg-violet/20 flex items-center justify-center text-violet font-display font-bold border border-violet/40">
          S
        </div>
        <div>
          <div className="font-display font-semibold text-sm leading-tight">SAATH</div>
          <div className="text-xs text-gray-400 leading-tight">CRISIS COMMANDER</div>
        </div>
      </div>

      <div className="flex items-center gap-2 bg-critical/10 border border-critical/40 rounded-full px-3 py-1 text-xs">
        <span className="w-2 h-2 rounded-full bg-critical pulse-dot" />
        <span className="text-critical font-semibold">LIVE SIMULATION</span>
        <Clock size={13} className="ml-1 text-gray-400" />
        <span className="font-mono text-gray-300">{hrs}:{mins}:{secs}</span>
      </div>

      <div className="flex items-center gap-1 text-xs text-gray-400">
        <Cloud size={14} /> Nagpur, simulated
      </div>

      <div className="flex items-center gap-2 bg-panel border border-panelborder rounded-full p-1">
        {roles.map(r => (
          <button
            key={r.id}
            onClick={() => setRole(r.id)}
            className={`text-xs px-3 py-1.5 rounded-full transition ${
              role === r.id ? 'bg-cyan/20 text-cyan border border-cyan/50' : 'text-gray-400 hover:text-gray-200'
            }`}
          >
            {r.label}
          </button>
        ))}
      </div>

      <Bell size={16} className="text-gray-400" />
    </div>
  )
}
