import { renderHook, waitFor, act } from '@testing-library/react';
import { usePatientList } from '../hooks/usePatientList';
import { usePatientData } from '../hooks/usePatientData';
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
  },
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

describe('usePatientList Hook', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    (api.getPatients as jest.Mock).mockResolvedValue({
      patients: mockPatients,
      total: mockPatients.length,
    });
  });

  it('loads patients on mount', async () => {
    const { result } = renderHook(() => usePatientList());

    expect(result.current.loading).toBe(true);
    expect(result.current.patients).toEqual([]);

    await waitFor(() => {
      expect(result.current.loading).toBe(false);
    });

    expect(result.current.patients).toEqual(mockPatients);
    expect(result.current.error).toBeNull();
  });

  it('handles API errors', async () => {
    (api.getPatients as jest.Mock).mockRejectedValue(new Error('API Error'));

    const { result } = renderHook(() => usePatientList());

    await waitFor(() => {
      expect(result.current.loading).toBe(false);
    });

    expect(result.current.error).toContain('Failed to fetch patients');
    expect(result.current.patients).toEqual([]);
  });

  it('provides pagination functionality', async () => {
    const { result } = renderHook(() => usePatientList());

    await waitFor(() => {
      expect(result.current.loading).toBe(false);
    });

    expect(result.current.page).toBe(0);
    expect(result.current.hasNextPage).toBe(false);
    expect(result.current.hasPrevPage).toBe(false);
    expect(result.current.pageSize).toBe(25);
  });

  it('allows manual refresh', async () => {
    const { result } = renderHook(() => usePatientList());

    await waitFor(() => {
      expect(result.current.loading).toBe(false);
    });

    // Call loadFirstPatientsPage again
    act(() => {
      result.current.loadFirstPatientsPage();
    });

    expect(result.current.loading).toBe(true);

    await waitFor(() => {
      expect(result.current.loading).toBe(false);
    });

    // Should have called the API twice
    expect(api.getPatients).toHaveBeenCalledTimes(2);
  });
});

describe('usePatientData Hook', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    (api.getPatient as jest.Mock).mockResolvedValue(mockPatientData);
    (api.getEncounters as jest.Mock).mockResolvedValue(mockEncounters);
    (api.getConditions as jest.Mock).mockResolvedValue(mockConditions);
  });

  it('fetches patient data when called', async () => {
    const { result } = renderHook(() => usePatientData());

    expect(result.current.loading).toBe(false);
    expect(result.current.currentPatient).toBeNull();

    // Fetch patient data
    act(() => {
      result.current.fetchPatientData(mockPatients[0]);
    });

    expect(result.current.loading).toBe(true);

    await waitFor(() => {
      expect(result.current.loading).toBe(false);
    });

    expect(result.current.currentPatient).toEqual({
      ...mockPatients[0],
      allergies: mockPatientData.allergies,
    });
    expect(result.current.error).toBeNull();
  });

  it('handles API errors when fetching patient data', async () => {
    (api.getPatient as jest.Mock).mockRejectedValue(new Error('API Error'));

    const { result } = renderHook(() => usePatientData());

    act(() => {
      result.current.fetchPatientData(mockPatients[0]);
    });

    await waitFor(() => {
      expect(result.current.loading).toBe(false);
    });

    expect(result.current.error).toContain('Failed to fetch patient data');
    expect(result.current.currentPatient).toBeNull();
  });

  it('fetches encounter data when called', async () => {
    const { result } = renderHook(() => usePatientData());

    // First fetch patient data
    act(() => {
      result.current.fetchPatientData(mockPatients[0]);
    });

    await waitFor(() => {
      expect(result.current.loading).toBe(false);
    });

    // Fetch encounter data
    act(() => {
      result.current.fetchEncounterData('test-patient-1', 'encounter-1');
    });

    await waitFor(() => {
      expect(result.current.encounterData.get('encounter-1')).toBeDefined();
    });
  });

  it('clears data when called', async () => {
    const { result } = renderHook(() => usePatientData());

    // Fetch patient data first
    act(() => {
      result.current.fetchPatientData(mockPatients[0]);
    });

    await waitFor(() => {
      expect(result.current.loading).toBe(false);
    });

    expect(result.current.currentPatient).not.toBeNull();

    // Clear data
    act(() => {
      result.current.clearData();
    });

    expect(result.current.currentPatient).toBeNull();
    expect(result.current.patientSummary).toBeNull();
    expect(result.current.encounters).toEqual([]);
    expect(result.current.conditions).toEqual([]);
    expect(result.current.encounterData.size).toBe(0);
    expect(result.current.error).toBeNull();
  });

  it('sorts encounters by date', async () => {
    const mockEncountersWithDates = {
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
        {
          resource: {
            id: 'encounter-2',
            resourceType: 'Encounter',
            status: 'finished',
            class: { code: 'AMB', display: 'Ambulatory' },
            period: { start: '2023-02-01', end: '2023-02-01' },
            subject: { reference: 'Patient/test-patient-1' },
          },
        },
      ],
    };

    (api.getEncounters as jest.Mock).mockResolvedValue(mockEncountersWithDates);

    const { result } = renderHook(() => usePatientData());

    act(() => {
      result.current.fetchPatientData(mockPatients[0]);
    });

    await waitFor(() => {
      expect(result.current.loading).toBe(false);
    });

    // Encounters should be sorted by date (most recent first)
    expect(result.current.encounters[0].id).toBe('encounter-2');
    expect(result.current.encounters[1].id).toBe('encounter-1');
  });

  it('caches encounter data', async () => {
    const { result } = renderHook(() => usePatientData());

    // Fetch patient data first
    act(() => {
      result.current.fetchPatientData(mockPatients[0]);
    });

    await waitFor(() => {
      expect(result.current.loading).toBe(false);
    });

    // Fetch encounter data
    act(() => {
      result.current.fetchEncounterData('test-patient-1', 'encounter-1');
    });

    await waitFor(() => {
      expect(result.current.encounterData.get('encounter-1')).toBeDefined();
    });

    // Fetch the same encounter data again
    act(() => {
      result.current.fetchEncounterData('test-patient-1', 'encounter-1');
    });

    // Should not call the API again since it's cached
    expect(api.getEncounterMedications).toHaveBeenCalledTimes(1);
    expect(api.getEncounterObservations).toHaveBeenCalledTimes(1);
    expect(api.getEncounterProcedures).toHaveBeenCalledTimes(1);
    expect(api.getEncounterSpecimens).toHaveBeenCalledTimes(1);
  });
});

describe('Hook Integration', () => {
  it('works together in a typical flow', async () => {
    const { result: patientListResult } = renderHook(() => usePatientList());
    const { result: patientDataResult } = renderHook(() => usePatientData());

    // Wait for patient list to load
    await waitFor(() => {
      expect(patientListResult.current.loading).toBe(false);
    });

    // Select a patient
    act(() => {
      patientDataResult.current.fetchPatientData(mockPatients[0]);
    });

    await waitFor(() => {
      expect(patientDataResult.current.loading).toBe(false);
    });

    // Verify both hooks are working
    expect(patientListResult.current.patients).toEqual(mockPatients);
    expect(patientDataResult.current.currentPatient).toEqual({
      ...mockPatients[0],
      allergies: mockPatientData.allergies,
    });
  });
});

