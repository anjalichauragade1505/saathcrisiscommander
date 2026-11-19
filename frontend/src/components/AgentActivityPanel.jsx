import { CheckCircle2, Loader2, CircleDashed, Bot } from 'lucide-react'

const LABELS = {
  situation_agent: 'Situation Agent',
  resource_agent: 'Resource Agent',
  routing_agent: 'Routing Agent',
  response_planner: 'Response Planner',
  inference_agent: 'Inference Agent (AI)',
}

export default function AgentActivityPanel({ activity }) {
  return (
    <div className="panel p-4">
      <div className="flex items-center gap-2 mb-3">
        <Bot size={15} className="text-violet" />
        <span className="font-display text-sm font-semibold text-violet">AI AGENT ACTIVITY</span>
      </div>
      <div className="space-y-2">
        {activity.map(a => {
          const label = LABELS[a.agent_name] || a.agent_name
          const isAI = a.agent_name === 'inference_agent'
          return (
            <div key={a.agent_name} className="flex items-start gap-2 text-xs">
              {a.has_run ? (
                <CheckCircle2 size={15} className="text-safe shrink-0 mt-0.5" />
              ) : (
                <CircleDashed size={15} className="text-gray-600 shrink-0 mt-0.5" />
              )}
              <div className="flex-1 min-w-0">
                <div className={`font-medium ${isAI ? 'text-violet' : 'text-gray-200'}`}>{label}</div>
                <div className="text-gray-500 truncate">
                  {a.has_run ? a.reasoning_summary : 'Waiting for event'}
                </div>
              </div>
            </div>
          )
        })}
      </div>
    </div>
  )
}
