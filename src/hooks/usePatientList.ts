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
  for (const [key, value] of patientListCache.entries()) {
    if (!isCacheValid(value.timestamp, value.ttl)) {
      patientListCache.delete(key);
    }
  }
};

const getCacheKey = (cursor?: string, allowlist?: string[]) => {
  if (allowlist && allowlist.length > 0) {
    return `allowlist:${allowlist.join(',')}`;
  }
  return `cursor:${cursor || 'initial'}`;
};

// API base URL
const API_BASE = process.env.REACT_APP_API_URL || 'http://localhost:8000';

// Allowlist IDs for specific patients
const ALLOWLIST_IDS = [
  '03632093-8e46-5c64-8d8b-76ce07fa7b35',
  '271cd75b-b278-51fe-a6cf-6efe41c3da2b',
  '4c5b5b5b-5b5b-5b5b-5b5b-5b5b5b5b5b5b',
  '5d6c6c6c-6c6c-6c6c-6c6c-6c6c6c6c6c6c',
  '6e7d7d7d-7d7d-7d7d-7d7d-7d7d7d7d7d7d',
  '7f8e8e8e-8e8e-8e8e-8e8e-8e8e8e8e8e8e',
  '8g9f9f9f-9f9f-9f9f-9f9f-9f9f9f9f9f9f',
  '9h0g0g0g-0g0g-0g0g-0g0g-0g0g0g0g0g0g',
  '0i1h1h1h-1h1h-1h1h-1h1h-1h1h1h1h1h1h',
  '1j2i2i2i-2i2i-2i2i-2i2i-2i2i2i2i2i2i',
  '2k3j3j3j-3j3j-3j3j-3j3j-3j3j3j3j3j3j',
  '3l4k4k4k-4k4k-4k4k-4k4k-4k4k4k4k4k4k',
  '4m5l5l5l-5l5l-5l5l-5l5l-5l5l5l5l5l5l',
  '5n6m6m6m-6m6m-6m6m-6m6m-6m6m6m6m6m6m',
  '6o7n7n7n-7n7n-7n7n-7n7n-7n7n7n7n7n7n',
  '7p8o8o8o-8o8o-8o8o-8o8o-8o8o8o8o8o8o',
  '8q9p9p9p-9p9p-9p9p-9p9p-9p9p9p9p9p9p',
  '9r0q0q0q-0q0q-0q0q-0q0q-0q0q0q0q0q0q',
  '0s1r1r1r-1r1r-1r1r-1r1r-1r1r1r1r1r1r',
  '1t2s2s2s-2s2s-2s2s-2s2s-2s2s2s2s2s2s',
  '2u3t3t3t-3t3t-3t3t-3t3t-3t3t3t3t3t3t',
  '3v4u4u4u-4u4u-4u4u-4u4u-4u4u4u4u4u4u',
  '4w5v5v5v-5v5v-5v5v-5v5v-5v5v5v5v5v5v',
  '5x6w6w6w-6w6w-6w6w-6w6w-6w6w6w6w6w6w',
  '6y7x7x7x-7x7x-7x7x-7x7x-7x7x7x7x7x7x'
];

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
      
      if (ALLOWLIST_IDS.length > 0) {
        // Use allowlist on initial load
        url = `${API_BASE}/Patient/by-ids?ids=${ALLOWLIST_IDS.join(',')}`;
      } else {
        url = `${API_BASE}/Patient?_count=${PATIENTS_PER_PAGE}`;
      }

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
      setPage(0);
      setNextPageCursor(null);
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
