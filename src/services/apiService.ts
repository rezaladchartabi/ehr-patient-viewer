/**
 * Centralized API service for all backend communication
 * Provides consistent error handling, retry logic, and type safety
 */

import { Patient, Allergy, Note, SearchResult, BackendStatus } from '../types';
import config from '../config';

// ========== ERROR HANDLING ==========

export class ApiError extends Error {
  constructor(
    message: string,
    public status?: number,
    public endpoint?: string,
    public response?: any
  ) {
    super(message);
    this.name = 'ApiError';
  }
}

// ========== VALIDATION UTILITIES ==========

const validateResponse = <T>(response: any, endpoint: string): T => {
  if (!response) {
    throw new ApiError(`Empty response from ${endpoint}`, undefined, endpoint);
  }
  
  // Log response structure for debugging
  console.debug(`[API] ${endpoint} response:`, {
    type: typeof response,
    keys: response ? Object.keys(response) : 'null',
    hasAllergies: response?.allergies !== undefined,
    hasNotes: response?.notes !== undefined,
    hasPatients: response?.patients !== undefined
  });
  
  return response as T;
};

const validateAllergiesResponse = (response: any, endpoint: string): Allergy[] => {
  const validated = validateResponse<{ allergies?: Allergy[]; patient_id?: string; count?: number }>(response, endpoint);
  
  if (!validated.allergies) {
    console.warn(`[API] ${endpoint} missing allergies field:`, response);
    return [];
  }
  
  if (!Array.isArray(validated.allergies)) {
    console.error(`[API] ${endpoint} allergies is not an array:`, validated.allergies);
    return [];
  }
  
  // Validate each allergy object
  const validAllergies = validated.allergies.filter((allergy, index) => {
    if (!allergy || typeof allergy !== 'object') {
      console.warn(`[API] ${endpoint} invalid allergy at index ${index}:`, allergy);
      return false;
    }
    
    if (!allergy.allergy_name) {
      console.warn(`[API] ${endpoint} allergy missing allergy_name at index ${index}:`, allergy);
      return false;
    }
    
    return true;
  });
  
  console.debug(`[API] ${endpoint} validated ${validAllergies.length}/${validated.allergies.length} allergies`);
  return validAllergies;
};

const validateNotesResponse = (response: any, endpoint: string): Note[] => {
  const validated = validateResponse<{ notes?: Note[] }>(response, endpoint);
  
  if (!validated.notes) {
    console.warn(`[API] ${endpoint} missing notes field:`, response);
    return [];
  }
  
  if (!Array.isArray(validated.notes)) {
    console.error(`[API] ${endpoint} notes is not an array:`, validated.notes);
    return [];
  }
  
  return validated.notes;
};

const validatePatientsResponse = (response: any, endpoint: string): Patient[] => {
  const validated = validateResponse<{ patients?: Patient[] }>(response, endpoint);
  
  if (!validated.patients) {
    console.warn(`[API] ${endpoint} missing patients field:`, response);
    return [];
  }
  
  if (!Array.isArray(validated.patients)) {
    console.error(`[API] ${endpoint} patients is not an array:`, validated.patients);
    return [];
  }
  
  return validated.patients;
};

// ========== API SERVICE CONFIGURATION ==========

interface ApiConfig {
  baseUrl: string;
  timeout: number;
  retryAttempts: number;
  retryDelay: number;
}

// ========== ROBUST API SERVICE ==========

class ApiService {
  private config: ApiConfig;
  private abortController: AbortController;

  constructor(config: ApiConfig) {
    this.config = config;
    this.abortController = new AbortController();
  }

  /**
   * Core request method with comprehensive error handling and retry logic
   */
  private async request<T>(
    endpoint: string, 
    options: RequestInit = {}, 
    retryCount = 0
  ): Promise<T> {
    const url = `${this.config.baseUrl}${endpoint}`;
    const signal = this.abortController.signal;

    try {
      console.debug(`[API] Requesting: ${url} (attempt ${retryCount + 1})`);
      
      const response = await fetch(url, {
        ...options,
        signal,
        headers: {
          'Content-Type': 'application/json',
          ...options.headers,
        },
      });

      if (!response.ok) {
        const errorText = await response.text();
        console.error(`[API] HTTP ${response.status} from ${url}:`, errorText);
        throw new ApiError(
          `HTTP ${response.status}: ${errorText}`,
          response.status,
          endpoint
        );
      }

      const data = await response.json();
      console.debug(`[API] Success: ${url}`, { status: response.status, dataKeys: Object.keys(data) });
      
      return data;

    } catch (error) {
      console.error(`[API] Error in ${url} (attempt ${retryCount + 1}):`, error);
      
      // Don't retry if it's an abort error or we've exceeded retry attempts
      if (
        error instanceof ApiError ||
        error.name === 'AbortError' ||
        retryCount >= this.config.retryAttempts
      ) {
        throw error;
      }

      // Exponential backoff retry
      await this.delay(this.config.retryDelay * Math.pow(2, retryCount));
      return this.request<T>(endpoint, options, retryCount + 1);
    }
  }

  /**
   * Utility method for delays
   */
  private delay(ms: number): Promise<void> {
    return new Promise(resolve => setTimeout(resolve, ms));
  }

  /**
   * Cancel all ongoing requests
   */
  public cancelRequests(): void {
    this.abortController.abort();
    this.abortController = new AbortController();
  }

  // ========== BACKEND STATUS ==========
  
  async checkBackendReadiness(): Promise<BackendStatus> {
    try {
      const data = await this.request<BackendStatus>('/ready');
      console.debug('[API] Backend readiness check:', data);
      return data;
          } catch (error) {
        console.error('[API] Backend readiness check failed:', error);
        throw error instanceof Error ? error : new Error(String(error));
      }
  }

  // ========== PATIENT OPERATIONS ==========

  async getPatients(limit = 100): Promise<Patient[]> {
    try {
      const endpoint = `/local/patients?limit=${limit}`;
      const response = await this.request(endpoint);
      const patients = validatePatientsResponse(response, endpoint);
      
      console.debug(`[API] Retrieved ${patients.length} patients`);
      return patients;
    } catch (error: unknown) {
      console.error('[API] Failed to get patients:', error);
      return [];
    }
  }

  async getPatientAllergies(patientId: string): Promise<Allergy[]> {
    try {
      if (!patientId) {
        console.warn('[API] getPatientAllergies called with empty patientId');
        return [];
      }

      const endpoint = `/local/patients/${patientId}/allergies`;
      const response = await this.request(endpoint);
      const allergies = validateAllergiesResponse(response, endpoint);
      
      console.debug(`[API] Retrieved ${allergies.length} allergies for patient ${patientId}`);
      return allergies;
    } catch (error: unknown) {
      console.error(`[API] Failed to get allergies for patient ${patientId}:`, error);
      return [];
    }
  }

  async getPatientNotes(patientId: string): Promise<Note[]> {
    try {
      if (!patientId) {
        console.warn('[API] getPatientNotes called with empty patientId');
        return [];
      }

      const endpoint = `/notes/patients/${patientId}`;
      const response = await this.request(endpoint);
      const notes = validateNotesResponse(response, endpoint);
      
      console.debug(`[API] Retrieved ${notes.length} notes for patient ${patientId}`);
      return notes;
    } catch (error: unknown) {
      console.error(`[API] Failed to get notes for patient ${patientId}:`, error);
      return [];
    }
  }

  // ========== SEARCH OPERATIONS ==========

  async performClinicalSearch(query: string, limit = 50): Promise<SearchResult[]> {
    try {
      if (!query || query.trim().length === 0) {
        console.warn('[API] performClinicalSearch called with empty query');
        return [];
      }

      const params = new URLSearchParams({
        q: query.trim(),
        limit: limit.toString()
      });
      
      const endpoint = `/clinical-search?${params}`;
      const response = await this.request(endpoint);
      const data = validateResponse<{ results?: SearchResult[] }>(response, endpoint);
      
      const results = data.results || [];
      console.debug(`[API] Search for "${query}" returned ${results.length} results`);
      return results;
    } catch (error) {
      console.error(`[API] Search failed for query "${query}":`, error);
      return [];
    }
  }

  // ========== BATCH OPERATIONS ==========

  /**
   * Fetch multiple patient data types in parallel with comprehensive error handling
   */
  async getPatientDetails(patientId: string): Promise<{
    allergies: Allergy[];
    notes: Note[];
  }> {
    if (!patientId) {
      console.warn('[API] getPatientDetails called with empty patientId');
      return { allergies: [], notes: [] };
    }

    console.debug(`[API] Fetching details for patient ${patientId}`);
    
    try {
      // Fetch in parallel for better performance
      const [allergies, notes] = await Promise.allSettled([
        this.getPatientAllergies(patientId),
        this.getPatientNotes(patientId)
      ]);

      const result = {
        allergies: allergies.status === 'fulfilled' ? allergies.value : [],
        notes: notes.status === 'fulfilled' ? notes.value : []
      };

      console.debug(`[API] Patient ${patientId} details:`, {
        allergiesCount: result.allergies.length,
        notesCount: result.notes.length,
        allergiesStatus: allergies.status,
        notesStatus: notes.status
      });

      return result;
    } catch (error) {
      console.error(`[API] Failed to get patient details for ${patientId}:`, error);
      return { allergies: [], notes: [] };
    }
  }

  // ========== HEALTH CHECK ==========
  
  /**
   * Comprehensive health check for all API endpoints
   */
  async healthCheck(): Promise<{
    status: 'healthy' | 'unhealthy';
    endpoints: Record<string, boolean>;
    errors: string[];
  }> {
    const endpoints = {
      readiness: false,
      patients: false,
      allergies: false,
      notes: false
    };
    const errors: string[] = [];

    try {
      // Test backend readiness
      try {
        await this.checkBackendReadiness();
        endpoints.readiness = true;
      } catch (error) {
        errors.push(`Readiness check failed: ${error.message}`);
      }

      // Test patients endpoint
      try {
        const patients = await this.getPatients(1);
        endpoints.patients = patients.length >= 0;
      } catch (error) {
        errors.push(`Patients endpoint failed: ${error.message}`);
      }

      // Test allergies endpoint (if we have a patient)
      try {
        const patients = await this.getPatients(1);
        if (patients.length > 0) {
          const allergies = await this.getPatientAllergies(patients[0].id);
          endpoints.allergies = true; // Success if no error
        }
      } catch (error) {
        errors.push(`Allergies endpoint failed: ${error.message}`);
      }

      // Test notes endpoint (if we have a patient)
      try {
        const patients = await this.getPatients(1);
        if (patients.length > 0) {
          const notes = await this.getPatientNotes(patients[0].id);
          endpoints.notes = true; // Success if no error
        }
      } catch (error) {
        errors.push(`Notes endpoint failed: ${error.message}`);
      }

      const status = errors.length === 0 ? 'healthy' : 'unhealthy';
      
      console.debug('[API] Health check result:', { status, endpoints, errors });
      
      return { status, endpoints, errors };
    } catch (error) {
      console.error('[API] Health check failed:', error);
      return { status: 'unhealthy', endpoints, errors: [error.message] };
    }
  }
}

// ========== DEFAULT INSTANCE ==========

const defaultConfig: ApiConfig = {
  baseUrl: config.api.baseUrl,
  timeout: config.api.timeout,
  retryAttempts: config.api.retryAttempts,
  retryDelay: config.api.retryDelay
};

export const apiService = new ApiService(defaultConfig);

// Export for easy access
export default apiService;
