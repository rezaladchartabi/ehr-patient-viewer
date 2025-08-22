import React, { useState, useEffect, useRef } from 'react';
import apiService from '../services/apiService';
import config from '../config';

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

// SearchResponse interface removed - handled by apiService

interface Suggestion {
  text: string;
  type: 'exact' | 'category' | 'related';
  icon?: string;
}

interface ClinicalSearchProps {
  onSearchResults: (results: SearchResult[]) => void;
}

// API_BASE removed - using centralized apiService

const ClinicalSearch: React.FC<ClinicalSearchProps> = ({ onSearchResults }) => {
  const [query, setQuery] = useState('');
  const [loading, setLoading] = useState(false);
  const [suggestions, setSuggestions] = useState<Suggestion[]>([]);
  const [showSuggestions, setShowSuggestions] = useState(false);
  const [selectedSuggestionIndex, setSelectedSuggestionIndex] = useState(-1);
  const searchTimeoutRef = useRef<NodeJS.Timeout | null>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  // Generate suggestions based on query
  const generateSuggestions = (searchQuery: string): Suggestion[] => {
    if (!searchQuery.trim()) return [];
    
    const query = searchQuery.toLowerCase();
    const suggestions: Suggestion[] = [];
    
    // Add exact match
    suggestions.push({
      text: searchQuery,
      type: 'exact',
      icon: '🔍'
    });

    // Add category suggestions based on common medical terms
    const medicalCategories = [
      { prefix: 'med', suggestions: ['Medication', 'Medication Request', 'Medication Administration'] },
      { prefix: 'diag', suggestions: ['Diagnosis', 'Diagnostic Test', 'Diagnostic Report'] },
      { prefix: 'all', suggestions: ['Allergy', 'Allergy Intolerance', 'Allergic Reaction'] },
      { prefix: 'cond', suggestions: ['Condition', 'Medical Condition', 'Health Condition'] },
      { prefix: 'note', suggestions: ['Clinical Note', 'Progress Note', 'Discharge Note'] },
      { prefix: 'pat', suggestions: ['Patient', 'Patient Information', 'Patient Record'] },
      { prefix: 'enc', suggestions: ['Encounter', 'Medical Encounter', 'Visit'] },
      { prefix: 'obs', suggestions: ['Observation', 'Vital Signs', 'Lab Results'] }
    ];

    medicalCategories.forEach(category => {
      if (query.includes(category.prefix)) {
        category.suggestions.forEach(suggestion => {
          if (suggestion.toLowerCase().includes(query)) {
            suggestions.push({
              text: suggestion,
              type: 'category',
              icon: '📋'
            });
          }
        });
      }
    });

    // Add related terms
    const relatedTerms = [
      'Blood Pressure', 'Heart Rate', 'Temperature', 'Weight',
      'Aspirin', 'Ibuprofen', 'Acetaminophen', 'Antibiotics',
      'Diabetes', 'Hypertension', 'Asthma', 'Depression',
      'Emergency', 'Urgent Care', 'Primary Care', 'Specialist'
    ];

    relatedTerms.forEach(term => {
      if (term.toLowerCase().includes(query) && suggestions.length < 8) {
        suggestions.push({
          text: term,
          type: 'related',
          icon: '💊'
        });
      }
    });

    return suggestions.slice(0, 8); // Limit to 8 suggestions
  };

  // Handle input change with debounced suggestions
  const handleInputChange = (value: string) => {
    setQuery(value);
    setSelectedSuggestionIndex(-1);
    
    if (searchTimeoutRef.current) {
      clearTimeout(searchTimeoutRef.current);
    }

    if (value.trim()) {
      searchTimeoutRef.current = setTimeout(() => {
        const newSuggestions = generateSuggestions(value);
        setSuggestions(newSuggestions);
        setShowSuggestions(newSuggestions.length > 0);
      }, config.ui.debounceDelay);
    } else {
      setSuggestions([]);
      setShowSuggestions(false);
    }
  };

  // Handle suggestion click
  const handleSuggestionClick = (suggestion: Suggestion) => {
    setQuery(suggestion.text);
    setShowSuggestions(false);
    performSearch(suggestion.text);
  };

  // Handle keyboard navigation
  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (!showSuggestions) return;

    switch (e.key) {
      case 'ArrowDown':
        e.preventDefault();
        setSelectedSuggestionIndex(prev => 
          prev < suggestions.length - 1 ? prev + 1 : prev
        );
        break;
      case 'ArrowUp':
        e.preventDefault();
        setSelectedSuggestionIndex(prev => prev > 0 ? prev - 1 : -1);
        break;
      case 'Enter':
        e.preventDefault();
        if (selectedSuggestionIndex >= 0) {
          handleSuggestionClick(suggestions[selectedSuggestionIndex]);
        } else {
          performSearch(query);
        }
        break;
      case 'Escape':
        setShowSuggestions(false);
        setSelectedSuggestionIndex(-1);
        break;
    }
  };

  // Close suggestions when clicking outside
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (inputRef.current && !inputRef.current.contains(event.target as Node)) {
        setShowSuggestions(false);
        setSelectedSuggestionIndex(-1);
      }
    };

    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  // Perform search
  const performSearch = async (searchQuery: string) => {
    if (!searchQuery.trim()) {
      onSearchResults([]);
      return;
    }

    setLoading(true);
    setShowSuggestions(false);
    try {
      const searchResults = await apiService.performClinicalSearch(searchQuery, config.ui.searchResultsLimit);
      onSearchResults(searchResults);
    } catch (error) {
      console.error('Error performing search:', error);
      onSearchResults([]);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="clinical-search relative">
      {/* Search Input with Suggestions */}
      <div className="flex gap-3 relative" style={{ width: '40%', minWidth: '400px' }}>
        <div className="relative flex-1">
          <input
            ref={inputRef}
            type="text"
            value={query}
            onChange={(e) => handleInputChange(e.target.value)}
            onKeyDown={handleKeyDown}
            onFocus={() => query.trim() && suggestions.length > 0 && setShowSuggestions(true)}
            placeholder="Search medications, diagnoses, notes..."
            className="w-full px-6 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent text-base text-center placeholder-gray-500"
            style={{ width: '100%' }}
          />
          
          {/* Suggestions Dropdown */}
          {showSuggestions && suggestions.length > 0 && (
            <div className="absolute top-full left-0 right-0 mt-1 bg-white border border-gray-200 rounded-lg shadow-lg z-50 max-h-64 overflow-y-auto">
              {suggestions.map((suggestion, index) => (
                <div
                  key={index}
                  onClick={() => handleSuggestionClick(suggestion)}
                  className={`px-4 py-3 cursor-pointer hover:bg-gray-50 transition-colors ${
                    index === selectedSuggestionIndex ? 'bg-blue-50 border-l-4 border-blue-500' : ''
                  }`}
                >
                  <div className="flex items-center gap-3">
                    <span className="text-gray-400 text-base">{suggestion.icon}</span>
                    <span className="text-gray-900 text-base">{suggestion.text}</span>
                    {suggestion.type === 'exact' && (
                      <span className="ml-auto text-sm text-gray-500 bg-gray-100 px-2 py-1 rounded">
                        Exact
                      </span>
                    )}
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
        
        <button
          onClick={() => performSearch(query)}
          disabled={!query.trim()}
          className="px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:bg-gray-300 disabled:cursor-not-allowed font-medium text-base transition-colors"
        >
          Search
        </button>
      </div>

      {/* Loading State */}
      {loading && (
        <div className="text-center py-4">
          <div className="inline-block animate-spin rounded-full h-6 w-6 border-b-2 border-blue-600"></div>
          <p className="mt-2 text-sm text-gray-600">Searching...</p>
        </div>
      )}
    </div>
  );
};

export default ClinicalSearch;
