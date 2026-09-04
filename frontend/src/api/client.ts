const API_BASE = 'http://localhost:8000/api/v1';

export const fetchMetrics = async () => {
  try {
    const res = await fetch(`${API_BASE}/metrics`);
    if (!res.ok) throw new Error('Failed to fetch metrics');
    return await res.json();
  } catch (err) {
    console.error(err);
    throw new Error("Metrics API unavailable");
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
