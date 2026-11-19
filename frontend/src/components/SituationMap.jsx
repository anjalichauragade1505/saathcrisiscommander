import { useState } from 'react'

const SEVERITY_COLOR = {
  LOW: '#22C55E',
  MODERATE: '#EAB308',
  HIGH: '#F59E0B',
  CRITICAL: '#EF4444',
}

export default function SituationMap({ zones, roads }) {
  const [selected, setSelected] = useState(null)
  const zoneById = Object.fromEntries(zones.map(z => [z.id, z]))
  const maxPop = Math.max(...zones.map(z => z.population), 1)

  return (
    <div className="panel p-4 flex flex-col lg:flex-row gap-4">
      <div className="flex-1">
        <div className="flex items-center justify-between mb-2">
          <span className="font-display text-sm font-semibold text-cyan">LIVE SITUATION MAP</span>
          <span className="text-[11px] text-gray-500">Nagpur - simulated grid, not real geography</span>
        </div>

        <svg viewBox="0 0 800 620" className="w-full h-auto rounded-lg" style={{ background: '#0B0F1A' }}>
          {roads.map(r => {
            const a = zoneById[r.zone_a_id], b = zoneById[r.zone_b_id]
            if (!a || !b) return null
            const blocked = r.status === 'blocked'
            return (
              <g key={r.id}>
                <line x1={a.x} y1={a.y} x2={b.x} y2={b.y}
                  stroke={blocked ? '#EF4444' : '#334155'}
                  strokeWidth={blocked ? 3 : 2}
                  strokeDasharray={blocked ? '6 4' : '0'} />
                {blocked && (
                  <text x={(a.x + b.x) / 2} y={(a.y + b.y) / 2 - 8} fill="#EF4444" fontSize="11" textAnchor="middle" className="font-mono">
                    {r.name} BLOCKED
                  </text>
                )}
              </g>
            )
          })}

          {zones.map(z => {
            const radius = 22 + (z.population / maxPop) * 30
            const color = SEVERITY_COLOR[z.severity_label] || '#22C55E'
            const isSelected = selected?.id === z.id
            return (
              <g key={z.id} onClick={() => setSelected(z)} className="cursor-pointer">
                {(z.severity_label === 'CRITICAL' || z.severity_label === 'HIGH') && (
                  <circle cx={z.x} cy={z.y} r={radius + 6} fill={color} opacity="0.25">
                    <animate attributeName="r" values={`${radius + 4};${radius + 12};${radius + 4}`} dur="2s" repeatCount="indefinite" />
                  </circle>
                )}
                <circle cx={z.x} cy={z.y} r={radius} fill={color} fillOpacity="0.25" stroke={color} strokeWidth={isSelected ? 3 : 1.5} />
                {z.is_shelter_hub && (
                  <circle cx={z.x} cy={z.y} r={4} fill="#22D3EE" />
                )}
                <text x={z.x} y={z.y - 4} textAnchor="middle" fontSize="12" fill="#E5E7EB" className="font-display font-semibold">
                  {z.name.length > 18 ? z.name.slice(0, 16) + '…' : z.name}
                </text>
                <text x={z.x} y={z.y + 12} textAnchor="middle" fontSize="10" fill={color} className="font-mono">
                  {z.severity_label}
                </text>
              </g>
            )
          })}
        </svg>

        <div className="flex flex-wrap gap-3 mt-2 text-[11px] text-gray-400">
          <LegendDot color="#EF4444" label="Critical" />
          <LegendDot color="#F59E0B" label="High" />
          <LegendDot color="#EAB308" label="Moderate" />
          <LegendDot color="#22C55E" label="Low/Safe" />
          <LegendDot color="#22D3EE" label="Shelter Hub" />
        </div>
      </div>

      <div className="w-full lg:w-64 shrink-0">
        {selected ? (
          <div className="bg-bgmain border border-panelborder rounded-lg p-3">
            <div className="font-display font-semibold text-sm mb-1">{selected.name}</div>
            <div className="text-xs text-gray-400 mb-2">{selected.population.toLocaleString()} people</div>
            <Row label="Severity" value={selected.severity_label} color={SEVERITY_COLOR[selected.severity_label]} />
            <Row label="Est. affected" value={selected.affected_population_est.toLocaleString()} />
            <Row label="Confidence" value={`${Math.round(selected.confidence * 100)}%`} />
            <Row label="Shelter capacity" value={selected.shelter_capacity.toLocaleString()} />
            {selected.field_network_down && (
              <div className="mt-2 text-[11px] text-critical">⚠ Field connectivity down in this zone</div>
            )}
          </div>
        ) : (
          <div className="text-xs text-gray-500 p-3">Click a zone to see details</div>
        )}
      </div>
    </div>
  )
}

function LegendDot({ color, label }) {
  return (
    <span className="flex items-center gap-1">
      <span className="w-2.5 h-2.5 rounded-full" style={{ background: color }} /> {label}
    </span>
  )
}

function Row({ label, value, color }) {
  return (
    <div className="flex justify-between text-xs py-1 border-b border-panelborder/50">
      <span className="text-gray-400">{label}</span>
      <span className="font-mono" style={{ color: color || '#E5E7EB' }}>{value}</span>
    </div>
  )
}
