import axios from 'axios';

const API_BASE_URL = 'http://localhost:8000/';

const api = axios.create({
  baseURL: API_BASE_URL,
  withCredentials: true // Ensure session cookies are sent
});

api.interceptors.request.use(config => {
  //  CSRF token for POST, PUT, PATCH requests
  const csrfToken = document.cookie.match(/csrftoken=([^;]+)/)?.[1];
  if (['post', 'put', 'patch'].includes(config.method) && csrfToken) {
    config.headers['X-CSRFToken'] = csrfToken;
  }
  return config;
});

api.interceptors.response.use(
  response => response,
  error => {
    console.error('API error:', error.response?.status, error.response?.data); // Debug log
    if (error.response?.status === 401) {
      console.log('Unauthorized, redirecting to /login');
      window.location.href = '/login';
    }
    return Promise.reject(error);
  }
);

export const checkSessionStatus = () => {
  console.log('Sending session status check request'); // Debug log
  return api.get('/api/auth/check-session-status/');
};

// Auth endpoints
export const fetchCsrfToken = async () => {
  await api.get('/api/auth/login/'); // Triggers CSRF cookie set
};
export const login = (credentials) => api.post('/api/auth/login/', credentials);
export const verify2FA = (data) => api.post('/api/auth/verify/', data);
export const setup2FA = () => api.get('/api/account/two_factor/setup/');
export const confirm2FASetup = (token) => api.post('/api/account/two_factor/setup/', { token });

// API endpoints
export const fetchSatellites = () => api.get('/api/satellites/');
export const fetchSubsystems = (satId) => api.get(`/api/satellites/${satId}/subsystems/`);
export const fetchFiles = (satId, subId) => api.get(`/api/satellites/${satId}/subsystems/${subId}/files/`);
export const fetchFileVersions = (satId, subId, fileId) => api.get(`/api/satellites/${satId}/subsystems/${subId}/files/${fileId}/`);
export const fetchFileMetadata = (satId, subId, fileId, fileVer) => api.get(`/api/satellites/${satId}/subsystems/${subId}/files/${fileId}/version/${fileVer}/`);
export const downloadFileVersion = (satId, subId, fileId, fileVer) => api.get(
  `/api/satellites/${satId}/subsystems/${subId}/files/${fileId}/version/${fileVer}/download/`,
  { responseType: 'blob' }
);

export default api;