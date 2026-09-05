import React, { useEffect, useState } from 'react';

const API_BASE = `${import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'}/api/v1`;

const RevenueLeak: React.FC = () => {
  const [failures, setFailures] = useState<any[]>([]);

  useEffect(() => {
    fetch(`${API_BASE}/failures`)
      .then(r => r.json())
      .then(data => setFailures(data.items || []))
      .catch(console.error);
  }, []);

  return (
    <div>
      <div className="page-header">
        <h2 className="page-title">RevenueLeak</h2>
        <p className="page-subtitle">Analyze conversion drops and causal clusters</p>
      </div>
      <div className="card">
        {failures.length === 0 ? (
          <p style={{ opacity: 0.5, textAlign: 'center' }}>No revenue leak signatures found.</p>
        ) : (
          <table className="table-container">
            <thead>
              <tr>
                <th>Failure ID</th>
                <th>Reason</th>
                <th>Status</th>
              </tr>
            </thead>
            <tbody>
              {failures.map((f: any, i: number) => (
                <tr key={i}>
                  <td style={{ fontFamily: 'var(--font-mono)' }}>{f.failure_id}</td>
                  <td>{f.reason}</td>
                  <td><span className="badge badge-warning">Active</span></td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </div>
  );
};

export default RevenueLeak;
