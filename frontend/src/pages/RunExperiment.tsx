import React, { useState } from 'react';

const RunExperiment: React.FC = () => {
  const [intent, setIntent] = useState('');
  const [status, setStatus] = useState<'idle' | 'running' | 'completed'>('idle');

  const handleRun = (e: React.FormEvent) => {
    e.preventDefault();
    if (!intent) return;
    
    setStatus('running');
    
    // Simulate the execution of run_demo.py
    setTimeout(() => {
      setStatus('completed');
    }, 3000);
  };

  return (
    <div>
      <div className="page-header">
        <h2 className="page-title">Run New Experiment</h2>
        <p className="page-subtitle">Inject synthetic buyer traffic into the sandbox.</p>
      </div>

      <div className="card" style={{ maxWidth: '800px' }}>
        <form onSubmit={handleRun}>
          <div className="form-group">
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
          </div>
        </form>
      </div>
      
      {status === 'completed' && (
        <div className="card" style={{ marginTop: '2rem', maxWidth: '800px', borderColor: 'var(--accent-green)' }}>
          <h3 className="card-title" style={{ color: 'var(--accent-green)' }}>Simulation Output</h3>
          <div style={{ fontFamily: 'var(--font-mono)', fontSize: '0.85rem', color: '#fff', whiteSpace: 'pre-wrap' }}>
            {`> Booting Semantic Buyer...
> Parsing Constraints: {"power_watts": 65, "budget": 3000}
> Injecting Chaos: [MISSING_TYPED_ATTRIBUTE]
> Transaction Aborted.
> Trace Id: TR-NEW-001
> Repair Patch Synthesized: {"power_watts": 65}
> Replay Status: READY_FOR_PAYMENT`}
          </div>
        </div>
      )}
    </div>
  );
};

export default RunExperiment;
