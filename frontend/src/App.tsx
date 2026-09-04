import React from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import Navigation from './components/Navigation';
import Overview from './pages/Overview';
import Experiments from './pages/Experiments';
import Traces from './pages/Traces';
import RevenueLeak from './pages/RevenueLeak';
import Repairs from './pages/Repairs';
import ChaosLab from './pages/ChaosLab';
import Payments from './pages/Payments';
import RunExperiment from './pages/RunExperiment';

const App: React.FC = () => {
  return (
    <BrowserRouter>
      <div className="app-container">
        <Navigation />
        <main className="main-content">
          <Routes>
            <Route path="/" element={<Navigate to="/dashboard" replace />} />
            
            <Route path="/dashboard" element={<Overview />} />
            <Route path="/run" element={<RunExperiment />} />
            <Route path="/experiments" element={<Experiments />} />
            <Route path="/traces" element={<Traces />} />
            <Route path="/revenue-leak" element={<RevenueLeak />} />
            <Route path="/repairs" element={<Repairs />} />
            <Route path="/chaos" element={<ChaosLab />} />
            <Route path="/payments" element={<Payments />} />
          </Routes>
        </main>
      </div>
    </BrowserRouter>
  );
};

export default App;
