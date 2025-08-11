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
const API_BASE = process.env.REACT_APP_API_URL || 'http://localhost:8000';

// Allowlist IDs for specific patients (only real IDs from FHIR server)
const ALLOWLIST_IDS = [
  '03632093-8e46-5c64-8d8b-76ce07fa7b35',
  '271cd75b-b278-51fe-a6cf-6efe41c3da2b'
  // Add more real patient IDs here as needed
];

// Set to false to fetch all patients instead of just allowlisted ones
const USE_ALLOWLIST = false;

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
      let url: string;
      let processedPatients: Patient[] = [];
      
      // Try allowlist first if we have IDs and allowlist is enabled
      if (ALLOWLIST_IDS.length > 0 && USE_ALLOWLIST) {
        try {
          url = `${API_BASE}/Patient/by-ids?ids=${ALLOWLIST_IDS.join(',')}`;
          const res = await fetch(url);
          if (res.ok) {
            const data = await res.json();
            processedPatients = data.entry ? data.entry.map((entry: any) => ({
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
          }
        } catch (allowlistError) {
          console.warn('Allowlist fetch failed, falling back to regular patient fetch:', allowlistError);
        }
      }
      
      // If allowlist failed or is empty, fetch regular patients
      if (processedPatients.length === 0) {
        url = `${API_BASE}/Patient?_count=${PATIENTS_PER_PAGE}`;
        const res = await fetch(url);
        if (!res.ok) {
          throw new Error(`HTTP error! status: ${res.status}`);
        }
        const data = await res.json();

        processedPatients = data.entry ? data.entry.map((entry: any) => ({
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

        // Set next page cursor for pagination
        const nextLink = data.link?.find((l: any) => l.relation === 'next')?.url;
        setNextPageCursor(nextLink || null);
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
        race: entry.resource.extension?.find((ext: any) => ext.url === 'http://hl7.org/fhir/us/core/StructureDefinition/us-core-race')?.valueCodeableConcept?.text,
        ethnicity: entry.resource.extension?.find((ext: any) => ext.url === 'http://hl7.org/fhir/us-core/StructureDefinition/us-core-ethnicity')?.valueCodeableConcept?.text,
        birth_sex: entry.resource.extension?.find((ext: any) => ext.url === 'http://hl7.org/fhir/us-core/StructureDefinition/us-core-birthsex')?.valueCode,
        identifier: entry.resource.identifier?.[0]?.value,
        marital_status: entry.resource.maritalStatus?.text,
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
