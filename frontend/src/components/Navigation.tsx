import React from 'react';
import { NavLink } from 'react-router-dom';

const Navigation: React.FC = () => {
  return (
    <div className="top-nav">
      <div className="nav-left">
        <div className="nav-logo">
          <div className="nav-logo-icon"></div>
          CommerceTwin
        </div>
        <nav className="nav-links">
          <NavLink to="/dashboard" className={({ isActive }) => `nav-link ${isActive ? 'active' : ''}`}>Dashboard</NavLink>
          <NavLink to="/run" className={({ isActive }) => `nav-link ${isActive ? 'active' : ''}`}>Run Experiment</NavLink>
          <NavLink to="/experiments" className={({ isActive }) => `nav-link ${isActive ? 'active' : ''}`}>Experiments</NavLink>
          <NavLink to="/traces" className={({ isActive }) => `nav-link ${isActive ? 'active' : ''}`}>Traces</NavLink>
          <NavLink to="/chaos" className={({ isActive }) => `nav-link ${isActive ? 'active' : ''}`}>Repair/Replay</NavLink>
          <NavLink to="/payments" className={({ isActive }) => `nav-link ${isActive ? 'active' : ''}`}>Payment Safety</NavLink>
        </nav>
      </div>
      <div className="nav-actions">
        {/* No auth buttons needed in judge view */}
      </div>
    </div>
  );
};

export default Navigation;
