import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';

const Login: React.FC = () => {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const { login } = useAuth();
  const navigate = useNavigate();

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (email && password) {
      login();
      navigate('/dashboard');
    } else {
      setError('ACCESS DENIED: Missing credentials.');
    }
  };

  return (
    <div className="landing-container">
      <div className="login-box">
        <h2 className="login-title">SYSTEM AUTHENTICATION</h2>
        {error && <div className="login-error">{error}</div>}
        <form onSubmit={handleSubmit} className="login-form">
          <div className="form-group">
            <label>Operator Email</label>
            <input 
              type="email" 
              value={email} 
              onChange={(e) => setEmail(e.target.value)} 
              placeholder="operator@commercetwin.ai"
              className="cyber-input"
            />
          </div>
          <div className="form-group">
            <label>Access Code</label>
            <input 
              type="password" 
              value={password} 
              onChange={(e) => setPassword(e.target.value)} 
              placeholder="••••••••"
              className="cyber-input"
            />
          </div>
          <button type="submit" className="btn btn-primary" style={{ width: '100%', marginTop: '1rem' }}>
            [ INITIALIZE SESSION ]
          </button>
        </form>
      </div>
    </div>
  );
};

export default Login;
