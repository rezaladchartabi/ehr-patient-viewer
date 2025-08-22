/**
 * Centralized API service for all backend communication
 * Provides consistent error handling, retry logic, and type safety
 */

import { Patient, Note, Allergy, SearchResult, BackendStatus } from '../types';
import config from '../config';

export class ApiError extends Error {
  constructor(
    public status: number,
    message: string,
    public response?: Response
  ) {
    super(message);
    this.name = 'ApiError';
  }
}

export interface ApiConfig {
  baseUrl: string;
  timeout: number;
  retryAttempts: number;
  retryDelay: number;
}

export class ApiService {
  private config: ApiConfig;
  private abortController: AbortController;

  constructor(config: ApiConfig) {
    this.config = config;
    this.abortController = new AbortController();
  }

  /**
   * Generic request method with error handling and retries
   */
  private async request<T>(
    endpoint: string,
    options: RequestInit = {},
    retryCount = 0
  ): Promise<T> {
    try {
      const controller = new AbortController();
      const timeoutId = setTimeout(() => controller.abort(), this.config.timeout);

      const response = await fetch(`${this.config.baseUrl}${endpoint}`, {
        headers: {
          'Content-Type': 'application/json',
          ...options.headers,
        },
        signal: controller.signal,
        ...options,
      });

      clearTimeout(timeoutId);

      if (!response.ok) {
        const errorMessage = await response.text().catch(() => 'Unknown error');
        throw new ApiError(response.status, errorMessage, response);
      }

      return await response.json();
    } catch (error) {
      // Retry logic for network errors (not for 4xx/5xx errors)
      if (
        retryCount < this.config.retryAttempts &&
        error instanceof Error &&
        (error instanceof TypeError || error.name === 'AbortError') &&
        error.name !== 'AbortError' // Don't retry timeouts
      ) {
        await this.delay(this.config.retryDelay * Math.pow(2, retryCount));
        return this.request<T>(endpoint, options, retryCount + 1);
      }

      throw error;
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
    return this.request<BackendStatus>('/ready');
  }

  // ========== PATIENT OPERATIONS ==========

  async getPatients(limit = 100): Promise<Patient[]> {
    const data = await this.request<{ patients: Patient[] }>(`/local/patients?limit=${limit}`);
    return data.patients || [];
  }

  async getPatientAllergies(patientId: string): Promise<Allergy[]> {
    return this.request<Allergy[]>(`/local/patients/${patientId}/allergies`);
  }

  async getPatientNotes(patientId: string): Promise<Note[]> {
    const data = await this.request<{ notes: Note[] }>(`/notes/patients/${patientId}`);
    return data.notes || [];
  }

  // ========== SEARCH OPERATIONS ==========

  async performClinicalSearch(query: string, limit = 50): Promise<SearchResult[]> {
    const params = new URLSearchParams({
      q: query,
      limit: limit.toString()
    });
    
    const data = await this.request<{ results: SearchResult[] }>(`/clinical-search?${params}`);
    return data.results || [];
  }

  // ========== BATCH OPERATIONS ==========

  /**
   * Fetch multiple patient data types in parallel
   */
  async getPatientDetails(patientId: string): Promise<{
    allergies: Allergy[];
    notes: Note[];
  }> {
    try {
      const [allergies, notes] = await Promise.all([
        this.getPatientAllergies(patientId),
        this.getPatientNotes(patientId)
      ]);

      return { allergies, notes };
    } catch (error) {
      console.error('Error fetching patient details:', error);
      // Return partial data on error
      return {
        allergies: [],
        notes: []
      };
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
