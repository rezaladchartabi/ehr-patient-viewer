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
  patientId?: string;
  onResultClick?: (result: SearchResult) => void;
}

const API_BASE = process.env.REACT_APP_API_BASE_URL || 'https://ehr-backend-87r9.onrender.com';

const ClinicalSearch: React.FC<ClinicalSearchProps> = ({ patientId, onResultClick }) => {
  const [query, setQuery] = useState('');
  const [suggestions, setSuggestions] = useState<string[]>([]);
  const [results, setResults] = useState<SearchResult[]>([]);
  const [loading, setLoading] = useState(false);
  const [showSuggestions, setShowSuggestions] = useState(false);
  const [expandedTerms, setExpandedTerms] = useState<string[]>([]);
  const [resourceType, setResourceType] = useState<string>('all');
  const searchTimeoutRef = useRef<number | null>(null);

  // Get search suggestions
  const getSuggestions = async (partialQuery: string) => {
    if (partialQuery.length < 2) {
      setSuggestions([]);
      return;
    }

    try {
      const response = await fetch(`${API_BASE}/clinical-search/suggestions?q=${encodeURIComponent(partialQuery)}&limit=10`);
      const data = await response.json();
      setSuggestions(data.suggestions || []);
    } catch (error) {
      console.error('Error getting suggestions:', error);
    }
  };

  // Perform search
  const performSearch = async (searchQuery: string) => {
    if (!searchQuery.trim()) {
      setResults([]);
      setExpandedTerms([]);
      return;
    }

    setLoading(true);
    try {
      const params = new URLSearchParams({
        q: searchQuery,
        limit: '50'
      });

      if (patientId) {
        params.append('patient_id', patientId);
      }

      if (resourceType !== 'all') {
        params.append('resource_types', resourceType);
      }

      const response = await fetch(`${API_BASE}/clinical-search?${params}`);
      const data: SearchResponse = await response.json();
      
      setResults(data.results || []);
      setExpandedTerms(data.expanded_terms || []);
    } catch (error) {
      console.error('Error performing search:', error);
      setResults([]);
    } finally {
      setLoading(false);
    }
  };

  // Handle query changes with debouncing
  useEffect(() => {
    if (searchTimeoutRef.current) {
      clearTimeout(searchTimeoutRef.current);
    }

    if (query.trim()) {
      searchTimeoutRef.current = setTimeout(() => {
        performSearch(query);
        getSuggestions(query);
      }, 300);
    } else {
      setResults([]);
      setSuggestions([]);
      setExpandedTerms([]);
    }

    return () => {
      if (searchTimeoutRef.current) {
        clearTimeout(searchTimeoutRef.current);
      }
    };
  }, [query, patientId, resourceType]);

  // Handle suggestion click
  const handleSuggestionClick = (suggestion: string) => {
    setQuery(suggestion);
    setShowSuggestions(false);
    performSearch(suggestion);
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
      {/* Search Header */}
      <div className="mb-4">
        <h2 className="text-xl font-semibold mb-2">Clinical Search</h2>
        <p className="text-sm text-gray-600 mb-4">
          Search across medications, diagnoses, and clinical notes with intelligent synonym expansion
        </p>
      </div>

      {/* Search Input */}
      <div className="relative mb-4">
        <div className="flex gap-2 mb-2">
          <input
            type="text"
            value={query}
            onChange={(e) => {
              setQuery(e.target.value);
              setShowSuggestions(true);
            }}
            onFocus={() => setShowSuggestions(true)}
            placeholder="Search for medications, diagnoses, or keywords (e.g., VTE, heparin, DVT)..."
            className="flex-1 px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
          />
          <select
            value={resourceType}
            onChange={(e) => setResourceType(e.target.value)}
            className="px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
          >
            <option value="all">All Types</option>
            <option value="note">Clinical Notes</option>
            <option value="medication-request">Medication Requests</option>
            <option value="medication-administration">Medication Administration</option>
            <option value="condition">Conditions</option>
          </select>
        </div>

        {/* Search Suggestions */}
        {showSuggestions && suggestions.length > 0 && (
          <div className="absolute z-10 w-full bg-white border border-gray-300 rounded-lg shadow-lg max-h-60 overflow-y-auto">
            {suggestions.map((suggestion, index) => (
              <div
                key={index}
                onClick={() => handleSuggestionClick(suggestion)}
                className="px-4 py-2 hover:bg-gray-100 cursor-pointer border-b border-gray-100 last:border-b-0"
              >
                {suggestion}
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Expanded Terms */}
      {expandedTerms.length > 1 && (
        <div className="mb-4 p-3 bg-blue-50 rounded-lg">
          <p className="text-sm text-blue-800 mb-2">
            <strong>Search expanded to include:</strong>
          </p>
          <div className="flex flex-wrap gap-2">
            {expandedTerms.map((term, index) => (
              <span
                key={index}
                className="px-2 py-1 bg-blue-100 text-blue-800 text-xs rounded"
              >
                {term}
              </span>
            ))}
          </div>
        </div>
      )}

      {/* Loading State */}
      {loading && (
        <div className="text-center py-8">
          <div className="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
          <p className="mt-2 text-gray-600">Searching clinical data...</p>
        </div>
      )}

      {/* Search Results */}
      {!loading && results.length > 0 && (
        <div className="space-y-4">
          <div className="flex justify-between items-center">
            <h3 className="text-lg font-semibold">
              Search Results ({results.length})
            </h3>
            <button
              onClick={() => {
                setQuery('');
                setResults([]);
                setExpandedTerms([]);
              }}
              className="text-sm text-gray-500 hover:text-gray-700"
            >
              Clear
            </button>
          </div>

          {results.map((result, index) => (
            <div
              key={index}
              onClick={() => handleResultClick(result)}
              className="p-4 border border-gray-200 rounded-lg hover:bg-gray-50 cursor-pointer transition-colors"
            >
              <div className="flex justify-between items-start mb-2">
                <div className="flex items-center gap-2">
                  <span className="px-2 py-1 bg-blue-100 text-blue-800 text-xs rounded">
                    {getResourceTypeDisplay(result.resource_type)}
                  </span>
                  {result.note_id && (
                    <span className="text-sm text-gray-500">
                      {result.note_id}
                    </span>
                  )}
                </div>
                <span className="text-sm text-gray-500">
                  {formatTimestamp(result.timestamp)}
                </span>
              </div>

              <div className="mb-2">
                <p className="text-sm text-gray-600">
                  Patient: {result.patient_id}
                </p>
              </div>

              <div className="prose prose-sm max-w-none">
                <div
                  dangerouslySetInnerHTML={{
                    __html: highlightContent(
                      result.content.length > 300
                        ? result.content.substring(0, 300) + '...'
                        : result.content,
                      result.matched_terms
                    )
                  }}
                  className="text-sm leading-relaxed"
                />
              </div>

              {result.matched_terms.length > 0 && (
                <div className="mt-2 flex flex-wrap gap-1">
                  {result.matched_terms.map((term, termIndex) => (
                    <span
                      key={termIndex}
                      className="px-1 py-0.5 bg-yellow-100 text-yellow-800 text-xs rounded"
                    >
                      {term}
                    </span>
                  ))}
                </div>
              )}
            </div>
          ))}
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

      {/* Search Tips */}
      {!query && (
        <div className="mt-8 p-4 bg-gray-50 rounded-lg">
          <h4 className="font-semibold mb-2">Search Tips:</h4>
          <ul className="text-sm text-gray-600 space-y-1">
            <li>• <strong>VTE/DVT/PE:</strong> Automatically expands to include anticoagulants</li>
            <li>• <strong>Statin:</strong> Finds all statin medications</li>
            <li>• <strong>Brand names:</strong> Coumadin, Lovenox, Xarelto, etc.</li>
            <li>• <strong>Abbreviations:</strong> CHF, MI, COPD, DM, HTN</li>
            <li>• <strong>Full text:</strong> Search within clinical notes</li>
          </ul>
        </div>
      )}
    </div>
  );
};

export default ClinicalSearch;
