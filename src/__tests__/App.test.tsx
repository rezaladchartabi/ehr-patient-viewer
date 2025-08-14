import React from 'react';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import App from '../App';
import { ErrorBoundary } from '../components/ErrorBoundary';
import { api } from '../services/api';

// Mock the API client
jest.mock('../services/api', () => ({
  api: {
    getPatients: jest.fn(),
    getPatient: jest.fn(),
    getEncounters: jest.fn(),
    getConditions: jest.fn(),
    getEncounterMedications: jest.fn(),
    getEncounterObservations: jest.fn(),
    getEncounterProcedures: jest.fn(),
    getEncounterSpecimens: jest.fn(),
    health: jest.fn(),
  },
}));

// Mock the theme provider
jest.mock('next-themes', () => ({
  useTheme: () => ({
    theme: 'light',
    setTheme: jest.fn(),
  }),
}));

// Mock patient data
const mockPatients = [
  {
    id: 'test-patient-1',
    family_name: 'TestPatient',
    gender: 'male',
    birth_date: '1990-01-01',
    race: 'White',
    ethnicity: 'Not Hispanic or Latino',
    allergies: [],
  },
  {
    id: 'test-patient-2',
    family_name: 'AnotherPatient',
    gender: 'female',
    birth_date: '1985-05-15',
    race: 'Asian',
    ethnicity: 'Hispanic or Latino',
    allergies: [],
  },
];

const mockPatientData = {
  id: 'test-patient-1',
  family_name: 'TestPatient',
  gender: 'male',
  birth_date: '1990-01-01',
  allergies: [
    {
      id: 'allergy-1',
      patient_id: 'test-patient-1',
      code: 'TEST001',
      code_display: 'Test Allergy',
      code_system: 'http://test.system',
      category: 'medication',
      clinical_status: 'active',
      verification_status: 'confirmed',
      type: 'allergy',
      criticality: 'high',
      onset_date: '2020-01-01',
      recorded_date: '2020-01-01',
      recorder: 'Dr. Test',
      asserter: 'Dr. Test',
      last_occurrence: '2020-01-01',
      note: 'Test allergy note',
    },
  ],
};

const mockEncounters = {
  entry: [
    {
      resource: {
        id: 'encounter-1',
        resourceType: 'Encounter',
        status: 'finished',
        class: { code: 'AMB', display: 'Ambulatory' },
        period: { start: '2023-01-01', end: '2023-01-01' },
        subject: { reference: 'Patient/test-patient-1' },
      },
    },
  ],
};

const mockConditions = {
  entry: [
    {
      resource: {
        id: 'condition-1',
        resourceType: 'Condition',
        code: { text: 'Test Condition' },
        status: 'active',
        subject: { reference: 'Patient/test-patient-1' },
      },
    },
  ],
};

describe('App Component', () => {
  beforeEach(() => {
    // Reset all mocks
    jest.clearAllMocks();
    
    // Setup default mock implementations
    (api.getPatients as jest.Mock).mockResolvedValue({
      patients: mockPatients,
      total: mockPatients.length,
    });
    
    (api.getPatient as jest.Mock).mockResolvedValue(mockPatientData);
    (api.getEncounters as jest.Mock).mockResolvedValue(mockEncounters);
    (api.getConditions as jest.Mock).mockResolvedValue(mockConditions);
    (api.health as jest.Mock).mockResolvedValue({ status: 'success' });
  });

  it('renders without crashing', async () => {
    render(
      <ErrorBoundary>
        <App />
      </ErrorBoundary>
    );
    
    await waitFor(() => {
      expect(screen.getByText('EHR Patient Viewer')).toBeInTheDocument();
    });
  });

  it('loads and displays patient list', async () => {
    render(
      <ErrorBoundary>
        <App />
      </ErrorBoundary>
    );
    
    await waitFor(() => {
      expect(api.getPatients).toHaveBeenCalledWith(25, 0);
    });
    
    await waitFor(() => {
      expect(screen.getByText('TestPatient')).toBeInTheDocument();
      expect(screen.getByText('AnotherPatient')).toBeInTheDocument();
    });
  });

  it('handles patient selection', async () => {
    const user = userEvent.setup();
    
    render(
      <ErrorBoundary>
        <App />
      </ErrorBoundary>
    );
    
    // Wait for patients to load
    await waitFor(() => {
      expect(screen.getByText('TestPatient')).toBeInTheDocument();
    });
    
    // Click on a patient
    const patientElement = screen.getByText('TestPatient');
    await user.click(patientElement);
    
    // Verify API calls were made
    await waitFor(() => {
      expect(api.getPatient).toHaveBeenCalledWith('test-patient-1');
      expect(api.getEncounters).toHaveBeenCalledWith('test-patient-1', 100);
      expect(api.getConditions).toHaveBeenCalledWith('test-patient-1', 100);
    });
  });

  it('displays patient summary when patient is selected', async () => {
    const user = userEvent.setup();
    
    render(
      <ErrorBoundary>
        <App />
      </ErrorBoundary>
    );
    
    // Wait for patients to load and click on one
    await waitFor(() => {
      expect(screen.getByText('TestPatient')).toBeInTheDocument();
    });
    
    const patientElement = screen.getByText('TestPatient');
    await user.click(patientElement);
    
    // Check that patient summary is displayed
    await waitFor(() => {
      expect(screen.getByText('TestPatient')).toBeInTheDocument();
      expect(screen.getByText('male')).toBeInTheDocument();
      expect(screen.getByText('1990-01-01')).toBeInTheDocument();
    });
  });

  it('handles API errors gracefully', async () => {
    // Mock API error
    (api.getPatients as jest.Mock).mockRejectedValue(new Error('API Error'));
    
    render(
      <ErrorBoundary>
        <App />
      </ErrorBoundary>
    );
    
    await waitFor(() => {
      expect(screen.getByText(/Failed to fetch patients/)).toBeInTheDocument();
    });
  });

  it('displays loading state while fetching data', async () => {
    // Mock slow API response
    (api.getPatients as jest.Mock).mockImplementation(
      () => new Promise(resolve => setTimeout(() => resolve({
        patients: mockPatients,
        total: mockPatients.length,
      }), 100))
    );
    
    render(
      <ErrorBoundary>
        <App />
      </ErrorBoundary>
    );
    
    // Should show loading state initially
    expect(screen.getByText(/loading/i)).toBeInTheDocument();
    
    // Wait for data to load
    await waitFor(() => {
      expect(screen.getByText('TestPatient')).toBeInTheDocument();
    });
  });
});

describe('Error Boundary', () => {
  const ThrowError = () => {
    throw new Error('Test error');
  };

  it('catches and displays errors', () => {
    render(
      <ErrorBoundary>
        <ThrowError />
      </ErrorBoundary>
    );
    
    expect(screen.getByText('Something went wrong')).toBeInTheDocument();
    expect(screen.getByText('Try Again')).toBeInTheDocument();
    expect(screen.getByText('Reload Page')).toBeInTheDocument();
  });

  it('allows retry after error', async () => {
    const user = userEvent.setup();
    
    render(
      <ErrorBoundary>
        <ThrowError />
      </ErrorBoundary>
    );
    
    const retryButton = screen.getByText('Try Again');
    await user.click(retryButton);
    
    // Should still show error since the component still throws
    expect(screen.getByText('Something went wrong')).toBeInTheDocument();
  });
});

describe('API Client', () => {
  it('handles successful API responses', async () => {
    const response = await api.getPatients(10, 0);
    expect(response).toEqual({
      patients: mockPatients,
      total: mockPatients.length,
    });
  });

  it('handles API errors', async () => {
    (api.getPatients as jest.Mock).mockRejectedValue(new Error('Network error'));
    
    await expect(api.getPatients(10, 0)).rejects.toThrow('Network error');
  });
});

