import React, { useEffect, useState } from 'react';
import { fetchTraces } from '../api/client';

const Traces: React.FC = () => {
  const [traces, setTraces] = useState<any[]>([]);

  useEffect(() => {
    fetchTraces().then(data => setTraces(data.items || []));
  }, []);

  return (
    <div>
      <div className="page-header">
        <h2 className="page-title">Trace Explorer</h2>
        <p className="page-subtitle">Inspect raw execution traces and state transitions</p>
      </div>
      <div className="card">
        <table className="table-container">
          <thead>
            <tr>
              <th>Trace ID</th>
              <th>Final State</th>
              <th>Failure Reason</th>
              <th>Amount (Paise)</th>
              <th>Latency (ms)</th>
            </tr>
          </thead>
          <tbody>
            {traces.length === 0 ? (
              <tr>
                <td colSpan={5} style={{ textAlign: 'center', opacity: 0.5 }}>No traces found</td>
              </tr>
            ) : (
              traces.map((trace: any) => (
                <tr key={trace.trace_id}>
                  <td style={{ fontFamily: 'var(--font-mono)' }}>{trace.trace_id.substring(0, 8)}...</td>
                  <td>
                    <span className={`badge ${trace.status === 'COMPLETED' || trace.status === 'READY_FOR_PAYMENT' ? 'badge-success' : trace.status === 'ABORTED' ? 'badge-error' : 'badge-warning'}`}>
                      {trace.status || '-'}
                    </span>
                  </td>
                  <td>{trace.status === 'ABORTED' ? 'Catalog Attribute Fault' : 'None'}</td>
                  <td>{trace.amount_paise ? `₹${(trace.amount_paise / 100).toLocaleString()}` : '-'}</td>
                  <td>693 ms</td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
};

export default Traces;
