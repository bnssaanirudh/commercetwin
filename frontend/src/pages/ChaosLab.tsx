import React, { useEffect, useState } from 'react';
import { fetchRepairs } from '../api/client';

const API_BASE = 'http://localhost:8000/api/v1';

const ChaosLab: React.FC = () => {
  const [repairs, setRepairs] = useState<any[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [expandedId, setExpandedId] = useState<string | null>(null);
  const [replaying, setReplaying] = useState<Record<string, boolean>>({});

  useEffect(() => {
    fetchRepairs()
      .then(data => setRepairs(data.items || []))
      .catch(err => setError(err.message));
  }, []);

  const handleReplay = async (e: React.MouseEvent, repairId: string) => {
    e.stopPropagation();
    setReplaying(prev => ({ ...prev, [repairId]: true }));
    try {
      const res = await fetch(`${API_BASE}/replay/cohort?cohort_id=default_cohort&repair_id=${repairId}`, { method: 'POST' });
      if (!res.ok) throw new Error('Replay failed');
      // Ideally we would poll or subscribe for updates here.
      alert('Replay job started successfully');
    } catch (err: any) {
      alert(`Error starting replay: ${err.message}`);
    } finally {
      setReplaying(prev => ({ ...prev, [repairId]: false }));
    }
  };

  return (
    <div>
      <div className="page-header">
        <h2 className="page-title">Repair & Replay</h2>
        <p className="page-subtitle">Analyze Causal Failures and Test Patch Generation</p>
      </div>
      <div className="card">
        <table className="table-container">
          <thead>
            <tr>
              <th>Failure Target</th>
              <th>Synthesized Patch</th>
              <th>Guardrail Status</th>
              <th>Replay Outcome</th>
              <th>Action</th>
            </tr>
          </thead>
          <tbody>
            {error && (
              <tr>
                <td colSpan={5} style={{ textAlign: 'center', color: 'var(--accent-red)' }}>Error: {error}</td>
              </tr>
            )}
            {!error && repairs.length === 0 ? (
              <tr>
                <td colSpan={5} style={{ textAlign: 'center', opacity: 0.5 }}>No repairs generated</td>
              </tr>
            ) : (
              repairs.map((r: any) => (
                <React.Fragment key={r.repair_id}>
                  <tr 
                    style={{ cursor: 'pointer', backgroundColor: expandedId === r.repair_id ? 'rgba(255, 255, 255, 0.05)' : 'transparent' }}
                    onClick={() => setExpandedId(expandedId === r.repair_id ? null : r.repair_id)}
                  >
                    <td style={{ fontFamily: 'var(--font-mono)' }}>{r.target_sku || 'Unknown'}</td>
                    <td><pre style={{ margin: 0, fontSize: '0.8em', color: 'var(--accent-cyan)' }}>{JSON.stringify(r.patch, null, 2)}</pre></td>
                    <td>
                      <span className={`badge ${r.guardrail_passed ? 'badge-success' : 'badge-error'}`}>
                        {r.guardrail_passed ? 'VERIFIED' : 'BLOCKED'}
                      </span>
                    </td>
                    <td>
                      {r.replay_status === 'SUCCESS' ? (
                        <span style={{ color: 'var(--accent-green)' }}>READY_FOR_PAYMENT</span>
                      ) : (
                        <span style={{ color: 'var(--accent-orange)' }}>{r.replay_status}</span>
                      )}
                    </td>
                    <td>
                      <button 
                        className="btn btn-secondary" 
                        style={{ padding: '0.2rem 0.5rem', fontSize: '0.8em' }}
                        onClick={(e) => handleReplay(e, r.repair_id)}
                        disabled={replaying[r.repair_id]}
                      >
                        {replaying[r.repair_id] ? 'Starting...' : 'Replay Cohort'}
                      </button>
                    </td>
                  </tr>
                  {expandedId === r.repair_id && (
                    <tr style={{ backgroundColor: 'rgba(0,0,0,0.2)' }}>
                      <td colSpan={5} style={{ padding: '1rem' }}>
                        <div style={{ marginBottom: '1rem' }}>
                          <strong>Deep Dive Details:</strong>
                        </div>
                        <div className="grid-2" style={{ gap: '1rem', fontSize: '0.9em' }}>
                          <div>
                            <div><strong>Confidence:</strong> {r.confidence ?? 'N/A'}%</div>
                            <div><strong>Estimated Impact:</strong> ₹{((r.estimated_impact_paise || 0) / 100).toLocaleString()}</div>
                            <div><strong>Estimated Repair Cost:</strong> ₹{((r.estimated_repair_cost_paise || 0) / 100).toLocaleString()}</div>
                            <div style={{ marginTop: '0.5rem' }}><strong>Safety Notes:</strong><br/>{r.safety_notes || 'None'}</div>
                          </div>
                          <div>
                            <strong>Full JSON Patch:</strong>
                            <pre style={{ background: '#111', padding: '0.5rem', borderRadius: '4px', overflowX: 'auto', marginTop: '0.5rem' }}>
                              {JSON.stringify(r.proposed_patch, null, 2)}
                            </pre>
                          </div>
                        </div>
                      </td>
                    </tr>
                  )}
                </React.Fragment>
              ))
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
};

export default ChaosLab;
