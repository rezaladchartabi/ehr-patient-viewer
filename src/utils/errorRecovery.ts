// Comprehensive error recovery and fallback system

export interface RecoveryStrategy {
  name: string;
  description: string;
  execute: () => Promise<boolean>;
  priority: number; // Lower number = higher priority
}

export interface ErrorContext {
  error: Error;
  endpoint?: string;
  data?: any;
  timestamp: Date;
  retryCount: number;
}

// ========== ERROR RECOVERY STRATEGIES ==========

export class ErrorRecoveryManager {
  private strategies: RecoveryStrategy[] = [];
  private errorHistory: ErrorContext[] = [];
  private maxHistorySize = 100;

  constructor() {
    this.registerDefaultStrategies();
  }

  private registerDefaultStrategies() {
    // Strategy 1: Retry with exponential backoff
    this.addStrategy({
      name: 'Exponential Backoff Retry',
      description: 'Retry the failed operation with exponential backoff',
      priority: 1,
      execute: async () => {
        console.debug('[RECOVERY] Attempting exponential backoff retry');
        return true; // This is handled by the API service
      }
    });

    // Strategy 2: Clear cache and retry
    this.addStrategy({
      name: 'Clear Cache and Retry',
      description: 'Clear any cached data and retry the operation',
      priority: 2,
      execute: async () => {
        console.debug('[RECOVERY] Clearing cache and retrying');
        // Clear localStorage cache
        try {
          localStorage.removeItem('ehr-cache');
          sessionStorage.clear();
        } catch (error) {
          console.warn('[RECOVERY] Failed to clear cache:', error);
        }
        return true;
      }
    });

    // Strategy 3: Fallback to cached data
    this.addStrategy({
      name: 'Fallback to Cached Data',
      description: 'Use cached data as fallback when API fails',
      priority: 3,
      execute: async () => {
        console.debug('[RECOVERY] Attempting fallback to cached data');
        try {
          const cached = localStorage.getItem('ehr-cache');
          if (cached) {
            const data = JSON.parse(cached);
            console.debug('[RECOVERY] Found cached data:', data);
            return true;
          }
        } catch (error) {
          console.warn('[RECOVERY] Failed to load cached data:', error);
        }
        return false;
      }
    });

    // Strategy 4: Refresh page
    this.addStrategy({
      name: 'Page Refresh',
      description: 'Refresh the page to reset application state',
      priority: 4,
      execute: async () => {
        console.debug('[RECOVERY] Refreshing page');
        window.location.reload();
        return true;
      }
    });
  }

  addStrategy(strategy: RecoveryStrategy) {
    this.strategies.push(strategy);
    this.strategies.sort((a, b) => a.priority - b.priority);
  }

  recordError(error: Error, endpoint?: string, data?: any) {
    const context: ErrorContext = {
      error,
      endpoint,
      data,
      timestamp: new Date(),
      retryCount: 0
    };

    this.errorHistory.push(context);
    
    // Keep only the most recent errors
    if (this.errorHistory.length > this.maxHistorySize) {
      this.errorHistory = this.errorHistory.slice(-this.maxHistorySize);
    }

    console.error('[RECOVERY] Error recorded:', {
      message: error.message,
      endpoint,
      timestamp: context.timestamp.toISOString()
    });
  }

  async attemptRecovery(error: Error, endpoint?: string, data?: any): Promise<boolean> {
    this.recordError(error, endpoint, data);

    console.debug('[RECOVERY] Starting recovery process with', this.strategies.length, 'strategies');

    for (const strategy of this.strategies) {
      try {
        console.debug(`[RECOVERY] Trying strategy: ${strategy.name}`);
        const success = await strategy.execute();
        
        if (success) {
          console.debug(`[RECOVERY] Strategy "${strategy.name}" succeeded`);
          return true;
        }
      } catch (strategyError) {
        console.warn(`[RECOVERY] Strategy "${strategy.name}" failed:`, strategyError);
      }
    }

    console.error('[RECOVERY] All recovery strategies failed');
    return false;
  }

  getErrorHistory(): ErrorContext[] {
    return [...this.errorHistory];
  }

  clearErrorHistory() {
    this.errorHistory = [];
  }

  getErrorStats() {
    const now = new Date();
    const oneHourAgo = new Date(now.getTime() - 60 * 60 * 1000);
    const oneDayAgo = new Date(now.getTime() - 24 * 60 * 60 * 1000);

    const recentErrors = this.errorHistory.filter(e => e.timestamp > oneHourAgo);
    const dailyErrors = this.errorHistory.filter(e => e.timestamp > oneDayAgo);

    return {
      totalErrors: this.errorHistory.length,
      recentErrors: recentErrors.length,
      dailyErrors: dailyErrors.length,
      mostCommonError: this.getMostCommonError()
    };
  }

  private getMostCommonError(): string | null {
    const errorCounts: Record<string, number> = {};
    
    this.errorHistory.forEach(context => {
      const errorType = context.error.constructor.name;
      errorCounts[errorType] = (errorCounts[errorType] || 0) + 1;
    });

    const sorted = Object.entries(errorCounts).sort(([,a], [,b]) => b - a);
    return sorted.length > 0 ? sorted[0][0] : null;
  }
}

// ========== DATA FALLBACK SYSTEM ==========

export class DataFallbackManager {
  private cache: Map<string, { data: any; timestamp: number; ttl: number }> = new Map();
  private defaultTTL = 5 * 60 * 1000; // 5 minutes

  setCache(key: string, data: any, ttl: number = this.defaultTTL) {
    this.cache.set(key, {
      data,
      timestamp: Date.now(),
      ttl
    });
  }

  getCache(key: string): any | null {
    const cached = this.cache.get(key);
    if (!cached) return null;

    const isExpired = Date.now() - cached.timestamp > cached.ttl;
    if (isExpired) {
      this.cache.delete(key);
      return null;
    }

    return cached.data;
  }

  clearCache(key?: string) {
    if (key) {
      this.cache.delete(key);
    } else {
      this.cache.clear();
    }
  }

  async getWithFallback<T>(
    key: string,
    fetchFunction: () => Promise<T>,
    ttl: number = this.defaultTTL
  ): Promise<T> {
    // Try cache first
    const cached = this.getCache(key);
    if (cached) {
      console.debug(`[FALLBACK] Using cached data for ${key}`);
      return cached;
    }

    try {
      // Try to fetch fresh data
      const data = await fetchFunction();
      this.setCache(key, data, ttl);
      return data;
    } catch (error) {
      console.warn(`[FALLBACK] Failed to fetch data for ${key}:`, error);
      
      // Try to get stale cache as fallback
      const staleCache = this.cache.get(key);
      if (staleCache) {
        console.debug(`[FALLBACK] Using stale cached data for ${key}`);
        return staleCache.data;
      }

      throw error;
    }
  }
}

// ========== GLOBAL INSTANCES ==========

export const errorRecoveryManager = new ErrorRecoveryManager();
export const dataFallbackManager = new DataFallbackManager();

// ========== UTILITY FUNCTIONS ==========

export const withErrorRecovery = async <T>(
  operation: () => Promise<T>,
  operationName: string,
  fallbackValue?: T
): Promise<T> => {
  try {
    return await operation();
  } catch (error) {
    console.error(`[RECOVERY] Operation "${operationName}" failed:`, error);
    
    const recovered = await errorRecoveryManager.attemptRecovery(
      error instanceof Error ? error : new Error(String(error)),
      operationName
    );

    if (recovered && fallbackValue !== undefined) {
      console.debug(`[RECOVERY] Using fallback value for "${operationName}"`);
      return fallbackValue;
    }

    throw error;
  }
};

export const withDataFallback = async <T>(
  key: string,
  fetchFunction: () => Promise<T>,
  fallbackValue?: T
): Promise<T> => {
  try {
    return await dataFallbackManager.getWithFallback(key, fetchFunction);
  } catch (error) {
    console.warn(`[FALLBACK] Failed to get data for ${key}:`, error);
    
    if (fallbackValue !== undefined) {
      console.debug(`[FALLBACK] Using fallback value for ${key}`);
      return fallbackValue;
    }

    throw error;
  }
};
