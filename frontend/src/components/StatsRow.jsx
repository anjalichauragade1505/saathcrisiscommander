import { AlertTriangle, Users, Truck, Activity, Gauge } from 'lucide-react'

function StatCard({ icon: Icon, value, label, sub, color }) {
  return (
    <div className="panel px-4 py-3 flex-1 min-w-[150px]">
      <div className="flex items-center gap-2 mb-1">
        <Icon size={16} style={{ color }} />
        <span className="text-xl font-display font-bold">{value}</span>
      </div>
      <div className="text-xs text-gray-300">{label}</div>
      {sub && <div className="text-[11px] mt-0.5" style={{ color }}>{sub}</div>}
    </div>
  )
}

export default function StatsRow({ stats }) {
  if (!stats) return null
  return (
    <div className="flex flex-wrap gap-3 mb-4">
      <StatCard icon={AlertTriangle} value={stats.critical_zones} label="Critical Zones" sub="High Priority" color="#EF4444" />
      <StatCard icon={Users} value={stats.people_affected.toLocaleString()} label="People Affected" color="#F59E0B" />
      <StatCard icon={Truck} value={stats.resources_deployed} label="Resources Deployed" sub="Active Now" color="#22D3EE" />
      <StatCard icon={Activity} value={stats.ongoing_operations} label="Ongoing Operations" sub="In Progress" color="#22C55E" />
      <StatCard icon={Gauge} value={`${stats.response_score}/100`} label="Response Score" sub={stats.response_score >= 70 ? "Good Response" : "Needs Attention"} color="#8B5CF6" />
    </div>
  )
}
