import React, { useState, useEffect } from 'react';
import './App.css';

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

const API_BASE = 'https://ehr-backend-87r9.onrender.com';

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

  // Load patients on mount
  useEffect(() => {
    fetch(`${API_BASE}/local/patients?limit=100&offset=0`)
      .then(res => res.json())
      .then(data => setPatients(data.patients || []))
      .catch(err => console.error('Failed to load patients:', err));
  }, []);

  // Load patient data when patient is selected
  useEffect(() => {
    if (!selectedPatient) return;
    
    setLoading(true);
    setAllergiesLoading(true);
    setPmhLoading(true);
    
    // Load encounters and all resource types in parallel
    Promise.all([
      fetch(`${API_BASE}/Encounter?patient=Patient/${selectedPatient.id}&_count=100`).then(r => r.json()),
      fetch(`${API_BASE}/Condition?patient=Patient/${selectedPatient.id}&_count=100`).then(r => r.json()),
      fetch(`${API_BASE}/MedicationAdministration?patient=Patient/${selectedPatient.id}&_count=100`).then(r => r.json()),
      fetch(`${API_BASE}/Observation?patient=Patient/${selectedPatient.id}&_count=100`).then(r => r.json()),
      fetch(`${API_BASE}/MedicationRequest?patient=Patient/${selectedPatient.id}&_count=100`).then(r => r.json()),
      fetch(`${API_BASE}/Specimen?patient=Patient/${selectedPatient.id}&_count=100`).then(r => r.json()),
      fetch(`${API_BASE}/MedicationDispense?patient=Patient/${selectedPatient.id}&_count=100`).then(r => r.json())
    ])
    .then(([encountersRes, conditionsRes, medAdminRes, obsRes, medReqRes, specimenRes, medDispRes]) => {
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
      
      // Process all resource types
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
  }, [selectedPatient]);

  // Filter resources by encounter
  const getFilteredResources = (resources: any[], resourceType: string) => {
    if (selectedEncounter === 'all') return resources;
    
    return resources.filter(item => {
      const resource = item.resource;
      // Different resource types reference encounters differently
      if (resource.encounter?.reference) {
        return resource.encounter.reference === `Encounter/${selectedEncounter}`;
      }
      if (resource.context?.reference) {
        return resource.context.reference === `Encounter/${selectedEncounter}`;
      }
      // For resources without direct encounter reference, filter by date if encounter has dates
      const encounter = encounters.find(e => e.id === selectedEncounter);
      if (encounter && encounter.start_date) {
        const resourceDate = resource.effectiveDateTime || resource.authoredOn || resource.recordedDate;
        if (resourceDate) {
          return resourceDate >= encounter.start_date && 
                 (!encounter.end_date || resourceDate <= encounter.end_date);
        }
      }
      return false;
    });
  };

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
    
    const filteredResources = getFilteredResources(resources, resourceType);
    
    if (loading) return <div className="p-4">Loading...</div>;
    
    if (filteredResources.length === 0) {
      return <div className="p-4 text-gray-500">No {tabName} found</div>;
    }

  return (
      <div className="p-4">
        <h3 className="font-semibold mb-3">{tabName} ({filteredResources.length})</h3>
        <div className="resource-list">
          {filteredResources.map((item, idx) => (
            <div key={idx} className="mb-3">
              {formatResource(item, resourceType)}
            </div>
          ))}
        </div>
      </div>
    );
  };

  return (
    <div className="flex h-screen">
        {/* Patient List */}
      <div className="w-1/3 border-r bg-white overflow-y-auto">
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
      <div className="flex-1 flex flex-col">
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
              
              {/* Past Medical History Section */}
              <div className="mt-4">
                <h3 className="font-medium text-sm mb-2">Past Medical History:</h3>
                {pmhLoading ? (
                  <div className="text-sm text-gray-500">Loading medical history...</div>
                ) : pmh.length > 0 ? (
                  <div className="flex flex-wrap gap-2">
                    {pmh.slice(0, 10).map((condition, index) => (
                      <span 
                        key={index}
                        className="inline-block bg-blue-100 text-blue-800 text-xs px-2 py-1 rounded-full"
                        title={condition.note || 'Clinical condition'}
                      >
                        {condition.condition_name.length > 40 
                          ? condition.condition_name.substring(0, 40) + '...'
                          : condition.condition_name}
                      </span>
                    ))}
                    {pmh.length > 10 && (
                      <span className="inline-block bg-gray-100 text-gray-600 text-xs px-2 py-1 rounded-full">
                        +{pmh.length - 10} more
                      </span>
                    )}
                  </div>
                ) : (
                  <div className="text-sm text-gray-500">No medical history available</div>
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
            </div>

            {/* Resource Tabs */}
            <div className="flex border-b bg-white">
              {[
                { id: 'conditions', label: 'Conditions', count: resourceData.conditions.length },
                { id: 'medicationAdministrations', label: 'Med Admin', count: resourceData.medicationAdministrations.length },
                { id: 'observations', label: 'Observations', count: resourceData.observations.length },
                { id: 'medicationRequests', label: 'Med Requests', count: resourceData.medicationRequests.length },
                { id: 'specimens', label: 'Specimens', count: resourceData.specimens.length },
                { id: 'medicationDispenses', label: 'Med Dispense', count: resourceData.medicationDispenses.length }
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
            </div>
          </>
        ) : (
          <div className="flex-1 flex items-center justify-center text-gray-500">
            Select a patient to view details
            </div>
          )}
      </div>
    </div>
  );
}

export default App;