import React, { useState, useEffect } from 'react';
import apiService from '../services/apiService';

interface SystemStatus {
  backendReady: boolean;
  apiHealth: {
    status: 'healthy' | 'unhealthy';
    endpoints: Record<string, boolean>;
    errors: string[];
  } | null;
  lastCheck: Date | null;
  errorCount: number;
  successCount: number;
}

const SystemMonitor: React.FC = () => {
  const [status, setStatus] = useState<SystemStatus>({
    backendReady: false,
    apiHealth: null,
    lastCheck: null,
    errorCount: 0,
    successCount: 0
  });
  const [isVisible, setIsVisible] = useState(false);
  const [logs, setLogs] = useState<string[]>([]);

  // Add log entry
  const addLog = (message: string) => {
    const timestamp = new Date().toISOString();
    const logEntry = `[${timestamp}] ${message}`;
    setLogs(prev => [...prev.slice(-49), logEntry]); // Keep last 50 logs
  };

  // Monitor system health
  useEffect(() => {
    const checkHealth = async () => {
      try {
        addLog('Starting system health check...');
        
        // Check backend readiness
        const readiness = await apiService.checkBackendReadiness();
        setStatus(prev => ({ ...prev, backendReady: readiness.ready }));
        
        if (readiness.ready) {
          addLog('Backend is ready');
          
          // Run comprehensive health check
          const health = await apiService.healthCheck();
          setStatus(prev => ({ 
            ...prev, 
            apiHealth: health,
            lastCheck: new Date(),
            successCount: prev.successCount + 1
          }));
          
          addLog(`Health check completed: ${health.status}`);
          if (health.errors.length > 0) {
            health.errors.forEach(error => addLog(`Error: ${error}`));
          }
        } else {
          addLog('Backend not ready yet');
          setStatus(prev => ({ 
            ...prev, 
            errorCount: prev.errorCount + 1 
          }));
        }
      } catch (error) {
        addLog(`Health check failed: ${error instanceof Error ? error.message : String(error)}`);
        setStatus(prev => ({ 
          ...prev, 
          errorCount: prev.errorCount + 1 
        }));
      }
    };

    // Initial check
    checkHealth();

    // Periodic health checks every 30 seconds
    const interval = setInterval(checkHealth, 30000);

    return () => clearInterval(interval);
  }, []);

  // Monitor console for API logs
  useEffect(() => {
    const originalDebug = console.debug;
    const originalWarn = console.warn;
    const originalError = console.error;

    console.debug = (...args) => {
      if (args[0]?.includes?.('[API]')) {
        addLog(`DEBUG: ${args.join(' ')}`);
      }
      originalDebug.apply(console, args);
    };

    console.warn = (...args) => {
      if (args[0]?.includes?.('[API]')) {
        addLog(`WARN: ${args.join(' ')}`);
      }
      originalWarn.apply(console, args);
    };

    console.error = (...args) => {
      if (args[0]?.includes?.('[API]')) {
        addLog(`ERROR: ${args.join(' ')}`);
      }
      originalError.apply(console, args);
    };

    return () => {
      console.debug = originalDebug;
      console.warn = originalWarn;
      console.error = originalError;
    };
  }, []);

  if (!isVisible) {
    return (
      <button
        onClick={() => setIsVisible(true)}
        className="fixed bottom-4 right-4 bg-blue-600 text-white p-2 rounded-full shadow-lg hover:bg-blue-700 z-50"
        title="System Monitor"
      >
        <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
        </svg>
      </button>
    );
  }

  return (
    <div className="fixed bottom-4 right-4 w-96 h-96 bg-white border border-gray-300 rounded-lg shadow-xl z-50">
      <div className="flex justify-between items-center p-3 border-b border-gray-200">
        <h3 className="text-lg font-semibold">System Monitor</h3>
        <button
          onClick={() => setIsVisible(false)}
          className="text-gray-500 hover:text-gray-700"
        >
          <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
          </svg>
        </button>
      </div>

      <div className="p-3 space-y-3">
        {/* Status Overview */}
        <div className="grid grid-cols-2 gap-2 text-sm">
          <div className={`p-2 rounded ${status.backendReady ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'}`}>
            Backend: {status.backendReady ? 'Ready' : 'Not Ready'}
          </div>
          <div className={`p-2 rounded ${status.apiHealth?.status === 'healthy' ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'}`}>
            API: {status.apiHealth?.status || 'Unknown'}
          </div>
          <div className="p-2 rounded bg-blue-100 text-blue-800">
            Success: {status.successCount}
          </div>
          <div className="p-2 rounded bg-red-100 text-red-800">
            Errors: {status.errorCount}
          </div>
        </div>

        {/* Endpoint Status */}
        {status.apiHealth && (
          <div className="text-sm">
            <h4 className="font-medium mb-1">Endpoints:</h4>
            <div className="space-y-1">
              {Object.entries(status.apiHealth.endpoints).map(([endpoint, healthy]) => (
                <div key={endpoint} className="flex justify-between">
                  <span>{endpoint}:</span>
                  <span className={healthy ? 'text-green-600' : 'text-red-600'}>
                    {healthy ? '✓' : '✗'}
                  </span>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Recent Logs */}
        <div className="text-sm">
          <h4 className="font-medium mb-1">Recent Logs:</h4>
          <div className="h-32 overflow-y-auto bg-gray-50 p-2 rounded text-xs font-mono">
            {logs.length === 0 ? (
              <div className="text-gray-500">No logs yet...</div>
            ) : (
              logs.map((log, index) => (
                <div key={index} className="mb-1">
                  {log}
                </div>
              ))
            )}
          </div>
        </div>

        {/* Last Check */}
        {status.lastCheck && (
          <div className="text-xs text-gray-500">
            Last check: {status.lastCheck.toLocaleTimeString()}
          </div>
        )}
      </div>
    </div>
  );
};

export default SystemMonitor;
