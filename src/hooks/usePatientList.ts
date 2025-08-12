import { useState, useCallback, useMemo } from 'react';
import { Patient } from './usePatientData';

// Cache for patient list data
const patientListCache = new Map<string, {
  data: Patient[];
  timestamp: number;
  ttl: number;
}>();

const CACHE_TTL = 10 * 60 * 1000; // 10 minutes for patient list

// Utility functions
const isCacheValid = (timestamp: number, ttl: number) => {
  return Date.now() - timestamp < ttl;
};

const clearExpiredCache = () => {
  const now = Date.now();
  Array.from(patientListCache.entries()).forEach(([key, value]) => {
    if (!isCacheValid(value.timestamp, value.ttl)) {
      patientListCache.delete(key);
    }
  });
};

const getCacheKey = (cursor?: string, allowlist?: string[]) => {
  if (allowlist && allowlist.length > 0) {
    return `allowlist:${allowlist.join(',')}`;
  }
  return `cursor:${cursor || 'initial'}`;
};

// API base URL
const API_BASE = process.env.REACT_APP_API_URL || 'https://ehr-backend-87r9.onrender.com';

// Allowlist IDs for specific patients (only real IDs from FHIR server)
const ALLOWLIST_IDS = [
  '03632093-8e46-5c64-8d8b-76ce07fa7b35',
  '063ef64a-f642-563f-b9f0-206e1d32b930',
  '08744ed5-b376-5a84-8cca-6b4f61ea633e',
  '10306acb-5f9d-596d-828c-ad1432efb89b',
  '146c9f68-5b1c-5713-a5ea-6a31f0d21543',
  '271cd75b-b278-51fe-a6cf-6efe41c3da2b',
  '2ae93a82-fd85-5a0b-88ac-683b152c7025',
  '2d4ea3ef-5bec-5529-92ce-a9926343b794',
  '408d1f02-a864-599e-ac5c-b358440a801c',
  '4b1cc63a-cbb0-5b64-ac10-f98bc3385292',
  '51b9ffda-5b82-5e91-a8bc-1b8d1e03451b',
  '540ab130-1abc-578d-8f6e-63c1f82bb305',
  '558e0386-a3d3-5bfb-ad28-939133fcc773',
  '5601a622-8a8f-5951-b5e3-17179238462e',
  '56c044dd-8545-57d3-a473-5a285c7311d7',
  '58639ace-d5e3-540d-8d0b-d479e60e2147',
  '5c52d57d-d13a-5f0d-a71d-b489f9b521b3',
  '5f3da891-ffc9-5381-9b37-c139fc99da00',
  '6027f3be-106c-5d2f-a260-6534b5c5c5b2',
  '62a85fdd-29d8-5d34-a217-bd770876cb24',
  '64437fe8-8298-515e-9195-04301b2402c8',
  '68048f1c-c0c9-550e-8bb1-78dc375f2e84',
  '7070642d-2d89-53f3-9803-d0edb424596c',
  '817e8a08-7dcb-51e1-ad8a-b516d82105ef',
  '81c60b68-489e-5464-aa80-a8b66703285b',
  '8e77dd0b-932d-5790-9ba6-5c6df8434457',
  '91b0e6ff-bdb7-523c-b0bb-22b5a2a70b3f',
  '92091486-6cbc-53d0-8a01-6df6e3ca6455',
  '962d6bd6-a1ed-58be-a9ca-30cd88be29de',
  '96b32ca3-178c-5974-aa33-c18706ee473f',
  'a33a2ab3-b8d6-5124-b768-b796fc2d2dd5',
  'a4b7554d-09c9-567a-8b4b-4b282362e510',
  'ad1ff22c-ce53-5dc0-8cca-e1081d59449d',
  'ae082d90-8911-5df9-910f-0fdb3565e830',
  'b2d5983f-72df-5009-9453-a9e3a33a7e32',
  'b84dffcf-f665-5b90-b220-e885889044c6',
  'b853fc07-c16c-57d5-9717-6222ea9ad34e',
  'bdc2b86a-6f4e-5acc-8205-75c46c6c2788',
  'bec8f6a0-ca78-5ae2-aa20-3c9855eb7020',
  'c105f41b-d00f-527e-aec1-475b17e98733',
  'c4c140ee-66ed-570a-acf6-b1b1c8e660b3',
  'c7ff882e-20c3-519e-bfbc-47a9b593c665',
  'db229499-93a2-5118-8195-33a48505a489',
  'dc8b0319-70b6-5467-8c78-7c0bb4e370d8',
  'e26f28b0-c110-5598-83ff-f369ebb5642b',
  'e5fe9e20-47d3-5287-b97d-a1de25e8a7c3',
  'e6eb2f3a-47e9-5837-a89d-37faf9bc073d',
  'f2464461-71fe-5800-aebf-39d65a5b4037',
  'f549d909-2219-5b6c-bc8d-b305089ed406',
  'f5a9fc1e-22b2-5289-b89b-3a4630a4c8f0',
  'f6bfab69-6556-5e1e-886b-46576a5c6980',
  'fcac65bf-eb99-5ac1-a90c-3ebe20083ce6',
  'fca25cfa-fe5d-586b-a231-8e97106ad7c5',
  '4adc57a7-71a4-5fed-a6e0-bd8b59a261f2',
  '727be2fe-b941-5561-bce0-6778e090f594'
];

// Set to false to fetch all patients instead of just allowlisted ones
const USE_ALLOWLIST = true; // Re-enabled to use the specific patient allowlist

export const usePatientList = () => {
  const [patients, setPatients] = useState<Patient[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [page, setPage] = useState<number>(0);
  const [nextPageCursor, setNextPageCursor] = useState<string | null>(null);
  const [prevPageCursors, setPrevPageCursors] = useState<string[]>([]);
  const PATIENTS_PER_PAGE = 25;

  // Clear expired cache entries periodically
  useMemo(() => {
    const interval = setInterval(clearExpiredCache, 60000); // Every minute
    return () => clearInterval(interval);
  }, []);

  // Load first page of patients
  const loadFirstPatientsPage = useCallback(async () => {
    const cacheKey = getCacheKey(undefined, ALLOWLIST_IDS);
    const cached = patientListCache.get(cacheKey);
    
    if (cached && isCacheValid(cached.timestamp, cached.ttl)) {
      setPatients(cached.data);
      setPage(0);
      setNextPageCursor(null);
      setPrevPageCursors([]);
      return;
    }

    setLoading(true);
    setError(null);

    try {
      let processedPatients: Patient[] = [];
      
      // Try allowlist first if we have IDs and allowlist is enabled
      if (ALLOWLIST_IDS.length > 0 && USE_ALLOWLIST) {
        try {
          const url = `${API_BASE}/local/patients/by-ids?ids=${ALLOWLIST_IDS.join(',')}`;
          const res = await fetch(url);
          if (res.ok) {
            const data = await res.json();
            processedPatients = data.patients ? data.patients.map((patient: any) => ({
              id: patient.id,
              family_name: patient.family_name || 'Unknown',
              gender: patient.gender || 'Unknown',
              birth_date: patient.birth_date || 'Unknown',
              race: patient.race,
              ethnicity: patient.ethnicity,
              birth_sex: patient.birth_sex,
              identifier: patient.identifier,
              marital_status: patient.marital_status,
              deceased_date: patient.deceased_date,
              managing_organization: patient.managing_organization,
              allergies: patient.allergies || []
            })) : [];
          }
        } catch (allowlistError) {
          console.warn('Allowlist fetch failed, falling back to regular patient fetch:', allowlistError);
        }
      }
      
      // If allowlist failed or is empty, fetch regular patients
      if (processedPatients.length === 0) {
        const url = `${API_BASE}/local/patients?limit=${PATIENTS_PER_PAGE}&offset=0`;
        const res = await fetch(url);
        if (!res.ok) {
          throw new Error(`HTTP error! status: ${res.status}`);
        }
        const data = await res.json();

        processedPatients = data.patients ? data.patients.map((patient: any) => ({
          id: patient.id,
          family_name: patient.family_name || 'Unknown',
          gender: patient.gender || 'Unknown',
          birth_date: patient.birth_date || 'Unknown',
          race: patient.race,
          ethnicity: patient.ethnicity,
          birth_sex: patient.birth_sex,
          identifier: patient.identifier,
          marital_status: patient.marital_status,
          deceased_date: patient.deceased_date,
          managing_organization: patient.managing_organization,
          allergies: patient.allergies || []
        })) : [];

        // Set next page cursor for pagination
        if (data.total_count > PATIENTS_PER_PAGE) {
          setNextPageCursor('1'); // Simple offset-based pagination
        }
      }

      // Cache the data
      patientListCache.set(cacheKey, {
        data: processedPatients,
        timestamp: Date.now(),
        ttl: CACHE_TTL
      });

      setPatients(processedPatients);
      setPage(0);
      if (processedPatients.length === 0) {
        setNextPageCursor(null);
      }
      setPrevPageCursors([]);

    } catch (err: any) {
      setError(`Failed to fetch patients: ${err.message}`);
    } finally {
      setLoading(false);
    }
  }, []);

  // Load patients by cursor
  const loadByCursor = useCallback(async (cursor: string, goingBack: boolean) => {
    const cacheKey = getCacheKey(cursor);
    const cached = patientListCache.get(cacheKey);
    
    if (cached && isCacheValid(cached.timestamp, cached.ttl)) {
      setPatients(cached.data);
      return;
    }

    setLoading(true);
    setError(null);

    try {
      const url = `${API_BASE}/paginate?cursor=${encodeURIComponent(cursor)}`;
      const res = await fetch(url);
      
      if (!res.ok) {
        throw new Error(`HTTP error! status: ${res.status}`);
      }
      const data = await res.json();

      const processedPatients = data.entry ? data.entry.map((entry: any) => ({
        id: entry.resource.id,
        family_name: entry.resource.name?.[0]?.family || 'Unknown',
        gender: entry.resource.gender || 'Unknown',
        birth_date: entry.resource.birthDate || 'Unknown',
        race: entry.resource.extension?.find((ext: any) => ext.url === 'http://hl7.org/fhir/us/core/StructureDefinition/us-core-race')?.extension?.find((subExt: any) => subExt.url === 'text')?.valueString,
        ethnicity: entry.resource.extension?.find((ext: any) => ext.url === 'http://hl7.org/fhir/us-core/StructureDefinition/us-core-ethnicity')?.extension?.find((subExt: any) => subExt.url === 'text')?.valueString,
        birth_sex: entry.resource.extension?.find((ext: any) => ext.url === 'http://hl7.org/fhir/us-core/StructureDefinition/us-core-birthsex')?.valueCode,
        identifier: entry.resource.identifier?.[0]?.value,
        marital_status: entry.resource.maritalStatus?.coding?.[0]?.code,
        deceased_date: entry.resource.deceasedDateTime,
        managing_organization: entry.resource.managingOrganization?.reference
      })) : [];

      // Cache the data
      patientListCache.set(cacheKey, {
        data: processedPatients,
        timestamp: Date.now(),
        ttl: CACHE_TTL
      });

      setPatients(processedPatients);

    } catch (err: any) {
      setError(`Failed to fetch patients: ${err.message}`);
    } finally {
      setLoading(false);
    }
  }, []);

  // Handle next page
  const handleNextPage = useCallback(() => {
    if (!nextPageCursor) return;
    
    setPrevPageCursors(prev => [...prev, nextPageCursor]);
    setPage(prev => prev + 1);
    loadByCursor(nextPageCursor, false);
  }, [nextPageCursor, loadByCursor]);

  // Handle previous page
  const handlePrevPage = useCallback(() => {
    if (prevPageCursors.length === 0) return;
    
    const prev = prevPageCursors[prevPageCursors.length - 1];
    const newPrevStack = prevPageCursors.slice(0, -1);
    
    setPrevPageCursors(newPrevStack);
    setPage(prev => prev - 1);
    loadByCursor(prev, true);
  }, [prevPageCursors, loadByCursor]);

  // Initialize on mount
  useMemo(() => {
    loadFirstPatientsPage();
  }, [loadFirstPatientsPage]);

  return {
    // State
    patients,
    loading,
    error,
    page,
    nextPageCursor,
    prevPageCursors,
    
    // Actions
    loadFirstPatientsPage,
    handleNextPage,
    handlePrevPage,
    
    // Utilities
    hasNextPage: !!nextPageCursor,
    hasPrevPage: prevPageCursors.length > 0,
    pageSize: PATIENTS_PER_PAGE
  };
};
