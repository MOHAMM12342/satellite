// components/SecuritySettings.js
import React, { useState } from 'react';
import axios from 'axios';

const SecuritySettings = () => {
  const [qrCode, setQrCode] = useState('');
  const [is2faEnabled, setIs2faEnabled] = useState(false);

  const setup2FA = async () => {
    const response = await axios.post('/api/setup-2fa/');
    setQrCode(response.data.qr_code);
  };

  return (
    <div>
      <h3>Sécurité</h3>
      {is2faEnabled ? (
        <button onClick={() => setIs2faEnabled(false)}>
          Désactiver la 2FA
        </button>
      ) : (
        <>
          <button onClick={setup2FA}>Activer la 2FA</button>
          {qrCode && <img src={qrCode} alt="QR Code" />}
        </>
      )}
    </div>
  );
};