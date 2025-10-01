import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import api from '../api/api';
import img from "../images/logo.jpeg"

const Login = () => {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [remember, setRemember] = useState(false);
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const { login, setTwoFactorPending } = useAuth();
  const navigate = useNavigate();

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError('');

    try {
      const response = await api.post('/api/auth/login/', { username, password, remember });
      console.log('Login response:', response.data); // Debug log
      if (response.data.status === '2fa_required') {
        setTwoFactorPending({
          user_id: response.data.user_id,
          remember: response.data.remember
        });
        navigate('/2fa');
      } else if (response.data.user) {
        login(
          response.data.user.username,
          response.data.user.is_superuser,
          remember
        );
        navigate(response.data.user.is_superuser ? '/admin-dashboard' : '/dashboard');
      } else {
        setError('Unexpected response from server');
      }
    } catch (err) {
      console.error('Login error:', err.response?.data); // Debug log
      setError(err.response?.data?.error || 'Login failed');
    } finally {
      setLoading(false);
    }
  };

  return (
   <div
  style={{
    backgroundImage: `url(${img})`,
    backgroundSize: "cover",
    backgroundPosition: "center",
    minHeight: "100vh",
  }}
  className="min-h-screen flex items-center justify-center relative"
>
  {/* Transparent overlay */}
  <div className="absolute inset-0 bg-black/50 backdrop-blur-sm"></div>

  {/* Login card (sits on top of overlay) */}
  <div className="relative z-10 bg-white p-8 rounded-lg shadow-md w-full max-w-md">
    <h2 className="text-2xl font-bold text-center mb-6">Satellite Data System</h2>
    
    {error && (
      <div className="mb-4 p-3 bg-red-100 text-red-700 rounded">{error}</div>
    )}
    
    <form onSubmit={handleSubmit}>
      <div className="mb-4">
        <label className="block text-sm font-medium mb-1">Username</label>
        <input
          type="text"
          value={username}
          onChange={(e) => setUsername(e.target.value)}
          className="w-full p-2 border rounded"
          required
        />
      </div>

      <div className="mb-4">
        <label className="block text-sm font-medium mb-1">Password</label>
        <input
          type="password"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          className="w-full p-2 border rounded"
          required
        />
      </div>

      <div className="mb-4 flex items-center">
        <input
          type="checkbox"
          checked={remember}
          onChange={() => setRemember(!remember)}
          className="mr-2"
        />
        <label>Remember me</label>
      </div>

      <button
        type="submit"
        disabled={loading}
        className="w-full bg-blue-600 text-white py-2 rounded hover:bg-blue-700 disabled:bg-blue-400"
      >
        {loading ? "Logging in..." : "Login"}
      </button>
    </form>
  </div>
</div>

  );
};

export default Login;