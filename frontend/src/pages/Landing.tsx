import React from 'react';
import { useNavigate } from 'react-router-dom';

const Landing: React.FC = () => {
  const navigate = useNavigate();

  return (
    <div className="landing-page" style={{ 
      color: '#fff', 
      fontFamily: 'Inter, sans-serif',
      minHeight: '100vh',
      backgroundColor: '#0a0a0a',
    }}>
      {/* Hero Section */}
      <section style={{ 
        padding: '100px 20px', 
        textAlign: 'center',
        background: 'linear-gradient(135deg, rgba(16,185,129,0.1) 0%, rgba(10,10,10,1) 100%)'
      }}>
        <div style={{ maxWidth: '800px', margin: '0 auto' }}>
          <div style={{ display: 'flex', justifyContent: 'center', marginBottom: '20px' }}>
            <div style={{
              width: '64px',
              height: '64px',
              borderRadius: '16px',
              background: 'linear-gradient(135deg, #10b981, #059669)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              fontSize: '32px',
              fontWeight: 'bold',
              color: '#fff',
              boxShadow: '0 0 30px rgba(16,185,129,0.3)'
            }}>
              C
            </div>
          </div>
          <h1 style={{ 
            fontSize: '4rem', 
            fontWeight: '800', 
            marginBottom: '1rem',
            background: 'linear-gradient(to right, #fff, #a1a1aa)',
            WebkitBackgroundClip: 'text',
            WebkitTextFillColor: 'transparent',
          }}>
            CommerceTwin
          </h1>
          <p style={{ 
            fontSize: '1.5rem', 
            color: '#a1a1aa', 
            marginBottom: '3rem',
            lineHeight: '1.6'
          }}>
            The definitive platform for Agentic Commerce testing. Simulate, identify, and self-heal integration failures before they hit production.
          </p>
          <div style={{ display: 'flex', gap: '20px', justifyContent: 'center' }}>
            <button 
              onClick={() => navigate('/dashboard')}
              style={{
                padding: '16px 32px',
                fontSize: '1.1rem',
                fontWeight: '600',
                backgroundColor: '#10b981',
                color: '#fff',
                border: 'none',
                borderRadius: '8px',
                cursor: 'pointer',
                boxShadow: '0 4px 14px 0 rgba(16,185,129,0.39)',
                transition: 'all 0.2s ease-in-out'
              }}
            >
              Enter Dashboard
            </button>
            <button 
              onClick={() => navigate('/run')}
              style={{
                padding: '16px 32px',
                fontSize: '1.1rem',
                fontWeight: '600',
                backgroundColor: 'transparent',
                color: '#fff',
                border: '1px solid #3f3f46',
                borderRadius: '8px',
                cursor: 'pointer',
                transition: 'all 0.2s ease-in-out'
              }}
            >
              Run Experiment
            </button>
          </div>
        </div>
      </section>

      {/* Features Section */}
      <section style={{ padding: '100px 20px', backgroundColor: '#0a0a0a' }}>
        <div style={{ maxWidth: '1200px', margin: '0 auto' }}>
          <h2 style={{ fontSize: '2.5rem', textAlign: 'center', marginBottom: '4rem' }}>
            Why CommerceTwin?
          </h2>
          <div style={{ 
            display: 'grid', 
            gridTemplateColumns: 'repeat(auto-fit, minmax(300px, 1fr))',
            gap: '30px'
          }}>
            {[
              {
                title: "Synthetic Buyers",
                desc: "Deploy autonomous AI agents that act like real humans, stress-testing your checkout flows with strict natural language intents and hard budgets.",
                icon: "🤖"
              },
              {
                title: "Causal Localization",
                desc: "When a transaction fails, our engine automatically pinpoints the exact catalog misconfiguration using counterfactual reasoning.",
                icon: "🔍"
              },
              {
                title: "Auto-Healing Catalogs",
                desc: "Generate authoritative JSON schema patches for your merchant catalog, verified in sandboxed replays before ever touching production.",
                icon: "✨"
              },
              {
                title: "Idempotent Webhooks",
                desc: "Battle-tested payment reconciliation layer ensures no duplicate orders, even when facing network chaos and retry storms.",
                icon: "🛡️"
              },
              {
                title: "Agentic Value at Risk (AVaR)",
                desc: "Quantify the exact monetary impact of integration flaws in your commerce funnel.",
                icon: "📈"
              },
              {
                title: "Red-Team Ready",
                desc: "Built-in defenses against prompt injection, hallucinated SKUs, budget overages, and malicious payload mutations.",
                icon: "🚨"
              }
            ].map((feature, i) => (
              <div key={i} style={{
                background: '#18181b',
                padding: '40px',
                borderRadius: '16px',
                border: '1px solid #27272a'
              }}>
                <div style={{ fontSize: '3rem', marginBottom: '20px' }}>{feature.icon}</div>
                <h3 style={{ fontSize: '1.5rem', marginBottom: '15px' }}>{feature.title}</h3>
                <p style={{ color: '#a1a1aa', lineHeight: '1.6' }}>{feature.desc}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Analytics Teaser */}
      <section style={{ 
        padding: '100px 20px', 
        background: 'linear-gradient(to bottom, #0a0a0a, #18181b)'
      }}>
        <div style={{ maxWidth: '1000px', margin: '0 auto', textAlign: 'center' }}>
          <h2 style={{ fontSize: '2.5rem', marginBottom: '2rem' }}>Data-Driven Intelligence</h2>
          <p style={{ fontSize: '1.2rem', color: '#a1a1aa', marginBottom: '3rem' }}>
            CommerceTwin monitors the Robust Transaction Yield (RTY) across all traffic. Understand exactly where value drops out.
          </p>
          <div style={{ 
            background: '#09090b',
            border: '1px solid #27272a',
            borderRadius: '16px',
            padding: '40px',
            boxShadow: '0 20px 40px rgba(0,0,0,0.4)'
          }}>
            <div style={{ display: 'flex', justifyContent: 'space-around', flexWrap: 'wrap', gap: '20px' }}>
              <div>
                <div style={{ fontSize: '3rem', fontWeight: 'bold', color: '#10b981' }}>98.5%</div>
                <div style={{ color: '#a1a1aa', marginTop: '10px' }}>Intent Integrity</div>
              </div>
              <div>
                <div style={{ fontSize: '3rem', fontWeight: 'bold', color: '#3b82f6' }}>0.2ms</div>
                <div style={{ color: '#a1a1aa', marginTop: '10px' }}>P99 Validation Latency</div>
              </div>
              <div>
                <div style={{ fontSize: '3rem', fontWeight: 'bold', color: '#ef4444' }}>0</div>
                <div style={{ color: '#a1a1aa', marginTop: '10px' }}>Unreconciled Payments</div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Footer CTA */}
      <section style={{ 
        padding: '100px 20px', 
        textAlign: 'center',
        background: '#10b981',
        color: '#fff'
      }}>
        <h2 style={{ fontSize: '3rem', marginBottom: '1.5rem', fontWeight: '800' }}>Ready to secure your commerce?</h2>
        <p style={{ fontSize: '1.2rem', marginBottom: '3rem', opacity: '0.9' }}>
          Stop losing revenue to undocumented edge cases and catalog misconfigurations.
        </p>
        <button 
          onClick={() => navigate('/dashboard')}
          style={{
            padding: '16px 40px',
            fontSize: '1.2rem',
            fontWeight: 'bold',
            backgroundColor: '#0a0a0a',
            color: '#fff',
            border: 'none',
            borderRadius: '8px',
            cursor: 'pointer',
            transition: 'transform 0.2s',
          }}
          onMouseOver={(e) => e.currentTarget.style.transform = 'scale(1.05)'}
          onMouseOut={(e) => e.currentTarget.style.transform = 'scale(1)'}
        >
          Launch Dashboard
        </button>
      </section>

      <footer style={{
        padding: '40px 20px',
        textAlign: 'center',
        backgroundColor: '#0a0a0a',
        color: '#52525b',
        borderTop: '1px solid #27272a'
      }}>
        <p>© 2026 CommerceTwin. Visa Innovation Labs.</p>
      </footer>
    </div>
  );
};

export default Landing;
