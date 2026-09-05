import React, { useEffect, useState } from 'react';
import { fetchMetrics } from '../api/client';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';


const Overview: React.FC = () => {
  const [metrics, setMetrics] = useState<any>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetchMetrics()
      .then(setMetrics)
      .catch(err => setError(err.message));
  }, []);

  if (error) return (
    <div style={{ padding: '2rem', textAlign: 'center' }}>
      <h3 style={{ color: 'var(--accent-red)' }}>Backend unavailable</h3>
      <p style={{ color: '#888' }}>{error}</p>
    </div>
  );
  if (!metrics || Object.keys(metrics).length === 0 || metrics.Total_Scenarios === 0 || metrics.Total_Eligible === 0) return (
    <div style={{ padding: '2rem', textAlign: 'center' }}>
      <h3 style={{ color: 'var(--accent-orange)' }}>No data</h3>
      <p style={{ color: '#888' }}>Run an experiment to generate metrics.</p>
    </div>
  );

  const chartData = [
    { name: 'Current', AVaR: (metrics.Agentic_Value_at_Risk_Paise || 0) / 100, REV: (metrics.Recovered_Eligible_Value_Paise || 0) / 100 }
  ];

  return (
    <div>
      <div className="page-header">
        <h2 className="page-title">
          Dashboard Overview
          <span className="badge badge-info" style={{ marginLeft: '12px', fontSize: '0.5em' }}>Synthetic Benchmark</span>
          <span className="badge badge-warning" style={{ marginLeft: '6px', fontSize: '0.5em' }}>Razorpay Test Mode</span>
        </h2>
        <p className="page-subtitle">Real-time metrics for CommerceTwin</p>
      </div>
      
      <div className="grid-4" style={{ marginBottom: '2rem' }}>
        <div className="card">
          <div className="card-title">Robust Transaction Yield (RTY)</div>
          <div className="card-value">{((metrics.Robust_Transaction_Yield || 0) * 100).toFixed(1)}%</div>
        </div>
        <div className="card">
          <div className="card-title">Intent Integrity (II)</div>
          <div className="card-value">{((metrics.Intent_Integrity || 0) * 100).toFixed(1)}%</div>
        </div>
        <div className="card">
          <div className="card-title">AVaR (Risk)</div>
          <div className="card-value">₹{((metrics.Agentic_Value_at_Risk_Paise || 0) / 100).toLocaleString()}</div>
        </div>
        <div className="card">
          <div className="card-title">REV (Recovered)</div>
          <div className="card-value">₹{((metrics.Recovered_Eligible_Value_Paise || 0) / 100).toLocaleString()}</div>
        </div>
      </div>

      <div className="grid-2">
        <div className="card">
          <div className="card-title">Risk vs Recovered Value</div>
          <div style={{ width: '100%', height: 300 }}>
            <ResponsiveContainer>
              <LineChart data={chartData}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="name" />
                <YAxis />
                <Tooltip />
                <Line type="monotone" dataKey="AVaR" stroke="#ef4444" />
                <Line type="monotone" dataKey="REV" stroke="#10b981" />
              </LineChart>
            </ResponsiveContainer>
          </div>
        </div>
        
        <div className="card">
          <div className="card-title">System Health</div>
          <table className="table-container">
            <tbody>
              <tr>
                <td>Constraint Violation Rate (CVR)</td>
                <td><span className="badge badge-success">{((metrics.Constraint_Violation_Rate || 0) * 100).toFixed(1)}%</span></td>
              </tr>
              <tr>
                <td>Failure Recovery Rate (FRR)</td>
                <td><span className="badge badge-info">{((metrics.Failure_Recovery_Rate || 0) * 100).toFixed(1)}%</span></td>
              </tr>
              <tr>
                <td>Median Latency</td>
                <td><span className="badge badge-warning">{(metrics.Latency_Median_ms || 0).toFixed(1)} ms</span></td>
              </tr>
              <tr>
                <td>Total LLM Calls</td>
                <td>{metrics.Total_LLM_Calls ?? 'N/A'}</td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};

export default Overview;
