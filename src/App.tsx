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
  // Pagination state for Patient list
  const [nextCursor, setNextCursor] = useState<string | null>(null);
  const [prevStack, setPrevStack] = useState<string[]>([]);
  const [currentSelfCursor, setCurrentSelfCursor] = useState<string | null>(null);

  // Encounter-scoped medication caches and state
  const [encounterMedReqCache, setEncounterMedReqCache] = useState<Record<string, MedicationRequest[]>>({});
  const [encounterMedAdminCache, setEncounterMedAdminCache] = useState<Record<string, MedicationAdministration[]>>({});
  const [encounterMedRequests, setEncounterMedRequests] = useState<MedicationRequest[]>([]);
  const [encounterMedAdministrations, setEncounterMedAdministrations] = useState<MedicationAdministration[]>([]);
  const [encounterMedLoading, setEncounterMedLoading] = useState<boolean>(false);
  const [encounterAdminLoading, setEncounterAdminLoading] = useState<boolean>(false);
  const [encounterMedNote, setEncounterMedNote] = useState<string | null>(null);
  const [encounterAdminNote, setEncounterAdminNote] = useState<string | null>(null);

  const getEncounterCacheKey = (patientId: string, encounterId: string, kind: 'req'|'admin') => `${patientId}|${encounterId}|${kind}`;

  // Helpers to map FHIR Medication resources consistently
  const mapMedicationRequest = (res: any): MedicationRequest => ({
    id: res.id,
    patient_id: res.subject?.reference?.split('/')[1] || '',
    encounter_id: res.encounter?.reference?.split('/')[1] || '',
    medication_code: res.medicationCodeableConcept?.coding?.[0]?.code || '',
    medication_display: res.medicationCodeableConcept?.coding?.[0]?.display || res.medicationCodeableConcept?.coding?.[0]?.code || 'Unknown Medication',
    medication_system: res.medicationCodeableConcept?.coding?.[0]?.system || '',
    status: res.status || '',
    intent: res.intent || '',
    priority: res.priority || '',
    authored_on: res.authoredOn || '',
    dosage_quantity: res.dosageInstruction?.[0]?.doseAndRate?.[0]?.doseQuantity?.value || 0,
    dosage_unit: res.dosageInstruction?.[0]?.doseAndRate?.[0]?.doseQuantity?.unit || '',
    frequency_code: res.dosageInstruction?.[0]?.timing?.repeat?.frequency || '',
    frequency_display: res.dosageInstruction?.[0]?.timing?.code?.text || '',
    route_code: res.dosageInstruction?.[0]?.route?.coding?.[0]?.code || '',
    route_display: res.dosageInstruction?.[0]?.route?.coding?.[0]?.display || '',
    reason_code: res.reasonCode?.[0]?.coding?.[0]?.code || '',
    reason_display: res.reasonCode?.[0]?.coding?.[0]?.display || ''
  });

  const mapMedicationAdministration = (res: any): MedicationAdministration => ({
    id: res.id,
    patient_id: res.subject?.reference?.split('/')[1] || '',
    encounter_id: res.context?.reference?.split('/')[1] || '',
    medication_code: res.medicationCodeableConcept?.coding?.[0]?.code || '',
    medication_display: res.medicationCodeableConcept?.coding?.[0]?.display || res.medicationCodeableConcept?.coding?.[0]?.code || 'Unknown Medication',
    medication_system: res.medicationCodeableConcept?.coding?.[0]?.system || '',
    status: res.status || '',
    effective_start: res.effectiveDateTime || res.effectivePeriod?.start || '',
    effective_end: res.effectivePeriod?.end || '',
    dosage_quantity: res.dosage?.dose?.value || 0,
    dosage_unit: res.dosage?.dose?.unit || '',
    route_code: res.dosage?.route?.coding?.[0]?.code || '',
    route_display: res.dosage?.route?.coding?.[0]?.display || '',
    site_code: res.dosage?.site?.coding?.[0]?.code || '',
    site_display: res.dosage?.site?.coding?.[0]?.display || '',
    method_code: res.dosage?.method?.coding?.[0]?.code || '',
    method_display: res.dosage?.method?.coding?.[0]?.display || '',
    reason_code: res.reasonCode?.[0]?.coding?.[0]?.code || '',
    reason_display: res.reasonCode?.[0]?.coding?.[0]?.display || ''
  });

  // Generic pagination follower using backend /paginate for link[next]
  const fetchAllPages = async (firstUrl: string) => {
    const all: any[] = [];
    let url: string | null = firstUrl;
    // minimal typing for FHIR Bundle shape
    type BundleLink = { relation: string; url: string };
    type Bundle = { entry?: any[]; link?: BundleLink[] };
    while (url) {
      const page: Bundle = await fetch(url).then(r => r.json());
      if (page.entry) all.push(...page.entry);
      const nextLink = (page.link || []).find((l: BundleLink) => l.relation === 'next');
      url = nextLink ? `${API_BASE}/paginate?cursor=${encodeURIComponent(nextLink.url)}` : null;
    }
    return all;
  };

  const isWithinWindow = (ts: string, start?: string, end?: string) => {
    if (!ts) return false;
    const t = Date.parse(ts);
    const s = start ? Date.parse(start) : undefined;
    const e = end ? Date.parse(end) : undefined;
    if (Number.isNaN(t)) return false;
    if (s && t < s) return false;
    if (e && t > e) return false;
    return true;
  };

  const loadEncounterMedications = async (patientId: string, encId: string, encStart?: string, encEnd?: string) => {
    const cacheKey = getEncounterCacheKey(patientId, encId, 'req');
    if (encounterMedReqCache[cacheKey]) {
      setEncounterMedRequests(encounterMedReqCache[cacheKey]);
    } else {
      setEncounterMedLoading(true);
      setEncounterMedNote(null);
      try {
        // Count first
        const countUrl = `${API_BASE}/MedicationRequest?patient=Patient/${patientId}&encounter=Encounter/${encId}&_summary=count`;
        const count = await fetch(countUrl).then(r => r.json()).then(j => j.total || 0);
        let mapped: MedicationRequest[] = [];
        if (count > 0) {
          const first = `${API_BASE}/MedicationRequest?patient=Patient/${patientId}&encounter=Encounter/${encId}&_count=50`;
          const entries = await fetchAllPages(first);
          mapped = entries.map((e: any) => mapMedicationRequest(e.resource));
        } else {
          // Fallback: fetch patient meds and include those authored within encounter period
          const first = `${API_BASE}/MedicationRequest?patient=Patient/${patientId}&_count=50`;
          const entries = await fetchAllPages(first);
          const all = entries.map((e: any) => mapMedicationRequest(e.resource));
          mapped = all.filter(m => m.encounter_id === encId || isWithinWindow(m.authored_on, encStart, encEnd));
          if (mapped.length > 0) setEncounterMedNote('Including orders inferred by time window (no explicit encounter link)');
        }
        setEncounterMedRequests(mapped);
        setEncounterMedReqCache(prev => ({ ...prev, [cacheKey]: mapped }));
      } finally {
        setEncounterMedLoading(false);
      }
    }
  };

  const loadEncounterAdministrations = async (patientId: string, encId: string, encStart?: string, encEnd?: string) => {
    const cacheKey = getEncounterCacheKey(patientId, encId, 'admin');
    if (encounterMedAdminCache[cacheKey]) {
      setEncounterMedAdministrations(encounterMedAdminCache[cacheKey]);
    } else {
      setEncounterAdminLoading(true);
      setEncounterAdminNote(null);
      try {
        const countUrl = `${API_BASE}/MedicationAdministration?patient=Patient/${patientId}&encounter=Encounter/${encId}&_summary=count`;
        const count = await fetch(countUrl).then(r => r.json()).then(j => j.total || 0);
        let mapped: MedicationAdministration[] = [];
        if (count > 0) {
          const first = `${API_BASE}/MedicationAdministration?patient=Patient/${patientId}&encounter=Encounter/${encId}&_count=50`;
          const entries = await fetchAllPages(first);
          mapped = entries.map((e: any) => mapMedicationAdministration(e.resource));
        } else {
          const first = `${API_BASE}/MedicationAdministration?patient=Patient/${patientId}&_count=50`;
          const entries = await fetchAllPages(first);
          const all = entries.map((e: any) => mapMedicationAdministration(e.resource));
          mapped = all.filter(a => a.encounter_id === encId || isWithinWindow(a.effective_start, encStart, encEnd));
          if (mapped.length > 0) setEncounterAdminNote('Including administrations inferred by time window (no explicit encounter link)');
        }
        setEncounterMedAdministrations(mapped);
        setEncounterMedAdminCache(prev => ({ ...prev, [cacheKey]: mapped }));
      } finally {
        setEncounterAdminLoading(false);
      }
    }
  };

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

  // When selected encounter changes, load encounter-scoped meds (with pagination and fallback)
  useEffect(() => {
    if (!selectedPatient || !selectedEncounterId) return;
    const enc = encounters.find(e => e.id === selectedEncounterId);
    const start = enc?.start_date;
    const end = enc?.end_date;
    // Switch to combined backend endpoint for simplicity
    const url = `${API_BASE}/encounter/medications?patient=Patient/${selectedPatient.id}&encounter=Encounter/${selectedEncounterId}` + (start ? `&start=${encodeURIComponent(start)}` : '') + (end ? `&end=${encodeURIComponent(end)}` : '');
    setEncounterMedLoading(true);
    setEncounterAdminLoading(true);
    setEncounterMedNote(null);
    setEncounterAdminNote(null);
    fetch(url)
      .then(r => r.json())
      .then(data => {
        const reqs: MedicationRequest[] = (data?.requests || []).map((r: any) => ({
          id: r.id, patient_id: r.patient_id, encounter_id: r.encounter_id, medication_code: r.medication_code, medication_display: r.medication_display, medication_system: r.medication_system, status: r.status, intent: r.intent, priority: r.priority, authored_on: r.authored_on, dosage_quantity: 0, dosage_unit: '', frequency_code: '', frequency_display: '', route_code: '', route_display: '', reason_code: '', reason_display: ''
        }));
        const admins: MedicationAdministration[] = (data?.administrations || []).map((a: any) => ({
          id: a.id, patient_id: a.patient_id, encounter_id: a.encounter_id, medication_code: a.medication_code, medication_display: a.medication_display, medication_system: a.medication_system, status: a.status, effective_start: a.effective_start, effective_end: a.effective_end, dosage_quantity: 0, dosage_unit: '', route_code: '', route_display: '', site_code: '', site_display: '', method_code: '', method_display: '', reason_code: '', reason_display: ''
        }));
        setEncounterMedRequests(reqs);
        setEncounterMedAdministrations(admins);
        if (data?.note) { setEncounterMedNote(data.note); setEncounterAdminNote(data.note); }
      })
      .finally(() => { setEncounterMedLoading(false); setEncounterAdminLoading(false); });
  }, [selectedEncounterId]);

  // Helper to map a FHIR Bundle to our patient list and update cursors
  const applyPatientBundle = (bundle: any) => {
    const mapped = bundle.entry ? bundle.entry.map((entry: any) => ({
      id: entry.resource.id,
      family_name: entry.resource.name?.[0]?.family || 'Unknown',
      gender: entry.resource.gender || 'Unknown',
      birth_date: entry.resource.birthDate || 'Unknown',
      race: entry.resource.extension?.find((ext: any) => ext.url === 'http://hl7.org/fhir/us/core/StructureDefinition/us-core-race')?.valueCodeableConcept?.text,
      ethnicity: entry.resource.extension?.find((ext: any) => ext.url === 'http://hl7.org/fhir/us/core/StructureDefinition/us-core-ethnicity')?.valueCodeableConcept?.text,
      birth_sex: entry.resource.extension?.find((ext: any) => ext.url === 'http://hl7.org/fhir/us/core/StructureDefinition/us-core-birthsex')?.valueCode,
      identifier: entry.resource.identifier?.[0]?.value,
      marital_status: entry.resource.maritalStatus?.text,
      deceased_date: entry.resource.deceasedDateTime,
      managing_organization: entry.resource.managingOrganization?.reference
    })) : [];
    setPatients(mapped);

    const links = Array.isArray(bundle.link) ? bundle.link : [];
    const next = links.find((l: any) => l.relation === 'next')?.url || null;
    const self = links.find((l: any) => l.relation === 'self')?.url || null;
    setNextCursor(next);
    setCurrentSelfCursor(self || null);

    if (mapped.length > 0) {
      selectPatient(mapped[0]);
    } else {
      setSelectedPatient(null);
      setPatientSummary(null);
    }
  };

  // Load first page
  const loadFirstPatientsPage = () => {
    setLoading(true);
    setError(null);
    console.log('Fetching patients (page 1) from:', API_BASE);
    fetch(`${API_BASE}/Patient/by-ids?ids=${encodeURIComponent([
      '03632093-8e46-5c64-8d8b-76ce07fa7b35','063ef64a-f642-563f-b9f0-206e1d32b930','08744ed5-b376-5a84-8cca-6b4f61ea633e','10306acb-5f9d-596d-828c-ad1432efb89b','146c9f68-5b1c-5713-a5ea-6a31f0d21543','271cd75b-b278-51fe-a6cf-6efe41c3da2b','2ae93a82-fd85-5a0b-88ac-683b152c7025','2d4ea3ef-5bec-5529-92ce-a9926343b794','408d1f02-a864-599e-ac5c-b358440a801c','4b1cc63a-cbb0-5b64-ac10-f98bc3385292','51b9ffda-5b82-5e91-a8bc-1b8d1e03451b','540ab130-1abc-578d-8f6e-63c1f82bb305','558e0386-a3d3-5bfb-ad28-939133fcc773','5601a622-8a8f-5951-b5e3-17179238462e','56c044dd-8545-57d3-a473-5a285c7311d7','58639ace-d5e3-540d-8d0b-d479e60e2147','5c52d57d-d13a-5f0d-a71d-b489f9b521b3','5f3da891-ffc9-5381-9b37-c139fc99da00','6027f3be-106c-5d2f-a260-6534b5c5c5b2','62a85fdd-29d8-5d34-a217-bd770876cb24','64437fe8-8298-515e-9195-04301b2402c8','68048f1c-c0c9-550e-8bb1-78dc375f2e84','7070642d-2d89-53f3-9803-d0edb424596c','817e8a08-7dcb-51e1-ad8a-b516d82105ef','81c60b68-489e-5464-aa80-a8b66703285b','8e77dd0b-932d-5790-9ba6-5c6df8434457','91b0e6ff-bdb7-523c-b0bb-22b5a2a70b3f','92091486-6cbc-53d0-8a01-6df6e3ca6455','962d6bd6-a1ed-58be-a9ca-30cd88be29de','96b32ca3-178c-5974-aa33-c18706ee473f','a33a2ab3-b8d6-5124-b768-b796fc2d2dd5','a4b7554d-09c9-567a-8b4b-4b282362e510','ad1ff22c-ce53-5dc0-8cca-e1081d59449d','ae082d90-8911-5df9-910f-0fdb3565e830','b2d5983f-72df-5009-9453-a9e3a33a7e32','b84dffcf-f665-5b90-b220-e885889044c6','b853fc07-c16c-57d5-9717-6222ea9ad34e','bdc2b86a-6f4e-5acc-8205-75c46c6c2788','bec8f6a0-ca78-5ae2-aa20-3c9855eb7020','c105f41b-d00f-527e-aec1-475b17e98733','c4c140ee-66ed-570a-acf6-b1b1c8e660b3','c7ff882e-20c3-519e-bfbc-47a9b593c665','db229499-93a2-5118-8195-33a48505a489','dc8b0319-70b6-5467-8c78-7c0bb4e370d8','e26f28b0-c110-5598-83ff-f369ebb5642b','e5fe9e20-47d3-5287-b97d-a1de25e8a7c3','e6eb2f3a-47e9-5837-a89d-37faf9bc073d','f2464461-71fe-5800-aebf-39d65a5b4037','f549d909-2219-5b6c-bc8d-b305089ed406','f5a9fc1e-22b2-5289-b89b-3a4630a4c8f0','f6bfab69-6556-5e1e-886b-46576a5c6980','fcac65bf-eb99-5ac1-a90c-3ebe20083ce6','fca25cfa-fe5d-586b-a231-8e97106ad7c5','4adc57a7-71a4-5fed-a6e0-bd8b59a261f2','727be2fe-b941-5561-bce0-6778e090f594'].join(', '))}`)
      .then(res => res.json())
      .then(bundle => {
        setPrevStack([]);
        // When we drive by IDs, there is no next/prev. Apply bundle directly.
        applyPatientBundle(bundle);
      })
      .catch(() => setError('Failed to fetch patients'))
      .finally(() => setLoading(false));
  };

  // --- Search helpers ---
  const parsePatientBundle = (bundle: any): Patient[] => {
    return bundle.entry ? bundle.entry.map((entry: any) => ({
      id: entry.resource.id,
      family_name: entry.resource.name?.[0]?.family || 'Unknown',
      gender: entry.resource.gender || 'Unknown',
      birth_date: entry.resource.birthDate || 'Unknown',
      identifier: entry.resource.identifier?.[0]?.value || ''
    })) : [];
  };

  const isUUID = (s: string) => /[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}/.test(s);

  const searchPatientsByQuery = async (q: string): Promise<Patient[]> => {
    if (q.trim().length === 0) return [];
    const url = `${API_BASE}/search/patients?q=${encodeURIComponent(q.trim())}`;
    const bundle = await fetch(url).then(r => r.json());
    return parsePatientBundle(bundle);
  };

  // Navigate to a page via backend /paginate
  const loadByCursor = (cursor: string, goingBack: boolean) => {
    setLoading(true);
    setError(null);
    fetch(`${API_BASE}/paginate?cursor=${encodeURIComponent(cursor)}`)
      .then(res => res.json())
      .then(bundle => {
        applyPatientBundle(bundle);
        // If we went back, prevStack already popped by caller
      })
      .catch(() => setError('Failed to paginate patients'))
      .finally(() => setLoading(false));
  };

  // Handlers for Next/Prev
  const handleNextPage = () => {
    if (!nextCursor) return;
    if (currentSelfCursor) {
      setPrevStack(prev => [...prev, currentSelfCursor]);
    }
    loadByCursor(nextCursor, false);
  };

  const handlePrevPage = () => {
    if (prevStack.length === 0) return;
    const prev = prevStack[prevStack.length - 1];
    setPrevStack(stack => stack.slice(0, stack.length - 1));
    loadByCursor(prev, true);
  };

  useEffect(() => {
    loadFirstPatientsPage();
  }, []);

  const selectPatient = (patient: Patient) => {
    setSelectedPatient(patient);
    setLoading(true);
    setError(null);
    setActiveTab('conditions');
    
    // Fetch patient summary via combined backend endpoint
    fetch(`${API_BASE}/patients/summary?patient=Patient/${patient.id}`)
      .then(r => r.json())
      .then(data => {
        const ps: PatientSummary = {
          patient,
          summary: {
            conditions: data?.summary?.conditions || 0,
            medications: data?.summary?.medications || 0,
            encounters: data?.summary?.encounters || 0,
            medication_administrations: data?.summary?.medication_administrations || 0,
            medication_requests: data?.summary?.medications || 0,
            observations: data?.summary?.observations || 0,
            procedures: data?.summary?.procedures || 0,
            specimens: data?.summary?.specimens || 0,
          }
        };
        setPatientSummary(ps);
      })
      .catch(() => {
        const fallback: PatientSummary = {
          patient,
          summary: {
            conditions: 0,
            medications: 0,
            encounters: 0,
            medication_administrations: 0,
            medication_requests: 0,
            observations: 0,
            procedures: 0,
            specimens: 0,
          }
        };
        setPatientSummary(fallback);
      });
    
    // Fetch all data types using FHIR endpoints
    const fetchPromises = [
      fetch(`${API_BASE}/Condition?patient=Patient/${patient.id}&_count=100`).then(res => res.json()).then(data => {
        const conditions = data.entry ? data.entry.map((entry: any) => ({
          id: entry.resource.id,
          code: entry.resource.code?.coding?.[0]?.code || '',
          code_system: entry.resource.code?.coding?.[0]?.system || '',
          code_display: entry.resource.code?.text || entry.resource.code?.coding?.[0]?.display || '',
          patient_id: entry.resource.subject?.reference?.split('/')[1] || '',
          category: entry.resource.category?.[0]?.coding?.[0]?.display || '',
          encounter_id: entry.resource.encounter?.reference?.split('/')[1] || '',
          status: entry.resource.clinicalStatus?.coding?.[0]?.code || ''
        })) : [];
        setConditions(conditions);
      }).catch(() => setConditions([])),
      
             fetch(`${API_BASE}/MedicationRequest?patient=Patient/${patient.id}&_count=100`).then(res => res.json()).then(data => {
         const medications = data.entry ? data.entry.map((entry: any) => ({
           id: entry.resource.id,
           patient_id: entry.resource.subject?.reference?.split('/')[1] || '',
           medication_code: entry.resource.medicationCodeableConcept?.coding?.[0]?.code || '',
           medication_display: entry.resource.medicationCodeableConcept?.coding?.[0]?.code || entry.resource.medicationCodeableConcept?.coding?.[0]?.display || 'Unknown Medication',
           medication_system: entry.resource.medicationCodeableConcept?.coding?.[0]?.system || '',
           status: entry.resource.status || '',
           quantity: entry.resource.dispenseRequest?.quantity?.value || 0,
           quantity_unit: entry.resource.dispenseRequest?.quantity?.unit || '',
           days_supply: entry.resource.dispenseRequest?.expectedSupplyDuration?.value || 0,
           dispense_date: entry.resource.authoredOn || '',
           encounter_id: entry.resource.encounter?.reference?.split('/')[1] || ''
         })) : [];
         setMedications(medications);
       }).catch(() => setMedications([])),
      
      fetch(`${API_BASE}/Encounter?patient=Patient/${patient.id}&_count=100`).then(res => res.json()).then(data => {
        const encounters = data.entry ? data.entry.map((entry: any) => ({
          id: entry.resource.id,
          patient_id: entry.resource.subject?.reference?.split('/')[1] || '',
          encounter_type: entry.resource.class?.code || '',
          status: entry.resource.status || '',
          start_date: entry.resource.period?.start || '',
          end_date: entry.resource.period?.end || '',
          class_code: entry.resource.class?.code || '',
          class_display: entry.resource.class?.display || '',
          service_type: entry.resource.serviceType?.coding?.[0]?.display || '',
          priority_code: entry.resource.priority?.coding?.[0]?.code || '',
          priority_display: entry.resource.priority?.coding?.[0]?.display || '',
          diagnosis_condition: entry.resource.diagnosis?.[0]?.condition?.reference || '',
          diagnosis_use: entry.resource.diagnosis?.[0]?.use?.coding?.[0]?.code || '',
          diagnosis_rank: entry.resource.diagnosis?.[0]?.rank || 0,
          hospitalization_admit_source_code: entry.resource.hospitalization?.admitSource?.coding?.[0]?.code || '',
          hospitalization_admit_source_display: entry.resource.hospitalization?.admitSource?.coding?.[0]?.display || '',
          hospitalization_discharge_disposition_code: entry.resource.hospitalization?.dischargeDisposition?.coding?.[0]?.code || '',
          hospitalization_discharge_disposition_display: entry.resource.hospitalization?.dischargeDisposition?.coding?.[0]?.display || ''
        })) : [];
        setEncounters(encounters);
        if (encounters.length > 0) {
          const sorted = [...encounters].sort((a, b) => Date.parse(b.start_date || b.end_date || '') - Date.parse(a.start_date || a.end_date || ''));
          setSelectedEncounterId(sorted[0]?.id || null);
        } else {
          setSelectedEncounterId(null);
        }
      }).catch(() => setEncounters([])),
      
             fetch(`${API_BASE}/MedicationAdministration?patient=Patient/${patient.id}&_count=100`).then(res => res.json()).then(data => {
         console.log('MedicationAdministration data for patient', patient.id, ':', data);
         const administrations = data.entry ? data.entry.map((entry: any) => ({
           id: entry.resource.id,
           patient_id: entry.resource.subject?.reference?.split('/')[1] || '',
           encounter_id: entry.resource.context?.reference?.split('/')[1] || '',
           medication_code: entry.resource.medicationCodeableConcept?.coding?.[0]?.code || '',
           medication_display: entry.resource.medicationCodeableConcept?.coding?.[0]?.display || entry.resource.medicationCodeableConcept?.coding?.[0]?.code || 'Unknown Medication',
           medication_system: entry.resource.medicationCodeableConcept?.coding?.[0]?.system || '',
           status: entry.resource.status || '',
           effective_start: entry.resource.effectiveDateTime || entry.resource.effectivePeriod?.start || '',
           effective_end: entry.resource.effectivePeriod?.end || '',
           dosage_quantity: entry.resource.dosage?.dose?.value || 0,
           dosage_unit: entry.resource.dosage?.dose?.unit || '',
           route_code: entry.resource.dosage?.route?.coding?.[0]?.code || '',
           route_display: entry.resource.dosage?.route?.coding?.[0]?.display || '',
           site_code: entry.resource.dosage?.site?.coding?.[0]?.code || '',
           site_display: entry.resource.dosage?.site?.coding?.[0]?.display || '',
           method_code: entry.resource.dosage?.method?.coding?.[0]?.code || '',
           method_display: entry.resource.dosage?.method?.coding?.[0]?.display || '',
           reason_code: entry.resource.reasonCode?.[0]?.coding?.[0]?.code || '',
           reason_display: entry.resource.reasonCode?.[0]?.coding?.[0]?.display || ''
         })) : [];
         setMedicationAdministrations(administrations);
       }).catch(() => setMedicationAdministrations([])),
      
             fetch(`${API_BASE}/MedicationRequest?patient=Patient/${patient.id}&_count=100`).then(res => res.json()).then(data => {
         console.log('MedicationRequest data for patient', patient.id, ':', data);
         const requests = data.entry ? data.entry.map((entry: any) => ({
           id: entry.resource.id,
           patient_id: entry.resource.subject?.reference?.split('/')[1] || '',
           encounter_id: entry.resource.encounter?.reference?.split('/')[1] || '',
           medication_code: entry.resource.medicationCodeableConcept?.coding?.[0]?.code || '',
           medication_display: entry.resource.medicationCodeableConcept?.coding?.[0]?.code || entry.resource.medicationCodeableConcept?.coding?.[0]?.display || 'Unknown Medication',
           medication_system: entry.resource.medicationCodeableConcept?.coding?.[0]?.system || '',
           status: entry.resource.status || '',
           intent: entry.resource.intent || '',
           priority: entry.resource.priority || '',
           authored_on: entry.resource.authoredOn || '',
           dosage_quantity: entry.resource.dosageInstruction?.[0]?.doseAndRate?.[0]?.doseQuantity?.value || 0,
           dosage_unit: entry.resource.dosageInstruction?.[0]?.doseAndRate?.[0]?.doseQuantity?.unit || '',
           frequency_code: entry.resource.dosageInstruction?.[0]?.timing?.repeat?.frequency || '',
           frequency_display: entry.resource.dosageInstruction?.[0]?.timing?.code?.text || '',
           route_code: entry.resource.dosageInstruction?.[0]?.route?.coding?.[0]?.code || '',
           route_display: entry.resource.dosageInstruction?.[0]?.route?.coding?.[0]?.display || '',
           reason_code: entry.resource.reasonCode?.[0]?.coding?.[0]?.code || '',
           reason_display: entry.resource.reasonCode?.[0]?.coding?.[0]?.display || ''
         })) : [];
         setMedicationRequests(requests);
       }).catch(() => setMedicationRequests([])),
      
      fetch(`${API_BASE}/Observation?patient=Patient/${patient.id}&_count=100`).then(res => res.json()).then(data => {
        const observations = data.entry ? data.entry.map((entry: any) => ({
          id: entry.resource.id,
          patient_id: entry.resource.subject?.reference?.split('/')[1] || '',
          encounter_id: entry.resource.encounter?.reference?.split('/')[1] || '',
          observation_type: entry.resource.category?.[0]?.coding?.[0]?.display || '',
          code: entry.resource.code?.coding?.[0]?.code || '',
          code_display: entry.resource.code?.text || entry.resource.code?.coding?.[0]?.display || '',
          code_system: entry.resource.code?.coding?.[0]?.system || '',
          status: entry.resource.status || '',
          effective_datetime: entry.resource.effectiveDateTime || '',
          issued_datetime: entry.resource.issued || '',
          value_quantity: entry.resource.valueQuantity?.value || 0,
          value_unit: entry.resource.valueQuantity?.unit || '',
          value_code: entry.resource.valueCodeableConcept?.coding?.[0]?.code || '',
          value_display: entry.resource.valueCodeableConcept?.coding?.[0]?.display || '',
          value_string: entry.resource.valueString || '',
          value_boolean: entry.resource.valueBoolean || false,
          value_datetime: entry.resource.valueDateTime || '',
          category_code: entry.resource.category?.[0]?.coding?.[0]?.code || '',
          category_display: entry.resource.category?.[0]?.coding?.[0]?.display || '',
          interpretation_code: entry.resource.interpretation?.[0]?.coding?.[0]?.code || '',
          interpretation_display: entry.resource.interpretation?.[0]?.coding?.[0]?.display || '',
          reference_range_low: entry.resource.referenceRange?.[0]?.low?.value || 0,
          reference_range_high: entry.resource.referenceRange?.[0]?.high?.value || 0,
          reference_range_unit: entry.resource.referenceRange?.[0]?.low?.unit || ''
        })) : [];
        setObservations(observations);
      }).catch(() => setObservations([])),
      
      fetch(`${API_BASE}/Procedure?patient=Patient/${patient.id}&_count=100`).then(res => res.json()).then(data => {
        const procedures = data.entry ? data.entry.map((entry: any) => ({
          id: entry.resource.id,
          patient_id: entry.resource.subject?.reference?.split('/')[1] || '',
          encounter_id: entry.resource.encounter?.reference?.split('/')[1] || '',
          procedure_code: entry.resource.code?.coding?.[0]?.code || '',
          procedure_display: entry.resource.code?.text || entry.resource.code?.coding?.[0]?.display || '',
          procedure_system: entry.resource.code?.coding?.[0]?.system || '',
          status: entry.resource.status || '',
          performed_datetime: entry.resource.performedDateTime || '',
          performed_period_start: entry.resource.performedPeriod?.start || '',
          performed_period_end: entry.resource.performedPeriod?.end || '',
          category_code: entry.resource.category?.coding?.[0]?.code || '',
          category_display: entry.resource.category?.coding?.[0]?.display || '',
          reason_code: entry.resource.reasonCode?.[0]?.coding?.[0]?.code || '',
          reason_display: entry.resource.reasonCode?.[0]?.coding?.[0]?.display || '',
          outcome_code: entry.resource.outcome?.coding?.[0]?.code || '',
          outcome_display: entry.resource.outcome?.coding?.[0]?.display || '',
          complication_code: entry.resource.complication?.[0]?.coding?.[0]?.code || '',
          complication_display: entry.resource.complication?.[0]?.coding?.[0]?.display || '',
          follow_up_code: entry.resource.followUp?.[0]?.coding?.[0]?.code || '',
          follow_up_display: entry.resource.followUp?.[0]?.coding?.[0]?.display || ''
        })) : [];
        setProcedures(procedures);
      }).catch(() => setProcedures([])),
      
      fetch(`${API_BASE}/Specimen?patient=Patient/${patient.id}&_count=100`).then(res => res.json()).then(data => {
        const specimens = data.entry ? data.entry.map((entry: any) => ({
          id: entry.resource.id,
          patient_id: entry.resource.subject?.reference?.split('/')[1] || '',
          encounter_id: entry.resource.encounter?.reference?.split('/')[1] || '',
          specimen_type_code: entry.resource.type?.coding?.[0]?.code || '',
          specimen_type_display: entry.resource.type?.text || entry.resource.type?.coding?.[0]?.display || '',
          specimen_type_system: entry.resource.type?.coding?.[0]?.system || '',
          status: entry.resource.status || '',
          collected_datetime: entry.resource.collection?.collectedDateTime || '',
          received_datetime: entry.resource.receivedTime || '',
          collection_method_code: entry.resource.collection?.method?.coding?.[0]?.code || '',
          collection_method_display: entry.resource.collection?.method?.coding?.[0]?.display || '',
          body_site_code: entry.resource.collection?.bodySite?.coding?.[0]?.code || '',
          body_site_display: entry.resource.collection?.bodySite?.coding?.[0]?.display || '',
          fasting_status_code: entry.resource.fastingStatus?.coding?.[0]?.code || '',
          fasting_status_display: entry.resource.fastingStatus?.coding?.[0]?.display || '',
          container_code: entry.resource.container?.[0]?.type?.coding?.[0]?.code || '',
          container_display: entry.resource.container?.[0]?.type?.coding?.[0]?.display || '',
          note: entry.resource.note?.[0]?.text || ''
        })) : [];
        setSpecimens(specimens);
      }).catch(() => setSpecimens([]))
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
              searchPatientsByQuery(searchQuery)
                .then(list => {
                  setSearchResults([]);
                  setSearchPatients(list);
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
              searchPatientsByQuery(searchQuery)
                .then(list => {
                  setSearchResults([]);
                  setSearchPatients(list);
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
          <div className="mt-3 flex items-center gap-2">
            <button
              onClick={handlePrevPage}
              disabled={prevStack.length === 0}
              className={`px-3 py-1 rounded border ${prevStack.length === 0 ? 'opacity-50 cursor-not-allowed' : 'hover:bg-gray-50 dark:hover:bg-neutral-800'}`}
            >
              Prev
            </button>
            <button
              onClick={handleNextPage}
              disabled={!nextCursor}
              className={`px-3 py-1 rounded border ${!nextCursor ? 'opacity-50 cursor-not-allowed' : 'hover:bg-gray-50 dark:hover:bg-neutral-800'}`}
            >
              Next
            </button>
            <div className="text-xs text-gray-500 ml-2">Page size: 25</div>
          </div>
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
                      className={"p-3 cursor-pointer hover:bg-gray-50 dark:hover:bg-neutral-800 border-l-4 " + (selectedEncounterId === enc.id ? 'bg-blue-100 dark:bg-blue-900/30 border-blue-500' : 'border-transparent')}
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

                          {activeTab === 'medications' && selectedEncounterId && (
                              <ul style={{ listStyle: 'none', padding: 0 }}>
                              {(encounterMedLoading ? [] : encounterMedRequests).map(med => (
                                  <li key={med.id} style={{ padding: '15px', border: '1px solid #ddd', marginBottom: '8px', borderRadius: '6px' }}>
                                    <div style={{ marginBottom: '8px' }}>
                                      <b style={{ fontSize: '16px', color: '#2563eb' }}>{med.medication_display}</b>
                                      <span style={{ fontSize: '12px', color: '#6b7280', marginLeft: '8px' }}>({med.medication_code})</span>
                                    </div>
                                    <div style={{ fontSize: '14px', lineHeight: '1.5' }}>
                                      <div><strong>Status:</strong> {med.status}</div>
                                      <div><strong>Intent:</strong> {med.intent}</div>
                                      <div><strong>Priority:</strong> {med.priority}</div>
                                      <div><strong>Dosage:</strong> {med.dosage_quantity} {med.dosage_unit}</div>
                                      <div><strong>Route:</strong> {med.route_display || med.route_code}</div>
                                      <div><strong>Frequency:</strong> {med.frequency_display || med.frequency_code}</div>
                                      <div><strong>Authored:</strong> {med.authored_on}</div>
                                    </div>
                                  </li>
                                ))}
                              {encounterMedLoading && <li>Loading...</li>}
                              {!encounterMedLoading && encounterMedRequests.length === 0 && <li>None</li>}
                              {encounterMedNote && !encounterMedLoading && (
                                <li className="text-xs text-gray-500">{encounterMedNote}</li>
                              )}
                              </ul>
                            )}

                          {activeTab === 'medication-administrations' && selectedEncounterId && (
                              <ul style={{ listStyle: 'none', padding: 0 }}>
                              {(encounterAdminLoading ? [] : encounterMedAdministrations).slice(0, 100).map(admin => (
                                  <li key={admin.id} style={{ padding: '10px', border: '1px solid #ddd', marginBottom: '5px', borderRadius: '4px' }}>
                                    <b>{admin.medication_display}</b> • Status: {admin.status} • Dosage: {admin.dosage_quantity} {admin.dosage_unit}
                                  </li>
                                ))}
                              {encounterAdminLoading && <li>Loading...</li>}
                              {!encounterAdminLoading && encounterMedAdministrations.length === 0 && <li>None</li>}
                              {encounterAdminNote && !encounterAdminLoading && (
                                <li className="text-xs text-gray-500">{encounterAdminNote}</li>
                              )}
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
