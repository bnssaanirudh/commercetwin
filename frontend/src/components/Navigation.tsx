import React from 'react';
import { NavLink, useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';

const Navigation: React.FC = () => {
  const { logout } = useAuth();
  const navigate = useNavigate();

  const handleLogout = () => {
    logout();
    navigate('/');
  };

  return (
    <div className="sidebar">
      <h1>CommerceTwin</h1>
      <nav style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem', flex: 1 }}>
        <NavLink to="/dashboard" className={({ isActive }) => `nav-link ${isActive ? 'active' : ''}`}>Overview</NavLink>
        <NavLink to="/run" className={({ isActive }) => `nav-link ${isActive ? 'active' : ''}`}>New Run</NavLink>
        <NavLink to="/experiments" className={({ isActive }) => `nav-link ${isActive ? 'active' : ''}`}>Experiments</NavLink>
        <NavLink to="/traces" className={({ isActive }) => `nav-link ${isActive ? 'active' : ''}`}>Traces</NavLink>
        <NavLink to="/revenue-leak" className={({ isActive }) => `nav-link ${isActive ? 'active' : ''}`}>Revenue Leak</NavLink>
        <NavLink to="/repairs" className={({ isActive }) => `nav-link ${isActive ? 'active' : ''}`}>Repairs</NavLink>
        <NavLink to="/chaos" className={({ isActive }) => `nav-link ${isActive ? 'active' : ''}`}>Chaos Lab</NavLink>
        <NavLink to="/payments" className={({ isActive }) => `nav-link ${isActive ? 'active' : ''}`}>Payments</NavLink>
      </nav>
      <div style={{ marginTop: 'auto', paddingTop: '2rem' }}>
        <button className="btn" style={{ width: '100%', color: 'var(--accent-red)', borderColor: 'var(--accent-red)' }} onClick={handleLogout}>
          [ LOGOUT ]
        </button>
      </div>
    </div>
  );
};

export default Navigation;
