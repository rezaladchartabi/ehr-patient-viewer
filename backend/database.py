import sqlite3
import threading
import time
from typing import Dict, List, Optional, Any, Tuple, Iterator
from contextlib import contextmanager
import logging
from config import get_config
from exceptions import DatabaseError

logger = logging.getLogger(__name__)

class DatabaseConnectionPool:
    """Thread-safe SQLite connection pool"""
    
    def __init__(self, db_path: str, max_connections: int = 10):
        self.db_path = db_path
        self.max_connections = max_connections
        self._connections: List[sqlite3.Connection] = []
        self._lock = threading.Lock()
        self._in_use = set()
    
    @contextmanager
    def get_connection(self):
        """Get a database connection from the pool"""
        conn = None
        try:
            with self._lock:
                if self._connections:
                    conn = self._connections.pop()
                else:
                    conn = self._create_connection()
                
                self._in_use.add(conn)
            
            yield conn
        except Exception as e:
            if conn:
                logger.error(f"Database error: {e}")
                raise DatabaseError(f"Database operation failed: {e}")
        finally:
            if conn:
                with self._lock:
                    self._in_use.discard(conn)
                    if len(self._connections) < self.max_connections:
                        self._connections.append(conn)
                    else:
                        conn.close()
    
    def _create_connection(self) -> sqlite3.Connection:
        """Create a new database connection with proper configuration"""
        conn = sqlite3.connect(self.db_path, check_same_thread=False)
        conn.execute("PRAGMA foreign_keys = ON")
        conn.execute("PRAGMA journal_mode = WAL")
        conn.execute("PRAGMA synchronous = NORMAL")
        conn.execute("PRAGMA cache_size = 10000")
        conn.execute("PRAGMA temp_store = MEMORY")
        conn.row_factory = sqlite3.Row
        return conn
    
    def close_all(self):
        """Close all connections in the pool"""
        with self._lock:
            for conn in self._connections:
                conn.close()
            self._connections.clear()
            
            for conn in self._in_use:
                conn.close()
            self._in_use.clear()

class DatabaseManager:
    """Database manager with improved error handling and transaction support"""
    
    def __init__(self, db_path: str):
        self.db_path = db_path
        self.pool = DatabaseConnectionPool(db_path)
        self._init_database()
    
    def _init_database(self):
        """Initialize database schema"""
        with self.pool.get_connection() as conn:
            self._create_tables(conn)
            self._create_indexes(conn)
    
    def _create_tables(self, conn: sqlite3.Connection):
        """Create database tables"""
        tables = {
            'patients': """
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
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    updated_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            """,
            'allergies': """
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
                    updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (patient_id) REFERENCES patients (id) ON DELETE CASCADE
                )
            """,
            'conditions': """
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
                    updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (patient_id) REFERENCES patients (id) ON DELETE CASCADE
                )
            """,
            'encounters': """
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
                    updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (patient_id) REFERENCES patients (id) ON DELETE CASCADE
                )
            """,
            'medication_requests': """
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
                    updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (patient_id) REFERENCES patients (id) ON DELETE CASCADE
                )
            """,
            'medication_administrations': """
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
                    updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (patient_id) REFERENCES patients (id) ON DELETE CASCADE
                )
            """,
            'observations': """
                CREATE TABLE IF NOT EXISTS observations (
                    id TEXT PRIMARY KEY,
                    patient_id TEXT,
                    encounter_id TEXT,
                    observation_type TEXT,
                    code TEXT,
                    code_display TEXT,
                    code_system TEXT,
                    status TEXT,
                    effective_datetime TEXT,
                    issued_datetime TEXT,
                    value_quantity REAL,
                    value_unit TEXT,
                    value_code TEXT,
                    value_display TEXT,
                    value_string TEXT,
                    value_boolean INTEGER,
                    value_datetime TEXT,
                    category_code TEXT,
                    category_display TEXT,
                    interpretation_code TEXT,
                    interpretation_display TEXT,
                    reference_range_low REAL,
                    reference_range_high REAL,
                    reference_range_unit TEXT,
                    last_updated TEXT,
                    version_id TEXT,
                    hash TEXT,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (patient_id) REFERENCES patients (id) ON DELETE CASCADE
                )
            """,
            'procedures': """
                CREATE TABLE IF NOT EXISTS procedures (
                    id TEXT PRIMARY KEY,
                    patient_id TEXT,
                    encounter_id TEXT,
                    procedure_code TEXT,
                    procedure_display TEXT,
                    procedure_system TEXT,
                    status TEXT,
                    performed_datetime TEXT,
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
                    updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (patient_id) REFERENCES patients (id) ON DELETE CASCADE
                )
            """,
            'specimens': """
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
                    updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (patient_id) REFERENCES patients (id) ON DELETE CASCADE
                )
            """,
            'sync_metadata': """
                CREATE TABLE IF NOT EXISTS sync_metadata (
                    resource_type TEXT PRIMARY KEY,
                    last_sync_time TEXT,
                    last_version_id TEXT,
                    total_count INTEGER,
                    last_hash TEXT,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    updated_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            """
        }
        
        for table_name, create_sql in tables.items():
            try:
                conn.execute(create_sql)
                logger.info(f"Created/verified table: {table_name}")
            except Exception as e:
                logger.error(f"Error creating table {table_name}: {e}")
                raise DatabaseError(f"Failed to create table {table_name}: {e}")
    
    def _create_indexes(self, conn: sqlite3.Connection):
        """Create database indexes for better performance"""
        indexes = [
            "CREATE INDEX IF NOT EXISTS idx_patients_family_name ON patients(family_name)",
            "CREATE INDEX IF NOT EXISTS idx_patients_gender ON patients(gender)",
            "CREATE INDEX IF NOT EXISTS idx_patients_birth_date ON patients(birth_date)",
            "CREATE INDEX IF NOT EXISTS idx_allergies_patient_id ON allergies(patient_id)",
            "CREATE INDEX IF NOT EXISTS idx_allergies_code ON allergies(code)",
            "CREATE INDEX IF NOT EXISTS idx_conditions_patient_id ON conditions(patient_id)",
            "CREATE INDEX IF NOT EXISTS idx_conditions_encounter_id ON conditions(encounter_id)",
            "CREATE INDEX IF NOT EXISTS idx_encounters_patient_id ON encounters(patient_id)",
            "CREATE INDEX IF NOT EXISTS idx_encounters_start_date ON encounters(start_date)",
            "CREATE INDEX IF NOT EXISTS idx_medication_requests_patient_id ON medication_requests(patient_id)",
            "CREATE INDEX IF NOT EXISTS idx_medication_requests_encounter_id ON medication_requests(encounter_id)",
            "CREATE INDEX IF NOT EXISTS idx_medication_administrations_patient_id ON medication_administrations(patient_id)",
            "CREATE INDEX IF NOT EXISTS idx_medication_administrations_encounter_id ON medication_administrations(encounter_id)",
            "CREATE INDEX IF NOT EXISTS idx_observations_patient_id ON observations(patient_id)",
            "CREATE INDEX IF NOT EXISTS idx_observations_encounter_id ON observations(encounter_id)",
            "CREATE INDEX IF NOT EXISTS idx_procedures_patient_id ON procedures(patient_id)",
            "CREATE INDEX IF NOT EXISTS idx_procedures_encounter_id ON procedures(encounter_id)",
            "CREATE INDEX IF NOT EXISTS idx_specimens_patient_id ON specimens(patient_id)",
            "CREATE INDEX IF NOT EXISTS idx_specimens_encounter_id ON specimens(encounter_id)"
        ]
        
        for index_sql in indexes:
            try:
                conn.execute(index_sql)
            except Exception as e:
                logger.warning(f"Error creating index: {e}")
    
    @contextmanager
    def transaction(self):
        """Context manager for database transactions"""
        with self.pool.get_connection() as conn:
            try:
                yield conn
                conn.commit()
            except Exception:
                conn.rollback()
                raise
    
    def execute_query(self, sql: str, params: Tuple = ()) -> List[Dict]:
        """Execute a query and return results as list of dictionaries"""
        with self.pool.get_connection() as conn:
            cursor = conn.execute(sql, params)
            return [dict(row) for row in cursor.fetchall()]
    
    def execute_single(self, sql: str, params: Tuple = ()) -> Optional[Dict]:
        """Execute a query and return single result"""
        with self.pool.get_connection() as conn:
            cursor = conn.execute(sql, params)
            row = cursor.fetchone()
            return dict(row) if row else None
    
    def execute_update(self, sql: str, params: Tuple = ()) -> int:
        """Execute an update/insert/delete and return affected rows"""
        with self.pool.get_connection() as conn:
            cursor = conn.execute(sql, params)
            return cursor.rowcount
    
    def close(self):
        """Close all database connections"""
        self.pool.close_all()

