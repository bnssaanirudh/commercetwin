import React from 'react';

const Payments: React.FC = () => {
  // In a real app, we'd fetch this from the backend `/api/v1/payments` endpoint
  // For the UI shell we'll just render an empty state for now until the backend endpoint is wired up.
  const payments: any[] = [];

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
            {payments.length === 0 ? (
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
