import React, { useState, useEffect } from 'react';
import './App.css';
import ClinicalSearch from './components/ClinicalSearch';
import PatientList from './components/PatientList';
import PatientDetails from './components/PatientDetails';
import NotesDisplay from './components/NotesDisplay';
import ErrorBoundary from './components/ErrorBoundary';
import SystemMonitor from './components/SystemMonitor';
import { Patient, SearchResult, Note, Allergy } from './types';
import apiService from './services/apiService';
import config from './config';

// API configuration now handled by apiService

function App() {
  const [patients, setPatients] = useState<Patient[]>([]);
  const [allPatients, setAllPatients] = useState<Patient[]>([]);
  const [selectedPatient, setSelectedPatient] = useState<Patient | null>(null);
  const [loading, setLoading] = useState(false);
  const [allergies, setAllergies] = useState<Allergy[]>([]);
  const [allergiesLoading, setAllergiesLoading] = useState(false);
  const [notes, setNotes] = useState<Note[]>([]);
  const [notesLoading, setNotesLoading] = useState(false);
  const [selectedNote, setSelectedNote] = useState<Note | null>(null);
  const [isSearching, setIsSearching] = useState(false);
  const [isBackendReady, setIsBackendReady] = useState(false);
  const [backendStatus, setBackendStatus] = useState('Loading backend data...');

  // Load patients on mount with readiness polling and retry/backoff
  useEffect(() => {
    let cancelled = false;

    const sleep = (ms: number) => new Promise(res => setTimeout(res, ms));

    const fetchWithRetry = async () => {
      try {
        setLoading(true);

        // 1) Poll readiness up to 20s
        const start = Date.now();
        while (!cancelled && Date.now() - start < 20000) {
          try {
            const data = await apiService.checkBackendReadiness();
            if (data.ready) break;
          } catch {}
          await sleep(1000);
        }

        // 2) Fetch patients (API service handles retries)
        if (cancelled) return;
        
        const fetched = await apiService.getPatients(config.ui.patientListLimit);
        
        if (cancelled) return;
        setAllPatients(fetched); // Store all patients
        setPatients(fetched); // Initially show all patients
        if (fetched.length > 0) setSelectedPatient(fetched[0]);
        setIsBackendReady(true);
        setBackendStatus('Backend ready');
      } catch (error) {
        console.error('Error in fetchWithRetry:', error);
        setBackendStatus('Error loading data');
      } finally {
        if (!cancelled) setLoading(false);
      }
    };

    fetchWithRetry();

    return () => {
      cancelled = true;
    };
  }, []);

  // Poll backend readiness (only when not ready)
  useEffect(() => {
    if (isBackendReady) return; // Don't poll if already ready

    const pollBackendReadiness = async () => {
      try {
        const data = await apiService.checkBackendReadiness();
        if (data.ready) {
          setIsBackendReady(true);
          setBackendStatus('Backend ready');
          return true; // Signal to stop polling
        } else {
          setBackendStatus('Backend is warming up...');
          return false;
        }
      } catch (error) {
        console.error('Error polling backend readiness:', error);
        setIsBackendReady(false);
        setBackendStatus('Backend connection error');
        return false;
      }
    };

    let timeoutId: NodeJS.Timeout;
    const poll = async () => {
      const ready = await pollBackendReadiness();
      if (!ready && !isBackendReady) {
        timeoutId = setTimeout(poll, config.ui.pollingInterval);
      }
    };

    // Start polling
    poll();

    return () => {
      if (timeoutId) clearTimeout(timeoutId);
    };
  }, [isBackendReady]);

  // Load patient details when selected
  useEffect(() => {
    if (!selectedPatient || !isBackendReady) return;

    let cancelled = false;

    const fetchPatientDetails = async () => {
      try {
        setAllergiesLoading(true);
        setNotesLoading(true);

        // Fetch all patient details in parallel using API service
        const { allergies, notes } = await apiService.getPatientDetails(selectedPatient.id);
        
        // Only update state if component is still mounted and request wasn't cancelled
        if (!cancelled) {
          setAllergies(allergies);
          setNotes(notes);
        }
      } catch (error) {
        if (!cancelled) {
          console.error('Error fetching patient details:', error);
          // Set empty arrays on error
          setAllergies([]);
          setNotes([]);
        }
      } finally {
        if (!cancelled) {
          setAllergiesLoading(false);
          setNotesLoading(false);
        }
      }
    };

    fetchPatientDetails();

    return () => {
      cancelled = true;
    };
  }, [selectedPatient, isBackendReady]);

  // Handle search results
  const handleSearchResults = (results: SearchResult[]) => {
    setIsSearching(true);
    
    // Filter patients based on search results
    const patientIds = Array.from(new Set(results.map(result => result.patient_id)));
    const filteredPatients = allPatients.filter(patient => patientIds.includes(patient.id));
    
    setPatients(filteredPatients);
    
    // Select the first filtered patient if available
    if (filteredPatients.length > 0) {
      setSelectedPatient(filteredPatients[0]);
    }
  };

  // Clear search
  const clearSearch = () => {
    setIsSearching(false);
    setPatients(allPatients);
  };

  return (
    <ErrorBoundary>
      <div className="flex flex-col h-screen bg-gray-50">
      {/* Global Search Header */}
      <div className="bg-gradient-to-r from-blue-600 to-blue-800 shadow-lg">
        <div className="max-w-7xl mx-auto py-3">
          <div className="flex justify-center items-center">
            {/* Search Bar - Centered */}
            <ClinicalSearch 
              onSearchResults={handleSearchResults}
            />
          </div>
        </div>
      </div>

      {/* Main Content */}
      <div className="flex flex-1 overflow-hidden">
        {/* Patient List Sidebar */}
        {/* 
          CRITICAL ALIGNMENT NOTE:
          The "Patient Directory" title below MUST use the ehr-title-alignment CSS class
          to maintain alignment with the "EHR Patient Viewer" title in the header.
          DO NOT change this without updating both titles.
        */}
        <div className="w-1/3 bg-white shadow-lg border-r border-gray-200 flex flex-col">
          <div className="ehr-title-alignment border-b border-gray-200">
            <h2 className="text-lg font-semibold text-gray-900">Patient Directory</h2>
            {!isBackendReady && (
              <p className="text-sm text-gray-500 mt-1">{backendStatus}</p>
            )}
          </div>
          
          <div className="flex-1 overflow-y-auto">
            <PatientList
              patients={patients}
              selectedPatient={selectedPatient}
              onPatientSelect={setSelectedPatient}
              loading={loading}
              isSearching={isSearching}
              onClearSearch={clearSearch}
            />
          </div>
        </div>

        {/* Patient Details */}
        <div className="flex-1 flex flex-col transition-all duration-300">
          {selectedPatient ? (
            <>
              <PatientDetails
                patient={selectedPatient}
                allergies={allergies}
                allergiesLoading={allergiesLoading}
              />

              <NotesDisplay
                notes={notes}
                notesLoading={notesLoading}
                selectedNote={selectedNote}
                onNoteSelect={setSelectedNote}
                selectedPatient={selectedPatient}
              />
            </>
          ) : (
            <div className="flex-1 flex flex-col items-center justify-center text-gray-500 bg-gray-50">
              <div className="text-center">
                <svg className="mx-auto h-24 w-24 text-gray-300 mb-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1} d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" />
                </svg>
                <h3 className="text-lg font-medium text-gray-900 mb-2">No Patient Selected</h3>
                <p className="text-gray-600">Choose a patient from the directory to view their clinical data</p>
              </div>
            </div>
          )}
        </div>
      </div>
      
      {/* System Monitor */}
      <SystemMonitor />
    </div>
    </ErrorBoundary>
  );
}

export default App;