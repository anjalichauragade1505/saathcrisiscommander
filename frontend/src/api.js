const BASE_URL = import.meta.env.VITE_API_URL || "http://localhost:8000"

async function request(path, options = {}) {
  const res = await fetch(`${BASE_URL}${path}`, {
    headers: { "Content-Type": "application/json" },
    ...options,
  })
  if (!res.ok) {
    const err = new Error(`Request failed: ${res.status}`)
    err.status = res.status
    try { err.body = await res.json() } catch (_) {}
    throw err
  }
  return res.json()
}

export const api = {
  getState: () => request("/api/simulation/state"),
  resetSimulation: () => request("/api/simulation/reset", { method: "POST" }),
  injectEvent: (payload) => request("/api/simulation/inject-event", {
    method: "POST", body: JSON.stringify(payload),
  }),
  approveAction: (id) => request(`/api/actions/${id}/approve`, { method: "POST" }),
  rejectAction: (id) => request(`/api/actions/${id}/reject`, { method: "POST" }),
  getAgentLog: () => request("/api/agent-log"),
  getNotifications: (role) => request(`/api/notifications?role=${role}`),
  respondNotification: (id, approve) => request(`/api/notifications/${id}/respond`, {
    method: "POST", body: JSON.stringify({ approve }),
  }),
  getRiskForecast: () => request("/api/risk-forecast"),
  fieldReport: (payload) => request("/api/field/report", {
    method: "POST", body: JSON.stringify(payload),
  }),
  fieldSync: (payload) => request("/api/field/sync", {
    method: "POST", body: JSON.stringify(payload),
  }),
  getFieldTasks: (zoneId) => request(`/api/field/tasks?zone_id=${zoneId}`),
  getZones: () => request("/api/zones"),
  getRoads: () => request("/api/roads"),
}
