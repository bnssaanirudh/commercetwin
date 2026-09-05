import React, { useEffect, useState } from 'react';

const Payments: React.FC = () => {
  const [payments, setPayments] = useState<any[]>([]);

  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetch('http://localhost:8000/api/v1/payments')
      .then(res => {
        if (!res.ok) throw new Error('Failed to fetch payments');
        return res.json();
      })
      .then(data => setPayments(data.items || []))
      .catch(err => setError(err.message));
  }, []);

  return (
    <div>
      <div className="page-header">
        <h2 className="page-title">Payment Safety</h2>
        <p className="page-subtitle">Verify Idempotent Payment Operations and Webhook Reconciliation</p>
      </div>
      <div className="card">
        <table className="table-container">
          <thead>
            <tr>
              <th>Trace ID</th>
              <th>Operation ID</th>
              <th>Razorpay Order</th>
              <th>Amount</th>
              <th>State</th>
              <th>Reconciliation</th>
            </tr>
          </thead>
          <tbody>
            {error && (
              <tr>
                <td colSpan={6} style={{ textAlign: 'center', color: 'var(--accent-red)' }}>Error: {error}</td>
              </tr>
            )}
            {!error && payments.length === 0 ? (
              <tr>
                <td colSpan={6} style={{ textAlign: 'center', opacity: 0.5 }}>No payments processed</td>
              </tr>
            ) : (
              payments.map((p: any) => (
                <tr key={p.operation_id}>
                  <td style={{ fontFamily: 'var(--font-mono)' }}>{p.trace_id.substring(0, 8)}</td>
                  <td style={{ fontFamily: 'var(--font-mono)' }}>{p.operation_id.substring(0, 8)}</td>
                  <td>{p.razorpay_order_id || '-'}</td>
                  <td>{p.amount_paise ? `₹${(p.amount_paise / 100).toLocaleString()}` : '-'}</td>
                  <td>
                    <span className={`badge ${p.state === 'COMPLETED' ? 'badge-success' : 'badge-warning'}`}>
                      {p.state}
                    </span>
                  </td>
                  <td>
                    {p.reconciled ? (
                      <span style={{ color: 'var(--accent-green)' }}>MATCHED</span>
                    ) : (
                      <span style={{ color: 'var(--accent-orange)' }}>PENDING</span>
                    )}
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>
      
      <div style={{ marginTop: '2rem', display: 'flex', gap: '1rem' }}>
        <button className="btn btn-primary" disabled>
          [ TRIGGER TEST PAYMENT ]
        </button>
      </div>
    </div>
  );
};

export default Payments;
