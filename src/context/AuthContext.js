import React, { createContext, useState, useEffect, useContext } from 'react';
import api from '../api/api';

const AuthContext = createContext();

export const AuthProvider = ({ children }) => {
  const [auth, setAuth] = useState(null);
  const [twoFactorPending, setTwoFactorPending] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const checkAuthStatus = async () => {
      try {
        const response = await api.checkSessionStatus();
        if (response.data.authenticated) {
          setAuth({
            username: localStorage.getItem('username') || sessionStorage.getItem('username'),
            isSuperuser: (localStorage.getItem('isSuperuser') || sessionStorage.getItem('isSuperuser')) === 'true'
          });
        }
      } catch (err) {
        setAuth(null);
      } finally {
        setLoading(false);
      }
    };
    checkAuthStatus();
  }, []);

  const login = (username, isSuperuser, remember) => {
    const storage = remember ? localStorage : sessionStorage;
    storage.setItem('username', username);
    storage.setItem('isSuperuser', isSuperuser);
    setAuth({ username, isSuperuser });
  };

  const logout = () => {
    localStorage.removeItem('username');
    localStorage.removeItem('isSuperuser');
    sessionStorage.removeItem('username');
    sessionStorage.removeItem('isSuperuser');
    setAuth(null);
    setTwoFactorPending(null);
  };

  return (
    <AuthContext.Provider value={{ 
      auth, 
      twoFactorPending,
      login, 
      logout,
      loading,
      setTwoFactorPending
    }}>
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => useContext(AuthContext);