// Frontend Configuration
export const config = {
  // Backend API Configuration
  api: {
    // Default backend URL - can be overridden by environment variable
    baseUrl: process.env.REACT_APP_API_URL || 'http://localhost:8005',
    
    // API endpoints
    endpoints: {
      health: '/',
      patients: '/local/patients',
      patient: (id: string) => `/local/patients/${id}`,
      search: '/local/patients/search',
      encounters: '/Encounter',
      conditions: '/Condition',
      cache: {
        status: '/cache/status',
        clear: '/cache/clear',
      },
      rateLimit: {
        status: '/rate-limit/status',
        reset: '/rate-limit/reset',
      },
      sync: {
        all: '/sync/all',
        patients: '/sync/patients',
      },
    },
    
    // Request configuration
    timeout: 30000, // 30 seconds
    retries: 3,
    retryDelay: 1000, // 1 second
  },
  
  // Application Configuration
  app: {
    name: 'EHR Patient Viewer',
    version: '1.0.0',
    environment: process.env.REACT_APP_ENV || 'development',
  },
  
  // Feature Flags
  features: {
    enableCache: process.env.REACT_APP_ENABLE_CACHE !== 'false',
    enableRateLimiting: process.env.REACT_APP_ENABLE_RATE_LIMITING !== 'false',
    enableErrorBoundaries: true,
    enablePerformanceMonitoring: process.env.NODE_ENV === 'production',
  },
  
  // UI Configuration
  ui: {
    patientsPerPage: 25,
    cacheTTL: 5 * 60 * 1000, // 5 minutes
    theme: {
      default: 'light',
      storageKey: 'ehr-theme',
    },
  },
};

// Helper function to get API URL
export const getApiUrl = (endpoint: string): string => {
  const baseUrl = config.api.baseUrl.replace(/\/$/, ''); // Remove trailing slash
  const cleanEndpoint = endpoint.replace(/^\//, ''); // Remove leading slash
  return `${baseUrl}/${cleanEndpoint}`;
};

// Helper function to check if running in development
export const isDevelopment = (): boolean => {
  return config.app.environment === 'development';
};

// Helper function to check if running in production
export const isProduction = (): boolean => {
  return config.app.environment === 'production';
};

export default config;

