from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import sqlite3
from typing import List, Dict
import os

# Database path
DB_PATH = os.path.join(os.path.dirname(__file__), "ehr_data.sqlite3")

app = FastAPI(title="EHR System API", version="1.0.0")

# Allow CORS for all origins (you can restrict this in production)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

@app.get("/")
def read_root():
    return {"message": "EHR System API is running"}

@app.get("/search", response_model=List[Dict])
def global_search(q: str, limit: int = 50) -> List[Dict]:
    """
    Simple global search across multiple resources. Uses case-insensitive LIKE
    matching on commonly searched columns and returns a unified result shape.
    """
    if not q:
        return []

    search_term = f"%{q}%"
    per_table_limit = max(5, limit // 7)

    conn = get_db_connection()
    cursor = conn.cursor()

    results: List[Dict] = []

    # Patients
    cursor.execute(
        """
        SELECT 'patient' as type, id, family_name as title,
               (COALESCE(identifier,'') || ' • ' || COALESCE(gender,'') || ' • ' || COALESCE(birth_date,'')) as subtitle,
               id as patient_id
        FROM patient
        WHERE family_name LIKE ? OR identifier LIKE ? OR id LIKE ?
        LIMIT ?
        """,
        (search_term, search_term, search_term, per_table_limit),
    )
    results.extend([dict(row) for row in cursor.fetchall()])

    # Conditions
    cursor.execute(
        """
        SELECT 'condition' as type, id, code_display as title,
               (COALESCE(code,'') || ' • ' || COALESCE(category,'')) as subtitle,
               patient_id
        FROM condition
        WHERE code_display LIKE ? OR code LIKE ? OR category LIKE ?
        LIMIT ?
        """,
        (search_term, search_term, search_term, per_table_limit),
    )
    results.extend([dict(row) for row in cursor.fetchall()])

    # Medications (Dispense)
    cursor.execute(
        """
        SELECT 'medication' as type, id, medication_display as title,
               (COALESCE(medication_code,'') || ' • ' || COALESCE(status,'')) as subtitle,
               patient_id
        FROM medication
        WHERE medication_display LIKE ? OR medication_code LIKE ? OR status LIKE ?
        LIMIT ?
        """,
        (search_term, search_term, search_term, per_table_limit),
    )
    results.extend([dict(row) for row in cursor.fetchall()])

    # Encounters
    cursor.execute(
        """
        SELECT 'encounter' as type, id, class_display as title,
               (COALESCE(encounter_type,'') || ' • ' || COALESCE(status,'')) as subtitle,
               patient_id
        FROM encounter
        WHERE class_display LIKE ? OR encounter_type LIKE ? OR status LIKE ?
        LIMIT ?
        """,
        (search_term, search_term, search_term, per_table_limit),
    )
    results.extend([dict(row) for row in cursor.fetchall()])

    # Medication administrations
    cursor.execute(
        """
        SELECT 'medication-administration' as type, id, medication_display as title,
               (COALESCE(status,'') || ' • ' || COALESCE(route_code,'')) as subtitle,
               patient_id
        FROM medication_administration
        WHERE medication_display LIKE ? OR medication_code LIKE ? OR status LIKE ?
        LIMIT ?
        """,
        (search_term, search_term, search_term, per_table_limit),
    )
    results.extend([dict(row) for row in cursor.fetchall()])

    # Medication requests
    cursor.execute(
        """
        SELECT 'medication-request' as type, id, medication_display as title,
               (COALESCE(status,'') || ' • ' || COALESCE(priority,'')) as subtitle,
               patient_id
        FROM medication_request
        WHERE medication_display LIKE ? OR medication_code LIKE ? OR status LIKE ?
        LIMIT ?
        """,
        (search_term, search_term, search_term, per_table_limit),
    )
    results.extend([dict(row) for row in cursor.fetchall()])

    # Observations
    cursor.execute(
        """
        SELECT 'observation' as type, id, code_display as title,
               (COALESCE(observation_type,'') || ' • ' || COALESCE(status,'')) as subtitle,
               patient_id
        FROM observation
        WHERE code_display LIKE ? OR code LIKE ? OR observation_type LIKE ?
        LIMIT ?
        """,
        (search_term, search_term, search_term, per_table_limit),
    )
    results.extend([dict(row) for row in cursor.fetchall()])

    # Procedures
    cursor.execute(
        """
        SELECT 'procedure' as type, id, procedure_display as title,
               (COALESCE(procedure_code,'') || ' • ' || COALESCE(status,'')) as subtitle,
               patient_id
        FROM procedure
        WHERE procedure_display LIKE ? OR procedure_code LIKE ? OR status LIKE ?
        LIMIT ?
        """,
        (search_term, search_term, search_term, per_table_limit),
    )
    results.extend([dict(row) for row in cursor.fetchall()])

    # Specimens
    cursor.execute(
        """
        SELECT 'specimen' as type, id, specimen_type_display as title,
               (COALESCE(status,'') || ' • ' || COALESCE(body_site_display,'')) as subtitle,
               patient_id
        FROM specimen
        WHERE specimen_type_display LIKE ? OR body_site_display LIKE ? OR status LIKE ?
        LIMIT ?
        """,
        (search_term, search_term, search_term, per_table_limit),
    )
    results.extend([dict(row) for row in cursor.fetchall()])

    conn.close()

    # Trim to global limit
    return results[:limit]


@app.get("/search/patients", response_model=List[Dict])
def search_patients(q: str, limit: int = 50) -> List[Dict]:
    """Return distinct patients whose data matches the query anywhere.
    Searches core patient attributes and commonly searched columns in related tables.
    """
    if not q:
        return []

    search_term = f"%{q}%"
    conn = get_db_connection()
    cursor = conn.cursor()

    matched_patient_ids = set()

    # Match by patient attributes
    cursor.execute(
        """
        SELECT id as patient_id FROM patient
        WHERE family_name LIKE ? OR identifier LIKE ? OR id LIKE ? OR gender LIKE ?
        """,
        (search_term, search_term, search_term, search_term),
    )
    matched_patient_ids.update([row[0] for row in cursor.fetchall()])

    def add_matches(query: str, params: tuple):
        cursor.execute(query, params)
        matched_patient_ids.update([row[0] for row in cursor.fetchall()])

    # Related tables
    add_matches(
        "SELECT DISTINCT patient_id FROM condition WHERE code_display LIKE ? OR code LIKE ? OR category LIKE ?",
        (search_term, search_term, search_term),
    )
    add_matches(
        "SELECT DISTINCT patient_id FROM medication WHERE medication_display LIKE ? OR medication_code LIKE ? OR status LIKE ?",
        (search_term, search_term, search_term),
    )
    add_matches(
        "SELECT DISTINCT patient_id FROM encounter WHERE class_display LIKE ? OR encounter_type LIKE ? OR status LIKE ?",
        (search_term, search_term, search_term),
    )
    add_matches(
        "SELECT DISTINCT patient_id FROM medication_administration WHERE medication_display LIKE ? OR medication_code LIKE ? OR status LIKE ?",
        (search_term, search_term, search_term),
    )
    add_matches(
        "SELECT DISTINCT patient_id FROM medication_request WHERE medication_display LIKE ? OR medication_code LIKE ? OR status LIKE ?",
        (search_term, search_term, search_term),
    )
    add_matches(
        "SELECT DISTINCT patient_id FROM observation WHERE code_display LIKE ? OR code LIKE ? OR observation_type LIKE ?",
        (search_term, search_term, search_term),
    )
    add_matches(
        "SELECT DISTINCT patient_id FROM procedure WHERE procedure_display LIKE ? OR procedure_code LIKE ? OR status LIKE ?",
        (search_term, search_term, search_term),
    )
    add_matches(
        "SELECT DISTINCT patient_id FROM specimen WHERE specimen_type_display LIKE ? OR body_site_display LIKE ? OR status LIKE ?",
        (search_term, search_term, search_term),
    )

    if not matched_patient_ids:
        conn.close()
        return []

    # Fetch patient rows for matched ids
    placeholders = ",".join(["?"] * len(matched_patient_ids))
    cursor.execute(
        f"SELECT * FROM patient WHERE id IN ({placeholders}) LIMIT ?",
        (*matched_patient_ids, limit),
    )
    patients = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return patients

@app.get("/patients", response_model=List[Dict])
def list_patients():
    conn = get_db_connection()
    patients = conn.execute("SELECT * FROM patient").fetchall()
    conn.close()
    return [dict(row) for row in patients]

@app.get("/patients/{patient_id}", response_model=Dict)
def get_patient(patient_id: str):
    conn = get_db_connection()
    patient = conn.execute("SELECT * FROM patient WHERE id = ?", (patient_id,)).fetchone()
    conn.close()
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")
    return dict(patient)

@app.get("/conditions", response_model=List[Dict])
def list_conditions():
    conn = get_db_connection()
    conditions = conn.execute("SELECT * FROM condition").fetchall()
    conn.close()
    return [dict(row) for row in conditions]

@app.get("/conditions/{condition_id}", response_model=Dict)
def get_condition(condition_id: str):
    conn = get_db_connection()
    condition = conn.execute("SELECT * FROM condition WHERE id = ?", (condition_id,)).fetchone()
    conn.close()
    if not condition:
        raise HTTPException(status_code=404, detail="Condition not found")
    return dict(condition)

@app.get("/patients/{patient_id}/conditions", response_model=List[Dict])
def get_patient_conditions(patient_id: str):
    conn = get_db_connection()
    conditions = conn.execute("SELECT * FROM condition WHERE patient_id = ?", (patient_id,)).fetchall()
    conn.close()
    return [dict(row) for row in conditions]

@app.get("/medications", response_model=List[Dict])
def list_medications():
    conn = get_db_connection()
    medications = conn.execute("SELECT * FROM medication").fetchall()
    conn.close()
    return [dict(row) for row in medications]

@app.get("/medications/{medication_id}", response_model=Dict)
def get_medication(medication_id: str):
    conn = get_db_connection()
    medication = conn.execute("SELECT * FROM medication WHERE id = ?", (medication_id,)).fetchone()
    conn.close()
    if not medication:
        raise HTTPException(status_code=404, detail="Medication not found")
    return dict(medication)

@app.get("/patients/{patient_id}/medications", response_model=List[Dict])
def get_patient_medications(patient_id: str):
    conn = get_db_connection()
    medications = conn.execute("SELECT * FROM medication WHERE patient_id = ?", (patient_id,)).fetchall()
    conn.close()
    return [dict(row) for row in medications]

# Encounter endpoints
@app.get("/encounters", response_model=List[Dict])
def list_encounters():
    conn = get_db_connection()
    encounters = conn.execute("SELECT * FROM encounter").fetchall()
    conn.close()
    return [dict(row) for row in encounters]

@app.get("/encounters/{encounter_id}", response_model=Dict)
def get_encounter(encounter_id: str):
    conn = get_db_connection()
    encounter = conn.execute("SELECT * FROM encounter WHERE id = ?", (encounter_id,)).fetchone()
    conn.close()
    if not encounter:
        raise HTTPException(status_code=404, detail="Encounter not found")
    return dict(encounter)

@app.get("/patients/{patient_id}/encounters", response_model=List[Dict])
def get_patient_encounters(patient_id: str):
    conn = get_db_connection()
    encounters = conn.execute("SELECT * FROM encounter WHERE patient_id = ?", (patient_id,)).fetchall()
    conn.close()
    return [dict(row) for row in encounters]

# Medication Administration endpoints
@app.get("/medication-administrations", response_model=List[Dict])
def list_medication_administrations():
    conn = get_db_connection()
    administrations = conn.execute("SELECT * FROM medication_administration").fetchall()
    conn.close()
    return [dict(row) for row in administrations]

@app.get("/medication-administrations/{admin_id}", response_model=Dict)
def get_medication_administration(admin_id: str):
    conn = get_db_connection()
    administration = conn.execute("SELECT * FROM medication_administration WHERE id = ?", (admin_id,)).fetchone()
    conn.close()
    if not administration:
        raise HTTPException(status_code=404, detail="Medication administration not found")
    return dict(administration)

@app.get("/patients/{patient_id}/medication-administrations", response_model=List[Dict])
def get_patient_medication_administrations(patient_id: str):
    conn = get_db_connection()
    administrations = conn.execute("SELECT * FROM medication_administration WHERE patient_id = ?", (patient_id,)).fetchall()
    conn.close()
    return [dict(row) for row in administrations]

# Medication Request endpoints
@app.get("/medication-requests", response_model=List[Dict])
def list_medication_requests():
    conn = get_db_connection()
    requests = conn.execute("SELECT * FROM medication_request").fetchall()
    conn.close()
    return [dict(row) for row in requests]

@app.get("/medication-requests/{request_id}", response_model=Dict)
def get_medication_request(request_id: str):
    conn = get_db_connection()
    request = conn.execute("SELECT * FROM medication_request WHERE id = ?", (request_id,)).fetchone()
    conn.close()
    if not request:
        raise HTTPException(status_code=404, detail="Medication request not found")
    return dict(request)

@app.get("/patients/{patient_id}/medication-requests", response_model=List[Dict])
def get_patient_medication_requests(patient_id: str):
    conn = get_db_connection()
    requests = conn.execute("SELECT * FROM medication_request WHERE patient_id = ?", (patient_id,)).fetchall()
    conn.close()
    return [dict(row) for row in requests]

# Observation endpoints
@app.get("/observations", response_model=List[Dict])
def list_observations():
    conn = get_db_connection()
    observations = conn.execute("SELECT * FROM observation LIMIT 1000").fetchall()  # Limit for performance
    conn.close()
    return [dict(row) for row in observations]

@app.get("/observations/{observation_id}", response_model=Dict)
def get_observation(observation_id: str):
    conn = get_db_connection()
    observation = conn.execute("SELECT * FROM observation WHERE id = ?", (observation_id,)).fetchone()
    conn.close()
    if not observation:
        raise HTTPException(status_code=404, detail="Observation not found")
    return dict(observation)

@app.get("/patients/{patient_id}/observations", response_model=List[Dict])
def get_patient_observations(patient_id: str):
    conn = get_db_connection()
    observations = conn.execute("SELECT * FROM observation WHERE patient_id = ? LIMIT 500", (patient_id,)).fetchall()
    conn.close()
    return [dict(row) for row in observations]

# Procedure endpoints
@app.get("/procedures", response_model=List[Dict])
def list_procedures():
    conn = get_db_connection()
    procedures = conn.execute("SELECT * FROM procedure").fetchall()
    conn.close()
    return [dict(row) for row in procedures]

@app.get("/procedures/{procedure_id}", response_model=Dict)
def get_procedure(procedure_id: str):
    conn = get_db_connection()
    procedure = conn.execute("SELECT * FROM procedure WHERE id = ?", (procedure_id,)).fetchone()
    conn.close()
    if not procedure:
        raise HTTPException(status_code=404, detail="Procedure not found")
    return dict(procedure)

@app.get("/patients/{patient_id}/procedures", response_model=List[Dict])
def get_patient_procedures(patient_id: str):
    conn = get_db_connection()
    procedures = conn.execute("SELECT * FROM procedure WHERE patient_id = ?", (patient_id,)).fetchall()
    conn.close()
    return [dict(row) for row in procedures]

# Specimen endpoints
@app.get("/specimens", response_model=List[Dict])
def list_specimens():
    conn = get_db_connection()
    specimens = conn.execute("SELECT * FROM specimen").fetchall()
    conn.close()
    return [dict(row) for row in specimens]

@app.get("/specimens/{specimen_id}", response_model=Dict)
def get_specimen(specimen_id: str):
    conn = get_db_connection()
    specimen = conn.execute("SELECT * FROM specimen WHERE id = ?", (specimen_id,)).fetchone()
    conn.close()
    if not specimen:
        raise HTTPException(status_code=404, detail="Specimen not found")
    return dict(specimen)

@app.get("/patients/{patient_id}/specimens", response_model=List[Dict])
def get_patient_specimens(patient_id: str):
    conn = get_db_connection()
    specimens = conn.execute("SELECT * FROM specimen WHERE patient_id = ?", (patient_id,)).fetchall()
    conn.close()
    return [dict(row) for row in specimens]

# Dashboard endpoint for patient summary
@app.get("/patients/{patient_id}/summary", response_model=Dict)
def get_patient_summary(patient_id: str):
    conn = get_db_connection()
    
    # Get patient info
    patient = conn.execute("SELECT * FROM patient WHERE id = ?", (patient_id,)).fetchone()
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")
    
    # Get counts for each data type
    condition_count = conn.execute("SELECT COUNT(*) FROM condition WHERE patient_id = ?", (patient_id,)).fetchone()[0]
    medication_count = conn.execute("SELECT COUNT(*) FROM medication WHERE patient_id = ?", (patient_id,)).fetchone()[0]
    encounter_count = conn.execute("SELECT COUNT(*) FROM encounter WHERE patient_id = ?", (patient_id,)).fetchone()[0]
    medication_admin_count = conn.execute("SELECT COUNT(*) FROM medication_administration WHERE patient_id = ?", (patient_id,)).fetchone()[0]
    medication_request_count = conn.execute("SELECT COUNT(*) FROM medication_request WHERE patient_id = ?", (patient_id,)).fetchone()[0]
    observation_count = conn.execute("SELECT COUNT(*) FROM observation WHERE patient_id = ?", (patient_id,)).fetchone()[0]
    procedure_count = conn.execute("SELECT COUNT(*) FROM procedure WHERE patient_id = ?", (patient_id,)).fetchone()[0]
    specimen_count = conn.execute("SELECT COUNT(*) FROM specimen WHERE patient_id = ?", (patient_id,)).fetchone()[0]
    
    conn.close()
    
    return {
        "patient": dict(patient),
        "summary": {
            "conditions": condition_count,
            "medications": medication_count,
            "encounters": encounter_count,
            "medication_administrations": medication_admin_count,
            "medication_requests": medication_request_count,
            "observations": observation_count,
            "procedures": procedure_count,
            "specimens": specimen_count
        }
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
