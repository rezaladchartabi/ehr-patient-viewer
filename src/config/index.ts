/**
 * Centralized configuration for the EHR application
 */

export interface AppConfig {
  api: {
    baseUrl: string;
    timeout: number;
    retryAttempts: number;
    retryDelay: number;
  };
  ui: {
    patientListLimit: number;
    searchResultsLimit: number;
    pollingInterval: number;
    debounceDelay: number;
  };
  development: {
    enableDebugLogs: boolean;
  };
}

const isDevelopment = process.env.NODE_ENV === 'development';

export const config: AppConfig = {
  api: {
    baseUrl: process.env.REACT_APP_API_BASE_URL || 'http://localhost:8006',
    timeout: parseInt(process.env.REACT_APP_API_TIMEOUT || '10000'),
    retryAttempts: parseInt(process.env.REACT_APP_RETRY_ATTEMPTS || '3'),
    retryDelay: parseInt(process.env.REACT_APP_RETRY_DELAY || '1000'),
  },
  ui: {
    patientListLimit: parseInt(process.env.REACT_APP_PATIENT_LIMIT || '100'),
    searchResultsLimit: parseInt(process.env.REACT_APP_SEARCH_LIMIT || '50'),
    pollingInterval: parseInt(process.env.REACT_APP_POLLING_INTERVAL || '5000'),
    debounceDelay: parseInt(process.env.REACT_APP_DEBOUNCE_DELAY || '300'),
  },
  development: {
    enableDebugLogs: isDevelopment && process.env.REACT_APP_DEBUG === 'true',
  },
};

export default config;
