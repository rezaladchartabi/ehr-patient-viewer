// Centralized TypeScript types for the EHR application

export interface Patient {
  id: string;
  family_name: string;
  gender: string;
  birth_date: string;
  race?: string;
  ethnicity?: string;
  identifier?: string;
  marital_status?: string;
  allergies?: Allergy[];
}

export interface Encounter {
  id: string;
  status: string;
  start_date: string;
  end_date?: string;
  class_display: string;
  encounter_type: string;
}

export interface Allergy {
  id?: string;
  allergy_name: string;
  severity?: string;
  reaction?: string;
  onset_date?: string;
}

export interface PMH {
  id?: string;
  condition_name: string;
  status: string;
  onset_date?: string;
  severity?: string;
}

export interface Note {
  id?: string;
  note_id?: string;
  patient_id: string;
  note_type?: string;
  text?: string;
  content?: string;
  charttime?: string;
  charttime_formatted?: string;
  store_time?: string;
  storetime_formatted?: string;
  created_at?: string;
  timestamp?: string;
  allergies?: Allergy[];
  conditions?: PMH[];
  medications?: any[];
}

export interface SearchResult {
  patient_id: string;
  resource_type: string;
  resource_id: string;
  content: string;
  timestamp: string;
  note_id: string;
  rank: number;
  matched_terms: string[];
}

export interface BackendStatus {
  ready: boolean;
  message?: string;
  timestamp?: string;
}

export interface HealthStatus {
  status: 'healthy' | 'unhealthy';
  timestamp: string;
  services: {
    database: 'healthy' | 'unhealthy';
    fhir_server: 'healthy' | 'unhealthy';
  };
  version: string;
  error?: string;
}
