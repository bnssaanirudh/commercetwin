import React from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { AuthProvider, useAuth } from './context/AuthContext';
import Navigation from './components/Navigation';
import Overview from './pages/Overview';
import Experiments from './pages/Experiments';
import Traces from './pages/Traces';
import RevenueLeak from './pages/RevenueLeak';
import Repairs from './pages/Repairs';
import ChaosLab from './pages/ChaosLab';
import Payments from './pages/Payments';
import Landing from './pages/Landing';
import Login from './pages/Login';
import RunExperiment from './pages/RunExperiment';

const ProtectedRoute: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const { isAuthenticated } = useAuth();
  if (!isAuthenticated) return <Navigate to="/login" replace />;
  return (
    <div className="app-container">
      <Navigation />
      <main className="main-content">
        {children}
      </main>
    </div>
  );
};

const App: React.FC = () => {
  return (
    <AuthProvider>
      <BrowserRouter>
        <Routes>
          <Route path="/" element={<Landing />} />
          <Route path="/login" element={<Login />} />
          
          <Route path="/dashboard" element={<ProtectedRoute><Overview /></ProtectedRoute>} />
          <Route path="/run" element={<ProtectedRoute><RunExperiment /></ProtectedRoute>} />
          <Route path="/experiments" element={<ProtectedRoute><Experiments /></ProtectedRoute>} />
          <Route path="/traces" element={<ProtectedRoute><Traces /></ProtectedRoute>} />
          <Route path="/revenue-leak" element={<ProtectedRoute><RevenueLeak /></ProtectedRoute>} />
          <Route path="/repairs" element={<ProtectedRoute><Repairs /></ProtectedRoute>} />
          <Route path="/chaos" element={<ProtectedRoute><ChaosLab /></ProtectedRoute>} />
          <Route path="/payments" element={<ProtectedRoute><Payments /></ProtectedRoute>} />
        </Routes>
      </BrowserRouter>
    </AuthProvider>
  );
};

export default App;
