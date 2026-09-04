import React, { useEffect, useState } from 'react';
import { fetchMetrics } from '../api/client';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';

const data = [
  { name: 'Mon', ARC: 4000, ARL: 2400 },
  { name: 'Tue', ARC: 3000, ARL: 1398 },
  { name: 'Wed', ARC: 2000, ARL: 9800 },
  { name: 'Thu', ARC: 2780, ARL: 3908 },
  { name: 'Fri', ARC: 1890, ARL: 4800 },
  { name: 'Sat', ARC: 2390, ARL: 3800 },
  { name: 'Sun', ARC: 3490, ARL: 4300 },
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
        <h2 className="page-title">Dashboard Overview</h2>
        <p className="page-subtitle">Real-time metrics for CommerceTwin</p>
      </div>
      
      <div className="grid-4" style={{ marginBottom: '2rem' }}>
        <div className="card">
          <div className="card-title">Robust Transaction Yield (RTY)</div>
          <div className="card-value">{(metrics.RTY * 100).toFixed(1)}%</div>
        </div>
        <div className="card">
          <div className="card-title">Intent Integrity (II)</div>
          <div className="card-value">{(metrics.II * 100).toFixed(1)}%</div>
        </div>
        <div className="card">
          <div className="card-title">Synthetic ARC</div>
          <div className="card-value">₹{(metrics.ARC_paise_SYNTHETIC / 100).toLocaleString()}</div>
        </div>
        <div className="card">
          <div className="card-title">Synthetic ARL</div>
          <div className="card-value">₹{(metrics.ARL_paise_SYNTHETIC / 100).toLocaleString()}</div>
        </div>
      </div>

      <div className="grid-2">
        <div className="card">
          <div className="card-title">Value Capture vs Leak</div>
          <div style={{ width: '100%', height: 300 }}>
            <ResponsiveContainer>
              <LineChart data={data}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="name" />
                <YAxis />
                <Tooltip />
                <Line type="monotone" dataKey="ARC" stroke="#10b981" />
                <Line type="monotone" dataKey="ARL" stroke="#ef4444" />
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
