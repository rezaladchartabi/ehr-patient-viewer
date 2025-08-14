// Core FHIR Resource Types
export interface FHIRResource {
  id: string;
  resourceType: string;
  meta?: {
    versionId?: string;
    lastUpdated?: string;
  };
}

// Patient Types
export interface Patient extends FHIRResource {
  resourceType: 'Patient';
  name?: Array<{
    family?: string;
    given?: string[];
  }>;
  gender?: 'male' | 'female' | 'other' | 'unknown';
  birthDate?: string;
  identifier?: Array<{
    system?: string;
    value?: string;
  }>;
  maritalStatus?: {
    coding?: Array<{
      code?: string;
      display?: string;
    }>;
  };
  deceasedDateTime?: string;
  managingOrganization?: {
    reference?: string;
  };
  extension?: Array<{
    url: string;
    valueCode?: string;
    valueString?: string;
    extension?: Array<{
      url: string;
      valueString?: string;
    }>;
  }>;
}

// Allergy Types
export interface Allergy extends FHIRResource {
  resourceType: 'AllergyIntolerance';
  patient?: {
    reference?: string;
  };
  code?: {
    coding?: Array<{
      code?: string;
      display?: string;
      system?: string;
    }>;
  };
  category?: Array<{
    coding?: Array<{
      code?: string;
      display?: string;
    }>;
  }>;
  clinicalStatus?: {
    coding?: Array<{
      code?: string;
      display?: string;
    }>;
  };
  verificationStatus?: {
    coding?: Array<{
      code?: string;
      display?: string;
    }>;
  };
  type?: 'allergy' | 'intolerance';
  criticality?: 'low' | 'high' | 'unable-to-assess';
  onsetDateTime?: string;
  recordedDate?: string;
  recorder?: {
    reference?: string;
  };
  asserter?: {
    reference?: string;
  };
  lastOccurrence?: string;
  note?: Array<{
    text?: string;
  }>;
}

// Condition Types
export interface Condition extends FHIRResource {
  resourceType: 'Condition';
  patient?: {
    reference?: string;
  };
  code?: {
    coding?: Array<{
      code?: string;
      display?: string;
      system?: string;
    }>;
    text?: string;
  };
  category?: Array<{
    coding?: Array<{
      code?: string;
      display?: string;
    }>;
  }>;
  encounter?: {
    reference?: string;
  };
  clinicalStatus?: {
    coding?: Array<{
      code?: string;
      display?: string;
    }>;
  };
}

// Encounter Types
export interface Encounter extends FHIRResource {
  resourceType: 'Encounter';
  patient?: {
    reference?: string;
  };
  class?: {
    code?: string;
    display?: string;
  };
  status?: 'planned' | 'arrived' | 'triaged' | 'in-progress' | 'onleave' | 'finished' | 'cancelled';
  period?: {
    start?: string;
    end?: string;
  };
  serviceType?: {
    coding?: Array<{
      code?: string;
      display?: string;
    }>;
  };
  priority?: {
    coding?: Array<{
      code?: string;
      display?: string;
    }>;
  };
  diagnosis?: Array<{
    condition?: {
      reference?: string;
    };
    use?: {
      coding?: Array<{
        code?: string;
        display?: string;
      }>;
    };
    rank?: number;
  }>;
  hospitalization?: {
    admitSource?: {
      coding?: Array<{
        code?: string;
        display?: string;
      }>;
    };
    dischargeDisposition?: {
      coding?: Array<{
        code?: string;
        display?: string;
      }>;
    };
  };
}

// Medication Types
export interface MedicationRequest extends FHIRResource {
  resourceType: 'MedicationRequest';
  patient?: {
    reference?: string;
  };
  encounter?: {
    reference?: string;
  };
  medicationCodeableConcept?: {
    coding?: Array<{
      code?: string;
      display?: string;
      system?: string;
    }>;
  };
  status?: string;
  intent?: string;
  priority?: string;
  authoredOn?: string;
  dosageInstruction?: Array<{
    doseAndRate?: Array<{
      doseQuantity?: {
        value?: number;
        unit?: string;
      };
    }>;
    timing?: {
      repeat?: {
        frequency?: number;
        period?: number;
        periodUnit?: string;
      };
    };
    route?: {
      coding?: Array<{
        code?: string;
        display?: string;
      }>;
    };
  }>;
  reasonCode?: Array<{
    coding?: Array<{
      code?: string;
      display?: string;
    }>;
  }>;
}

export interface MedicationAdministration extends FHIRResource {
  resourceType: 'MedicationAdministration';
  patient?: {
    reference?: string;
  };
  encounter?: {
    reference?: string;
  };
  medicationCodeableConcept?: {
    coding?: Array<{
      code?: string;
      display?: string;
      system?: string;
    }>;
  };
  status?: string;
  effectiveDateTime?: string;
  effectivePeriod?: {
    start?: string;
    end?: string;
  };
  dosage?: {
    dose?: {
      value?: number;
      unit?: string;
    };
    route?: {
      coding?: Array<{
        code?: string;
        display?: string;
      }>;
    };
    site?: {
      coding?: Array<{
        code?: string;
        display?: string;
      }>;
    };
    method?: {
      coding?: Array<{
        code?: string;
        display?: string;
      }>;
    };
  };
  reasonCode?: Array<{
    coding?: Array<{
      code?: string;
      display?: string;
    }>;
  }>;
}

// Observation Types
export interface Observation extends FHIRResource {
  resourceType: 'Observation';
  patient?: {
    reference?: string;
  };
  encounter?: {
    reference?: string;
  };
  code?: {
    coding?: Array<{
      code?: string;
      display?: string;
      system?: string;
    }>;
  };
  status?: string;
  effectiveDateTime?: string;
  issued?: string;
  valueQuantity?: {
    value?: number;
    unit?: string;
  };
  valueCodeableConcept?: {
    coding?: Array<{
      code?: string;
      display?: string;
    }>;
  };
  valueString?: string;
  valueBoolean?: boolean;
  valueDateTime?: string;
  category?: Array<{
    coding?: Array<{
      code?: string;
      display?: string;
    }>;
  }>;
  interpretation?: Array<{
    coding?: Array<{
      code?: string;
      display?: string;
    }>;
  }>;
  referenceRange?: Array<{
    low?: {
      value?: number;
      unit?: string;
    };
    high?: {
      value?: number;
      unit?: string;
    };
  }>;
}

// Procedure Types
export interface Procedure extends FHIRResource {
  resourceType: 'Procedure';
  patient?: {
    reference?: string;
  };
  encounter?: {
    reference?: string;
  };
  code?: {
    coding?: Array<{
      code?: string;
      display?: string;
      system?: string;
    }>;
  };
  status?: string;
  performedDateTime?: string;
  performedPeriod?: {
    start?: string;
    end?: string;
  };
  category?: {
    coding?: Array<{
      code?: string;
      display?: string;
    }>;
  };
  reasonCode?: Array<{
    coding?: Array<{
      code?: string;
      display?: string;
    }>;
  }>;
  outcome?: {
    coding?: Array<{
      code?: string;
      display?: string;
    }>;
  };
  complication?: Array<{
    coding?: Array<{
      code?: string;
      display?: string;
    }>;
  }>;
  followUp?: Array<{
    coding?: Array<{
      code?: string;
      display?: string;
    }>;
  }>;
}

// Specimen Types
export interface Specimen extends FHIRResource {
  resourceType: 'Specimen';
  patient?: {
    reference?: string;
  };
  encounter?: {
    reference?: string;
  };
  type?: {
    coding?: Array<{
      code?: string;
      display?: string;
      system?: string;
    }>;
  };
  status?: string;
  collectedDateTime?: string;
  receivedTime?: string;
  collection?: {
    method?: {
      coding?: Array<{
        code?: string;
        display?: string;
      }>;
    };
    bodySite?: {
      coding?: Array<{
        code?: string;
        display?: string;
      }>;
    };
  };
  fastingStatus?: {
    coding?: Array<{
      code?: string;
      display?: string;
    }>;
  };
  container?: Array<{
    type?: {
      coding?: Array<{
        code?: string;
        display?: string;
      }>;
    };
  }>;
  note?: Array<{
    text?: string;
  }>;
}

// Bundle Types
export interface FHIRBundle {
  resourceType: 'Bundle';
  type: 'searchset' | 'history' | 'transaction' | 'batch';
  total?: number;
  link?: Array<{
    relation: string;
    url: string;
  }>;
  entry?: Array<{
    resource: FHIRResource;
    search?: {
      mode?: string;
    };
  }>;
}

// API Response Types
export interface APIResponse<T = any> {
  data?: T;
  error?: string;
  message?: string;
  status: 'success' | 'error';
}

export interface PaginatedResponse<T> {
  data: T[];
  total: number;
  page: number;
  pageSize: number;
  hasNext: boolean;
  hasPrevious: boolean;
}

// Local Database Types
export interface LocalPatient {
  id: string;
  family_name: string;
  gender: string;
  birth_date: string;
  race?: string;
  ethnicity?: string;
  birth_sex?: string;
  identifier?: string;
  marital_status?: string;
  deceased_date?: string;
  managing_organization?: string;
  allergies?: LocalAllergy[];
}

export interface LocalAllergy {
  id: string;
  patient_id: string;
  code: string;
  code_display: string;
  code_system: string;
  category: string;
  clinical_status: string;
  verification_status: string;
  type: string;
  criticality: string;
  onset_date: string;
  recorded_date: string;
  recorder: string;
  asserter: string;
  last_occurrence: string;
  note: string;
}

// UI Component Props
export interface PatientCardProps {
  patient: LocalPatient;
  onSelect: (patient: LocalPatient) => void;
  isSelected: boolean;
}

export interface EncounterCardProps {
  encounter: Encounter;
  onSelect: (encounterId: string) => void;
  isSelected: boolean;
}

export interface SearchBarProps {
  onSearch: (query: string) => void;
  placeholder?: string;
  disabled?: boolean;
}

// Hook Return Types
export interface UsePatientListReturn {
  patients: LocalPatient[];
  loading: boolean;
  error: string | null;
  page: number;
  nextPageCursor: string | null;
  prevPageCursors: string[];
  loadFirstPatientsPage: () => Promise<void>;
  handleNextPage: () => void;
  handlePrevPage: () => void;
  hasNextPage: boolean;
  hasPrevPage: boolean;
  pageSize: number;
}

export interface UsePatientDataReturn {
  loading: boolean;
  error: string | null;
  currentPatient: LocalPatient | null;
  patientSummary: PatientSummary | null;
  encounters: Encounter[];
  conditions: Condition[];
  encounterData: Map<string, EncounterData>;
  fetchPatientData: (patient: LocalPatient) => Promise<void>;
  fetchEncounterData: (patientId: string, encounterId: string) => Promise<void>;
  clearData: () => void;
  getEncounterData: (encounterId: string) => EncounterData | undefined;
}

// Summary Types
export interface PatientSummary {
  patient: LocalPatient;
  summary: {
    conditions: number;
    medications: number;
    encounters: number;
    medication_administrations: number;
    medication_requests: number;
    observations: number;
    procedures: number;
    specimens: number;
  };
}

export interface EncounterData {
  conditions: Condition[];
  medicationRequests: MedicationRequest[];
  medicationAdministrations: MedicationAdministration[];
  observations: Observation[];
  procedures: Procedure[];
  specimens: Specimen[];
  note?: string;
}

// Error Types
export interface APIError {
  error: string;
  error_code?: string;
  details?: Record<string, any>;
}

// Configuration Types
export interface AppConfig {
  apiBaseUrl: string;
  fhirBaseUrl: string;
  enableCache: boolean;
  cacheTTL: number;
  enableRateLimiting: boolean;
  maxRequestsPerMinute: number;
}

// Theme Types
export type Theme = 'light' | 'dark' | 'system';

export interface ThemeContextType {
  theme: Theme;
  setTheme: (theme: Theme) => void;
  isDark: boolean;
}

