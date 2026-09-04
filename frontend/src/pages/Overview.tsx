import React, { useEffect, useState } from 'react';
import { fetchMetrics } from '../api/client';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';

const data = [
  { name: 'Mon', AVaR: 4000, REV: 2400 },
  { name: 'Tue', AVaR: 3000, REV: 1398 },
  { name: 'Wed', AVaR: 2000, REV: 9800 },
  { name: 'Thu', AVaR: 2780, REV: 3908 },
  { name: 'Fri', AVaR: 1890, REV: 4800 },
  { name: 'Sat', AVaR: 2390, REV: 3800 },
  { name: 'Sun', AVaR: 3490, REV: 4300 },
];

const Overview: React.FC = () => {
  const [metrics, setMetrics] = useState<any>(null);

  useEffect(() => {
    fetchMetrics().then(setMetrics);
  }, []);

  if (!metrics) return <div>Loading...</div>;

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
          <div className="card-value">{(metrics.RTY * 100).toFixed(1)}%</div>
        </div>
        <div className="card">
          <div className="card-title">Intent Integrity (II)</div>
          <div className="card-value">{(metrics.Intent_Integrity * 100 || 0).toFixed(1)}%</div>
        </div>
        <div className="card">
          <div className="card-title">AVaR (Risk)</div>
          <div className="card-value">₹{((metrics.AVaR || 0) / 100).toLocaleString()}</div>
        </div>
        <div className="card">
          <div className="card-title">REV (Recovered)</div>
          <div className="card-value">₹{((metrics.REV || 0) / 100).toLocaleString()}</div>
        </div>
      </div>

      <div className="grid-2">
        <div className="card">
          <div className="card-title">Risk vs Recovered Value</div>
          <div style={{ width: '100%', height: 300 }}>
            <ResponsiveContainer>
              <LineChart data={data}>
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
                <td><span className="badge badge-success">{(metrics.CVR * 100).toFixed(1)}%</span></td>
              </tr>
              <tr>
                <td>Failure Recovery Rate (FRR)</td>
                <td><span className="badge badge-info">{(metrics.FRR * 100).toFixed(1)}%</span></td>
              </tr>
              <tr>
                <td>Median Latency</td>
                <td><span className="badge badge-warning">{metrics.latency?.median_ms ?? 120} ms</span></td>
              </tr>
              <tr>
                <td>Total LLM Calls</td>
                <td>{metrics.llm?.total_calls ?? 42}</td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};

export default Overview;
