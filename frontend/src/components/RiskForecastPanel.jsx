import { useEffect, useState } from 'react'
import { AreaChart, Area, XAxis, YAxis, Tooltip, ResponsiveContainer } from 'recharts'
import { api } from '../api'

export default function RiskForecastPanel({ refreshKey }) {
  const [data, setData] = useState([])

  useEffect(() => {
    api.getRiskForecast().then(d => setData(d.forecast)).catch(() => {})
  }, [refreshKey])

  return (
    <div className="panel p-4">
      <div className="font-display text-sm font-semibold mb-2">RISK FORECAST</div>
      <div className="text-[11px] text-gray-500 mb-2">Projected next 6 hours (simplified model, not weather-driven)</div>
      <div style={{ width: '100%', height: 160 }}>
        <ResponsiveContainer>
          <AreaChart data={data.map(d => ({ hour: `${d.hour}h`, risk: Math.round(d.risk * 100) }))}>
            <defs>
              <linearGradient id="riskFill" x1="0" y1="0" x2="0" y2="1">
                <stop offset="0%" stopColor="#EF4444" stopOpacity={0.5} />
                <stop offset="100%" stopColor="#EF4444" stopOpacity={0} />
              </linearGradient>
            </defs>
            <XAxis dataKey="hour" tick={{ fill: '#94A3B8', fontSize: 11 }} axisLine={{ stroke: '#334155' }} tickLine={false} />
            <YAxis hide domain={[0, 100]} />
            <Tooltip contentStyle={{ background: '#111827', border: '1px solid rgba(34,211,238,0.2)', fontSize: 12 }} />
            <Area type="monotone" dataKey="risk" stroke="#EF4444" fill="url(#riskFill)" strokeWidth={2} />
          </AreaChart>
        </ResponsiveContainer>
      </div>
    </div>
  )
}
