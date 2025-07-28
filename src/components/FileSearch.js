// src/components/FileSearch.js
import React, { useState, useEffect } from 'react';
import { useAuth } from '../context/AuthContext';
import api from '../api/api';

const FileSearch = ({ onSearchResults, onSelectResult }) => {
  const { auth } = useAuth();
  const [satellites, setSatellites] = useState([]);
  const [loading, setLoading] = useState(false);
  const [searchParams, setSearchParams] = useState({
    satellite_id: '',
    subsystem_id: '',
    file_id: ''
  });

  // Fetch satellites on component mount
  useEffect(() => {
    if (!auth) return;
    
    const fetchSatellites = async () => {
      try {
        const response = await api.get('/api/satellites/');
        setSatellites(response.data.data.satellites || []);
      } catch (err) {
        console.error("Failed to fetch satellites:", err);
      }
    };

    fetchSatellites();
  }, [auth]);

  const handleInputChange = (e) => {
    const { name, value } = e.target;
    setSearchParams(prev => ({
      ...prev,
      [name]: value
    }));
  };

  const handleSearch = async (e) => {
    e.preventDefault();
    if (!auth) return;
    
    setLoading(true);
    
    try {
      // For now, we'll simulate a search response since the API endpoint might not exist yet
      // This will be replaced with the actual API call when it's ready
      
      // Simulated search results
      const simulatedResults = [];
      
      if (searchParams.satellite_id || searchParams.subsystem_id || searchParams.file_id) {
        // Add sample results - these will be replaced with real results from API
        simulatedResults.push({
          satellite_id: parseInt(searchParams.satellite_id) || 2,
          satellite_name: searchParams.satellite_id === "1" ? "UM5-EOSAT" : "MOHAMMEDIA-SAT",
          subsystem_id: parseInt(searchParams.subsystem_id) || 6,
          file_id: parseInt(searchParams.file_id) || 14,
          updated_date: "2025-03-15 10:42:17"
        });
      }
      
      onSearchResults(simulatedResults);
      
    } catch (err) {
      console.error("Search error:", err);
      onSearchResults([]);
    } finally {
      setLoading(false);
    }
  };

  const clearSearch = () => {
    setSearchParams({
      satellite_id: '',
      subsystem_id: '',
      file_id: ''
    });
    onSearchResults(null);
  };

  return (
    <div className="bg-white rounded-xl shadow p-6 mb-6">
      <h2 className="text-xl font-semibold text-gray-800 mb-4">Search Files</h2>
      
      <form onSubmit={handleSearch} className="space-y-4">
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          {/* Satellite Selection */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Satellite
            </label>
            <select
              name="satellite_id"
              value={searchParams.satellite_id}
              onChange={handleInputChange}
              className="w-full p-2 border border-gray-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500"
            >
              <option value="">All Satellites</option>
              {satellites.map((sat) => (
                <option key={sat.id} value={sat.id}>
                  {sat.name}
                </option>
              ))}
            </select>
          </div>
          
          {/* Subsystem Input */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Subsystem ID
            </label>
            <input
              type="text"
              name="subsystem_id"
              value={searchParams.subsystem_id}
              onChange={handleInputChange}
              placeholder="e.g., 6"
              className="w-full p-2 border border-gray-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500"
            />
          </div>
          
          {/* File Name Input */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              File ID
            </label>
            <input
              type="text"
              name="file_id"
              value={searchParams.file_id}
              onChange={handleInputChange}
              placeholder="e.g., 14"
              className="w-full p-2 border border-gray-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500"
            />
          </div>
        </div>
        
        {/* Search Instructions */}
        <div className="text-sm text-gray-500 italic">
          <p>Search tips:</p>
          <ul className="list-disc list-inside ml-2">
            <li>Select a satellite or leave blank to search all satellites</li>
            <li>Enter the subsystem ID (numeric value)</li>
            <li>Enter the file ID (numeric value)</li>
            <li>You can search with any combination of these fields</li>
          </ul>
        </div>
        
        {/* Buttons */}
        <div className="flex justify-end space-x-4">
          <button
            type="button"
            onClick={clearSearch}
            className="py-2 px-4 border border-gray-300 rounded-md shadow-sm text-sm font-medium text-gray-700 hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
          >
            Clear
          </button>
          <button
            type="submit"
            disabled={loading}
            className={`py-2 px-4 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 ${
              loading ? 'opacity-50 cursor-not-allowed' : ''
            }`}
          >
            {loading ? 'Searching...' : 'Search'}
          </button>
        </div>
      </form>
    </div>
  );
};

export default FileSearch;