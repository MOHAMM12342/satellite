// src/pages/Dashboard.js
import React, { useState, useRef } from 'react';
import { useAuth } from '../context/AuthContext';
import SatelliteDashboard from './SatelliteDashboard';
import FileSearch from '../components/FileSearch';



const Dashboard = () => {
  const { auth } = useAuth();
  const [searchResults, setSearchResults] = useState(null);
  const [selectedResult, setSelectedResult] = useState(null);
  const satelliteDashboardRef = useRef(null);

  const handleViewClick = (result) => {
    // Set the selected satellite and subsystem
    setSelectedResult(result);
    
    // Scroll to the SatelliteDashboard component
    if (satelliteDashboardRef.current) {
      satelliteDashboardRef.current.scrollIntoView({ behavior: 'smooth' });
    }
  };

  return (
    <div className="min-h-screen bg-gray-100">
      {/* Header */}
      <div className="bg-space-blue text-white p-6 shadow-lg">
        <div className="container mx-auto">
          <h1 className="text-2xl font-bold">User Dashboard</h1>
          <p className="text-accent-light">
            Bienvenue, {auth?.username} | Access level: Standard
          </p>
        </div>
      </div>


      <div className="container mx-auto p-4">
        {/* Search Section */}
        <FileSearch onSearchResults={setSearchResults} />
        
        
        {/* Search Results (if any) */}
        {searchResults && searchResults.length > 0 && (
          <div className="mb-6">
            <h2 className="text-xl font-semibold text-gray-800 mb-4">Search Results</h2>
            <div className="bg-white rounded-xl shadow overflow-hidden">
              <table className="min-w-full divide-y divide-gray-200">
                <thead className="bg-gray-50">
                  <tr>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Satellite</th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Subsystem</th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">File ID</th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Last Updated</th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Actions</th>
                  </tr>
                </thead>
                <tbody className="bg-white divide-y divide-gray-200">
                  {searchResults.map((file) => (
                    <tr key={`${file.satellite_id}-${file.subsystem_id}-${file.file_id}`}>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <div className="text-sm text-gray-900">{file.satellite_name}</div>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <div className="text-sm text-gray-900">Subsystem {file.subsystem_id}</div>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <div className="text-sm font-medium text-gray-900">File {file.file_id}</div>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <div className="text-sm text-gray-500">{file.updated_date}</div>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                        <button 
                          onClick={() => handleViewClick(file)}
                          className="text-blue-600 hover:text-blue-900"
                        >
                          View
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}

        {/* Empty Search Results */}
        {searchResults && searchResults.length === 0 && (
          <div className="mb-6">
            <h2 className="text-xl font-semibold text-gray-800 mb-4">Search Results</h2>
            <div className="bg-white rounded-xl shadow p-4">
              <p className="text-gray-500 text-center py-4">No files found matching your search criteria.</p>
            </div>
          </div>
        )}

        {/* SatelliteDashboard */}
        <div ref={satelliteDashboardRef}>
          <SatelliteDashboard 
            initialSearchResults={searchResults} 
            selectedResult={selectedResult}
          />
        </div>
      </div>
    </div>
  );
};

export default Dashboard;