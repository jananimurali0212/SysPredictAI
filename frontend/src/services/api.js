/**
 * Centralized API service for communicating with the SysPredictAI FastAPI backend.
 */

const BASE_URL = import.meta.env.VITE_API_URL || '';

async function fetchJSON(endpoint, options = {}) {
  const url = `${BASE_URL}${endpoint}`;
  try {
    const response = await fetch(url, {
      headers: {
        'Accept': 'application/json',
        'Content-Type': 'application/json',
        ...options.headers,
      },
      ...options,
    });

    if (!response.ok) {
      const errorBody = await response.text();
      let errorMsg = `HTTP ${response.status}: ${response.statusText}`;
      try {
        const parsed = JSON.parse(errorBody);
        errorMsg = parsed.detail || parsed.message || errorMsg;
      } catch {
        // use default errorMsg
      }
      throw new Error(errorMsg);
    }

    return await response.json();
  } catch (err) {
    console.error(`API Error on ${endpoint}:`, err);
    throw err;
  }
}

export const api = {
  // Day 1 Core Monitoring
  getHealth: () => fetchJSON('/api/health'),
  getCurrentMetrics: () => fetchJSON('/api/metrics/current'),
  getHistory: (limit = 60, startTime = null, endTime = null) => {
    const params = new URLSearchParams({ limit: String(limit) });
    if (startTime) params.append('start_time', startTime);
    if (endTime) params.append('end_time', endTime);
    return fetchJSON(`/api/metrics/history?${params.toString()}`);
  },
  getProcesses: (limit = 25, sortBy = 'cpu') => {
    return fetchJSON(`/api/processes?limit=${limit}&sort_by=${sortBy}`);
  },
  getSystemInfo: () => fetchJSON('/api/system/info'),

  // Day 2 Predictive Analytics & Anomalies
  getCPUPrediction: (horizons = '60,300,900') => {
    return fetchJSON(`/api/predictions/cpu?horizons=${horizons}`);
  },
  getMemoryPrediction: (horizons = '60,300,900') => {
    return fetchJSON(`/api/predictions/memory?horizons=${horizons}`);
  },
  getPredictionSummary: () => fetchJSON('/api/predictions/summary'),
  getAnomalies: () => fetchJSON('/api/anomalies'),
  getRisk: () => fetchJSON('/api/risk'),

  // Day 3 Gemini AI Insights
  getAISummary: () => fetchJSON('/api/insights/summary'),
  queryAI: (question) => {
    return fetchJSON('/api/insights/query', {
      method: 'POST',
      body: JSON.stringify({ question }),
    });
  },
};
