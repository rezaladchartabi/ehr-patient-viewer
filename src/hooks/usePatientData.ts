import { useState, useCallback, useMemo } from 'react';

// Types
export interface Patient {
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
  allergies?: Allergy[];
}

export interface Allergy {
  id: string;
  patient_id: string;
  code: string;
  code_display: string;
  code_system: string;
  category: string;
  clinical_status: string;
  verification_status: string;
  type: string;
  criticality: string;
  onset_date: string;
  recorded_date: string;
  recorder: string;
  asserter: string;
  last_occurrence: string;
  note: string;
}

export interface Condition {
  id: string;
  code: string;
  code_system: string;
  code_display: string;
  patient_id: string;
  category: string;
  encounter_id: string;
  status: string;
}

export interface Encounter {
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

export interface MedicationRequest {
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

export interface MedicationAdministration {
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

export interface Observation {
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

export interface Procedure {
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

export interface Specimen {
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

export interface PatientSummary {
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

export interface EncounterData {
  conditions: Condition[];
  medicationRequests: MedicationRequest[];
  medicationAdministrations: MedicationAdministration[];
  observations: Observation[];
  procedures: Procedure[];
  specimens: Specimen[];
  note?: string;
}

// Cache for patient data
const patientDataCache = new Map<string, {
  data: any;
  timestamp: number;
  ttl: number;
}>();

const CACHE_TTL = 5 * 60 * 1000; // 5 minutes

// Utility functions
const isCacheValid = (timestamp: number, ttl: number) => {
  return Date.now() - timestamp < ttl;
};

const clearExpiredCache = () => {
  const now = Date.now();
  Array.from(patientDataCache.entries()).forEach(([key, value]) => {
    if (!isCacheValid(value.timestamp, value.ttl)) {
      patientDataCache.delete(key);
    }
  });
};

const getCacheKey = (patientId: string, encounterId?: string, resourceType?: string) => {
  return `${patientId}:${encounterId || 'all'}:${resourceType || 'all'}`;
};

// API base URL
const API_BASE = process.env.REACT_APP_API_URL || 'https://ehr-backend-87r9.onrender.com';

export const usePatientData = () => {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [currentPatient, setCurrentPatient] = useState<Patient | null>(null);
  const [patientSummary, setPatientSummary] = useState<PatientSummary | null>(null);
  const [encounters, setEncounters] = useState<Encounter[]>([]);
  const [conditions, setConditions] = useState<Condition[]>([]);
  const [encounterData, setEncounterData] = useState<Map<string, EncounterData>>(new Map());

  // Clear expired cache entries periodically
  useMemo(() => {
    const interval = setInterval(clearExpiredCache, 60000); // Every minute
    return () => clearInterval(interval);
  }, []);

  // Fetch patient summary and basic data
  const fetchPatientData = useCallback(async (patient: Patient) => {
    const cacheKey = getCacheKey(patient.id);
    const cached = patientDataCache.get(cacheKey);
    
    if (cached && isCacheValid(cached.timestamp, cached.ttl)) {
      setPatientSummary(cached.data.summary);
      setEncounters(cached.data.encounters);
      setConditions(cached.data.conditions);
      setCurrentPatient({ ...patient, allergies: cached.data.allergies });
      return;
    }

    setLoading(true);
    setError(null);

    try {
      // Parallel fetch for better performance
      const [summaryRes, encountersRes, conditionsRes, allergiesRes] = await Promise.all([
        fetch(`${API_BASE}/patients/summary?patient=Patient/${patient.id}`),
        fetch(`${API_BASE}/Encounter?patient=Patient/${patient.id}&_count=100`),
        fetch(`${API_BASE}/Condition?patient=Patient/${patient.id}&_count=100`),
        fetch(`${API_BASE}/AllergyIntolerance?patient=Patient/${patient.id}&_count=100`)
      ]);

      const [summaryData, encountersData, conditionsData, allergiesData] = await Promise.all([
        summaryRes.json(),
        encountersRes.json(),
        conditionsRes.json(),
        allergiesRes.json()
      ]);

      // Process encounters
      const processedEncounters = encountersData.entry ? encountersData.entry.map((entry: any) => ({
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

      // Process conditions
      const processedConditions = conditionsData.entry ? conditionsData.entry.map((entry: any) => ({
        id: entry.resource.id,
        code: entry.resource.code?.coding?.[0]?.code || '',
        code_system: entry.resource.code?.coding?.[0]?.system || '',
        code_display: entry.resource.code?.text || entry.resource.code?.coding?.[0]?.display || '',
        patient_id: entry.resource.subject?.reference?.split('/')[1] || '',
        category: entry.resource.category?.[0]?.coding?.[0]?.display || '',
        encounter_id: entry.resource.encounter?.reference?.split('/')[1] || '',
        status: entry.resource.clinicalStatus?.coding?.[0]?.code || ''
      })) : [];

      // Process allergies
      const processedAllergies = allergiesData.entry ? allergiesData.entry.map((entry: any) => ({
        id: entry.resource.id,
        patient_id: entry.resource.patient?.reference?.split('/')[1] || '',
        code: entry.resource.code?.coding?.[0]?.code || '',
        code_display: entry.resource.code?.text || entry.resource.code?.coding?.[0]?.display || '',
        code_system: entry.resource.code?.coding?.[0]?.system || '',
        category: entry.resource.category?.[0]?.coding?.[0]?.display || '',
        clinical_status: entry.resource.clinicalStatus?.coding?.[0]?.code || '',
        verification_status: entry.resource.verificationStatus?.coding?.[0]?.code || '',
        type: entry.resource.type?.[0]?.coding?.[0]?.display || '',
        criticality: entry.resource.criticality?.coding?.[0]?.code || '',
        onset_date: entry.resource.onsetDateTime || '',
        recorded_date: entry.resource.recordedDate || '',
        recorder: entry.resource.recorder?.display || '',
        asserter: entry.resource.asserter?.display || '',
        last_occurrence: entry.resource.lastOccurrence || '',
        note: entry.resource.note?.[0]?.text || ''
      })) : [];

      // Create patient summary
      const summary: PatientSummary = {
        patient: { ...patient, allergies: processedAllergies },
        summary: {
          conditions: summaryData?.summary?.conditions || 0,
          medications: summaryData?.summary?.medications || 0,
          encounters: summaryData?.summary?.encounters || 0,
          medication_administrations: summaryData?.summary?.medication_administrations || 0,
          medication_requests: summaryData?.summary?.medication_requests || 0,
          observations: summaryData?.summary?.observations || 0,
          procedures: summaryData?.summary?.procedures || 0,
          specimens: summaryData?.summary?.specimens || 0,
        }
      };

      // Cache the data
      patientDataCache.set(cacheKey, {
        data: { summary, encounters: processedEncounters, conditions: processedConditions, allergies: processedAllergies },
        timestamp: Date.now(),
        ttl: CACHE_TTL
      });

      setPatientSummary(summary);
      setEncounters(processedEncounters);
      setConditions(processedConditions);
      setCurrentPatient({ ...patient, allergies: processedAllergies });

    } catch (err: any) {
      setError(`Failed to fetch patient data: ${err.message}`);
    } finally {
      setLoading(false);
    }
  }, []);

  // Fetch encounter-specific data
  const fetchEncounterData = useCallback(async (patientId: string, encounterId: string) => {
    const cacheKey = getCacheKey(patientId, encounterId, 'encounter');
    const cached = patientDataCache.get(cacheKey);
    
    if (cached && isCacheValid(cached.timestamp, cached.ttl)) {
      setEncounterData(prev => new Map(prev.set(encounterId, cached.data)));
      return;
    }

    const encounter = encounters.find(e => e.id === encounterId);
    if (!encounter) return;

    try {
      const params = new URLSearchParams({
        patient: `Patient/${patientId}`,
        encounter: `Encounter/${encounterId}`
      });
      
      if (encounter.start_date) params.append('start', encounter.start_date);
      if (encounter.end_date) params.append('end', encounter.end_date);

      // Parallel fetch for all encounter data
      const [medsRes, obsRes, procRes, specRes] = await Promise.all([
        fetch(`${API_BASE}/encounter/medications?${params.toString()}`),
        fetch(`${API_BASE}/encounter/observations?${params.toString()}`),
        fetch(`${API_BASE}/encounter/procedures?${params.toString()}`),
        fetch(`${API_BASE}/encounter/specimens?${params.toString()}`)
      ]);

      const [medsData, obsData, procData, specData] = await Promise.all([
        medsRes.json(),
        obsRes.json(),
        procRes.json(),
        specRes.json()
      ]);

      // Process the data
      const encounterData: EncounterData = {
        conditions: conditions.filter(c => c.encounter_id === encounterId),
        medicationRequests: medsData.requests || [],
        medicationAdministrations: medsData.administrations || [],
        observations: obsData.observations || [],
        procedures: procData.procedures || [],
        specimens: specData.specimens || [],
        note: medsData.note || obsData.note || procData.note || specData.note
      };

      // Cache the encounter data
      patientDataCache.set(cacheKey, {
        data: encounterData,
        timestamp: Date.now(),
        ttl: CACHE_TTL
      });

      setEncounterData(prev => new Map(prev.set(encounterId, encounterData)));

    } catch (err: any) {
      console.error('Failed to fetch encounter data:', err);
    }
  }, [encounters, conditions]);

  // Get sorted encounters
  const sortedEncounters = useMemo(() => {
    return [...encounters].sort((a, b) => {
      const aTime = Date.parse(a.start_date || a.end_date || '');
      const bTime = Date.parse(b.start_date || b.end_date || '');
      return bTime - aTime; // Most recent first
    });
  }, [encounters]);

  // Clear all data
  const clearData = useCallback(() => {
    setCurrentPatient(null);
    setPatientSummary(null);
    setEncounters([]);
    setConditions([]);
    setEncounterData(new Map());
    setError(null);
  }, []);

  return {
    // State
    loading,
    error,
    currentPatient,
    patientSummary,
    encounters: sortedEncounters,
    conditions,
    encounterData,
    
    // Actions
    fetchPatientData,
    fetchEncounterData,
    clearData,
    
    // Utilities
    getEncounterData: (encounterId: string) => encounterData.get(encounterId)
  };
};
