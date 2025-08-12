import React, { useState, useCallback, useEffect } from 'react';
import './App.css';
import { SidebarPatients } from './components/SidebarPatients';
import SearchBar from './components/SearchBar';
import { EncounterDetails } from './components/EncounterDetails';
import { useTheme } from 'next-themes';
import { usePatientList } from './hooks/usePatientList';
import { usePatientData, Patient } from './hooks/usePatientData';

function App() {
  const { theme, setTheme } = useTheme();
  const isDark = theme === 'dark';
  const toggleTheme = () => setTheme(isDark ? 'light' : 'dark');

  // Patient list management
  const {
    patients,
    loading: patientsLoading,
    error: patientsError,
    hasNextPage,
    hasPrevPage,
    handleNextPage,
    handlePrevPage,
    pageSize
  } = usePatientList();

  // Patient data management
  const {
    loading: patientDataLoading,
    error: patientDataError,
    currentPatient,
    patientSummary,
    encounters,
    encounterData,
    fetchPatientData,
    fetchEncounterData,
    clearData,
    getEncounterData
  } = usePatientData();

  // Local state
  const [selectedEncounterId, setSelectedEncounterId] = useState<string | null>(null);
  const [showSearchOverlay, setShowSearchOverlay] = useState(false);

  // Handle patient selection
  const handlePatientSelect = useCallback(async (patient: Patient) => {
    setSelectedEncounterId(null);
    await fetchPatientData(patient);
  }, [fetchPatientData]);

  // Handle encounter selection
  const handleEncounterSelect = useCallback(async (encounterId: string) => {
    if (!currentPatient) return;
    
    if (encounterId === selectedEncounterId) {
      setSelectedEncounterId(null);
      return;
    }
    
    setSelectedEncounterId(encounterId);
    
    // Fetch encounter data if not already cached
    const existingData = getEncounterData(encounterId);
    if (!existingData) {
      await fetchEncounterData(currentPatient.id, encounterId);
    }
  }, [currentPatient, selectedEncounterId, fetchEncounterData, getEncounterData]);

  // Auto-select first encounter when encounters load
  useEffect(() => {
    if (encounters.length > 0 && !selectedEncounterId) {
      const firstEncounter = encounters[0];
      handleEncounterSelect(firstEncounter.id);
    }
  }, [encounters, selectedEncounterId, handleEncounterSelect]);

  // Handle search
  const handleSearch = useCallback((query: string) => {
    // Search functionality is handled by SearchBar component
    console.log('Search query:', query);
  }, []);

  const loading = patientsLoading || patientDataLoading;
  const error = patientsError || patientDataError;

  return (
    <div className="App">
      <h1>EHR Patient Viewer</h1>
      
      {error && (
        <div style={{ 
          color: 'red', 
          padding: '10px', 
          backgroundColor: '#ffebee', 
          borderRadius: '4px', 
          margin: '10px 0' 
        }}>
          {error}
        </div>
      )}
      
      <SearchBar 
        apiBase={process.env.REACT_APP_API_URL || 'http://localhost:8000'} 
        onPickPatient={handlePatientSelect} 
      />

      <div style={{ display: 'flex', alignItems: 'flex-start', gap: '2rem' }}>
        {/* Patient List */}
        <div style={{ minWidth: '300px', width: '320px' }}>
          {loading && <div>Loading...</div>}
          <SidebarPatients
            patients={patients}
            selectedId={currentPatient?.id}
            onSelect={handlePatientSelect}
            renderItem={(p: Patient) => (
              <div>
                <div className="font-semibold">{p.family_name}</div>
                <div className="text-xs text-gray-500 dark:text-neutral-400">
                  {p.gender} • {p.birth_date} • {p.identifier}
                </div>
              </div>
            )}
          />
          
          {/* Pagination Controls */}
          <div className="mt-3 flex items-center gap-2">
            <button
              onClick={handlePrevPage}
              disabled={!hasPrevPage}
              className={`px-3 py-1 rounded border ${
                !hasPrevPage ? 'opacity-50 cursor-not-allowed' : 'hover:bg-gray-50 dark:hover:bg-neutral-800'
              }`}
            >
              Prev
            </button>
            <button
              onClick={handleNextPage}
              disabled={!hasNextPage}
              className={`px-3 py-1 rounded border ${
                !hasNextPage ? 'opacity-50 cursor-not-allowed' : 'hover:bg-gray-50 dark:hover:bg-neutral-800'
              }`}
            >
              Next
            </button>
            <div className="text-xs text-gray-500 ml-2">
              Page size: {pageSize}
            </div>
          </div>
        </div>

        {/* Patient Details */}
        <div style={{ flex: 1 }}>
          {currentPatient && patientSummary && (
            <div>
              {/* Patient Information Table */}
              <table style={{ 
                width: '100%', 
                borderCollapse: 'collapse', 
                marginBottom: '20px' 
              }}>
                <tbody>
                  <tr>
                    <td style={{ padding: '8px', border: '1px solid #ddd', fontWeight: 'bold' }}>ID</td>
                    <td style={{ padding: '8px', border: '1px solid #ddd' }}>{currentPatient.id}</td>
                  </tr>
                  <tr>
                    <td style={{ padding: '8px', border: '1px solid #ddd', fontWeight: 'bold' }}>Name</td>
                    <td style={{ padding: '8px', border: '1px solid #ddd' }}>{currentPatient.family_name}</td>
                  </tr>
                  <tr>
                    <td style={{ padding: '8px', border: '1px solid #ddd', fontWeight: 'bold' }}>Gender</td>
                    <td style={{ padding: '8px', border: '1px solid #ddd' }}>{currentPatient.gender}</td>
                  </tr>
                  <tr>
                    <td style={{ padding: '8px', border: '1px solid #ddd', fontWeight: 'bold' }}>Birth Date</td>
                    <td style={{ padding: '8px', border: '1px solid #ddd' }}>{currentPatient.birth_date}</td>
                  </tr>
                  <tr>
                    <td style={{ padding: '8px', border: '1px solid #ddd', fontWeight: 'bold' }}>Race</td>
                    <td style={{ padding: '8px', border: '1px solid #ddd' }}>{currentPatient.race}</td>
                  </tr>
                  <tr>
                    <td style={{ padding: '8px', border: '1px solid #ddd', fontWeight: 'bold' }}>Ethnicity</td>
                    <td style={{ padding: '8px', border: '1px solid #ddd' }}>{currentPatient.ethnicity}</td>
                  </tr>
                  <tr>
                    <td style={{ padding: '8px', border: '1px solid #ddd', fontWeight: 'bold' }}>Birth Sex</td>
                    <td style={{ padding: '8px', border: '1px solid #ddd' }}>{currentPatient.birth_sex}</td>
                  </tr>
                  <tr>
                    <td style={{ padding: '8px', border: '1px solid #ddd', fontWeight: 'bold' }}>Identifier</td>
                    <td style={{ padding: '8px', border: '1px solid #ddd' }}>{currentPatient.identifier}</td>
                  </tr>
                  <tr>
                    <td style={{ padding: '8px', border: '1px solid #ddd', fontWeight: 'bold' }}>Marital Status</td>
                    <td style={{ padding: '8px', border: '1px solid #ddd' }}>{currentPatient.marital_status}</td>
                  </tr>
                  <tr>
                    <td style={{ padding: '8px', border: '1px solid #ddd', fontWeight: 'bold' }}>Deceased Date</td>
                    <td style={{ padding: '8px', border: '1px solid #ddd' }}>{currentPatient.deceased_date || 'N/A'}</td>
                  </tr>
                  <tr>
                    <td style={{ padding: '8px', border: '1px solid #ddd', fontWeight: 'bold' }}>Managing Org</td>
                    <td style={{ padding: '8px', border: '1px solid #ddd' }}>{currentPatient.managing_organization}</td>
                  </tr>
                  <tr>
                    <td style={{ padding: '8px', border: '1px solid #ddd', fontWeight: 'bold' }}>Allergies</td>
                    <td style={{ padding: '8px', border: '1px solid #ddd' }}>
                      {currentPatient.allergies && currentPatient.allergies.length > 0 ? (
                        <ul style={{ margin: 0, paddingLeft: '20px' }}>
                          {currentPatient.allergies.map((allergy, index) => (
                            <li key={allergy.id} style={{ marginBottom: '4px' }}>
                              <strong>{allergy.code_display}</strong>
                              {allergy.clinical_status && ` (${allergy.clinical_status})`}
                              {allergy.criticality && ` - ${allergy.criticality}`}
                              {allergy.note && ` - ${allergy.note}`}
                            </li>
                          ))}
                        </ul>
                      ) : (
                        'None known'
                      )}
                    </td>
                  </tr>
                </tbody>
              </table>

              {/* Encounters List */}
              <div className="mb-4">
                <h2 className="text-lg font-semibold mb-2">Encounters</h2>
                <ul className="divide-y divide-gray-200 dark:divide-neutral-800 rounded-lg border border-gray-200 dark:border-neutral-800 overflow-hidden">
                  {encounters.map((encounter, idx) => (
                    <EncounterDetails
                      key={encounter.id}
                      encounter={encounter}
                      encounterData={getEncounterData(encounter.id)}
                      isSelected={selectedEncounterId === encounter.id}
                      onSelect={handleEncounterSelect}
                      index={idx}
                    />
                  ))}
                  {encounters.length === 0 && (
                    <li className="p-3 text-sm text-gray-500">No encounters</li>
                  )}
                </ul>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

export default App;