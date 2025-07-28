import React from 'react';
import { useAuth } from '../context/AuthContext';
import SatelliteDashboard from './SatelliteDashboard';

const Dashboard = () => {
  const { auth } = useAuth();

  return (
    <div className="min-h-screen bg-gray-100">
      {/* Header simplifié */}
      <div className="bg-space-blue text-white p-6 shadow-lg">
        <div className="container mx-auto">
          <h1 className="text-2xl font-bold">User Dashboard</h1>
          <p className="text-accent-light">
            Bienvenue, {auth.username} | Access level: Standard
          </p>
        </div>
      </div>

      {/* Intégration du SatelliteDashboard */}
      <div className="container mx-auto p-4">
        <SatelliteDashboard />
      </div>
    </div>
  );
};

export default Dashboard;