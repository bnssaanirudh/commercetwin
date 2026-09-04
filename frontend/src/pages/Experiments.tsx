import React, { useEffect, useState } from 'react';
import { fetchExperiments } from '../api/client';

const Experiments: React.FC = () => {
  const [experiments, setExperiments] = useState<any[]>([]);

  useEffect(() => {
    fetchExperiments().then(data => setExperiments(data.items || []));
  }, []);

  return (
    <div>
      <div className="page-header">
        <h2 className="page-title">Experiments</h2>
        <p className="page-subtitle">Manage your experiment runs</p>
      </div>
      <div className="card">
        {experiments.length === 0 ? (
          <p style={{ opacity: 0.5, textAlign: 'center' }}>No experiments found.</p>
        ) : (
          <table className="table-container">
            <thead>
              <tr>
                <th>ID</th>
                <th>Experiment ID</th>
                <th>Status</th>
              </tr>
            </thead>
            <tbody>
              {experiments.map((exp: any, i: number) => (
                <tr key={i}>
                  <td>{exp.id}</td>
                  <td style={{ fontFamily: 'var(--font-mono)' }}>{exp.experiment_id}</td>
                  <td><span className="badge badge-info">Completed</span></td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </div>
  );
};

export default Experiments;
