import { useState } from 'react'
import { api } from '../api'

const PRIORITY_COLOR = { HIGH: '#EF4444', MEDIUM: '#F59E0B', LOW: '#22C55E' }

export default function PendingApprovalsPanel({ pendingActions, onChanged }) {
  const [busyId, setBusyId] = useState(null)
  const [lastResult, setLastResult] = useState(null)

  async function handle(id, action) {
    setBusyId(id)
    setLastResult(null)
    try {
      const res = action === 'approve' ? await api.approveAction(id) : await api.rejectAction(id)
      if (res.inference) {
        setLastResult({
          zone: res.action.target_zone_name,
          need: res.inference.notification.need_type,
          qty: res.inference.notification.estimated_quantity,
          confidence: res.inference.notification.confidence,
          fallback: res.inference.decision.output.was_fallback,
        })
      }
      onChanged()
    } catch (e) {
      console.error(e)
    } finally {
      setBusyId(null)
    }
  }

  return (
    <div className="panel p-4">
      <div className="flex items-center justify-between mb-3">
        <span className="font-display text-sm font-semibold">PENDING APPROVAL</span>
        {pendingActions.length > 0 && (
          <span className="text-[10px] bg-critical/20 text-critical rounded-full px-2 py-0.5">{pendingActions.length}</span>
        )}
      </div>

      {lastResult && (
        <div className="mb-3 text-xs bg-violet/10 border border-violet/30 rounded-lg p-2">
          <div className="text-violet font-medium mb-1">Inference Agent {lastResult.fallback ? '(fallback)' : '(AI)'}</div>
          <div className="text-gray-300">
            Predicted <span className="text-gray-100">{lastResult.need.replace('_', ' ')}</span> shortage in {lastResult.zone}
            {' '}(~{lastResult.qty} units, {Math.round(lastResult.confidence * 100)}% confidence) → District Food Officer notified.
          </div>
        </div>
      )}

      <div className="space-y-2 max-h-72 overflow-y-auto pr-1">
        {pendingActions.length === 0 && <div className="text-xs text-gray-500">No pending actions.</div>}
        {pendingActions.map(a => (
          <div key={a.id} className="bg-bgmain border border-panelborder rounded-lg p-2.5 text-xs">
            <div className="flex justify-between items-start">
              <div>
                <div className="text-gray-100 font-medium">
                  Deploy {a.quantity}x {a.resource_type.replace('_', ' ')} → {a.target_zone_name}
                </div>
                <div className="mt-0.5" style={{ color: PRIORITY_COLOR[a.priority] }}>Priority: {a.priority}</div>
                {a.is_evacuation && <div className="text-cyan mt-0.5">Evacuation-scale action</div>}
                {!a.route_valid && <div className="text-critical mt-0.5">⚠ No valid route currently</div>}
                {a.eta_minutes && <div className="text-gray-500 mt-0.5">ETA ~{a.eta_minutes} min</div>}
              </div>
              <div className="flex gap-1.5 shrink-0">
                <button disabled={busyId === a.id} onClick={() => handle(a.id, 'reject')}
                  className="px-2 py-1 rounded bg-critical/15 text-critical border border-critical/30 hover:bg-critical/25 disabled:opacity-50">
                  Reject
                </button>
                <button disabled={busyId === a.id} onClick={() => handle(a.id, 'approve')}
                  className="px-2 py-1 rounded bg-safe/15 text-safe border border-safe/30 hover:bg-safe/25 disabled:opacity-50">
                  Approve
                </button>
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}
