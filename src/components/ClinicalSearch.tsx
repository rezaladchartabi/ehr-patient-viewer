import React, { useState, useEffect, useRef } from 'react';

interface SearchResult {
  patient_id: string;
  resource_type: string;
  resource_id: string;
  content: string;
  timestamp: string;
  note_id: string;
  rank: number;
  matched_terms: string[];
}

interface SearchResponse {
  query: string;
  expanded_terms: string[];
  results: SearchResult[];
  total_count: number;
}

interface ClinicalSearchProps {
  onResultClick?: (result: SearchResult) => void;
  onPatientSelect?: (patientId: string) => void;
}

const API_BASE = process.env.REACT_APP_API_BASE_URL || 'https://ehr-backend-87r9.onrender.com';

const ClinicalSearch: React.FC<ClinicalSearchProps> = ({ onResultClick, onPatientSelect }) => {
  const [query, setQuery] = useState('');
  const [results, setResults] = useState<SearchResult[]>([]);
  const [loading, setLoading] = useState(false);

  // Perform search
  const performSearch = async (searchQuery: string) => {
    if (!searchQuery.trim()) {
      setResults([]);
      return;
    }

    setLoading(true);
    try {
      const params = new URLSearchParams({
        q: searchQuery,
        limit: '50'
      });

      const response = await fetch(`${API_BASE}/clinical-search?${params}`);
      const data: SearchResponse = await response.json();
      
      setResults(data.results || []);
    } catch (error) {
      console.error('Error performing search:', error);
      setResults([]);
    } finally {
      setLoading(false);
    }
  };



  // Handle result click
  const handleResultClick = (result: SearchResult) => {
    if (onResultClick) {
      onResultClick(result);
    }
  };

  // Format timestamp
  const formatTimestamp = (timestamp: string) => {
    if (!timestamp) return 'Unknown';
    try {
      return new Date(timestamp).toLocaleDateString();
    } catch {
      return timestamp;
    }
  };

  // Get resource type display name
  const getResourceTypeDisplay = (type: string) => {
    const typeMap: { [key: string]: string } = {
      'note': 'Clinical Note',
      'medication-request': 'Medication Request',
      'medication-administration': 'Medication Administration',
      'condition': 'Condition',
      'patient': 'Patient'
    };
    return typeMap[type] || type;
  };

  // Get resource type color
  const getResourceTypeColor = (type: string) => {
    const colorMap: { [key: string]: string } = {
      'note': 'bg-blue-100 text-blue-800',
      'medication-request': 'bg-green-100 text-green-800',
      'medication-administration': 'bg-purple-100 text-purple-800',
      'condition': 'bg-orange-100 text-orange-800',
      'patient': 'bg-gray-100 text-gray-800'
    };
    return colorMap[type] || 'bg-gray-100 text-gray-800';
  };

  // Highlight matched terms in content
  const highlightContent = (content: string, matchedTerms: string[]) => {
    let highlightedContent = content;
    matchedTerms.forEach(term => {
      const regex = new RegExp(`(${term})`, 'gi');
      highlightedContent = highlightedContent.replace(regex, '<mark>$1</mark>');
    });
    return highlightedContent;
  };

  return (
    <div className="clinical-search">
      {/* Simple Search Input */}
      <div className="flex gap-3">
        <input
          type="text"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          onKeyPress={(e) => e.key === 'Enter' && performSearch(query)}
          placeholder="Search medications, diagnoses, notes..."
          className="flex-1 px-4 py-2.5 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent text-base"
        />
        <button
          onClick={() => performSearch(query)}
          disabled={!query.trim()}
          className="px-5 py-2.5 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:bg-gray-300 disabled:cursor-not-allowed font-medium transition-colors"
        >
          Search
        </button>
      </div>



      {/* Loading State */}
      {loading && (
        <div className="text-center py-8">
          <div className="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
          <p className="mt-2 text-gray-600">Searching clinical data...</p>
        </div>
      )}

      {/* Search Results */}
      {!loading && results.length > 0 && (
        <div className="mt-6">
          <div className="flex justify-between items-center mb-4">
            <h3 className="text-lg font-semibold text-gray-900">
              Found {results.length} results
            </h3>
            <button
              onClick={() => {
                setQuery('');
                setResults([]);
              }}
              className="text-sm text-gray-500 hover:text-gray-700"
            >
              Clear
            </button>
          </div>

          <div className="space-y-3">
            {results.map((result, index) => (
              <div
                key={index}
                onClick={() => handleResultClick(result)}
                className="bg-white border border-gray-200 rounded-lg p-4 hover:shadow-md cursor-pointer transition-shadow"
              >
                <div className="flex items-center justify-between mb-2">
                  <div className="flex items-center gap-2">
                    <span className={`px-2 py-1 text-xs rounded-full font-medium ${getResourceTypeColor(result.resource_type)}`}>
                      {getResourceTypeDisplay(result.resource_type)}
                    </span>
                    <span className="text-sm text-gray-600">Patient {result.patient_id}</span>
                  </div>
                  <span className="text-sm text-gray-500">
                    {formatTimestamp(result.timestamp)}
                  </span>
                </div>
                
                <div className="text-sm text-gray-700 line-clamp-3">
                  {result.content.length > 200 
                    ? result.content.substring(0, 200) + '...' 
                    : result.content}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* No Results */}
      {!loading && query && results.length === 0 && (
        <div className="text-center py-8">
          <p className="text-gray-500">No results found for "{query}"</p>
          <p className="text-sm text-gray-400 mt-2">
            Try different keywords or check spelling
          </p>
        </div>
      )}

      {/* Tips removed per request */}
    </div>
  );
};

export default ClinicalSearch;
