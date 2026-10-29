const API_BASE = (import.meta.env.VITE_API_BASE_URL || '').replace(/\/$/, '')

export async function apiRequest(path, options = {}) {
  const response = await fetch(`${API_BASE}${path}`, {
    headers: { 'Content-Type': 'application/json', ...(options.headers || {}) },
    ...options,
  })
  const text = await response.text()
  let data = null
  try { data = text ? JSON.parse(text) : null } catch { data = { detail: text } }
  if (!response.ok) {
    const message = data?.detail || `Request failed (${response.status})`
    throw new Error(typeof message === 'string' ? message : JSON.stringify(message))
  }
  return data
}

export const api = {
  health: () => apiRequest('/api/health'),
  summary: () => apiRequest('/api/reports/summary'),
  experiments: (page = 1) => apiRequest(`/api/experiments?page=${page}&page_size=20`),
  tradeProtection: (payload) => apiRequest('/api/trade-protection/simulate', { method: 'POST', body: JSON.stringify(payload) }),
  protectionScenarios: () => apiRequest('/api/trade-protection/scenarios'),
  sampleData: () => apiRequest('/api/decentralization/sample-data'),
  decentralization: (payload) => apiRequest('/api/decentralization/analyze', { method: 'POST', body: JSON.stringify(payload) }),
  pbs: (payload) => apiRequest('/api/decentralization/pbs-simulate', { method: 'POST', body: JSON.stringify(payload) }),
  outage: (payload) => apiRequest('/api/decentralization/outage-simulate', { method: 'POST', body: JSON.stringify(payload) }),
  epbsCompare: (payload) => apiRequest('/api/decentralization/epbs-compare', { method: 'POST', body: JSON.stringify(payload) }),
  efficiency: (payload) => apiRequest('/api/efficiency/simulate', { method: 'POST', body: JSON.stringify(payload) }),
  reorgSmoothing: (payload) => apiRequest('/api/efficiency/reorg-smoothing-simulate', { method: 'POST', body: JSON.stringify(payload) }),
  taxonomy: () => apiRequest('/api/efficiency/taxonomy'),
}
