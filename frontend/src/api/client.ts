const API_BASE = 'http://localhost:8000/api/v1';

export const fetchMetrics = async () => {
  try {
    const res = await fetch(`${API_BASE}/metrics`);
    if (!res.ok) throw new Error('Failed to fetch metrics');
    return await res.json();
  } catch (err) {
    console.error(err);
    // Mock fallback if backend is down
    return {
      RTY: 0.85,
      II: 0.92,
      ARC_paise_SYNTHETIC: 1250000,
      ARL_paise_SYNTHETIC: 150000,
      CVR: 0.03,
      RVR: 0.8,
      FRR: 0.4,
      latency: { median_ms: 120, p95_ms: 350 },
      llm: { total_calls: 1450 }
    };
  }
};

export const fetchExperiments = async () => {
  try {
    const res = await fetch(`${API_BASE}/experiments`);
    if (!res.ok) throw new Error('Failed to fetch experiments');
    return await res.json();
  } catch (err) {
    return { items: [], total: 0 };
  }
};

export const fetchTraces = async () => {
  try {
    const res = await fetch(`${API_BASE}/traces`);
    if (!res.ok) throw new Error('Failed to fetch traces');
    return await res.json();
  } catch (err) {
    return { items: [], total: 0 };
  }
};

export const fetchRepairs = async () => {
  try {
    const res = await fetch(`${API_BASE}/repairs`);
    if (!res.ok) throw new Error('Failed to fetch repairs');
    return await res.json();
  } catch (err) {
    return { items: [], total: 0 };
  }
};

export const runExperiment = async (id: string) => {
  const res = await fetch(`${API_BASE}/experiments/${id}/run`, { method: 'POST' });
  return await res.json();
};

export const injectChaos = async (profileId: string) => {
  const res = await fetch(`${API_BASE}/chaos/inject?profile_id=${profileId}`, { method: 'POST' });
  return await res.json();
};
