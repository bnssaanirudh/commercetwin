import React from 'react';
import { useNavigate } from 'react-router-dom';

const Landing: React.FC = () => {
  const navigate = useNavigate();

  return (
    <div className="landing-container">
      <div className="landing-content">
        <h1 className="landing-title">CommerceTwin</h1>
        <p className="landing-subtitle">
          AI-Driven Penetration Testing for Agentic Commerce
        </p>
        <p className="landing-description">
          Simulate synthetic AI buyers. Inject tactical chaos. Isolate revenue leaks. Synthesize AST catalog repairs. Verify counterfactual success. 
        </p>
        
        <div className="landing-actions">
          <button className="btn btn-primary" onClick={() => navigate('/login')}>
            [ Access Secure Lab ]
          </button>
          <button className="btn btn-secondary" onClick={() => window.open('https://github.com', '_blank')}>
            View Documentation
          </button>
        </div>

        <div className="grid-3" style={{ marginTop: '4rem' }}>
          <div className="card" style={{ textAlign: 'center' }}>
            <h3 className="card-title" style={{ color: 'var(--accent-cyan)' }}>Simulate Chaos</h3>
            <p className="text-muted" style={{ fontSize: '0.85rem' }}>Drop catalog schemas and test agent resilience under fire.</p>
          </div>
          <div className="card" style={{ textAlign: 'center' }}>
            <h3 className="card-title" style={{ color: 'var(--accent-green)' }}>Synthesize Repairs</h3>
            <p className="text-muted" style={{ fontSize: '0.85rem' }}>Automated JSON patch generation for missing merchant policy constraints.</p>
          </div>
          <div className="card" style={{ textAlign: 'center' }}>
            <h3 className="card-title" style={{ color: 'var(--accent-orange)' }}>Verify Replay</h3>
            <p className="text-muted" style={{ fontSize: '0.85rem' }}>Deterministic cohort re-execution to mathematically prove revenue capture.</p>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Landing;
