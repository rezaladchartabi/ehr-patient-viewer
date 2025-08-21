import React, { useState, useEffect } from 'react';
import './App.css';
import ChatInterface from './components/ChatInterface';
import ClinicalSearch from './components/ClinicalSearch';

// Types
interface Patient {
  id: string;
  family_name: string;
  gender: string;
  birth_date: string;
  race?: string;
  ethnicity?: string;
  identifier?: string;
  marital_status?: string;
  allergies?: any[];
}

interface Encounter {
  id: string;
  status: string;
  start_date: string;
  end_date?: string;
  class_display: string;
  encounter_type: string;
}

interface ResourceData {
  medicationAdministrations: any[];
  observations: any[];
  medicationRequests: any[];
  specimens: any[];
  medicationDispenses: any[];
  conditions: any[];
}

const API_BASE = process.env.REACT_APP_API_BASE_URL || 'https://ehr-backend-87r9.onrender.com';

function App() {
  const [patients, setPatients] = useState<Patient[]>([]);
  const [selectedPatient, setSelectedPatient] = useState<Patient | null>(null);
  const [encounters, setEncounters] = useState<Encounter[]>([]);
  const [selectedEncounter, setSelectedEncounter] = useState<string>('all');
  const [resourceData, setResourceData] = useState<ResourceData>({
    medicationAdministrations: [],
    observations: [],
    medicationRequests: [],
    specimens: [],
    medicationDispenses: [],
    conditions: []
  });
  const [activeTab, setActiveTab] = useState('conditions');
  const [loading, setLoading] = useState(false);
  const [allergies, setAllergies] = useState<any[]>([]);
  const [allergiesLoading, setAllergiesLoading] = useState(false);
  const [pmh, setPmh] = useState<any[]>([]);
  const [pmhLoading, setPmhLoading] = useState(false);
  const [notes, setNotes] = useState<any[]>([]);
  const [notesLoading, setNotesLoading] = useState(false);
  const [selectedNote, setSelectedNote] = useState<any>(null);
  const [showChatbot, setShowChatbot] = useState(false);

  // Load patients on mount
  useEffect(() => {
    setLoading(true);
    
    // Fetch patients from local database
    fetch(`${API_BASE}/local/patients?limit=100`)
      .then(res => {
        if (!res.ok) {
          throw new Error(`HTTP error! status: ${res.status}`);
        }
        return res.json();
      })
      .then(data => {
        const fetched = Array.isArray(data.patients) ? data.patients : [];
        setPatients(fetched);
        console.log(`✅ Loaded ${fetched.length} patients from local database`);
        
        // Auto-select first patient
        if (fetched.length > 0) {
          setSelectedPatient(fetched[0]);
        }
      })
      .catch(err => {
        console.error('❌ Error loading patients:', err);
        setPatients([]);
      })
      .finally(() => {
        setLoading(false);
      });
  }, []);

  // Load patient data when patient is selected
  useEffect(() => {
    if (!selectedPatient) return;
    
    setLoading(true);
    setAllergiesLoading(true);
    setPmhLoading(true);
    setNotesLoading(true);
    
    // Load encounters first
    fetch(`${API_BASE}/Encounter?patient=Patient/${selectedPatient.id}&_count=100`)
      .then(r => r.json())
      .then(encountersRes => {
        // Process encounters
        const encounterList = (encountersRes.entry || []).map((e: any) => ({
          id: e.resource.id,
          status: e.resource.status,
          start_date: e.resource.period?.start || '',
          end_date: e.resource.period?.end || '',
          class_display: e.resource.class?.display || e.resource.class?.code || '',
          encounter_type: e.resource.type?.[0]?.coding?.[0]?.display || ''
        }));
        
        setEncounters(encounterList);
        setSelectedEncounter('all');
        
        // Load all patient data (for "All Encounters" view)
        return Promise.all([
          fetch(`${API_BASE}/Condition?patient=Patient/${selectedPatient.id}&_count=100`).then(r => r.json()),
          fetch(`${API_BASE}/MedicationAdministration?patient=Patient/${selectedPatient.id}&_count=100`).then(r => r.json()),
          fetch(`${API_BASE}/Observation?patient=Patient/${selectedPatient.id}&_count=100`).then(r => r.json()),
          fetch(`${API_BASE}/MedicationRequest?patient=Patient/${selectedPatient.id}&_count=100`).then(r => r.json()),
          fetch(`${API_BASE}/Specimen?patient=Patient/${selectedPatient.id}&_count=100`).then(r => r.json()),
          fetch(`${API_BASE}/MedicationDispense?patient=Patient/${selectedPatient.id}&_count=100`).then(r => r.json())
        ]);
      })
      .then(([conditionsRes, medAdminRes, obsRes, medReqRes, specimenRes, medDispRes]) => {
        // Process all resource types for "All Encounters" view
        setResourceData({
          conditions: conditionsRes.entry || [],
          medicationAdministrations: medAdminRes.entry || [],
          observations: obsRes.entry || [],
          medicationRequests: medReqRes.entry || [],
          specimens: specimenRes.entry || [],
          medicationDispenses: medDispRes.entry || []
        });
        
        setLoading(false);
      })
      .catch(err => {
        console.error('Failed to load patient data:', err);
        setLoading(false);
      });

    // Load allergies separately
    fetch(`${API_BASE}/local/patients/${selectedPatient.id}/allergies`)
      .then(res => res.json())
      .then(data => {
        setAllergies(data.allergies || []);
        setAllergiesLoading(false);
      })
      .catch(err => {
        console.error('Failed to load allergies:', err);
        setAllergies([]);
        setAllergiesLoading(false);
      });

    // Load Past Medical History separately
    fetch(`${API_BASE}/local/patients/${selectedPatient.id}/pmh`)
      .then(res => res.json())
      .then(data => {
        setPmh(data.pmh_conditions || []);
        setPmhLoading(false);
      })
      .catch(err => {
        console.error('Failed to load PMH:', err);
        setPmh([]);
        setPmhLoading(false);
      });

    // Load Notes separately from Excel file with timestamp information
    fetch(`${API_BASE}/local/patients/${selectedPatient.id}/notes/with-timestamps`)
      .then(res => res.json())
      .then(data => {
        setNotes(data.notes || []);
        setNotesLoading(false);
      })
      .catch(err => {
        console.error('Failed to load notes:', err);
        setNotes([]);
        setNotesLoading(false);
      });
  }, [selectedPatient]);

  // Load encounter-specific data when encounter is selected
  useEffect(() => {
    if (!selectedPatient || selectedEncounter === 'all') return;
    
    setLoading(true);
    
    const encounter = encounters.find(e => e.id === selectedEncounter);
    if (!encounter) {
      setLoading(false);
      return;
    }
    
    // Make API calls to encounter-specific endpoints
    Promise.all([
      fetch(`${API_BASE}/encounter/medications?patient=Patient/${selectedPatient.id}&encounter=Encounter/${selectedEncounter}&start=${encounter.start_date}&end=${encounter.end_date || ''}`).then(r => r.json()),
      fetch(`${API_BASE}/encounter/observations?patient=Patient/${selectedPatient.id}&encounter=Encounter/${selectedEncounter}&start=${encounter.start_date}&end=${encounter.end_date || ''}`).then(r => r.json()),
      fetch(`${API_BASE}/encounter/procedures?patient=Patient/${selectedPatient.id}&encounter=Encounter/${selectedEncounter}&start=${encounter.start_date}&end=${encounter.end_date || ''}`).then(r => r.json()),
      fetch(`${API_BASE}/encounter/specimens?patient=Patient/${selectedPatient.id}&encounter=Encounter/${selectedEncounter}&start=${encounter.start_date}&end=${encounter.end_date || ''}`).then(r => r.json())
    ])
    .then(([medicationsRes, observationsRes, proceduresRes, specimensRes]) => {
      // Process encounter-specific data
      setResourceData({
        conditions: [], // Conditions are typically not encounter-specific
        medicationAdministrations: medicationsRes.administrations || [],
        observations: observationsRes.observations || [],
        medicationRequests: medicationsRes.requests || [],
        specimens: specimensRes.specimens || [],
        medicationDispenses: medicationsRes.dispenses || []
      });
      
      setLoading(false);
    })
    .catch(err => {
      console.error('Failed to load encounter data:', err);
      setLoading(false);
    });
  }, [selectedEncounter, selectedPatient, encounters]);

    // No longer need client-side filtering since we use server-side API calls

  // Format different resource types for display
  const formatResource = (item: any, resourceType: string) => {
    const resource = item.resource;
    
    switch (resourceType) {
      case 'conditions':
        return (
          <div className="resource-item">
            <div className="resource-title">
              {resource.code?.text || resource.code?.coding?.[0]?.display || 'Unknown Condition'}
            </div>
            <div className="resource-details">
              <span className="detail-item">Status: {resource.clinicalStatus?.coding?.[0]?.code || 'Unknown'}</span>
              <span className="detail-item">Category: {resource.category?.[0]?.coding?.[0]?.display || 'N/A'}</span>
              <span className="detail-item">Recorded: {resource.recordedDate || 'N/A'}</span>
              {resource.code?.coding?.[0]?.code && (
                <span className="detail-item">Code: {resource.code.coding[0].code}</span>
              )}
            </div>
          </div>
        );
        
      case 'medicationRequests':
        return (
          <div className="resource-item">
            <div className="resource-title">
              {resource.medicationCodeableConcept?.text || 
               resource.medicationCodeableConcept?.coding?.[0]?.display ||
               resource.medicationCodeableConcept?.coding?.[0]?.code ||
               resource.medicationReference?.display || 'Unknown Medication'}
            </div>
            <div className="resource-details">
              <span className="detail-item">Status: {resource.status || 'Unknown'}</span>
              <span className="detail-item">Intent: {resource.intent || 'N/A'}</span>
              <span className="detail-item">Authored: {resource.authoredOn || 'N/A'}</span>
              {resource.route_display && (
                <span className="detail-item">Route: {resource.route_display}</span>
              )}
              {resource.timing_display && (
                <span className="detail-item">Timing: {resource.timing_display}</span>
              )}
              {resource.medicationCodeableConcept?.coding?.[0]?.code && (
                <span className="detail-item">Code: {resource.medicationCodeableConcept.coding[0].code}</span>
              )}
              {resource.dosageInstruction?.[0]?.text && (
                <span className="detail-item">Dosage: {resource.dosageInstruction[0].text}</span>
              )}
            </div>
          </div>
        );
        
      case 'medicationAdministrations':
        return (
          <div className="resource-item">
            <div className="resource-title">
              {resource.medicationCodeableConcept?.text || 
               resource.medicationCodeableConcept?.coding?.[0]?.display ||
               resource.medicationCodeableConcept?.coding?.[0]?.code ||
               resource.medicationReference?.display || 'Unknown Medication'}
            </div>
            <div className="resource-details">
              <span className="detail-item">Status: {resource.status || 'Unknown'}</span>
              <span className="detail-item">Effective: {resource.effectiveDateTime || resource.effectivePeriod?.start || 'N/A'}</span>
              {resource.route_display && (
                <span className="detail-item">Route: {resource.route_display}</span>
              )}
              {resource.timing_display && (
                <span className="detail-item">Timing: {resource.timing_display}</span>
              )}
              {resource.medicationCodeableConcept?.coding?.[0]?.code && (
                <span className="detail-item">Code: {resource.medicationCodeableConcept.coding[0].code}</span>
              )}
              {resource.dosage?.dose?.value && (
                <span className="detail-item">Dose: {resource.dosage.dose.value} {resource.dosage.dose.unit}</span>
              )}
            </div>
          </div>
        );
        
      case 'observations':
        return (
          <div className="resource-item">
            <div className="resource-title">
              {resource.code?.text || resource.code?.coding?.[0]?.display || 'Unknown Observation'}
            </div>
            <div className="resource-details">
              <span className="detail-item">Status: {resource.status || 'Unknown'}</span>
              <span className="detail-item">Effective: {resource.effectiveDateTime || 'N/A'}</span>
              {resource.valueQuantity && (
                <span className="detail-item">Value: {resource.valueQuantity.value} {resource.valueQuantity.unit}</span>
              )}
              {resource.valueString && (
                <span className="detail-item">Value: {resource.valueString}</span>
              )}
              {resource.valueCodeableConcept?.text && (
                <span className="detail-item">Value: {resource.valueCodeableConcept.text}</span>
              )}
            </div>
          </div>
        );
        
      case 'specimens':
        return (
          <div className="resource-item">
            <div className="resource-title">
              {resource.type?.text || resource.type?.coding?.[0]?.display || 'Unknown Specimen'}
            </div>
            <div className="resource-details">
              <span className="detail-item">Status: {resource.status || 'Unknown'}</span>
              <span className="detail-item">Collected: {resource.collection?.collectedDateTime || 'N/A'}</span>
              {resource.collection?.bodySite?.text && (
                <span className="detail-item">Body Site: {resource.collection.bodySite.text}</span>
              )}
              {resource.collection?.method?.text && (
                <span className="detail-item">Method: {resource.collection.method.text}</span>
              )}
            </div>
          </div>
        );
        
      case 'medicationDispenses':
        return (
          <div className="resource-item">
            <div className="resource-title">
              {resource.medicationCodeableConcept?.text || 
               resource.medicationCodeableConcept?.coding?.[0]?.display ||
               resource.medicationCodeableConcept?.coding?.[0]?.code ||
               resource.medicationReference?.display || 'Unknown Medication'}
            </div>
            <div className="resource-details">
              <span className="detail-item">Status: {resource.status || 'Unknown'}</span>
              <span className="detail-item">Dispensed: {resource.whenHandedOver || resource.whenPrepared || 'N/A'}</span>
              {resource.route_display && (
                <span className="detail-item">Route: {resource.route_display}</span>
              )}
              {resource.timing_display && (
                <span className="detail-item">Timing: {resource.timing_display}</span>
              )}
              {/* Show quantity even if 0 to help debug */}
              {resource.quantity && (
                <span className="detail-item">Quantity: {resource.quantity.value || 0} {resource.quantity.unit || resource.quantity.code || ''}</span>
              )}
              {resource.daysSupply && (
                <span className="detail-item">Days Supply: {resource.daysSupply.value || 0}</span>
              )}
              {/* Additional quantity fields that might exist */}
              {resource.dosageInstruction?.[0]?.doseAndRate?.[0]?.doseQuantity?.value && (
                <span className="detail-item">Dose: {resource.dosageInstruction[0].doseAndRate[0].doseQuantity.value} {resource.dosageInstruction[0].doseAndRate[0].doseQuantity.unit}</span>
              )}
              {/* Show performer/dispenser if available */}
              {resource.performer?.[0]?.actor?.display && (
                <span className="detail-item">Dispenser: {resource.performer[0].actor.display}</span>
              )}
              {/* Show location if available */}
              {resource.location?.display && (
                <span className="detail-item">Location: {resource.location.display}</span>
              )}
            </div>
          </div>
        );
        
      default:
        return (
          <div className="resource-item">
            <div className="resource-title">
              {resource.resourceType} - {resource.id}
            </div>
            <div className="resource-details">
              <span className="detail-item">Status: {resource.status || 'N/A'}</span>
            </div>
          </div>
        );
    }
  };

  const renderResourceTab = (tabName: string, resources: any[], resourceType: string) => {
    if (activeTab !== tabName) return null;
    
    if (loading) return <div className="p-4">Loading...</div>;
    
    if (resources.length === 0) {
      return <div className="p-4 text-gray-500">No {tabName} found</div>;
    }

    return (
      <div className="p-4">
        <h3 className="font-semibold mb-3">{tabName} ({resources.length})</h3>
        <div className="resource-list">
          {resources.map((item: any, idx: number) => (
            <div key={idx} className="mb-3">
              {formatResource(item, resourceType)}
            </div>
          ))}
        </div>
      </div>
    );
  };

  return (
    <div className="flex flex-col h-screen">
      {/* Global Search Header */}
      <div className="bg-white border-b border-gray-200 p-4">
        <div className="max-w-4xl mx-auto">
          <h1 className="text-2xl font-bold text-gray-900 mb-4">EHR Patient Viewer</h1>
          <ClinicalSearch 
            onResultClick={(result) => {
              // Handle search result click - could navigate to specific note or resource
              console.log('Search result clicked:', result);
            }}
            onPatientSelect={(patientId) => {
              // Find and select the patient from the search results
              const patient = patients.find(p => p.id === patientId);
              if (patient) {
                setSelectedPatient(patient);
              }
            }}
          />
        </div>
      </div>

      {/* Main Content */}
      <div className="flex flex-1 overflow-hidden">
        {/* Patient List */}
        <div className={`${showChatbot ? 'w-1/4' : 'w-1/3'} border-r bg-white overflow-y-auto transition-all duration-300`}>
          <div className="p-4 border-b">
            <h2 className="font-bold text-lg">Patients ({patients.length})</h2>
          </div>
          <div className="divide-y">
            {patients.map(patient => (
              <div
                key={patient.id}
                className={`p-3 cursor-pointer hover:bg-gray-50 ${
                  selectedPatient?.id === patient.id ? 'bg-blue-50 border-l-4 border-blue-500' : ''
                }`}
                onClick={() => setSelectedPatient(patient)}
              >
                <div className="font-medium">{patient.family_name}</div>
                <div className="text-sm text-gray-500">
                  {patient.gender} • {patient.birth_date}
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Patient Details */}
      <div className={`${showChatbot ? 'w-1/2' : 'flex-1'} flex flex-col transition-all duration-300`}>
        {selectedPatient ? (
          <>
            {/* Patient Info Header */}
            <div className="border-b bg-white p-4">
              <h1 className="text-xl font-bold">{selectedPatient.family_name}</h1>
              <div className="grid grid-cols-2 gap-4 mt-2 text-sm">
                <div>Gender: {selectedPatient.gender}</div>
                <div>Birth Date: {selectedPatient.birth_date}</div>
                <div>Race: {selectedPatient.race || 'N/A'}</div>
                <div>Ethnicity: {selectedPatient.ethnicity || 'N/A'}</div>
                <div>Marital Status: {selectedPatient.marital_status || 'N/A'}</div>
                <div>Identifier: {selectedPatient.identifier || 'N/A'}</div>
              </div>
              
              {/* Allergies Section */}
              <div className="mt-4">
                <h3 className="font-medium text-sm mb-2">Allergies:</h3>
                {allergiesLoading ? (
                  <div className="text-sm text-gray-500">Loading allergies...</div>
                ) : allergies.length > 0 ? (
                  <div className="flex flex-wrap gap-2">
                    {allergies.map((allergy, index) => (
                      <span 
                        key={index}
                        className="inline-block bg-red-100 text-red-800 text-xs px-2 py-1 rounded-full"
                        title={allergy.note || 'Clinical allergy'}
                      >
                        {allergy.allergy_name}
                      </span>
                    ))}
                  </div>
                ) : (
                  <div className="text-sm text-gray-500">No known allergies</div>
                )}
              </div>
              

              
              {/* Encounter Filter */}
              <div className="mt-4">
                <label className="block text-sm font-medium mb-1">Filter by Encounter:</label>
                <select
                  value={selectedEncounter}
                  onChange={(e) => setSelectedEncounter(e.target.value)}
                  className="border rounded px-3 py-1"
                >
                  <option value="all">All Encounters</option>
                  {encounters.map(encounter => (
                    <option key={encounter.id} value={encounter.id}>
                      {encounter.class_display} - {encounter.start_date} ({encounter.status})
                    </option>
                  ))}
                </select>
              </div>

              {/* Chatbot Toggle */}
              <div className="mt-4">
                <button
                  onClick={() => setShowChatbot(!showChatbot)}
                  className={`px-4 py-2 rounded-lg font-medium transition-colors ${
                    showChatbot 
                      ? 'bg-blue-600 text-white hover:bg-blue-700' 
                      : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                  }`}
                >
                  <div className="flex items-center space-x-2">
                    <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z" />
                    </svg>
                    <span>{showChatbot ? 'Hide' : 'Show'} AI Assistant</span>
                  </div>
                </button>
              </div>
            </div>

            {/* Resource Tabs */}
            <div className="flex border-b bg-white">
              {[
                { id: 'conditions', label: 'Conditions', count: resourceData.conditions.length },
                { id: 'medicationAdministrations', label: 'Med Admin', count: resourceData.medicationAdministrations.length },
                { id: 'observations', label: 'Observations', count: resourceData.observations.length },
                { id: 'medicationRequests', label: 'Med Requests', count: resourceData.medicationRequests.length },
                { id: 'specimens', label: 'Specimens', count: resourceData.specimens.length },
                { id: 'medicationDispenses', label: 'Med Dispense', count: resourceData.medicationDispenses.length },
                { id: 'pmh', label: 'PMH', count: pmh.length },
                { id: 'notes', label: 'Notes', count: notes.length }
              ].map(tab => (
                <button
                  key={tab.id}
                  onClick={() => setActiveTab(tab.id)}
                  className={`px-4 py-2 text-sm font-medium border-b-2 ${
                    activeTab === tab.id
                      ? 'border-blue-500 text-blue-600'
                      : 'border-transparent text-gray-500 hover:text-gray-700'
                  }`}
                >
                  {tab.label} ({tab.count})
                </button>
              ))}
            </div>

            {/* Tab Content */}
            <div className="flex-1 overflow-y-auto">
              {renderResourceTab('conditions', resourceData.conditions, 'conditions')}
              {renderResourceTab('medicationAdministrations', resourceData.medicationAdministrations, 'medicationAdministrations')}
              {renderResourceTab('observations', resourceData.observations, 'observations')}
              {renderResourceTab('medicationRequests', resourceData.medicationRequests, 'medicationRequests')}
              {renderResourceTab('specimens', resourceData.specimens, 'specimens')}
              {renderResourceTab('medicationDispenses', resourceData.medicationDispenses, 'medicationDispenses')}
              
              {/* PMH Tab Content */}
              {activeTab === 'pmh' && (
                <div className="p-4">
                  <h3 className="font-semibold mb-3">Past Medical History ({pmh.length})</h3>
                  {pmhLoading ? (
                    <div className="text-gray-500">Loading medical history...</div>
                  ) : pmh.length > 0 ? (
                    <div className="space-y-3">
                      {pmh
                        .sort((a, b) => {
                          // Sort by chart_time, most recent first
                          const dateA = new Date(a.chart_time || a.recorded_date || '1900-01-01').getTime();
                          const dateB = new Date(b.chart_time || b.recorded_date || '1900-01-01').getTime();
                          return dateB - dateA;
                        })
                        .map((condition, index) => (
                        <div key={index} className="resource-item">
                          <div className="resource-title">
                            {condition.condition_name}
                          </div>
                          <div className="resource-details">
                            <span className="detail-item">
                              Chart Date: {condition.chart_time ? new Date(condition.chart_time).toLocaleDateString() : 
                                         (condition.recorded_date ? new Date(condition.recorded_date).toLocaleDateString() : 'Unknown')}
                            </span>
                            {condition.note && (
                              <span className="detail-item">Source: {condition.note}</span>
                            )}
                            <span className="detail-item">Category: {condition.category || 'Medical History'}</span>
                          </div>
                        </div>
                      ))}
                    </div>
                  ) : (
                    <div className="text-gray-500">No medical history available</div>
                  )}
                </div>
              )}

              {/* Notes Tab Content */}
              {activeTab === 'notes' && (
                <div className="p-4">
                  <h3 className="font-semibold mb-3">Clinical Notes ({notes.length})</h3>
                  {notesLoading ? (
                    <div className="text-gray-500">Loading clinical notes...</div>
                  ) : notes.length > 0 ? (
                    <div className="space-y-3">
                      {notes.map((note, index) => (
                        <div key={index} className="resource-item cursor-pointer hover:bg-gray-50" 
                             onClick={() => setSelectedNote(note)}>
                          <div className="resource-title">
                            {note.note_id || `Note ${index + 1}`}
                          </div>
                          <div className="resource-details">
                            <span className="detail-item">
                              Charted: {note.charttime_formatted || 'Unknown'}
                            </span>
                            <span className="detail-item">
                              Stored: {note.storetime_formatted || 'Unknown'}
                            </span>
                            <span className="detail-item">
                              Type: {note.note_type || 'General'}
                            </span>
                            <span className="detail-item">
                              Preview: {note.text.substring(0, 100)}...
                            </span>
                          </div>
                        </div>
                      ))}
                    </div>
                  ) : (
                    <div className="text-gray-500">No clinical notes available</div>
                  )}
                </div>
              )}



              {/* Note Detail Modal */}
              {selectedNote && (
                <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
                  <div className="bg-white rounded-lg p-6 max-w-4xl w-full mx-4 max-h-[90vh] overflow-y-auto">
                    <div className="flex justify-between items-center mb-4">
                      <h2 className="text-xl font-semibold">
                        {selectedNote.note_id || 'Clinical Note'}
                      </h2>
                      <button 
                        onClick={() => setSelectedNote(null)}
                        className="text-gray-500 hover:text-gray-700"
                      >
                        ✕
                      </button>
                    </div>
                    <div className="mb-4 text-sm text-gray-600">
                      <span className="mr-4">
                        Charted: {selectedNote.charttime_formatted || 'Unknown'}
                      </span>
                      <span className="mr-4">
                        Stored: {selectedNote.storetime_formatted || 'Unknown'}
                      </span>
                      <span>
                        Type: {selectedNote.note_type || 'General'}
                      </span>
                    </div>
                    <div className="whitespace-pre-wrap text-sm leading-relaxed">
                      {selectedNote.text}
                    </div>
                  </div>
                </div>
              )}
            </div>
          </>
        ) : (
          <div className="flex-1 flex items-center justify-center text-gray-500">
            Select a patient to view details
          </div>
        )}
      </div>
    </div>

      {/* Chatbot Panel */}
      {showChatbot && (
        <div className="w-1/4 border-l border-gray-200 transition-all duration-300">
          <ChatInterface
            patientId={selectedPatient?.id}
            patientName={selectedPatient?.family_name}
            onClose={() => setShowChatbot(false)}
          />
        </div>
      )}
    </div>
  );
}

export default App;