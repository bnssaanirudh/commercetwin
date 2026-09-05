import React, { useState } from 'react';
import { runExperiment, createExperiment } from '../api/client';

const RunExperiment: React.FC = () => {
  const [intent, setIntent] = useState('');
  const [merchantVersion, setMerchantVersion] = useState('v1');
  const [chaosProfile, setChaosProfile] = useState('none');
  const [seed, setSeed] = useState(42);
  const [cohortSize, setCohortSize] = useState(1);
  const [status, setStatus] = useState<'idle' | 'running' | 'completed' | 'error'>('idle');
  const [result, setResult] = useState<any>(null);

  const handleRun = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!intent) return;
    
    setStatus('running');
    
    try {
      const expRes = await createExperiment({
        merchant_version: merchantVersion,
        chaos_profile: chaosProfile,
        seed: seed
      });
      const data = await runExperiment(expRes.experiment_id, {
        buyer_cohort_size: cohortSize,
        seed: seed,
        intent: intent
      });
      setResult(data);
      setStatus('completed');
    } catch (err) {
      console.error(err);
      setStatus('error');
    }
  };

  return (
    <div>
      <div className="page-header">
        <h2 className="page-title">Run New Experiment</h2>
        <p className="page-subtitle">Inject synthetic buyer traffic into the sandbox.</p>
      </div>

      <div className="card" style={{ maxWidth: '800px' }}>
        <form onSubmit={handleRun}>
          <div className="form-group" style={{ marginBottom: '1.5rem' }}>
            <label style={{ display: 'block', marginBottom: '0.5rem', color: 'var(--accent-cyan)' }}>
              Buyer Intent Definition
            </label>
            <textarea 
              value={intent}
              onChange={(e) => setIntent(e.target.value)}
              className="cyber-input"
              rows={4}
              placeholder='e.g., "I need a USB-C charger for my MacBook Air. It must support at least 65W USB Power Delivery and cost less than ₹3,000."'
              style={{ width: '100%', resize: 'vertical' }}
            />
          </div>

          <div className="grid-2" style={{ gap: '1.5rem', marginBottom: '1.5rem' }}>
            <div className="form-group">
              <label style={{ display: 'block', marginBottom: '0.5rem', color: 'var(--accent-cyan)' }}>Merchant Twin Version</label>
              <select className="cyber-input" style={{ width: '100%' }} value={merchantVersion} onChange={(e) => setMerchantVersion(e.target.value)}>
                <option value="v1">v1 - Base Catalog</option>
                <option value="v2">v2 - Sandboxed Repair</option>
                <option value="v3">v3 - Patched Production</option>
              </select>
            </div>
            
            <div className="form-group">
              <label style={{ display: 'block', marginBottom: '0.5rem', color: 'var(--accent-cyan)' }}>Chaos Profile</label>
              <select className="cyber-input" style={{ width: '100%' }} value={chaosProfile} onChange={(e) => setChaosProfile(e.target.value)}>
                <option value="none">None (Clean Run)</option>
                <option value="drop_attribute">Attribute Dropout</option>
                <option value="stale_inventory">Stale Inventory</option>
                <option value="payment_timeout">Payment Timeout</option>
              </select>
            </div>
            
            <div className="form-group">
              <label style={{ display: 'block', marginBottom: '0.5rem', color: 'var(--accent-cyan)' }}>Execution Seed</label>
              <input type="number" className="cyber-input" style={{ width: '100%' }} value={seed} onChange={(e) => setSeed(parseInt(e.target.value))} />
            </div>
            
            <div className="form-group">
              <label style={{ display: 'block', marginBottom: '0.5rem', color: 'var(--accent-cyan)' }}>Cohort Size</label>
              <input type="number" className="cyber-input" style={{ width: '100%' }} value={cohortSize} onChange={(e) => setCohortSize(parseInt(e.target.value))} min="1" max="50" />
            </div>
          </div>

          <div style={{ marginTop: '1.5rem', display: 'flex', gap: '1rem', alignItems: 'center' }}>
            <button 
              type="submit" 
              className="btn btn-primary" 
              disabled={status === 'running' || !intent}
            >
              {status === 'running' ? '[ EXECUTING... ]' : '[ LAUNCH BUYER ]'}
            </button>
            
            {status === 'running' && (
              <span style={{ color: 'var(--accent-orange)', fontFamily: 'var(--font-mono)' }}>
                Tracing state transitions...
              </span>
            )}
            
            {status === 'completed' && (
              <span style={{ color: 'var(--accent-green)', fontFamily: 'var(--font-mono)' }}>
                [SUCCESS] Trace logged to Revenue Leak graph.
              </span>
            )}
            
            {status === 'error' && (
              <span style={{ color: 'red', fontFamily: 'var(--font-mono)' }}>
                [ERROR] Failed to run experiment. Backend unavailable.
              </span>
            )}
          </div>
        </form>
      </div>
      
      {status === 'completed' && result && (
        <div className="card" style={{ marginTop: '2rem', maxWidth: '800px', borderColor: 'var(--accent-green)' }}>
          <h3 className="card-title" style={{ color: 'var(--accent-green)' }}>Simulation Output</h3>
          <div style={{ fontFamily: 'var(--font-mono)', fontSize: '0.85rem', color: '#fff', whiteSpace: 'pre-wrap' }}>
            {JSON.stringify(result, null, 2)}
          </div>
        </div>
      )}
    </div>
  );
};

export default RunExperiment;
