import React, { useEffect, useMemo, useState } from 'react';
import './App.css';
import { SidebarPatients } from './components/SidebarPatients';
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
  const [selectedEncounterId, setSelectedEncounterId] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState<string>('conditions');
  const [searchQuery, setSearchQuery] = useState<string>('');
  const [searchResults, setSearchResults] = useState<Array<{ type: string; id: string; title: string; subtitle: string; patient_id: string }>>([]);
  const [isSearching, setIsSearching] = useState<boolean>(false);
  const [searchPatients, setSearchPatients] = useState<Patient[]>([]);
  const [showSearchOverlay, setShowSearchOverlay] = useState<boolean>(false);

  type ServiceLine = 'ICU' | 'ED' | 'Default';

  const getServiceLineFromEncounter = (enc: Encounter): ServiceLine => {
    if (!enc) return 'Default';
    const type = (enc.encounter_type || '').toLowerCase();
    if (type === 'icu') return 'ICU';
    if (type === 'emergency') return 'ED';
    return 'Default';
  };

  const sortedEncounters = useMemo(() => {
    const toMs = (e: Encounter) => {
      const d = e.start_date || e.end_date || '';
      const ms = Date.parse(d);
      return Number.isNaN(ms) ? 0 : ms;
    };
    return [...encounters].sort((a, b) => toMs(b) - toMs(a));
  }, [encounters]);

  useEffect(() => {
    if (encounters.length === 0) {
      setSelectedEncounterId(null);
      return;
    }
    const first = sortedEncounters[0];
    setSelectedEncounterId(first ? first.id : null);
  }, [encounters, sortedEncounters]);

  useEffect(() => {
    setLoading(true);
    fetch(`${API_BASE}/patients`)
      .then(res => res.json())
      .then(data => {
        setPatients(data);
        setLoading(false);
        if (Array.isArray(data) && data.length > 0) {
          selectPatient(data[0]);
        }
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
      fetch(`${API_BASE}/patients/${patient.id}/encounters`).then(res => res.json()).then((encs) => {
        setEncounters(encs);
        if (Array.isArray(encs) && encs.length > 0) {
          const sorted = [...encs].sort((a, b) => Date.parse(b.start_date || b.end_date || '') - Date.parse(a.start_date || a.end_date || ''));
          setSelectedEncounterId(sorted[0]?.id || null);
        } else {
          setSelectedEncounterId(null);
        }
      }).catch(() => setEncounters([])),
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
      
      {/* Global Search (right-aligned) */}
      <div className="relative z-50 ml-auto w-full max-w-[25vw]" style={{ marginTop: '10px' }}>
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
              {/* Patient header banner removed per request */}
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

              {/* Encounters list sorted by most recent */}
              <div className="mb-4">
                <h2 className="text-lg font-semibold mb-2">Encounters</h2>
                <ul className="divide-y divide-gray-200 dark:divide-neutral-800 rounded-lg border border-gray-200 dark:border-neutral-800 overflow-hidden">
                  {sortedEncounters.map((enc, idx) => (
                    <li
                      key={enc.id}
                      className={"p-3 cursor-pointer hover:bg-gray-50 dark:hover:bg-neutral-800 " + (selectedEncounterId === enc.id ? 'bg-blue-50 dark:bg-neutral-800/50' : '')}
                      onClick={() => setSelectedEncounterId(selectedEncounterId === enc.id ? null : enc.id)}
                    >
                      <div className="flex items-center justify-between">
                        <div className="flex items-center gap-3">
                          <span className="inline-flex h-6 w-6 items-center justify-center rounded-full bg-gray-100 dark:bg-neutral-800 text-xs font-medium text-gray-700 dark:text-neutral-300">
                            {idx + 1}
                          </span>
                          <div>
                            <div className="font-medium">{enc.class_display || enc.encounter_type || 'Encounter'}</div>
                            <div className="text-xs text-gray-500">{enc.start_date} {enc.end_date ? `- ${enc.end_date}` : ''} • {enc.status} • {enc.service_type || getServiceLineFromEncounter(enc)}</div>
                          </div>
                        </div>
                        <div className="text-xs text-gray-500">{enc.priority_display}</div>
                      </div>
                      {selectedEncounterId === enc.id && (
                        <div className="mt-3 border-t border-gray-200 dark:border-neutral-800 pt-3">
                          <div onClick={(e) => e.stopPropagation()}>
                            <PatientTabs
                              tabs={[
                                { id: 'conditions', label: 'Conditions' },
                                { id: 'medications', label: 'Medications' },
                                { id: 'medication-administrations', label: 'Med Admin' },
                                { id: 'medication-requests', label: 'Med Requests' },
                                { id: 'observations', label: 'Observations' },
                                { id: 'procedures', label: 'Procedures' },
                                { id: 'specimens', label: 'Specimens' },
                              ]}
                              active={activeTab}
                              onChange={setActiveTab}
                            />
                          </div>

                          <div className="mt-3">
                            {activeTab === 'conditions' && (
                              <ul style={{ listStyle: 'none', padding: 0 }}>
                                {conditions.filter(c => c.encounter_id === selectedEncounterId).map(cond => (
                                  <li key={cond.id} style={{ padding: '10px', border: '1px solid #ddd', marginBottom: '5px', borderRadius: '4px' }}>
                                    <b>{cond.code_display}</b> (ICD: {cond.code}) • Category: {cond.category} • Status: {cond.status}
                                  </li>
                                ))}
                                {conditions.filter(c => c.encounter_id === selectedEncounterId).length === 0 && <li>None</li>}
                              </ul>
                            )}

                            {activeTab === 'medications' && (
                              <ul style={{ listStyle: 'none', padding: 0 }}>
                                {medications.filter(m => m.encounter_id === selectedEncounterId).map(med => (
                                  <li key={med.id} style={{ padding: '10px', border: '1px solid #ddd', marginBottom: '5px', borderRadius: '4px' }}>
                                    <b>{med.medication_display}</b> (Code: {med.medication_code}) • Status: {med.status} • Qty: {med.quantity} {med.quantity_unit}
                                  </li>
                                ))}
                                {medications.filter(m => m.encounter_id === selectedEncounterId).length === 0 && <li>None</li>}
                              </ul>
                            )}

                            {activeTab === 'medication-administrations' && (
                              <ul style={{ listStyle: 'none', padding: 0 }}>
                                {medicationAdministrations.filter(a => a.encounter_id === selectedEncounterId).slice(0, 50).map(admin => (
                                  <li key={admin.id} style={{ padding: '10px', border: '1px solid #ddd', marginBottom: '5px', borderRadius: '4px' }}>
                                    <b>{admin.medication_display}</b> • Status: {admin.status} • Dosage: {admin.dosage_quantity} {admin.dosage_unit}
                                  </li>
                                ))}
                                {medicationAdministrations.filter(a => a.encounter_id === selectedEncounterId).length === 0 && <li>None</li>}
                              </ul>
                            )}

                            {activeTab === 'medication-requests' && (
                              <ul style={{ listStyle: 'none', padding: 0 }}>
                                {medicationRequests.filter(r => r.encounter_id === selectedEncounterId).map(req => (
                                  <li key={req.id} style={{ padding: '10px', border: '1px solid #ddd', marginBottom: '5px', borderRadius: '4px' }}>
                                    <b>{req.medication_display}</b> • Status: {req.status} • Priority: {req.priority}
                                  </li>
                                ))}
                                {medicationRequests.filter(r => r.encounter_id === selectedEncounterId).length === 0 && <li>None</li>}
                              </ul>
                            )}

                            {activeTab === 'observations' && (
                              <ul style={{ listStyle: 'none', padding: 0 }}>
                                {observations.filter(o => o.encounter_id === selectedEncounterId).slice(0, 50).map(obs => (
                                  <li key={obs.id} style={{ padding: '10px', border: '1px solid #ddd', marginBottom: '5px', borderRadius: '4px' }}>
                                    <b>{obs.code_display}</b> • Value: {obs.value_quantity || obs.value_string || obs.value_display || obs.value_code || 'N/A'} {obs.value_unit}
                                  </li>
                                ))}
                                {observations.filter(o => o.encounter_id === selectedEncounterId).length === 0 && <li>None</li>}
                              </ul>
                            )}

                            {activeTab === 'procedures' && (
                              <ul style={{ listStyle: 'none', padding: 0 }}>
                                {procedures.filter(p => p.encounter_id === selectedEncounterId).map(proc => (
                                  <li key={proc.id} style={{ padding: '10px', border: '1px solid #ddd', marginBottom: '5px', borderRadius: '4px' }}>
                                    <b>{proc.procedure_display}</b> • Status: {proc.status}
                                  </li>
                                ))}
                                {procedures.filter(p => p.encounter_id === selectedEncounterId).length === 0 && <li>None</li>}
                              </ul>
                            )}

                            {activeTab === 'specimens' && (
                              <ul style={{ listStyle: 'none', padding: 0 }}>
                                {specimens.filter(s => s.encounter_id === selectedEncounterId).map(spec => (
                                  <li key={spec.id} style={{ padding: '10px', border: '1px solid #ddd', marginBottom: '5px', borderRadius: '4px' }}>
                                    <b>{spec.specimen_type_display}</b> • Status: {spec.status}
                                  </li>
                                ))}
                                {specimens.filter(s => s.encounter_id === selectedEncounterId).length === 0 && <li>None</li>}
                              </ul>
                            )}
                          </div>
                        </div>
                      )}
                    </li>
                  ))}
                  {sortedEncounters.length === 0 && <li className="p-3 text-sm text-gray-500">No encounters</li>}
                </ul>
              </div>

              {/* Row-level details removed; now expanded inline in the encounter row */}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

export default App;
