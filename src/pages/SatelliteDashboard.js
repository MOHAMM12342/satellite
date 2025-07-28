import React, { useState, useEffect } from "react";
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import api, { checkSessionStatus } from '../api/api';
import TwoFactorSetup from '../components/TowFactorSetup';

const SatelliteDashboard = ({ adminMode = false }) => {
  const { auth, loading: authLoading } = useAuth();
  const navigate = useNavigate();

  // States for satellite data
  const [satellites, setSatellites] = useState([]);
  const [selectedSatellite, setSelectedSatellite] = useState(null);
  const [subsystems, setSubsystems] = useState([]);
  const [selectedSubsystem, setSelectedSubsystem] = useState(null);
  const [files, setFiles] = useState([]);
  const [fileVersions, setFileVersions] = useState({});
  const [metadata, setMetadata] = useState(null);
  const [loading, setLoading] = useState({
    satellites: false,
    subsystems: false,
    files: false,
    versions: false
  });
  const [error, setError] = useState(null);
  const [requires2FASetup, setRequires2FASetup] = useState(false);

  // Redirect if not authenticated
  useEffect(() => {
    if (!authLoading && !auth) {
      console.log('No auth, redirecting to /login'); // Debug log
      navigate('/login', { replace: true });
    }
  }, [auth, authLoading, navigate]);

  // Check 2FA status
  useEffect(() => {
    const check2FAStatus = async () => {
      try {
        const response = await api.get('/account/two_factor/');
        console.log('2FA status:', response.data); // Debug log
        if (response.data.required && !response.data.enabled) {
          setRequires2FASetup(true);
        }
      } catch (error) {
        console.error('2FA check failed:', error.response?.data || error.message);
      }
    };

    if (auth) {
      check2FAStatus();
    }
  }, [auth]);

  // Check session status periodically
  useEffect(() => {
    if (!auth || requires2FASetup) return;

    const interval = setInterval(async () => {
      console.log('Checking session status...'); // Debug log
      try {
        const response = await checkSessionStatus();
        console.log('Session status response:', response.data); // Debug log
        if (!response.data.authenticated) {
          console.log('Session invalid, redirecting to /login');
          navigate('/login', { replace: true });
        }
      } catch (err) {
        console.error('Session check failed:', err.response?.data || err.message);
        navigate('/login', { replace: true });
      }
    }, 30000); // Check every 30 seconds

    return () => clearInterval(interval);
  }, [auth, requires2FASetup, navigate]);

  // Fetch satellites
  useEffect(() => {
    const fetchSatellites = async () => {
      setLoading(prev => ({...prev, satellites: true}));
      try {
        const response = await api.get('/api/satellites/');
        setSatellites(response.data.data?.satellites || []);
      } catch (err) {
        console.error('Fetch satellites failed:', err.response?.data || err.message);
        setError({ type: 'error', message: "Failed to fetch satellites list" });
      } finally {
        setLoading(prev => ({...prev, satellites: false}));
      }
    };

    if (auth && !requires2FASetup) {
      fetchSatellites();
    }
  }, [auth, requires2FASetup]);

  // Fetch subsystems when satellite is selected
  useEffect(() => {
    if (!selectedSatellite || requires2FASetup) return;

    const fetchSubsystems = async () => {
      setLoading(prev => ({...prev, subsystems: true}));
      setSelectedSubsystem(null);
      setFiles([]);
      setFileVersions({});
      
      try {
        const response = await api.get(
          `/api/satellites/${selectedSatellite}/subsystems/`
        );
        setSubsystems(response.data.subsystems?.map(item => item.id) || []);
      } catch (err) {
        console.error('Fetch subsystems failed:', err.response?.data || err.message);
        setError({ 
          type: 'error', 
          message: `Error: ${err.response?.data?.detail || err.message}`
        });
      } finally {
        setLoading(prev => ({...prev, subsystems: false}));
      }
    };

    fetchSubsystems();
  }, [selectedSatellite, requires2FASetup]);

  // Fetch files when subsystem is selected
  useEffect(() => {
    if (!selectedSatellite || !selectedSubsystem || requires2FASetup) return;

    const fetchFiles = async () => {
      setLoading(prev => ({...prev, files: true}));
      setFileVersions({});
      
      try {
        const response = await api.get(
          `/api/satellites/${selectedSatellite}/subsystems/${selectedSubsystem}/files/`
        );
        setFiles(response.data?.files || []);
      } catch (err) {
        console.error('Fetch files failed:', err.response?.data || err.message);
        setError({ 
          type: 'error', 
          message: `Failed to fetch files: ${err.response?.data?.detail || err.message}`
        });
      } finally {
        setLoading(prev => ({...prev, files: false}));
      }
    };

    fetchFiles();
  }, [selectedSatellite, selectedSubsystem, requires2FASetup]);

  // Fetch versions for a file
  const fetchVersions = async (fileId) => {
    if (!selectedSatellite || !selectedSubsystem || !fileId || requires2FASetup) return;

    setLoading(prev => ({...prev, versions: true}));
    setMetadata(null);
    
    try {
      const response = await api.get(
        `/api/satellites/${selectedSatellite}/subsystems/${selectedSubsystem}/files/${fileId}/`
      );
      
      setFileVersions(prev => ({
        ...prev,
        [fileId]: response.data.data || []
      }));
    } catch (err) {
        console.error('Fetch versions failed:', err.response?.data || err.message);
      setError({ type: 'error', message: "Failed to fetch file versions" });
    } finally {
      setLoading(prev => ({...prev, versions: false}));
    }
  };

  // Fetch metadata
  const fetchMetadata = async (fileId, fileVer) => {
    if (!selectedSatellite || !selectedSubsystem || !fileId || !fileVer || requires2FASetup) return;

    try {
      const response = await api.get(
        `/api/satellites/${selectedSatellite}/subsystems/${selectedSubsystem}/files/${fileId}/version/${fileVer}`
      );
      setMetadata(response.data.data);
    } catch (err) {
        console.error('Fetch metadata failed:', err.response?.data || err.message);
      setError({ type: 'error', message: "Failed to fetch metadata" });
    }
  };

  // Download file
  const downloadFile = async (fileId, fileVer) => {
    if (!selectedSatellite || !selectedSubsystem || !fileId || !fileVer || requires2FASetup) return;

    try {
      const response = await api.get(
        `/api/satellites/${selectedSatellite}/subsystems/${selectedSubsystem}/files/${fileId}/version/${fileVer}/download/`,
        { responseType: "blob" }
      );
      
      const blobUrl = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement("a");
      link.href = blobUrl;
      link.setAttribute("download", `sat${selectedSatellite}_sub${selectedSubsystem}_file${fileId}_v${fileVer}.bin`);
      document.body.appendChild(link);
      link.click();
      link.remove();
    } catch (err) {
        console.error('Download file failed:', err.response?.data || err.message);
      setError({ type: 'error', message: "Failed to download file" });
    }
  };

  // Handle 2FA setup completion
  const handle2FASetupComplete = () => {
    setRequires2FASetup(false);
  };

  if (requires2FASetup) {
    return <TwoFactorSetup onComplete={handle2FASetupComplete} />;
  }

  if (authLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-center">
          <div className="spinner-border animate-spin inline-block w-8 h-8 border-4 rounded-full" role="status">
            <span className="visually-hidden">Loading...</span>
          </div>
          <p className="mt-2">Verifying authentication...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-100 p-6">
      {!adminMode && (
        <div className="bg-space-blue text-white p-6 rounded-xl shadow-lg mb-6">
          <h1 className="text-3xl font-bold">Satellite Data Management</h1>
          <p className="text-accent-light mt-2">
            Interactive dashboard for satellite data exploration
          </p>
        </div>
      )}

      {/* Satellite Selection */}
      <div className="bg-white rounded-xl shadow p-6 mb-6">
        <h2 className="text-xl font-semibold text-gray-800 mb-4">Satellite Selection</h2>
        <div className="flex flex-col md:flex-row gap-4">
          <div className="flex-1">
            <label className="block text-sm font-medium text-gray-700 mb-1">Select Satellite</label>
            <select
              className="w-full p-2 border border-gray-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500"
              onChange={(e) => setSelectedSatellite(parseInt(e.target.value))}
              value={selectedSatellite || ""}
              disabled={loading.satellites}
            >
              <option value="" disabled>-- Select --</option>
              {satellites.map((sat) => (
                <option key={sat.id} value={sat.id}>
                  {sat.name} (ID: {sat.id})
                </option>
              ))}
            </select>
          </div>
          
          {selectedSatellite && (
            <div className="flex-1">
              <label className="block text-sm font-medium text-gray-700 mb-1">Select Subsystem</label>
              <select
                className="w-full p-2 border border-gray-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500"
                onChange={(e) => setSelectedSubsystem(parseInt(e.target.value))}
                value={selectedSubsystem || ""}
                disabled={loading.subsystems || !selectedSatellite}
              >
                <option value="" disabled>-- Select --</option>
                {subsystems.map((subId) => (
                  <option key={subId} value={subId}>
                    Subsystem {subId}
                  </option>
                ))}
              </select>
            </div>
          )}
        </div>
      </div>

      {/* Loading Indicators */}
      {loading.subsystems && (
        <div className="bg-white p-4 rounded-xl shadow mb-6">
          <p className="text-gray-600">Loading subsystems...</p>
          <div className="w-full bg-gray-200 rounded-full h-2.5 mt-2">
            <div className="bg-blue-600 h-2.5 rounded-full animate-pulse" style={{ width: '50%' }}></div>
          </div>
        </div>
      )}

      {/* Error Display */}
      {error && (
        <div className="bg-red-100 border-l-4 border-red-500 text-red-700 p-4 mb-6 rounded">
          <p>Le fichier ne contient aucune version!!</p>
        </div>
      )}

      {/* Files List */}
      {selectedSubsystem && files.length > 0 && (
        <div className="bg-white rounded-xl shadow overflow-hidden mb-6">
          <div className="px-6 py-4 border-b border-gray-200">
            <h2 className="text-xl font-semibold text-gray-800">Files in Subsystem {selectedSubsystem}</h2>
          </div>
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">File ID</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider" style={{ textAlign: 'center' }}>Actions</th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {files.map((file) => (
                  <React.Fragment key={file.file_id}>
                    <tr>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <div className="text-sm font-medium text-gray-900">File {file.file_id}</div>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-right text-sm font-medium" style={{ textAlign: 'center' }}>
                        <button
                          onClick={() => fetchVersions(file.file_id)}
                          className="text-blue-600 hover:text-blue-900 mr-3"
                          disabled={loading.versions}
                        >
                          {fileVersions[file.file_id] ? 'Hide Versions' : 'Show Versions'}
                        </button>
                      </td>
                    </tr>
                    
                    {/* Versions for this file */}
                    {fileVersions[file.file_id] && (
                      <tr>
                        <td colSpan="2" className="px-6 py-4 bg-gray-50">
                          <div className="ml-8">
                            <h4 className="text-sm font-medium text-gray-700 mb-2">Versions:</h4>
                            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                              {fileVersions[file.file_id].map((version) => (
                                <div key={version.file_ver} className="bg-gray-100 p-3 rounded-lg">
                                  <div className="flex justify-between items-start">
                                    <div>
                                      <span className="text-xs font-medium text-gray-500">Version:</span>
                                      <p className="text-sm font-semibold">{version.file_ver}</p>
                                    </div>
                                    <div className="flex space-x-2">
                                      <button
                                        onClick={() => fetchMetadata(file.file_id, version.file_ver)}
                                        className="text-green-600 hover:text-green-800 text-xs"
                                      >
                                        Metadata
                                      </button>
                                      <button
                                        onClick={() => downloadFile(file.file_id, version.file_ver)}
                                        className="text-purple-600 hover:text-purple-800 text-xs"
                                      >
                                        Download
                                      </button>
                                    </div>
                                  </div>
                                </div>
                              ))}
                            </div>
                          </div>
                        </td>
                      </tr>
                    )}
                  </React.Fragment>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Metadata Display */}
      {metadata && (
        <div className="bg-white rounded-xl shadow p-6">
          <div className="flex justify-between items-center mb-4">
            <h3 className="text-lg font-semibold text-gray-800">File Metadata</h3>
            <button
              onClick={() => setMetadata(null)}
              className="text-gray-500 hover:text-gray-700"
            >
              Close
            </button>
          </div>
          <div className="bg-gray-50 p-4 rounded-lg overflow-x-auto">
            <pre className="text-sm text-gray-800">{JSON.stringify(metadata, null, 2)}</pre>
          </div>
        </div>
      )}

      {/* Empty States */}
      {selectedSubsystem && !loading.files && files.length === 0 && (
        <div className="bg-white rounded-xl shadow p-6 text-center">
          <p className="text-gray-500">No files found for this subsystem</p>
        </div>
      )}
    </div>
  );
};

export default SatelliteDashboard;