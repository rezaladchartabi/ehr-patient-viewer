import React, { useEffect, useMemo, useState } from 'react';
import './App.css';
import { SidebarPatients } from './components/SidebarPatients';
import { PatientHeaderBanner } from './components/PatientHeaderBanner';
import { PatientTabs } from './components/PatientTabs';
import { useTheme } from 'next-themes';

interface Patient {
  id: string;
  family_name: string;
  gender: string;
  birth_date: string;
  race?: string;
  ethnicity?: string;
  birth_sex?: string;
  identifier?: string;
  marital_status?: string;
  deceased_date?: string;
  managing_organization?: string;
}

interface Condition {
  id: string;
  code: string;
  code_system: string;
  code_display: string;
  patient_id: string;
  category: string;
  encounter_id: string;
  status: string;
}

interface Medication {
  id: string;
  patient_id: string;
  medication_code: string;
  medication_display: string;
  medication_system: string;
  status: string;
  quantity: number;
  quantity_unit: string;
  days_supply: number;
  dispense_date: string;
  encounter_id: string;
}

interface Encounter {
  id: string;
  patient_id: string;
  encounter_type: string;
  status: string;
  start_date: string;
  end_date: string;
  class_code: string;
  class_display: string;
  service_type: string;
  priority_code: string;
  priority_display: string;
  diagnosis_condition: string;
  diagnosis_use: string;
  diagnosis_rank: number;
  hospitalization_admit_source_code: string;
  hospitalization_admit_source_display: string;
  hospitalization_discharge_disposition_code: string;
  hospitalization_discharge_disposition_display: string;
}

interface MedicationAdministration {
  id: string;
  patient_id: string;
  encounter_id: string;
  medication_code: string;
  medication_display: string;
  medication_system: string;
  status: string;
  effective_start: string;
  effective_end: string;
  dosage_quantity: number;
  dosage_unit: string;
  route_code: string;
  route_display: string;
  site_code: string;
  site_display: string;
  method_code: string;
  method_display: string;
  reason_code: string;
  reason_display: string;
}

interface MedicationRequest {
  id: string;
  patient_id: string;
  encounter_id: string;
  medication_code: string;
  medication_display: string;
  medication_system: string;
  status: string;
  intent: string;
  priority: string;
  authored_on: string;
  dosage_quantity: number;
  dosage_unit: string;
  frequency_code: string;
  frequency_display: string;
  route_code: string;
  route_display: string;
  reason_code: string;
  reason_display: string;
}

interface Observation {
  id: string;
  patient_id: string;
  encounter_id: string;
  observation_type: string;
  code: string;
  code_display: string;
  code_system: string;
  status: string;
  effective_datetime: string;
  issued_datetime: string;
  value_quantity: number;
  value_unit: string;
  value_code: string;
  value_display: string;
  value_string: string;
  value_boolean: boolean;
  value_datetime: string;
  category_code: string;
  category_display: string;
  interpretation_code: string;
  interpretation_display: string;
  reference_range_low: number;
  reference_range_high: number;
  reference_range_unit: string;
}

interface Procedure {
  id: string;
  patient_id: string;
  encounter_id: string;
  procedure_code: string;
  procedure_display: string;
  procedure_system: string;
  status: string;
  performed_datetime: string;
  performed_period_start: string;
  performed_period_end: string;
  category_code: string;
  category_display: string;
  reason_code: string;
  reason_display: string;
  outcome_code: string;
  outcome_display: string;
  complication_code: string;
  complication_display: string;
  follow_up_code: string;
  follow_up_display: string;
}

interface Specimen {
  id: string;
  patient_id: string;
  encounter_id: string;
  specimen_type_code: string;
  specimen_type_display: string;
  specimen_type_system: string;
  status: string;
  collected_datetime: string;
  received_datetime: string;
  collection_method_code: string;
  collection_method_display: string;
  body_site_code: string;
  body_site_display: string;
  fasting_status_code: string;
  fasting_status_display: string;
  container_code: string;
  container_display: string;
  note: string;
}

interface PatientSummary {
  patient: Patient;
  summary: {
    conditions: number;
    medications: number;
    encounters: number;
    medication_administrations: number;
    medication_requests: number;
    observations: number;
    procedures: number;
    specimens: number;
  };
}

const API_BASE = process.env.REACT_APP_API_URL || 'https://ehr-backend-87r9.onrender.com';

function App() {
  const { theme, setTheme } = useTheme();
  const isDark = theme === 'dark';
  const toggleTheme = () => setTheme(isDark ? 'light' : 'dark');
  const [patients, setPatients] = useState<Patient[]>([]);
  const [selectedPatient, setSelectedPatient] = useState<Patient | null>(null);
  const [patientSummary, setPatientSummary] = useState<PatientSummary | null>(null);
  const [conditions, setConditions] = useState<Condition[]>([]);
  const [medications, setMedications] = useState<Medication[]>([]);
  const [encounters, setEncounters] = useState<Encounter[]>([]);
  const [medicationAdministrations, setMedicationAdministrations] = useState<MedicationAdministration[]>([]);
  const [medicationRequests, setMedicationRequests] = useState<MedicationRequest[]>([]);
  const [observations, setObservations] = useState<Observation[]>([]);
  const [procedures, setProcedures] = useState<Procedure[]>([]);
  const [specimens, setSpecimens] = useState<Specimen[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState<string>('conditions');
  const [searchQuery, setSearchQuery] = useState<string>('');
  const [searchResults, setSearchResults] = useState<Array<{ type: string; id: string; title: string; subtitle: string; patient_id: string }>>([]);
  const [isSearching, setIsSearching] = useState<boolean>(false);
  const [searchPatients, setSearchPatients] = useState<Patient[]>([]);
  const [showSearchOverlay, setShowSearchOverlay] = useState<boolean>(false);

  type ServiceLine = 'ICU' | 'ED' | 'Default';
  const [activeServiceLine, setActiveServiceLine] = useState<ServiceLine>('Default');

  const getServiceLineFromEncounter = (enc: Encounter): ServiceLine => {
    if (!enc) return 'Default';
    const type = (enc.encounter_type || '').toLowerCase();
    if (type === 'icu') return 'ICU';
    if (type === 'emergency') return 'ED';
    return 'Default';
  };

  const encounterIdToServiceLine: Record<string, ServiceLine> = useMemo(() => {
    const map: Record<string, ServiceLine> = {};
    for (const enc of encounters) {
      map[enc.id] = getServiceLineFromEncounter(enc);
    }
    return map;
  }, [encounters]);

  const groupItemsByServiceLine = <T extends { encounter_id?: string }>(items: T[]): Record<ServiceLine, T[]> => {
    const groups: Record<ServiceLine, T[]> = { ICU: [], ED: [], Default: [] };
    for (const item of items) {
      const line = item.encounter_id ? (encounterIdToServiceLine[item.encounter_id] || 'Default') : 'Default';
      groups[line].push(item);
    }
    return groups;
  };

  const groupedEncounters = useMemo(() => {
    const groups: Record<ServiceLine, Encounter[]> = { ICU: [], ED: [], Default: [] };
    for (const enc of encounters) {
      groups[getServiceLineFromEncounter(enc)].push(enc);
    }
    return groups;
  }, [encounters]);

  const groupedConditions = useMemo(() => groupItemsByServiceLine(conditions), [conditions, encounterIdToServiceLine]);
  const groupedMedications = useMemo(() => groupItemsByServiceLine(medications), [medications, encounterIdToServiceLine]);
  const groupedMedicationAdministrations = useMemo(() => groupItemsByServiceLine(medicationAdministrations), [medicationAdministrations, encounterIdToServiceLine]);
  const groupedMedicationRequests = useMemo(() => groupItemsByServiceLine(medicationRequests), [medicationRequests, encounterIdToServiceLine]);
  const groupedObservations = useMemo(() => groupItemsByServiceLine(observations), [observations, encounterIdToServiceLine]);
  const groupedProcedures = useMemo(() => groupItemsByServiceLine(procedures), [procedures, encounterIdToServiceLine]);
  const groupedSpecimens = useMemo(() => groupItemsByServiceLine(specimens), [specimens, encounterIdToServiceLine]);

  useEffect(() => {
    setLoading(true);
    fetch(`${API_BASE}/patients`)
      .then(res => res.json())
      .then(data => {
        setPatients(data);
        setLoading(false);
      })
      .catch(err => {
        setError('Failed to fetch patients');
        setLoading(false);
      });
  }, []);

  const selectPatient = (patient: Patient) => {
    setSelectedPatient(patient);
    setLoading(true);
    setError(null);
    setActiveTab('conditions');
    
    // Fetch patient summary
    fetch(`${API_BASE}/patients/${patient.id}/summary`)
      .then(res => res.json())
      .then(data => {
        setPatientSummary(data);
      })
      .catch(err => {
        setError('Failed to fetch patient summary');
      });
    
    // Fetch all data types
    const fetchPromises = [
      fetch(`${API_BASE}/patients/${patient.id}/conditions`).then(res => res.json()).then(setConditions).catch(() => setConditions([])),
      fetch(`${API_BASE}/patients/${patient.id}/medications`).then(res => res.json()).then(setMedications).catch(() => setMedications([])),
      fetch(`${API_BASE}/patients/${patient.id}/encounters`).then(res => res.json()).then(setEncounters).catch(() => setEncounters([])),
      fetch(`${API_BASE}/patients/${patient.id}/medication-administrations`).then(res => res.json()).then(setMedicationAdministrations).catch(() => setMedicationAdministrations([])),
      fetch(`${API_BASE}/patients/${patient.id}/medication-requests`).then(res => res.json()).then(setMedicationRequests).catch(() => setMedicationRequests([])),
      fetch(`${API_BASE}/patients/${patient.id}/observations`).then(res => res.json()).then(setObservations).catch(() => setObservations([])),
      fetch(`${API_BASE}/patients/${patient.id}/procedures`).then(res => res.json()).then(setProcedures).catch(() => setProcedures([])),
      fetch(`${API_BASE}/patients/${patient.id}/specimens`).then(res => res.json()).then(setSpecimens).catch(() => setSpecimens([]))
    ];
    
    Promise.all(fetchPromises)
      .then(() => {
        setLoading(false);
      })
      .catch(() => {
        setLoading(false);
      });
  };

  return (
    <div className="App">
      <h1>EHR Patient Viewer</h1>
      {error && <div style={{ color: 'red', padding: '10px', backgroundColor: '#ffebee', borderRadius: '4px', margin: '10px 0' }}>{error}</div>}
      
      {/* Global Search */}
      <div className="relative z-50 mx-auto w-full max-w-[25vw]">
        <div className="flex gap-2">
          <input
            type="text"
            placeholder="Search patients, conditions, medications, encounters, observations, procedures, specimens..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === 'Enter') {
                setIsSearching(true);
                setShowSearchOverlay(true);
                Promise.all([
                  fetch(`${API_BASE}/search?q=${encodeURIComponent(searchQuery)}`).then(r => r.json()),
                  fetch(`${API_BASE}/search/patients?q=${encodeURIComponent(searchQuery)}`).then(r => r.json()),
                ])
                  .then(([items, patients]) => {
                    setSearchResults(items);
                    setSearchPatients(patients);
                  })
                  .finally(() => setIsSearching(false));
              }
            }}
            className="w-full rounded-lg border border-gray-300 dark:border-neutral-700 bg-white dark:bg-neutral-900 px-3 py-2 shadow-soft focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
          <button
            onClick={() => {
              setIsSearching(true);
              setShowSearchOverlay(true);
              Promise.all([
                fetch(`${API_BASE}/search?q=${encodeURIComponent(searchQuery)}`).then(r => r.json()),
                fetch(`${API_BASE}/search/patients?q=${encodeURIComponent(searchQuery)}`).then(r => r.json()),
              ])
                .then(([items, patients]) => {
                  setSearchResults(items);
                  setSearchPatients(patients);
                })
                .finally(() => setIsSearching(false));
            }}
            className="rounded-lg bg-blue-600 px-4 py-2 text-white hover:bg-blue-700"
          >
            Search
          </button>
        </div>

        {showSearchOverlay && (
          <>
            <div
              className="fixed inset-0 bg-black/30 z-40"
              onClick={() => setShowSearchOverlay(false)}
            />
            <div className="absolute left-0 right-0 mt-2 z-50 rounded-xl border border-gray-200 dark:border-neutral-800 bg-white dark:bg-neutral-900 shadow-soft max-h-[60vh] overflow-y-auto">
              <div className="border-b border-gray-200 dark:border-neutral-800 px-4 py-2 text-sm text-gray-500">
                {isSearching ? 'Searching...' : 'Search Results'}
              </div>
              {!isSearching && (
                <div className="p-2">
                  {searchPatients.length > 0 && (
                    <div className="mb-2">
                      <div className="px-2 py-1 text-xs uppercase tracking-wide text-gray-500">Patients</div>
                      <ul className="divide-y divide-gray-100 dark:divide-neutral-800">
                        {searchPatients.map((p) => (
                          <li
                            key={p.id}
                            className="cursor-pointer px-3 py-2 hover:bg-gray-50 dark:hover:bg-neutral-800 rounded-md"
                            onClick={() => {
                              setShowSearchOverlay(false);
                              selectPatient(p);
                              setActiveTab('conditions');
                            }}
                          >
                            <div className="font-medium">{p.family_name}</div>
                            <div className="text-xs text-gray-500">{p.gender} • {p.birth_date} • {p.identifier}</div>
                          </li>
                        ))}
                      </ul>
                    </div>
                  )}

                  {searchResults.length > 0 && (
                    <div>
                      <div className="px-2 py-1 text-xs uppercase tracking-wide text-gray-500">Items</div>
                      <ul className="divide-y divide-gray-100 dark:divide-neutral-800">
                        {searchResults.map((r) => (
                          <li
                            key={`${r.type}-${r.id}`}
                            className="cursor-pointer px-3 py-2 hover:bg-gray-50 dark:hover:bg-neutral-800 rounded-md"
                            onClick={() => {
                              const patient = patients.find(p => p.id === r.patient_id || p.id === r.id);
                              if (patient) {
                                setShowSearchOverlay(false);
                                selectPatient(patient);
                                const tabMap: Record<string, string> = {
                                  'patient': 'conditions',
                                  'condition': 'conditions',
                                  'medication': 'medications',
                                  'encounter': 'encounters',
                                  'medication-administration': 'medication-administrations',
                                  'medication-request': 'medication-requests',
                                  'observation': 'observations',
                                  'procedure': 'procedures',
                                  'specimen': 'specimens',
                                };
                                const t = tabMap[r.type] || 'conditions';
                                setActiveTab(t);
                              }
                            }}
                          >
                            <div className="font-medium">{r.title}</div>
                            <div className="text-xs text-gray-500">{r.type} • {r.subtitle}</div>
                          </li>
                        ))}
                      </ul>
                    </div>
                  )}

                  {searchPatients.length === 0 && searchResults.length === 0 && (
                    <div className="px-3 py-4 text-sm text-gray-500">No results</div>
                  )}
                </div>
              )}
            </div>
          </>
        )}
      </div>

      <div style={{ display: 'flex', alignItems: 'flex-start', gap: '2rem' }}>
        {/* Patient List */}
        <div style={{ minWidth: '300px', width: '320px' }}>
          {loading && <div>Loading...</div>}
          <SidebarPatients
            patients={patients}
            selectedId={selectedPatient?.id}
            onSelect={selectPatient}
            renderItem={(p: Patient) => (
              <div>
                <div className="font-semibold">{p.family_name}</div>
                <div className="text-xs text-gray-500 dark:text-neutral-400">{p.gender} • {p.birth_date} • {p.identifier}</div>
              </div>
            )}
          />
        </div>

        {/* Patient Details */}
        <div style={{ flex: 1 }}>
          {selectedPatient && patientSummary && (
            <div>
              <PatientHeaderBanner
                title={selectedPatient.family_name}
                subtitle={`${selectedPatient.gender} • ${selectedPatient.birth_date} • ${selectedPatient.identifier || ''}`}
                onToggleTheme={toggleTheme}
                isDark={isDark}
              />
              <table style={{ width: '100%', borderCollapse: 'collapse', marginBottom: '20px' }}>
                <tbody>
                  <tr><td style={{ padding: '8px', border: '1px solid #ddd', fontWeight: 'bold' }}>ID</td><td style={{ padding: '8px', border: '1px solid #ddd' }}>{selectedPatient.id}</td></tr>
                  <tr><td style={{ padding: '8px', border: '1px solid #ddd', fontWeight: 'bold' }}>Name</td><td style={{ padding: '8px', border: '1px solid #ddd' }}>{selectedPatient.family_name}</td></tr>
                  <tr><td style={{ padding: '8px', border: '1px solid #ddd', fontWeight: 'bold' }}>Gender</td><td style={{ padding: '8px', border: '1px solid #ddd' }}>{selectedPatient.gender}</td></tr>
                  <tr><td style={{ padding: '8px', border: '1px solid #ddd', fontWeight: 'bold' }}>Birth Date</td><td style={{ padding: '8px', border: '1px solid #ddd' }}>{selectedPatient.birth_date}</td></tr>
                  <tr><td style={{ padding: '8px', border: '1px solid #ddd', fontWeight: 'bold' }}>Race</td><td style={{ padding: '8px', border: '1px solid #ddd' }}>{selectedPatient.race}</td></tr>
                  <tr><td style={{ padding: '8px', border: '1px solid #ddd', fontWeight: 'bold' }}>Ethnicity</td><td style={{ padding: '8px', border: '1px solid #ddd' }}>{selectedPatient.ethnicity}</td></tr>
                  <tr><td style={{ padding: '8px', border: '1px solid #ddd', fontWeight: 'bold' }}>Birth Sex</td><td style={{ padding: '8px', border: '1px solid #ddd' }}>{selectedPatient.birth_sex}</td></tr>
                  <tr><td style={{ padding: '8px', border: '1px solid #ddd', fontWeight: 'bold' }}>Identifier</td><td style={{ padding: '8px', border: '1px solid #ddd' }}>{selectedPatient.identifier}</td></tr>
                  <tr><td style={{ padding: '8px', border: '1px solid #ddd', fontWeight: 'bold' }}>Marital Status</td><td style={{ padding: '8px', border: '1px solid #ddd' }}>{selectedPatient.marital_status}</td></tr>
                  <tr><td style={{ padding: '8px', border: '1px solid #ddd', fontWeight: 'bold' }}>Deceased Date</td><td style={{ padding: '8px', border: '1px solid #ddd' }}>{selectedPatient.deceased_date || 'N/A'}</td></tr>
                  <tr><td style={{ padding: '8px', border: '1px solid #ddd', fontWeight: 'bold' }}>Managing Org</td><td style={{ padding: '8px', border: '1px solid #ddd' }}>{selectedPatient.managing_organization}</td></tr>
                </tbody>
              </table>

              

              {/* Tabs */}
              <div style={{ marginBottom: '20px' }}>
                {/* Top-level: Data Type */}
                <PatientTabs
                  tabs={[
                    { id: 'conditions', label: 'Conditions' },
                    { id: 'medications', label: 'Medications' },
                    { id: 'encounters', label: 'Encounters' },
                    { id: 'medication-administrations', label: 'Med Admin' },
                    { id: 'medication-requests', label: 'Med Requests' },
                    { id: 'observations', label: 'Observations' },
                    { id: 'procedures', label: 'Procedures' },
                    { id: 'specimens', label: 'Specimens' },
                  ]}
                  active={activeTab}
                  onChange={setActiveTab}
                />
                {/* Sub-level: Service Line */}
                <div style={{ marginTop: '10px' }}>
                  <PatientTabs
                    tabs={[
                      { id: 'Default', label: 'Default' },
                      { id: 'ED', label: 'ED' },
                      { id: 'ICU', label: 'ICU' },
                    ]}
                    active={activeServiceLine}
                    onChange={(id) => setActiveServiceLine(id as ServiceLine)}
                  />
                </div>

                {/* Tab Content */}
                {loading ? (
                  <div>Loading...</div>
                ) : (
                  <div>
                    {activeTab === 'conditions' && (
                      <div>
                        <h3>Conditions ({groupedConditions[activeServiceLine].length})</h3>
                        <ul style={{ listStyle: 'none', padding: 0 }}>
                          {groupedConditions[activeServiceLine].map(cond => (
                            <li key={cond.id} style={{ padding: '10px', border: '1px solid #ddd', marginBottom: '5px', borderRadius: '4px' }}>
                              <b>{cond.code_display}</b> (ICD: {cond.code})<br />
                              Category: {cond.category} | Status: {cond.status}
                            </li>
                          ))}
                          {groupedConditions[activeServiceLine].length === 0 && <li>None</li>}
                        </ul>
                      </div>
                    )}

                    {activeTab === 'medications' && (
                      <div>
                        <h3>Medications ({groupedMedications[activeServiceLine].length})</h3>
                        <ul style={{ listStyle: 'none', padding: 0 }}>
                          {groupedMedications[activeServiceLine].map(med => (
                            <li key={med.id} style={{ padding: '10px', border: '1px solid #ddd', marginBottom: '5px', borderRadius: '4px' }}>
                              <b>{med.medication_display}</b> (Code: {med.medication_code})<br />
                              Status: {med.status} | Quantity: {med.quantity} {med.quantity_unit}<br />
                              Days Supply: {med.days_supply} | Dispense Date: {med.dispense_date}
                            </li>
                          ))}
                          {groupedMedications[activeServiceLine].length === 0 && <li>None</li>}
                        </ul>
                      </div>
                    )}

                    {activeTab === 'encounters' && (
                      <div>
                        <h3>Encounters ({groupedEncounters[activeServiceLine].length})</h3>
                        <ul style={{ listStyle: 'none', padding: 0 }}>
                          {groupedEncounters[activeServiceLine].map(enc => (
                            <li key={enc.id} style={{ padding: '10px', border: '1px solid #ddd', marginBottom: '5px', borderRadius: '4px' }}>
                              <b>{enc.class_display}</b> ({enc.encounter_type})<br />
                              Status: {enc.status} | Start: {enc.start_date} | End: {enc.end_date}<br />
                              Priority: {enc.priority_display} | Service: {enc.service_type}
                            </li>
                          ))}
                          {groupedEncounters[activeServiceLine].length === 0 && <li>None</li>}
                        </ul>
                      </div>
                    )}

                    {activeTab === 'medication-administrations' && (
                      <div>
                        <h3>Medication Administrations ({groupedMedicationAdministrations[activeServiceLine].length})</h3>
                        <ul style={{ listStyle: 'none', padding: 0 }}>
                          {groupedMedicationAdministrations[activeServiceLine].slice(0, 50).map(admin => (
                            <li key={admin.id} style={{ padding: '10px', border: '1px solid #ddd', marginBottom: '5px', borderRadius: '4px' }}>
                              <b>{admin.medication_display}</b> (Code: {admin.medication_code})<br />
                              Status: {admin.status} | Dosage: {admin.dosage_quantity} {admin.dosage_unit}<br />
                              Route: {admin.route_code} | Effective: {admin.effective_start}
                            </li>
                          ))}
                          {groupedMedicationAdministrations[activeServiceLine].length === 0 && <li>None</li>}
                          {groupedMedicationAdministrations[activeServiceLine].length > 50 && (
                            <li>... and {groupedMedicationAdministrations[activeServiceLine].length - 50} more</li>
                          )}
                        </ul>
                      </div>
                    )}

                    {activeTab === 'medication-requests' && (
                      <div>
                        <h3>Medication Requests ({groupedMedicationRequests[activeServiceLine].length})</h3>
                        <ul style={{ listStyle: 'none', padding: 0 }}>
                          {groupedMedicationRequests[activeServiceLine].map(req => (
                            <li key={req.id} style={{ padding: '10px', border: '1px solid #ddd', marginBottom: '5px', borderRadius: '4px' }}>
                              <b>{req.medication_display}</b> (Code: {req.medication_code})<br />
                              Status: {req.status} | Intent: {req.intent} | Priority: {req.priority}<br />
                              Dosage: {req.dosage_quantity} {req.dosage_unit} | Frequency: {req.frequency_display}<br />
                              Authored: {req.authored_on}
                            </li>
                          ))}
                          {groupedMedicationRequests[activeServiceLine].length === 0 && <li>None</li>}
                        </ul>
                      </div>
                    )}

                    {activeTab === 'observations' && (
                      <div>
                        <h3>Observations ({groupedObservations[activeServiceLine].length})</h3>
                        <ul style={{ listStyle: 'none', padding: 0 }}>
                          {groupedObservations[activeServiceLine].slice(0, 50).map(obs => (
                            <li key={obs.id} style={{ padding: '10px', border: '1px solid #ddd', marginBottom: '5px', borderRadius: '4px' }}>
                              <b>{obs.code_display}</b> (Type: {obs.observation_type})<br />
                              Value: {obs.value_quantity || obs.value_string || obs.value_display || obs.value_code || 'N/A'} {obs.value_unit}<br />
                              Category: {obs.category_display} | Effective: {obs.effective_datetime}
                            </li>
                          ))}
                          {groupedObservations[activeServiceLine].length === 0 && <li>None</li>}
                          {groupedObservations[activeServiceLine].length > 50 && (
                            <li>... and {groupedObservations[activeServiceLine].length - 50} more</li>
                          )}
                        </ul>
                      </div>
                    )}

                    {activeTab === 'procedures' && (
                      <div>
                        <h3>Procedures ({groupedProcedures[activeServiceLine].length})</h3>
                        <ul style={{ listStyle: 'none', padding: 0 }}>
                          {groupedProcedures[activeServiceLine].map(proc => (
                            <li key={proc.id} style={{ padding: '10px', border: '1px solid #ddd', marginBottom: '5px', borderRadius: '4px' }}>
                              <b>{proc.procedure_display}</b> (Code: {proc.procedure_code})<br />
                              Status: {proc.status} | Category: {proc.category_display}<br />
                              Performed: {proc.performed_datetime || proc.performed_period_start}<br />
                              Outcome: {proc.outcome_display} | Follow-up: {proc.follow_up_display}
                            </li>
                          ))}
                          {groupedProcedures[activeServiceLine].length === 0 && <li>None</li>}
                        </ul>
                      </div>
                    )}

                    {activeTab === 'specimens' && (
                      <div>
                        <h3>Specimens ({groupedSpecimens[activeServiceLine].length})</h3>
                        <ul style={{ listStyle: 'none', padding: 0 }}>
                          {groupedSpecimens[activeServiceLine].map(spec => (
                            <li key={spec.id} style={{ padding: '10px', border: '1px solid #ddd', marginBottom: '5px', borderRadius: '4px' }}>
                              <b>{spec.specimen_type_display}</b> (Code: {spec.specimen_type_code})<br />
                              Status: {spec.status} | Collection Method: {spec.collection_method_display}<br />
                              Body Site: {spec.body_site_display} | Collected: {spec.collected_datetime}<br />
                              Container: {spec.container_display} | Note: {spec.note || 'N/A'}
                            </li>
                          ))}
                          {groupedSpecimens[activeServiceLine].length === 0 && <li>None</li>}
                        </ul>
                      </div>
                    )}
                  </div>
                )}
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

export default App;
