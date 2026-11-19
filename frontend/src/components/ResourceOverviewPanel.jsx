const LABELS = {
  ambulance: 'Ambulances', rescue_team: 'Rescue Teams',
  food_kit_batch: 'Food Kit Batches', water_tanker: 'Water Tankers',
}

function Bar({ segment, total, color }) {
  const pct = total > 0 ? (segment / total) * 100 : 0
  return <div className="h-1.5 rounded-full" style={{ width: `${pct}%`, background: color }} />
}

export default function ResourceOverviewPanel({ resources }) {
  return (
    <div className="panel p-4">
      <div className="font-display text-sm font-semibold mb-3">RESOURCE OVERVIEW</div>
      <div className="grid grid-cols-2 gap-3">
        {Object.entries(resources).map(([type, r]) => (
          <div key={type} className="bg-bgmain border border-panelborder rounded-lg p-3">
            <div className="text-2xl font-display font-bold">{r.total}</div>
            <div className="text-[11px] text-gray-400 mb-2">{LABELS[type] || type}</div>
            <div className="flex h-1.5 rounded-full overflow-hidden bg-gray-800 gap-0.5">
              <Bar segment={r.deployed} total={r.total} color="#F59E0B" />
              <Bar segment={r.available} total={r.total} color="#22C55E" />
              <Bar segment={r.unavailable} total={r.total} color="#EF4444" />
            </div>
            <div className="flex gap-2 text-[10px] text-gray-500 mt-1">
              <span>{r.deployed} deployed</span>
              <span>{r.available} free</span>
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}
