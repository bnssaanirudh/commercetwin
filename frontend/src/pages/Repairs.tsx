import React, { useEffect, useState } from 'react';
import { fetchRepairs, triggerReplay } from '../api/client';

interface RepairItem {
  repair_id: string;
  failure_id: string;
  snapshot_id: string | null;
  repair_type: string;
  status: string;
  confidence: number | null;
  target_sku: string | null;
  operations: Array<{ op: string; path: string; value: string; type: string }>;
  estimated_impact_paise: number;
  created_at: string | null;
}

interface ReplayResult {
  repair_id: string;
  replay_id: string;
  status: string;
  success: boolean;
}

const Repairs: React.FC = () => {
  const [repairs, setRepairs] = useState<RepairItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [replaying, setReplaying] = useState<Record<string, boolean>>({});
  const [replayResults, setReplayResults] = useState<Record<string, ReplayResult>>({});

  useEffect(() => {
    fetchRepairs()
      .then((data) => setRepairs(data.items || []))
      .catch((err: Error) => setError(err.message))
      .finally(() => setLoading(false));
  }, []);

  const handleReplay = async (repairId: string) => {
    setReplaying((prev) => ({ ...prev, [repairId]: true }));
    try {
      const result = await triggerReplay(repairId);
      setReplayResults((prev) => ({ ...prev, [repairId]: result }));
      // Refresh repairs list to show updated status
      fetchRepairs().then((data) => setRepairs(data.items || [])).catch(() => null);
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : 'Replay failed';
      setReplayResults((prev) => ({
        ...prev,
        [repairId]: { repair_id: repairId, replay_id: '', status: 'error', success: false, error: message } as ReplayResult,
      }));
    } finally {
      setReplaying((prev) => ({ ...prev, [repairId]: false }));
    }
  };

  const formatPaise = (paise: number) =>
    paise > 0 ? `₹${(paise / 100).toLocaleString('en-IN', { maximumFractionDigits: 2 })}` : '-';

  const statusBadge = (status: string) => {
    const cls =
      status === 'verified'
        ? 'badge badge-success'
        : status === 'failed'
        ? 'badge badge-error'
        : 'badge badge-warning';
    return <span className={cls}>{status.toUpperCase()}</span>;
  };

  return (
    <div>
      <div className="page-header">
        <h2 className="page-title">Repair Proposals</h2>
        <p className="page-subtitle">
          Evidence-backed patches generated from localised failure clusters — verify via sandbox
          replay
        </p>
      </div>

      {loading && (
        <div className="card" style={{ textAlign: 'center', opacity: 0.6 }}>
          Loading repairs…
        </div>
      )}

      {error && !loading && (
        <div className="card" style={{ color: 'var(--accent-red)' }}>
          Backend unavailable: {error}
        </div>
      )}

      {!loading && !error && repairs.length === 0 && (
        <div className="card" style={{ textAlign: 'center', opacity: 0.5 }}>
          No repair proposals yet — run an experiment with chaos injection to generate failures.
        </div>
      )}

      {!loading && !error && repairs.length > 0 && (
        <div className="card">
          <table className="table-container">
            <thead>
              <tr>
                <th>Repair ID</th>
                <th>Target SKU</th>
                <th>Patch Operations</th>
                <th>Confidence</th>
                <th>Est. Impact</th>
                <th>Status</th>
                <th>Replay</th>
              </tr>
            </thead>
            <tbody>
              {repairs.map((r) => {
                const rr = replayResults[r.repair_id];
                return (
                  <React.Fragment key={r.repair_id}>
                    <tr>
                      <td style={{ fontFamily: 'var(--font-mono)', fontSize: '0.8em' }}>
                        {r.repair_id.substring(0, 12)}…
                      </td>
                      <td style={{ fontFamily: 'var(--font-mono)' }}>{r.target_sku || '—'}</td>
                      <td>
                        {r.operations.length === 0 ? (
                          <span style={{ opacity: 0.4 }}>no-op</span>
                        ) : (
                          r.operations.map((op, idx) => (
                            <div key={idx} style={{ fontSize: '0.78em', fontFamily: 'var(--font-mono)' }}>
                              <span style={{ color: 'var(--accent-green)' }}>{op.op}</span>{' '}
                              <span style={{ color: 'var(--accent-blue)' }}>{op.path}</span>
                              {' = '}
                              <span style={{ color: 'var(--accent-orange)' }}>{op.value}</span>
                              <span style={{ opacity: 0.5 }}> ({op.type})</span>
                            </div>
                          ))
                        )}
                      </td>
                      <td>{r.confidence != null ? `${r.confidence}%` : '—'}</td>
                      <td>{formatPaise(r.estimated_impact_paise)}</td>
                      <td>{statusBadge(r.status)}</td>
                      <td>
                        {r.status === 'proposed' ? (
                          <button
                            id={`replay-btn-${r.repair_id}`}
                            className="btn btn-primary"
                            style={{ fontSize: '0.78em', padding: '4px 10px' }}
                            disabled={!!replaying[r.repair_id]}
                            onClick={() => handleReplay(r.repair_id)}
                          >
                            {replaying[r.repair_id] ? 'Running…' : '▶ Replay'}
                          </button>
                        ) : (
                          <span style={{ opacity: 0.4 }}>—</span>
                        )}
                      </td>
                    </tr>
                    {rr && (
                      <tr>
                        <td
                          colSpan={7}
                          style={{
                            background: rr.success
                              ? 'rgba(0,200,80,0.07)'
                              : 'rgba(220,50,50,0.07)',
                            padding: '8px 16px',
                            fontSize: '0.82em',
                          }}
                        >
                          <strong>Replay {rr.replay_id || rr.repair_id}: </strong>
                          {rr.success ? (
                            <span style={{ color: 'var(--accent-green)' }}>
                              ✓ VERIFIED — trace recovered to READY_FOR_PAYMENT
                            </span>
                          ) : (
                            <span style={{ color: 'var(--accent-red)' }}>
                              ✗ FAILED — repair did not resolve the failure
                            </span>
                          )}
                        </td>
                      </tr>
                    )}
                  </React.Fragment>
                );
              })}
            </tbody>
          </table>
        </div>
      )}

      <div style={{ marginTop: '1.5rem', opacity: 0.55, fontSize: '0.82em' }}>
        Repairs are sandbox-only. They are applied to a frozen ReplaySnapshot — never to live
        merchant data. Only a successful replay promotes a repair to{' '}
        <code>status=verified</code>.
      </div>
    </div>
  );
};

export default Repairs;
