import React, { useState } from 'react';
import api from '../api/api';

const TwoFactorSetup = ({ onComplete }) => {
  const [qrCode, setQrCode] = useState('');
  const [token, setToken] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    const initialize2FA = async () => {
      try {
        const response = await api.get('/account/setup/');
        setQrCode(response.data.qr_code_url);
      } catch (err) {
        setError('Failed to initialize 2FA setup');
      }
    };
    initialize2FA();
  }, []);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError('');

    try {
      await api.post('/account/setup/', { token });
      onComplete();
    } catch (err) {
      setError(err.response?.data?.detail || 'Invalid verification code');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-100">
      <div className="bg-white p-8 rounded-lg shadow-md w-full max-w-md">
        <h2 className="text-2xl font-bold text-center mb-6">Setup Two-Factor Authentication</h2>
        
        {error && (
          <div className="mb-4 p-3 bg-red-100 text-red-700 rounded">
            {error}
          </div>
        )}

        {qrCode ? (
          <div className="text-center">
            <p className="mb-4">Scan this QR code with your authenticator app:</p>
            <img src={qrCode} alt="2FA QR Code" className="mx-auto mb-6" />
            
            <form onSubmit={handleSubmit}>
              <div className="mb-4">
                <label className="block text-sm font-medium mb-1">Verification Code</label>
                <input
                  type="text"
                  value={token}
                  onChange={(e) => setToken(e.target.value)}
                  className="w-full p-2 border rounded"
                  placeholder="6-digit code"
                  required
                />
              </div>
              <button
                type="submit"
                disabled={loading}
                className="w-full py-2 px-4 bg-blue-600 text-white rounded hover:bg-blue-700 disabled:bg-blue-400"
              >
                {loading ? 'Verifying...' : 'Complete Setup'}
              </button>
            </form>
          </div>
        ) : (
          <p>Loading 2FA setup...</p>
        )}
      </div>
    </div>
  );
};

export default TwoFactorSetup;