import React, { useEffect, useState } from 'react';
import { Navigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { checkSessionStatus } from '../api/api';

const ProtectedRoute = ({ children, adminOnly = false }) => {
  const { auth, loading } = useAuth();
  const [sessionValid, setSessionValid] = useState(null);

  useEffect(() => {
    const verifySession = async () => {
      try {
        const response = await checkSessionStatus();
        console.log('Session status response:', response.data); // Debug log
        setSessionValid(response.data.authenticated);
      } catch (err) {
        console.error('Session verification failed:', err.response?.data || err.message);
        setSessionValid(false);
      }
    };
    if (!loading) {
      verifySession();
    }
  }, [loading]);

  if (loading || sessionValid === null) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-center">
          <div className="spinner-border animate-spin inline-block w-8 h-8 border-4 rounded-full" role="status">
            <span className="visually-hidden">Loading...</span>
          </div>
          <p className="mt-2">Verifying session...</p>
        </div>
      </div>
    );
  }

  if (!auth || !sessionValid) {
    return <Navigate to="/login" replace />;
  }

  if (adminOnly && !auth.isSuperuser) {
    return <Navigate to="/dashboard" replace />;
  }

  return children;
};

export default ProtectedRoute;