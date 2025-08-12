import sqlite3
import json
import hashlib
import time
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class LocalDatabase:
    def __init__(self, db_path: str = "local_ehr.db"):
        self.db_path = db_path
        self.init_database()
    
    def init_database(self):
        """Initialize the local database with all required tables"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("PRAGMA foreign_keys = ON")
            
            # Patients table
            conn.execute("""
                CREATE TABLE IF NOT EXISTS patients (
                    id TEXT PRIMARY KEY,
                    family_name TEXT,
                    gender TEXT,
                    birth_date TEXT,
                    race TEXT,
                    ethnicity TEXT,
                    birth_sex TEXT,
                    identifier TEXT,
                    marital_status TEXT,
                    deceased_date TEXT,
                    managing_organization TEXT,
                    last_updated TEXT,
                    version_id TEXT,
                    hash TEXT,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Allergies table
            conn.execute("""
                CREATE TABLE IF NOT EXISTS allergies (
                    id TEXT PRIMARY KEY,
                    patient_id TEXT,
                    code TEXT,
                    code_display TEXT,
                    code_system TEXT,
                    category TEXT,
                    clinical_status TEXT,
                    verification_status TEXT,
                    type TEXT,
                    criticality TEXT,
                    onset_date TEXT,
                    recorded_date TEXT,
                    recorder TEXT,
                    asserter TEXT,
                    last_occurrence TEXT,
                    note TEXT,
                    last_updated TEXT,
                    version_id TEXT,
                    hash TEXT,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (patient_id) REFERENCES patients (id) ON DELETE CASCADE
                )
            """)
            
            # Conditions table
            conn.execute("""
                CREATE TABLE IF NOT EXISTS conditions (
                    id TEXT PRIMARY KEY,
                    patient_id TEXT,
                    code TEXT,
                    code_display TEXT,
                    code_system TEXT,
                    category TEXT,
                    encounter_id TEXT,
                    status TEXT,
                    last_updated TEXT,
                    version_id TEXT,
                    hash TEXT,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (patient_id) REFERENCES patients (id) ON DELETE CASCADE
                )
            """)
            
            # Encounters table
            conn.execute("""
                CREATE TABLE IF NOT EXISTS encounters (
                    id TEXT PRIMARY KEY,
                    patient_id TEXT,
                    encounter_type TEXT,
                    status TEXT,
                    start_date TEXT,
                    end_date TEXT,
                    class_code TEXT,
                    class_display TEXT,
                    service_type TEXT,
                    priority_code TEXT,
                    priority_display TEXT,
                    diagnosis_condition TEXT,
                    diagnosis_use TEXT,
                    diagnosis_rank INTEGER,
                    hospitalization_admit_source_code TEXT,
                    hospitalization_admit_source_display TEXT,
                    hospitalization_discharge_disposition_code TEXT,
                    hospitalization_discharge_disposition_display TEXT,
                    last_updated TEXT,
                    version_id TEXT,
                    hash TEXT,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (patient_id) REFERENCES patients (id) ON DELETE CASCADE
                )
            """)
            
            # Medication Requests table
            conn.execute("""
                CREATE TABLE IF NOT EXISTS medication_requests (
                    id TEXT PRIMARY KEY,
                    patient_id TEXT,
                    encounter_id TEXT,
                    medication_code TEXT,
                    medication_display TEXT,
                    medication_system TEXT,
                    status TEXT,
                    intent TEXT,
                    priority TEXT,
                    authored_on TEXT,
                    dosage_quantity REAL,
                    dosage_unit TEXT,
                    frequency_code TEXT,
                    frequency_display TEXT,
                    route_code TEXT,
                    route_display TEXT,
                    reason_code TEXT,
                    reason_display TEXT,
                    last_updated TEXT,
                    version_id TEXT,
                    hash TEXT,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (patient_id) REFERENCES patients (id) ON DELETE CASCADE
                )
            """)
            
            # Medication Administrations table
            conn.execute("""
                CREATE TABLE IF NOT EXISTS medication_administrations (
                    id TEXT PRIMARY KEY,
                    patient_id TEXT,
                    encounter_id TEXT,
                    medication_code TEXT,
                    medication_display TEXT,
                    medication_system TEXT,
                    status TEXT,
                    effective_start TEXT,
                    effective_end TEXT,
                    dosage_quantity REAL,
                    dosage_unit TEXT,
                    route_code TEXT,
                    route_display TEXT,
                    site_code TEXT,
                    site_display TEXT,
                    method_code TEXT,
                    method_display TEXT,
                    reason_code TEXT,
                    reason_display TEXT,
                    last_updated TEXT,
                    version_id TEXT,
                    hash TEXT,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (patient_id) REFERENCES patients (id) ON DELETE CASCADE
                )
            """)
            
            # Observations table
            conn.execute("""
                CREATE TABLE IF NOT EXISTS observations (
                    id TEXT PRIMARY KEY,
                    patient_id TEXT,
                    encounter_id TEXT,
                    observation_type TEXT,
                    code TEXT,
                    code_display TEXT,
                    code_system TEXT,
                    value_quantity REAL,
                    value_unit TEXT,
                    value_code TEXT,
                    value_code_display TEXT,
                    value_string TEXT,
                    value_boolean BOOLEAN,
                    effective_datetime TEXT,
                    issued TEXT,
                    status TEXT,
                    category_code TEXT,
                    category_display TEXT,
                    last_updated TEXT,
                    version_id TEXT,
                    hash TEXT,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (patient_id) REFERENCES patients (id) ON DELETE CASCADE
                )
            """)
            
            # Procedures table
            conn.execute("""
                CREATE TABLE IF NOT EXISTS procedures (
                    id TEXT PRIMARY KEY,
                    patient_id TEXT,
                    encounter_id TEXT,
                    procedure_code TEXT,
                    procedure_display TEXT,
                    procedure_system TEXT,
                    status TEXT,
                    performed_period_start TEXT,
                    performed_period_end TEXT,
                    category_code TEXT,
                    category_display TEXT,
                    reason_code TEXT,
                    reason_display TEXT,
                    outcome_code TEXT,
                    outcome_display TEXT,
                    complication_code TEXT,
                    complication_display TEXT,
                    follow_up_code TEXT,
                    follow_up_display TEXT,
                    last_updated TEXT,
                    version_id TEXT,
                    hash TEXT,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (patient_id) REFERENCES patients (id) ON DELETE CASCADE
                )
            """)
            
            # Specimens table
            conn.execute("""
                CREATE TABLE IF NOT EXISTS specimens (
                    id TEXT PRIMARY KEY,
                    patient_id TEXT,
                    encounter_id TEXT,
                    specimen_type_code TEXT,
                    specimen_type_display TEXT,
                    specimen_type_system TEXT,
                    status TEXT,
                    collected_datetime TEXT,
                    received_datetime TEXT,
                    collection_method_code TEXT,
                    collection_method_display TEXT,
                    body_site_code TEXT,
                    body_site_display TEXT,
                    fasting_status_code TEXT,
                    fasting_status_display TEXT,
                    container_code TEXT,
                    container_display TEXT,
                    note TEXT,
                    last_updated TEXT,
                    version_id TEXT,
                    hash TEXT,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (patient_id) REFERENCES patients (id) ON DELETE CASCADE
                )
            """)
            
            # Sync metadata table
            conn.execute("""
                CREATE TABLE IF NOT EXISTS sync_metadata (
                    resource_type TEXT PRIMARY KEY,
                    last_sync_time TEXT,
                    last_version_id TEXT,
                    total_count INTEGER,
                    last_hash TEXT
                )
            """)
            
            # Create indexes for better performance
            conn.execute("CREATE INDEX IF NOT EXISTS idx_patients_identifier ON patients(identifier)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_allergies_patient ON allergies(patient_id)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_conditions_patient ON conditions(patient_id)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_encounters_patient ON encounters(patient_id)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_med_requests_patient ON medication_requests(patient_id)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_med_admin_patient ON medication_administrations(patient_id)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_observations_patient ON observations(patient_id)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_procedures_patient ON procedures(patient_id)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_specimens_patient ON specimens(patient_id)")
            
            conn.commit()
    
    def calculate_hash(self, data: Dict[str, Any]) -> str:
        """Calculate a hash for change detection"""
        # Remove metadata fields that shouldn't affect content hash
        content_data = {k: v for k, v in data.items() 
                       if k not in ['id', 'last_updated', 'version_id', 'hash', 'created_at']}
        return hashlib.md5(json.dumps(content_data, sort_keys=True).encode()).hexdigest()
    
    def get_last_sync_info(self, resource_type: str) -> Optional[Dict[str, Any]]:
        """Get last sync information for a resource type"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(
                "SELECT last_sync_time, last_version_id, total_count, last_hash FROM sync_metadata WHERE resource_type = ?",
                (resource_type,)
            )
            row = cursor.fetchone()
            if row:
                return {
                    'last_sync_time': row[0],
                    'last_version_id': row[1],
                    'total_count': row[2],
                    'last_hash': row[3]
                }
            return None
    
    def update_sync_metadata(self, resource_type: str, sync_info: Dict[str, Any]):
        """Update sync metadata for a resource type"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                INSERT OR REPLACE INTO sync_metadata 
                (resource_type, last_sync_time, last_version_id, total_count, last_hash)
                VALUES (?, ?, ?, ?, ?)
            """, (
                resource_type,
                sync_info.get('last_sync_time'),
                sync_info.get('last_version_id'),
                sync_info.get('total_count'),
                sync_info.get('last_hash')
            ))
            conn.commit()
    
    def upsert_patient(self, patient_data: Dict[str, Any]) -> bool:
        """Insert or update a patient record, returns True if changed"""
        hash_value = self.calculate_hash(patient_data)
        
        with sqlite3.connect(self.db_path) as conn:
            # Check if record exists and if hash is different
            cursor = conn.execute(
                "SELECT hash FROM patients WHERE id = ?",
                (patient_data['id'],)
            )
            existing = cursor.fetchone()
            
            if existing and existing[0] == hash_value:
                return False  # No change
            
            # Insert or update
            conn.execute("""
                INSERT OR REPLACE INTO patients (
                    id, family_name, gender, birth_date, race, ethnicity, birth_sex,
                    identifier, marital_status, deceased_date, managing_organization,
                    last_updated, version_id, hash
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                patient_data['id'],
                patient_data.get('family_name'),
                patient_data.get('gender'),
                patient_data.get('birth_date'),
                patient_data.get('race'),
                patient_data.get('ethnicity'),
                patient_data.get('birth_sex'),
                patient_data.get('identifier'),
                patient_data.get('marital_status'),
                patient_data.get('deceased_date'),
                patient_data.get('managing_organization'),
                patient_data.get('last_updated'),
                patient_data.get('version_id'),
                hash_value
            ))
            conn.commit()
            return True
    
    def upsert_allergy(self, allergy_data: Dict[str, Any]) -> bool:
        """Insert or update an allergy record, returns True if changed"""
        hash_value = self.calculate_hash(allergy_data)
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(
                "SELECT hash FROM allergies WHERE id = ?",
                (allergy_data['id'],)
            )
            existing = cursor.fetchone()
            
            if existing and existing[0] == hash_value:
                return False  # No change
            
            conn.execute("""
                INSERT OR REPLACE INTO allergies (
                    id, patient_id, code, code_display, code_system, category,
                    clinical_status, verification_status, type, criticality,
                    onset_date, recorded_date, recorder, asserter, last_occurrence, note,
                    last_updated, version_id, hash
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                allergy_data['id'],
                allergy_data.get('patient_id'),
                allergy_data.get('code'),
                allergy_data.get('code_display'),
                allergy_data.get('code_system'),
                allergy_data.get('category'),
                allergy_data.get('clinical_status'),
                allergy_data.get('verification_status'),
                allergy_data.get('type'),
                allergy_data.get('criticality'),
                allergy_data.get('onset_date'),
                allergy_data.get('recorded_date'),
                allergy_data.get('recorder'),
                allergy_data.get('asserter'),
                allergy_data.get('last_occurrence'),
                allergy_data.get('note'),
                allergy_data.get('last_updated'),
                allergy_data.get('version_id'),
                hash_value
            ))
            conn.commit()
            return True
    
    def get_patient_with_allergies(self, patient_id: str) -> Optional[Dict[str, Any]]:
        """Get a patient with their allergies"""
        with sqlite3.connect(self.db_path) as conn:
            # Get patient
            cursor = conn.execute(
                "SELECT * FROM patients WHERE id = ?",
                (patient_id,)
            )
            patient_row = cursor.fetchone()
            
            if not patient_row:
                return None
            
            # Get allergies
            cursor = conn.execute(
                "SELECT * FROM allergies WHERE patient_id = ?",
                (patient_id,)
            )
            allergy_rows = cursor.fetchall()
            
            # Convert to dict
            patient = dict(zip([col[0] for col in cursor.description], patient_row))
            allergies = [dict(zip([col[0] for col in cursor.description], row)) for row in allergy_rows]
            
            patient['allergies'] = allergies
            return patient
    
    def get_patients_by_ids(self, patient_ids: List[str]) -> List[Dict[str, Any]]:
        """Get multiple patients by their IDs"""
        if not patient_ids:
            return []
        
        with sqlite3.connect(self.db_path) as conn:
            placeholders = ','.join(['?' for _ in patient_ids])
            cursor = conn.execute(
                f"SELECT * FROM patients WHERE id IN ({placeholders})",
                patient_ids
            )
            rows = cursor.fetchall()
            
            return [dict(zip([col[0] for col in cursor.description], row)) for row in rows]
    
    def get_all_patients(self, limit: int = 25, offset: int = 0) -> List[Dict[str, Any]]:
        """Get all patients with pagination"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(
                "SELECT * FROM patients ORDER BY family_name LIMIT ? OFFSET ?",
                (limit, offset)
            )
            rows = cursor.fetchall()
            
            return [dict(zip([col[0] for col in cursor.description], row)) for row in rows]
    
    def get_patient_count(self) -> int:
        """Get total number of patients"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("SELECT COUNT(*) FROM patients")
            return cursor.fetchone()[0]
