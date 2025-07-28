import React, { useState, useEffect } from 'react';
import { useAuth } from '../context/AuthContext';
import api from '../api/api';
import SatelliteDashboard from './SatelliteDashboard';

const AdminDashboard = () => {
  const { auth, logout } = useAuth();
  const [systemMetrics, setSystemMetrics] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    const fetchSystemMetrics = async () => {
      try {
        const response = await api.get('/admin/system-status/');
        setSystemMetrics(response.data);
      } catch (err) {
        setError(err.response?.data?.detail || 'Failed to load system metrics');
      } finally {
        setLoading(false);
      }
    };

    fetchSystemMetrics();
  }, []);

  if (loading) return <div className="text-center p-8">Loading system metrics...</div>;
  if (error) return <div className="text-center text-red-500 p-8">{error}</div>;

  return (
    <div className="min-h-screen bg-gray-100">
      {/* Admin Header */} 
      <div className="bg-space-blue text-white p-6 shadow-lg">
        <div className="container mx-auto flex justify-between items-center">
          <div>
            <h1 className="text-2xl font-bold">Admin Dashboard</h1>
            <p className="text-accent-light">
              Welcome, {auth.username} | Access level: Administrator
            </p>
          </div>
          <button
            onClick={logout}
            className="bg-red-600 hover:bg-red-700 px-4 py-2 rounded"
          >
            Logout
          </button>
        </div>
      </div>

      <div className="container mx-auto p-4 space-y-6">
        {/* System Metrics */}
        <div className="bg-white rounded-xl shadow p-6">
          <h2 className="text-xl font-semibold mb-4">System Overview</h2>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <MetricCard 
              title="Active Users" 
              value={systemMetrics.active_users} 
              change="+5%"
            />
            <MetricCard 
              title="Storage Used" 
              value={systemMetrics.storage_used} 
              change="+2%"
            />
            <MetricCard 
              title="Daily Alerts" 
              value={systemMetrics.today_alerts} 
              change="-1%"
            />
          </div>
        </div>

        {/* Satellite Dashboard */}
        <div className="bg-white rounded-xl shadow p-6">
          <h2 className="text-xl font-semibold mb-4">Satellite Management</h2>
          <SatelliteDashboard adminMode={true} />
        </div>
      </div>
    </div>
  );
};

// Composant réutilisable pour les métriques
const MetricCard = ({ title, value, change }) => (
  <div className="bg-gray-50 p-4 rounded-lg border border-gray-200">
    <h3 className="text-sm font-medium text-gray-500">{title}</h3>
    <div className="flex items-end mt-1">
      <p className="text-2xl font-bold mr-2">{value}</p>
      <span className={`text-sm ${
        change.startsWith('+') ? 'text-green-500' : 'text-red-500'
      }`}>
        {change}
      </span>
    </div>
  </div>
);

export default AdminDashboard;