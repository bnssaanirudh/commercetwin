const API_BASE = `${import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'}/api/v1`;

export const fetchMetrics = async () => {
  try {
    const res = await fetch(`${API_BASE}/metrics`);
    if (!res.ok) throw new Error('Failed to fetch metrics');
    return await res.json();
  } catch (err) {
    console.error(err);
    throw new Error('Metrics API unavailable');
  }
};

export const fetchExperiments = async () => {
  try {
    const res = await fetch(`${API_BASE}/experiments`);
    if (!res.ok) throw new Error('Failed to fetch experiments');
    return await res.json();
  } catch (err) {
    console.error(err);
    throw err;
  }
};

export const fetchTraces = async () => {
  try {
    const res = await fetch(`${API_BASE}/traces`);
    if (!res.ok) throw new Error('Failed to fetch traces');
    return await res.json();
  } catch (err) {
    console.error(err);
    throw err;
  }
};

export const fetchRepairs = async () => {
  try {
    const res = await fetch(`${API_BASE}/repairs`);
    if (!res.ok) throw new Error('Failed to fetch repairs');
    return await res.json();
  } catch (err) {
    console.error(err);
    throw err;
  }
};

export const triggerReplay = async (repairId: string) => {
  const res = await fetch(`${API_BASE}/replays`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ repair_id: repairId }),
  });
  if (!res.ok) throw new Error('Failed to trigger replay');
  return await res.json();
};

export const createExperiment = async (payload: Record<string, unknown>) => {
  const res = await fetch(`${API_BASE}/experiments`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  });
  if (!res.ok) throw new Error('Failed to create experiment');
  return await res.json();
};

export const runExperiment = async (id: string, payload: Record<string, unknown>) => {
  const res = await fetch(`${API_BASE}/experiments/${id}/run`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  });
  if (!res.ok) throw new Error('Failed to run experiment');
  return await res.json();
};

export const injectChaos = async (profileId: string) => {
  const res = await fetch(`${API_BASE}/chaos/inject?profile_id=${profileId}`, { method: 'POST' });
  return await res.json();
};
