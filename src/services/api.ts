import { 
  APIResponse, 
  PaginatedResponse, 
  LocalPatient, 
  LocalAllergy, 
  Encounter, 
  Condition,
  APIError 
} from '../types';

import config from '../config';

// Configuration
const API_BASE = config.api.baseUrl;
const DEFAULT_TIMEOUT = config.api.timeout;
const MAX_RETRIES = config.api.retries;
const RETRY_DELAY = config.api.retryDelay;

// Error types
export class APIException extends Error {
  constructor(
    message: string,
    public status: number,
    public code?: string,
    public details?: Record<string, any>
  ) {
    super(message);
    this.name = 'APIException';
  }
}

export class NetworkException extends Error {
  constructor(message: string, public originalError?: Error) {
    super(message);
    this.name = 'NetworkException';
  }
}

// Request configuration
interface RequestConfig {
  timeout?: number;
  retries?: number;
  retryDelay?: number;
  headers?: Record<string, string>;
}

// Default request configuration
const defaultConfig: RequestConfig = {
  timeout: DEFAULT_TIMEOUT,
  retries: MAX_RETRIES,
  retryDelay: RETRY_DELAY,
  headers: {
    'Content-Type': 'application/json',
  },
};

// Utility functions
const sleep = (ms: number) => new Promise(resolve => setTimeout(resolve, ms));

const isRetryableError = (error: any): boolean => {
  // Retry on network errors or 5xx server errors
  if (error instanceof NetworkException) return true;
  if (error instanceof APIException) {
    return error.status >= 500 && error.status < 600;
  }
  return false;
};

const parseErrorResponse = async (response: Response): Promise<APIError> => {
  try {
    const errorData = await response.json();
    return {
      error: errorData.error || `HTTP ${response.status}`,
      error_code: errorData.error_code,
      details: errorData.details
    };
  } catch {
    return {
      error: `HTTP ${response.status}: ${response.statusText}`
    };
  }
};

// Core request function
async function request<T>(
  endpoint: string,
  options: RequestInit = {},
  config: RequestConfig = {}
): Promise<T> {
  const finalConfig = { ...defaultConfig, ...config };
  const url = `${API_BASE}${endpoint}`;
  
  let lastError: Error | null = null;
  
  for (let attempt = 0; attempt <= finalConfig.retries!; attempt++) {
    try {
      const controller = new AbortController();
      const timeoutId = setTimeout(() => controller.abort(), finalConfig.timeout);
      
      const response = await fetch(url, {
        ...options,
        headers: {
          ...finalConfig.headers,
          ...options.headers,
        },
        signal: controller.signal,
      });
      
      clearTimeout(timeoutId);
      
      if (!response.ok) {
        const errorData = await parseErrorResponse(response);
        throw new APIException(
          errorData.error,
          response.status,
          errorData.error_code,
          errorData.details
        );
      }
      
      // Handle empty responses
      const contentType = response.headers.get('content-type');
      if (contentType && contentType.includes('application/json')) {
        return await response.json();
      } else {
        return await response.text() as T;
      }
      
    } catch (error: any) {
      lastError = error;
      
      // Handle abort (timeout)
      if (error.name === 'AbortError') {
        throw new NetworkException('Request timeout', error);
      }
      
      // Handle network errors
      if (error instanceof TypeError) {
        throw new NetworkException('Network error', error);
      }
      
      // Don't retry non-retryable errors
      if (!isRetryableError(error)) {
        throw error;
      }
      
      // Don't retry on last attempt
      if (attempt === finalConfig.retries!) {
        throw error;
      }
      
      // Wait before retry
      await sleep(finalConfig.retryDelay! * Math.pow(2, attempt));
    }
  }
  
  throw lastError || new Error('Unknown error occurred');
}

// API client class
export class APIClient {
  private static instance: APIClient;
  
  private constructor() {}
  
  static getInstance(): APIClient {
    if (!APIClient.instance) {
      APIClient.instance = new APIClient();
    }
    return APIClient.instance;
  }
  
  // Health check
  async healthCheck(): Promise<APIResponse> {
    return request<APIResponse>('/');
  }
  
  // Local database endpoints
  async getPatients(limit: number = 25, offset: number = 0): Promise<PaginatedResponse<LocalPatient>> {
    return request<PaginatedResponse<LocalPatient>>(
      `/local/patients?limit=${limit}&offset=${offset}`
    );
  }
  
  async getPatient(patientId: string): Promise<LocalPatient> {
    return request<LocalPatient>(`/local/patients/${patientId}`);
  }
  
  async searchPatients(query: string, limit: number = 25): Promise<LocalPatient[]> {
    return request<LocalPatient[]>(`/local/patients/search?q=${encodeURIComponent(query)}&limit=${limit}`);
  }
  
  // FHIR proxy endpoints
  async getFHIRResource<T>(resourceType: string, params?: Record<string, any>): Promise<T> {
    const searchParams = params ? new URLSearchParams(params).toString() : '';
    const endpoint = searchParams ? `/${resourceType}?${searchParams}` : `/${resourceType}`;
    return request<T>(endpoint);
  }
  
  async getEncounters(patientId: string, limit: number = 100): Promise<{ entry: Array<{ resource: Encounter }> }> {
    return this.getFHIRResource<{ entry: Array<{ resource: Encounter }> }>(
      'Encounter',
      { patient: `Patient/${patientId}`, '_count': limit }
    );
  }
  
  async getConditions(patientId: string, limit: number = 100): Promise<{ entry: Array<{ resource: Condition }> }> {
    return this.getFHIRResource<{ entry: Array<{ resource: Condition }> }>(
      'Condition',
      { patient: `Patient/${patientId}`, '_count': limit }
    );
  }
  
  async getEncounterMedications(patientId: string, encounterId: string): Promise<{
    requests: any[];
    administrations: any[];
    note?: string;
  }> {
    return request<{
      requests: any[];
      administrations: any[];
      note?: string;
    }>(`/encounter/medications?patient=Patient/${patientId}&encounter=Encounter/${encounterId}`);
  }
  
  async getEncounterObservations(patientId: string, encounterId: string): Promise<{
    observations: any[];
    note?: string;
  }> {
    return request<{
      observations: any[];
      note?: string;
    }>(`/encounter/observations?patient=Patient/${patientId}&encounter=Encounter/${encounterId}`);
  }
  
  async getEncounterProcedures(patientId: string, encounterId: string): Promise<{
    procedures: any[];
    note?: string;
  }> {
    return request<{
      procedures: any[];
      note?: string;
    }>(`/encounter/procedures?patient=Patient/${patientId}&encounter=Encounter/${encounterId}`);
  }
  
  async getEncounterSpecimens(patientId: string, encounterId: string): Promise<{
    specimens: any[];
    note?: string;
  }> {
    return request<{
      specimens: any[];
      note?: string;
    }>(`/encounter/specimens?patient=Patient/${patientId}&encounter=Encounter/${encounterId}`);
  }
  
  // Cache management
  async getCacheStatus(): Promise<{
    total_cache_entries: number;
    active_cache_entries: number;
    expired_cache_entries: number;
    cache_ttl_seconds: number;
    rate_limit_requests: number;
  }> {
    return request('/cache/status');
  }
  
  async clearCache(): Promise<{ message: string }> {
    return request<{ message: string }>('/cache/clear', { method: 'POST' });
  }
  
  // Rate limiting
  async getRateLimitStatus(): Promise<{
    total_requests: number;
    allowed_requests: number;
    blocked_requests: number;
    unique_clients: number;
    max_requests: number;
    window_seconds: number;
    success_rate: number;
  }> {
    return request('/rate-limit/status');
  }
  
  async resetRateLimit(): Promise<{ message: string }> {
    return request<{ message: string }>('/rate-limit/reset', { method: 'POST' });
  }
  
  // Pagination
  async paginate(cursor: string): Promise<any> {
    return request(`/paginate?cursor=${encodeURIComponent(cursor)}`);
  }
  
  // Sync operations
  async syncAllResources(): Promise<Record<string, any>> {
    return request<Record<string, any>>('/sync/all', { method: 'POST' });
  }
  
  async syncSpecificPatients(patientIds: string[]): Promise<Record<string, any>> {
    return request<Record<string, any>>('/sync/patients', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ patient_ids: patientIds })
    });
  }
  
  // Search
  async searchResources(resourceType: string, query: string, limit: number = 50): Promise<any> {
    return request(`/search/${resourceType}?q=${encodeURIComponent(query)}&limit=${limit}`);
  }
}

// Export singleton instance
export const apiClient = APIClient.getInstance();

// Convenience functions for common operations
export const api = {
  // Health
  health: () => apiClient.healthCheck(),
  
  // Patients
  getPatients: (limit?: number, offset?: number) => apiClient.getPatients(limit, offset),
  getPatient: (id: string) => apiClient.getPatient(id),
  searchPatients: (query: string, limit?: number) => apiClient.searchPatients(query, limit),
  
  // FHIR Resources
  getEncounters: (patientId: string, limit?: number) => apiClient.getEncounters(patientId, limit),
  getConditions: (patientId: string, limit?: number) => apiClient.getConditions(patientId, limit),
  
  // Encounter Data
  getEncounterMedications: (patientId: string, encounterId: string) => 
    apiClient.getEncounterMedications(patientId, encounterId),
  getEncounterObservations: (patientId: string, encounterId: string) => 
    apiClient.getEncounterObservations(patientId, encounterId),
  getEncounterProcedures: (patientId: string, encounterId: string) => 
    apiClient.getEncounterProcedures(patientId, encounterId),
  getEncounterSpecimens: (patientId: string, encounterId: string) => 
    apiClient.getEncounterSpecimens(patientId, encounterId),
  
  // Cache
  getCacheStatus: () => apiClient.getCacheStatus(),
  clearCache: () => apiClient.clearCache(),
  
  // Rate Limiting
  getRateLimitStatus: () => apiClient.getRateLimitStatus(),
  resetRateLimit: () => apiClient.resetRateLimit(),
  
  // Sync
  syncAll: () => apiClient.syncAllResources(),
  syncPatients: (patientIds: string[]) => apiClient.syncSpecificPatients(patientIds),
  
  // Search
  search: (resourceType: string, query: string, limit?: number) => 
    apiClient.searchResources(resourceType, query, limit),
};
