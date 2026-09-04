import React, { useEffect, useState } from 'react';
import { fetchRepairs } from '../api/client';

const ChaosLab: React.FC = () => {
  const [repairs, setRepairs] = useState<any[]>([]);

  useEffect(() => {
    fetchRepairs().then(data => setRepairs(data.items || []));
  }, []);

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
            {repairs.length === 0 ? (
              <tr>
                <td colSpan={5} style={{ textAlign: 'center', opacity: 0.5 }}>No repairs generated</td>
              </tr>
            ) : (
              repairs.map((r: any) => (
                <tr key={r.repair_id}>
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
                    <button className="btn btn-secondary" style={{ padding: '0.2rem 0.5rem', fontSize: '0.8em' }}>Replay Cohort</button>
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
};

export default ChaosLab;
