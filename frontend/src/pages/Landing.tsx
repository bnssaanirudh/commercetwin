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
        padding: '120px 20px', 
        textAlign: 'center',
        background: 'linear-gradient(135deg, rgba(16,185,129,0.15) 0%, rgba(10,10,10,1) 100%)',
        borderBottom: '1px solid rgba(255,255,255,0.05)'
      }}>
        <div style={{ maxWidth: '900px', margin: '0 auto' }}>
          <div style={{ display: 'flex', justifyContent: 'center', marginBottom: '30px' }}>
            <div style={{
              width: '80px',
              height: '80px',
              borderRadius: '20px',
              background: 'linear-gradient(135deg, #10b981, #059669)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              fontSize: '40px',
              fontWeight: 'bold',
              color: '#fff',
              boxShadow: '0 0 40px rgba(16,185,129,0.4)'
            }}>
              C
            </div>
          </div>
          <h1 style={{ 
            fontSize: '4.5rem', 
            fontWeight: '800', 
            marginBottom: '1.5rem',
            background: 'linear-gradient(to right, #ffffff, #a1a1aa)',
            WebkitBackgroundClip: 'text',
            WebkitTextFillColor: 'transparent',
            lineHeight: '1.1'
          }}>
            CommerceTwin
          </h1>
          <p style={{ 
            fontSize: '1.5rem', 
            color: '#a1a1aa', 
            marginBottom: '3rem',
            lineHeight: '1.6',
            maxWidth: '800px',
            margin: '0 auto 3rem'
          }}>
            The definitive platform for Agentic Commerce testing. Simulate millions of buyer interactions, pinpoint integration failures with causal reasoning, and self-heal your catalogs before they impact production.
          </p>
          <div style={{ display: 'flex', gap: '20px', justifyContent: 'center' }}>
            <button 
              onClick={() => navigate('/dashboard')}
              style={{
                padding: '16px 36px',
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
              onMouseOver={(e) => e.currentTarget.style.transform = 'translateY(-2px)'}
              onMouseOut={(e) => e.currentTarget.style.transform = 'translateY(0)'}
            >
              Enter Dashboard
            </button>
            <button 
              onClick={() => navigate('/run')}
              style={{
                padding: '16px 36px',
                fontSize: '1.1rem',
                fontWeight: '600',
                backgroundColor: 'rgba(255,255,255,0.05)',
                color: '#fff',
                border: '1px solid rgba(255,255,255,0.1)',
                borderRadius: '8px',
                cursor: 'pointer',
                transition: 'all 0.2s ease-in-out'
              }}
              onMouseOver={(e) => {
                e.currentTarget.style.backgroundColor = 'rgba(255,255,255,0.1)';
                e.currentTarget.style.borderColor = 'rgba(255,255,255,0.2)';
              }}
              onMouseOut={(e) => {
                e.currentTarget.style.backgroundColor = 'rgba(255,255,255,0.05)';
                e.currentTarget.style.borderColor = 'rgba(255,255,255,0.1)';
              }}
            >
              Run Experiment
            </button>
          </div>
        </div>
      </section>

      {/* Trusted By / Logos (Mock) */}
      <section style={{ padding: '60px 20px', backgroundColor: '#0a0a0a', borderBottom: '1px solid rgba(255,255,255,0.05)' }}>
        <div style={{ maxWidth: '1200px', margin: '0 auto', textAlign: 'center' }}>
          <p style={{ color: '#71717a', fontSize: '0.9rem', textTransform: 'uppercase', letterSpacing: '2px', marginBottom: '30px' }}>
            Built for enterprise-grade reliability
          </p>
          <div style={{ display: 'flex', justifyContent: 'center', gap: '60px', flexWrap: 'wrap', opacity: 0.5, filter: 'grayscale(100%)' }}>
            <span style={{ fontSize: '1.5rem', fontWeight: 'bold' }}>Visa Innovation Labs</span>
            <span style={{ fontSize: '1.5rem', fontWeight: 'bold' }}>Acme E-Commerce</span>
            <span style={{ fontSize: '1.5rem', fontWeight: 'bold' }}>Global Retail Inc.</span>
            <span style={{ fontSize: '1.5rem', fontWeight: 'bold' }}>TechMart Solutions</span>
          </div>
        </div>
      </section>

      {/* Features Section */}
      <section style={{ padding: '120px 20px', backgroundColor: '#0a0a0a' }}>
        <div style={{ maxWidth: '1200px', margin: '0 auto' }}>
          <h2 style={{ fontSize: '3rem', textAlign: 'center', marginBottom: '1rem', fontWeight: '800' }}>
            Why CommerceTwin?
          </h2>
          <p style={{ textAlign: 'center', color: '#a1a1aa', fontSize: '1.2rem', maxWidth: '700px', margin: '0 auto 4rem' }}>
            A comprehensive suite of tools designed to ensure your checkout flows are unbreakable, even under the most chaotic conditions.
          </p>
          <div style={{ 
            display: 'grid', 
            gridTemplateColumns: 'repeat(auto-fit, minmax(350px, 1fr))',
            gap: '30px'
          }}>
            {[
              {
                title: "Synthetic Buyers",
                desc: "Deploy autonomous AI agents that act like real humans, stress-testing your checkout flows with strict natural language intents and hard budgets. They browse, evaluate, and attempt to checkout autonomously.",
                icon: "🤖",
                color: "#3b82f6"
              },
              {
                title: "Causal Localization",
                desc: "When a transaction fails, our engine automatically pinpoints the exact catalog misconfiguration using counterfactual reasoning. No more guessing why a checkout aborted at step 4.",
                icon: "🔍",
                color: "#10b981"
              },
              {
                title: "Auto-Healing Catalogs",
                desc: "Generate authoritative JSON schema patches for your merchant catalog, verified in sandboxed replays before ever touching production. Automatically resolve missing attributes or pricing mismatches.",
                icon: "✨",
                color: "#8b5cf6"
              },
              {
                title: "Idempotent Webhooks",
                desc: "Battle-tested payment reconciliation layer ensures no duplicate orders, even when facing network chaos, retry storms, or out-of-order Razorpay webhook events.",
                icon: "🛡️",
                color: "#f59e0b"
              },
              {
                title: "Agentic Value at Risk (AVaR)",
                desc: "Quantify the exact monetary impact of integration flaws in your commerce funnel. See exactly how many 'Paise' are lost due to specific misconfigurations.",
                icon: "📈",
                color: "#ef4444"
              },
              {
                title: "Red-Team Ready",
                desc: "Built-in defenses against prompt injection, hallucinated SKUs, budget overages, and malicious payload mutations. Test your platform's resilience against adversarial actors.",
                icon: "🚨",
                color: "#ec4899"
              }
            ].map((feature, i) => (
              <div key={i} style={{
                background: '#121214',
                padding: '40px',
                borderRadius: '24px',
                border: '1px solid #27272a',
                transition: 'transform 0.3s ease, box-shadow 0.3s ease',
                cursor: 'default'
              }}
              onMouseOver={(e) => {
                e.currentTarget.style.transform = 'translateY(-5px)';
                e.currentTarget.style.boxShadow = `0 10px 30px -10px ${feature.color}33`;
                e.currentTarget.style.borderColor = `${feature.color}55`;
              }}
              onMouseOut={(e) => {
                e.currentTarget.style.transform = 'translateY(0)';
                e.currentTarget.style.boxShadow = 'none';
                e.currentTarget.style.borderColor = '#27272a';
              }}
              >
                <div style={{ 
                  fontSize: '2.5rem', 
                  marginBottom: '20px',
                  width: '60px',
                  height: '60px',
                  background: `${feature.color}15`,
                  borderRadius: '16px',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  border: `1px solid ${feature.color}33`
                }}>
                  {feature.icon}
                </div>
                <h3 style={{ fontSize: '1.5rem', marginBottom: '15px', color: '#fff' }}>{feature.title}</h3>
                <p style={{ color: '#a1a1aa', lineHeight: '1.7', fontSize: '1.05rem' }}>{feature.desc}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* How it Works Section */}
      <section style={{ padding: '120px 20px', backgroundColor: '#121214', borderTop: '1px solid #27272a', borderBottom: '1px solid #27272a' }}>
        <div style={{ maxWidth: '1000px', margin: '0 auto' }}>
          <h2 style={{ fontSize: '3rem', textAlign: 'center', marginBottom: '4rem', fontWeight: '800' }}>
            How CommerceTwin Works
          </h2>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '60px' }}>
            
            <div style={{ display: 'flex', gap: '40px', alignItems: 'center', flexWrap: 'wrap' }}>
              <div style={{ flex: '1 1 400px' }}>
                <div style={{ color: '#10b981', fontWeight: 'bold', fontSize: '1.2rem', marginBottom: '10px' }}>Step 1</div>
                <h3 style={{ fontSize: '2rem', marginBottom: '20px' }}>Define Buyer Intents</h3>
                <p style={{ color: '#a1a1aa', fontSize: '1.1rem', lineHeight: '1.7' }}>
                  Provide natural language intents and hard constraints (like budgets or required attributes). CommerceTwin generates thousands of synthetic buyers who browse your catalog exactly like real humans would.
                </p>
              </div>
              <div style={{ flex: '1 1 400px', background: '#18181b', padding: '30px', borderRadius: '16px', border: '1px solid #27272a' }}>
                <pre style={{ color: '#a1a1aa', fontSize: '0.9rem', overflowX: 'auto' }}>
{`{
  "intent_id": "INT-8492",
  "raw_intent": "I need noise-cancelling headphones under ₹4000",
  "hard_constraints": {
    "required_categories": ["headphones"],
    "max_budget_paise": 400000
  }
}`}
                </pre>
              </div>
            </div>

            <div style={{ display: 'flex', gap: '40px', alignItems: 'center', flexWrap: 'wrap', flexDirection: 'row-reverse' }}>
              <div style={{ flex: '1 1 400px' }}>
                <div style={{ color: '#3b82f6', fontWeight: 'bold', fontSize: '1.2rem', marginBottom: '10px' }}>Step 2</div>
                <h3 style={{ fontSize: '2rem', marginBottom: '20px' }}>Inject Chaos</h3>
                <p style={{ color: '#a1a1aa', fontSize: '1.1rem', lineHeight: '1.7' }}>
                  The Chaos Engine introduces real-world unpredictability: inventory stockouts right before checkout, pricing mismatches between frontend and database, and delayed or duplicate payment webhooks.
                </p>
              </div>
              <div style={{ flex: '1 1 400px', background: '#18181b', padding: '30px', borderRadius: '16px', border: '1px solid #27272a' }}>
                <div style={{ display: 'flex', flexDirection: 'column', gap: '15px' }}>
                  <div style={{ padding: '15px', background: 'rgba(239,68,68,0.1)', borderLeft: '4px solid #ef4444', borderRadius: '4px' }}>
                    <span style={{ color: '#ef4444', fontWeight: 'bold' }}>ERROR:</span> PRICE_MISMATCH detected
                  </div>
                  <div style={{ padding: '15px', background: 'rgba(245,158,11,0.1)', borderLeft: '4px solid #f59e0b', borderRadius: '4px' }}>
                    <span style={{ color: '#f59e0b', fontWeight: 'bold' }}>WARN:</span> Duplicate Webhook received
                  </div>
                </div>
              </div>
            </div>

            <div style={{ display: 'flex', gap: '40px', alignItems: 'center', flexWrap: 'wrap' }}>
              <div style={{ flex: '1 1 400px' }}>
                <div style={{ color: '#8b5cf6', fontWeight: 'bold', fontSize: '1.2rem', marginBottom: '10px' }}>Step 3</div>
                <h3 style={{ fontSize: '2rem', marginBottom: '20px' }}>Localize & Repair</h3>
                <p style={{ color: '#a1a1aa', fontSize: '1.1rem', lineHeight: '1.7' }}>
                  When a failure occurs, the Causal Localizer traces the exact root cause. The Repair Synthesizer then proposes a strict, sandboxed JSON patch to auto-heal the catalog—without violating merchant policies.
                </p>
              </div>
              <div style={{ flex: '1 1 400px', background: '#18181b', padding: '30px', borderRadius: '16px', border: '1px solid #27272a' }}>
                 <pre style={{ color: '#a1a1aa', fontSize: '0.9rem', overflowX: 'auto' }}>
{`"proposed_patch": {
  "target_sku": "HEADPHONE-01",
  "operations": [
    { 
      "op": "add", 
      "path": "/attributes/noise_cancelling",
      "value": "true" 
    }
  ]
}`}
                </pre>
              </div>
            </div>

          </div>
        </div>
      </section>

      {/* Analytics Teaser */}
      <section style={{ 
        padding: '120px 20px', 
        background: 'linear-gradient(to bottom, #0a0a0a, #18181b)'
      }}>
        <div style={{ maxWidth: '1000px', margin: '0 auto', textAlign: 'center' }}>
          <h2 style={{ fontSize: '3rem', marginBottom: '1.5rem', fontWeight: '800' }}>Data-Driven Intelligence</h2>
          <p style={{ fontSize: '1.2rem', color: '#a1a1aa', marginBottom: '4rem', maxWidth: '700px', margin: '0 auto 4rem' }}>
            CommerceTwin continuously monitors the Robust Transaction Yield (RTY) across all traffic. Understand exactly where value drops out and why.
          </p>
          <div style={{ 
            background: '#09090b',
            border: '1px solid #27272a',
            borderRadius: '24px',
            padding: '60px 40px',
            boxShadow: '0 20px 50px rgba(0,0,0,0.5)'
          }}>
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '40px' }}>
              <div>
                <div style={{ fontSize: '3.5rem', fontWeight: '900', color: '#10b981', marginBottom: '10px' }}>98.5%</div>
                <div style={{ color: '#e4e4e7', fontSize: '1.1rem', fontWeight: '600' }}>Robust Transaction Yield</div>
                <div style={{ color: '#71717a', marginTop: '5px', fontSize: '0.9rem' }}>Reliable successful checkouts</div>
              </div>
              <div>
                <div style={{ fontSize: '3.5rem', fontWeight: '900', color: '#3b82f6', marginBottom: '10px' }}>0.2ms</div>
                <div style={{ color: '#e4e4e7', fontSize: '1.1rem', fontWeight: '600' }}>P95 Validation Latency</div>
                <div style={{ color: '#71717a', marginTop: '5px', fontSize: '0.9rem' }}>Lightning fast state machine</div>
              </div>
              <div>
                <div style={{ fontSize: '3.5rem', fontWeight: '900', color: '#ef4444', marginBottom: '10px' }}>$0</div>
                <div style={{ color: '#e4e4e7', fontSize: '1.1rem', fontWeight: '600' }}>Unreconciled Payments</div>
                <div style={{ color: '#71717a', marginTop: '5px', fontSize: '0.9rem' }}>Idempotent webhook safety</div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Footer CTA */}
      <section style={{ 
        padding: '120px 20px', 
        textAlign: 'center',
        background: '#10b981',
        color: '#fff',
        position: 'relative',
        overflow: 'hidden'
      }}>
        <div style={{ 
          position: 'absolute', 
          top: 0, 
          left: 0, 
          right: 0, 
          bottom: 0, 
          background: 'radial-gradient(circle at center, transparent 0%, rgba(0,0,0,0.2) 100%)',
          pointerEvents: 'none'
        }} />
        <div style={{ position: 'relative', zIndex: 1, maxWidth: '800px', margin: '0 auto' }}>
          <h2 style={{ fontSize: '3.5rem', marginBottom: '1.5rem', fontWeight: '900', letterSpacing: '-1px' }}>
            Ready to secure your commerce?
          </h2>
          <p style={{ fontSize: '1.3rem', marginBottom: '3rem', opacity: '0.95', lineHeight: '1.6' }}>
            Stop losing revenue to undocumented edge cases, missing metadata, and payment reconciliation bugs. Start simulating today.
          </p>
          <button 
            onClick={() => navigate('/dashboard')}
            style={{
              padding: '18px 48px',
              fontSize: '1.2rem',
              fontWeight: 'bold',
              backgroundColor: '#0a0a0a',
              color: '#fff',
              border: 'none',
              borderRadius: '12px',
              cursor: 'pointer',
              transition: 'transform 0.2s, box-shadow 0.2s',
              boxShadow: '0 10px 25px rgba(0,0,0,0.2)'
            }}
            onMouseOver={(e) => {
              e.currentTarget.style.transform = 'translateY(-3px)';
              e.currentTarget.style.boxShadow = '0 15px 35px rgba(0,0,0,0.3)';
            }}
            onMouseOut={(e) => {
              e.currentTarget.style.transform = 'translateY(0)';
              e.currentTarget.style.boxShadow = '0 10px 25px rgba(0,0,0,0.2)';
            }}
          >
            Launch Dashboard
          </button>
        </div>
      </section>

      <footer style={{
        padding: '60px 20px',
        textAlign: 'center',
        backgroundColor: '#0a0a0a',
        color: '#52525b',
        borderTop: '1px solid #27272a'
      }}>
        <div style={{ maxWidth: '1200px', margin: '0 auto', display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '20px' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
             <div style={{
              width: '32px',
              height: '32px',
              borderRadius: '8px',
              background: '#10b981',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              fontWeight: 'bold',
              color: '#fff',
            }}>
              C
            </div>
            <span style={{ fontWeight: 'bold', color: '#e4e4e7', fontSize: '1.2rem' }}>CommerceTwin</span>
          </div>
          <p>© 2026 CommerceTwin. Visa Innovation Labs. All rights reserved.</p>
        </div>
      </footer>
    </div>
  );
};

export default Landing;
